# -*- coding: utf-8 -*-
"""
HireStream Match - Gradio 版本

基于 Gradio 的现代化简历匹配工具界面
"""

import gradio as gr
import time
import os
from datetime import datetime

from log import logger as log
from auth import verify_jwt_token, get_mock_user, UserInfo
from user_service import UserService, get_user_service
from match_engine import extract_text_from_upload, call_qwen_json
from token_calculator import TokenCalculator
from privacy_policy import PRIVACY_POLICY, CONSENT_DIALOG_CONTENT
from database import get_db_session, init_db
from models import User, MatchRecord

# 初始化数据库
init_db()

# ========== 配置 ==========
QWEN_MODEL = os.getenv("QWEN_MODEL", "qwen3-235b-a22b")
USER_AUTH_MODE = os.getenv("USER_AUTH_MODE", "jwt")  # jwt / mock

# 匹配分析的 system prompt
SYSTEM_PROMPT = """你是专业的HR招聘专家，擅长分析简历与职位描述(JD)的匹配程度。
请仔细分析候选人简历与目标职位的匹配情况，从多个维度给出专业评估。"""

USER_TEMPLATE = """## 职位描述 (JD)
{job_description}

## 候选人简历
{resume_content}

请分析以上简历与职位的匹配程度，返回JSON格式：
{{
    "match_score": 85,
    "summary": "一句话总结匹配情况",
    "strengths": ["优势1", "优势2", "优势3"],
    "risks": ["风险1", "风险2"],
    "suggestions": ["建议1", "建议2"],
    "detail_analysis": "详细分析..."
}}"""


# ========== 工具函数 ==========
def generate_request_id():
    """生成唯一请求ID"""
    import uuid
    return f"req_{uuid.uuid4().hex[:12]}"


def get_user_from_token(token: str) -> UserInfo:
    """从 token 获取用户信息"""
    if not token:
        if USER_AUTH_MODE == "mock":
            return get_mock_user()
        return None
    
    user_info = verify_jwt_token(token)
    if not user_info and USER_AUTH_MODE == "mock":
        return get_mock_user()
    return user_info


def ensure_user_exists(user_info: UserInfo):
    """确保用户在数据库中存在"""
    service = get_user_service()
    try:
        service.get_or_create_user(user_info)
        return service.get_user_summary(user_info.user_id)
    finally:
        service.db.close()


def check_user_consent(user_id: int) -> bool:
    """检查用户是否同意数据存储"""
    with get_db_session() as db:
        user = db.query(User).filter(User.id == user_id).first()
        return user.consent_data_storage if user else None


def save_user_consent(user_id: int, consent: bool):
    """保存用户同意状态"""
    with get_db_session() as db:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.consent_data_storage = consent
            user.consent_updated_at = datetime.utcnow()
            db.commit()


# ========== 核心分析函数 ==========
def analyze_match(jd_text: str, resume_file, token: str, progress=gr.Progress()):
    """执行简历匹配分析"""
    
    # 1. 验证用户
    user_info = get_user_from_token(token)
    if not user_info:
        return None, "❌ 请先登录", "", ""
    
    # 确保用户存在
    user_summary = ensure_user_exists(user_info)
    
    # 2. 检查余额
    if user_summary["total_available"] <= 0:
        return None, "❌ 余额不足，请充值后使用", "", ""
    
    # 3. 验证输入
    if not jd_text or not jd_text.strip():
        return None, "⚠️ 请输入职位描述", "", ""
    
    if resume_file is None:
        return None, "⚠️ 请上传简历文件", "", ""
    
    progress(0.1, desc="正在解析简历...")
    
    # 4. 提取简历文本
    try:
        resume_text, ocr_usage = extract_text_from_upload(resume_file.name)
        if not resume_text:
            return None, "❌ 简历解析失败，请检查文件格式", "", ""
    except Exception as e:
        log.exception("resume_parse_failed")
        return None, f"❌ 简历解析错误: {str(e)}", "", ""
    
    progress(0.3, desc="正在分析匹配度...")
    
    # 5. 调用 AI 分析
    service = get_user_service()
    try:
        request_id = generate_request_id()
        t0 = time.perf_counter()
        
        user_prompt = USER_TEMPLATE.format(
            job_description=jd_text.strip(),
            resume_content=resume_text.strip()
        )
        
        result = call_qwen_json(user_prompt=user_prompt)
        result["request_id"] = request_id
        
        score = int(result.get("match_score", 0))
        token_usage = result.get("token_usage", {})
        analysis_cost = token_usage.get("cost", 0)
        
        progress(0.7, desc="正在记录使用量...")
        
        # 记录使用量
        service.record_usage(
            user_id=user_info.user_id,
            request_id=request_id,
            operation="analysis",
            model=token_usage.get("model", QWEN_MODEL),
            prompt_tokens=token_usage.get("prompt_tokens", 0),
            completion_tokens=token_usage.get("completion_tokens", 0),
            cost=analysis_cost
        )
        
        # OCR 使用量
        total_cost = analysis_cost
        if ocr_usage:
            ocr_request_id = generate_request_id()
            ocr_cost = ocr_usage.get("cost", 0)
            service.record_usage(
                user_id=user_info.user_id,
                request_id=ocr_request_id,
                operation="ocr",
                model=ocr_usage.get("model", "qwen-vl-ocr"),
                prompt_tokens=ocr_usage.get("prompt_tokens", 0),
                completion_tokens=ocr_usage.get("completion_tokens", 0),
                cost=ocr_cost
            )
            total_cost += ocr_cost
        
        # 扣费
        deduct_result = service.deduct_balance(
            user_id=user_info.user_id,
            cost=total_cost,
            reference_id=request_id,
            remark=f"简历匹配分析 (匹配度 {score}%)"
        )
        
        progress(0.9, desc="正在生成报告...")
        
        # 如果用户同意，保存匹配记录
        if check_user_consent(user_info.user_id):
            try:
                match_record = MatchRecord(
                    user_id=user_info.user_id,
                    jd_text=jd_text.strip(),
                    resume_text=resume_text.strip(),
                    resume_filename=os.path.basename(resume_file.name) if resume_file else None,
                    match_score=score,
                    report_json=result,
                    prompt_tokens=token_usage.get("prompt_tokens", 0),
                    completion_tokens=token_usage.get("completion_tokens", 0),
                    cost=total_cost
                )
                service.db.add(match_record)
                service.db.commit()
                log.info("match_record_saved | user_id={} | score={}", user_info.user_id, score)
            except Exception as e:
                log.warning("match_record_save_failed | error={}", str(e))
        
        ms = int((time.perf_counter() - t0) * 1000)
        log.info("analysis_complete | score={} | ms={} | cost={}", score, ms, total_cost)
        
        # 格式化结果
        score_display = f"## 🎯 匹配度: {score}%"
        
        strengths_md = "### ✅ 优势\n" + "\n".join([f"- {s}" for s in result.get("strengths", [])])
        risks_md = "### ⚠️ 风险\n" + "\n".join([f"- {r}" for r in result.get("risks", [])])
        suggestions_md = "### 💡 建议\n" + "\n".join([f"- {s}" for s in result.get("suggestions", [])])
        
        detail_md = f"""
### 📋 详细分析

{result.get("detail_analysis", "")}

---
*本次分析消耗: ¥{total_cost:.4f} | 耗时: {ms}ms*
"""
        
        full_report = f"{strengths_md}\n\n{risks_md}\n\n{suggestions_md}\n\n{detail_md}"
        
        return score, score_display, result.get("summary", ""), full_report
        
    except Exception as e:
        log.exception("analysis_failed")
        return None, f"❌ 分析失败: {str(e)}", "", ""
    finally:
        service.db.close()


def get_user_info_display(token: str):
    """获取用户信息显示"""
    user_info = get_user_from_token(token)
    if not user_info:
        return "未登录", "¥0.00", "¥0.00"
    
    summary = ensure_user_exists(user_info)
    return (
        f"👤 {user_info.nickname}",
        f"¥{summary['balance']:.2f}",
        f"¥{summary['total_available']:.2f}"
    )


# ========== 自定义 CSS ==========
CUSTOM_CSS = """
/* 全局样式 */
.gradio-container {
    max-width: 1200px !important;
    margin: auto;
}

/* 标题 */
.app-title {
    text-align: center;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 2.5rem;
    font-weight: 700;
    margin-bottom: 0.5rem;
}

/* 匹配分数 */
.score-display {
    text-align: center;
    font-size: 3rem;
    font-weight: bold;
    padding: 20px;
    border-radius: 16px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
}

/* 卡片样式 */
.info-card {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 12px;
    padding: 16px;
    border: 1px solid rgba(255, 255, 255, 0.1);
}

/* 按钮 */
.primary-btn {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    border: none !important;
    font-weight: 600 !important;
}
"""


# ========== 构建 Gradio 界面 ==========
def create_app():
    with gr.Blocks(
        title="HireStream Match - 简历智能匹配",
        theme=gr.themes.Soft(
            primary_hue="purple",
            secondary_hue="blue",
            neutral_hue="slate",
        ),
        css=CUSTOM_CSS
    ) as demo:
        
        # Token 状态（从 URL 参数获取）
        token_state = gr.State("")
        
        # ===== 头部 =====
        gr.HTML("""
        <div style="text-align: center; padding: 20px 0;">
            <h1 class="app-title">🧲 HireStream Match</h1>
            <p style="color: #888; font-size: 1.1rem;">AI 驱动的简历与职位智能匹配分析</p>
        </div>
        """)
        
        with gr.Row():
            # ===== 左侧：用户信息 =====
            with gr.Column(scale=1):
                gr.Markdown("### 👤 账户信息")
                user_name = gr.Textbox(label="用户", value="未登录", interactive=False)
                user_balance = gr.Textbox(label="余额", value="¥0.00", interactive=False)
                user_available = gr.Textbox(label="可用", value="¥0.00", interactive=False)
                
                refresh_btn = gr.Button("🔄 刷新", size="sm")
            
            # ===== 中间：输入区 =====
            with gr.Column(scale=2):
                gr.Markdown("### 📝 职位描述 (JD)")
                jd_input = gr.Textbox(
                    placeholder="请粘贴完整的职位描述...\n\n包括：职位名称、职责要求、任职资格、薪资福利等",
                    lines=12,
                    max_lines=20,
                    show_label=False
                )
            
            # ===== 右侧：上传区 =====
            with gr.Column(scale=2):
                gr.Markdown("### 📄 简历上传")
                resume_upload = gr.File(
                    label="上传简历",
                    file_types=[".pdf", ".png", ".jpg", ".jpeg", ".doc", ".docx"],
                    type="filepath"
                )
                gr.Markdown("*支持 PDF、图片、Word 格式*", elem_classes=["text-muted"])
        
        # ===== 分析按钮 =====
        with gr.Row():
            analyze_btn = gr.Button(
                "🚀 开始匹配分析",
                variant="primary",
                size="lg",
                elem_classes=["primary-btn"]
            )
        
        # ===== 结果区 =====
        gr.Markdown("---")
        gr.Markdown("### 📊 匹配结果")
        
        with gr.Row():
            with gr.Column(scale=1):
                score_output = gr.Slider(
                    label="匹配度",
                    minimum=0,
                    maximum=100,
                    value=0,
                    interactive=False
                )
                score_md = gr.Markdown("")
            
            with gr.Column(scale=1):
                summary_output = gr.Textbox(
                    label="总结",
                    lines=3,
                    interactive=False
                )
        
        report_output = gr.Markdown(
            label="详细报告",
            value="*请上传简历并输入 JD 后点击分析*"
        )
        
        # ===== 底部信息 =====
        with gr.Accordion("📋 数据使用说明", open=False):
            gr.Markdown(PRIVACY_POLICY)
        
        gr.HTML("""
        <div style="text-align: center; padding: 20px; color: #666; font-size: 0.9rem;">
            © 2025 简序智能 · AI Agent 技术服务
        </div>
        """)
        
        # ===== 事件绑定 =====
        
        # 页面加载时获取 token（从 URL query 参数）
        def on_load(request: gr.Request):
            token = request.query_params.get("token", "")
            if token:
                user_info = get_user_from_token(token)
                if user_info:
                    summary = ensure_user_exists(user_info)
                    return (
                        token,
                        f"👤 {user_info.nickname}",
                        f"¥{summary['balance']:.2f}",
                        f"¥{summary['total_available']:.2f}"
                    )
            # Mock 模式
            if USER_AUTH_MODE == "mock":
                user_info = get_mock_user()
                summary = ensure_user_exists(user_info)
                return (
                    "mock",
                    f"👤 {user_info.nickname}",
                    f"¥{summary['balance']:.2f}",
                    f"¥{summary['total_available']:.2f}"
                )
            return "", "未登录", "¥0.00", "¥0.00"
        
        demo.load(
            on_load,
            inputs=None,
            outputs=[token_state, user_name, user_balance, user_available]
        )
        
        # 刷新用户信息
        def refresh_user(token):
            return get_user_info_display(token)
        
        refresh_btn.click(
            refresh_user,
            inputs=[token_state],
            outputs=[user_name, user_balance, user_available]
        )
        
        # 分析按钮
        analyze_btn.click(
            analyze_match,
            inputs=[jd_input, resume_upload, token_state],
            outputs=[score_output, score_md, summary_output, report_output]
        )
    
    return demo


# ========== 启动 ==========
if __name__ == "__main__":
    demo = create_app()
    demo.queue(max_size=100, default_concurrency_limit=5)
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )
