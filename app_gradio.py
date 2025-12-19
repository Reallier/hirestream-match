# -*- coding: utf-8 -*-
"""
HireStream Match - Gradio 版本 v2

专业化 UI 设计：
- 右上角头像下拉菜单
- 两列布局（JD + 简历）
- 使用记录页面
- 设置页面（深浅主题）
"""

import gradio as gr
import time
import os
import json
from datetime import datetime, timedelta

from log import logger as log
from auth import verify_jwt_token, get_mock_user, UserInfo
from user_service import UserService, get_user_service
from match_engine import extract_text_from_upload, call_qwen_json
from token_calculator import TokenCalculator
from privacy_policy import PRIVACY_POLICY
from database import get_db_session, init_db
from models import User, MatchRecord, UsageRecord

# 初始化数据库
init_db()

# ========== 配置 ==========
QWEN_MODEL = os.getenv("QWEN_MODEL", "qwen3-235b-a22b")
USER_AUTH_MODE = os.getenv("USER_AUTH_MODE", "jwt")

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
    import uuid
    return f"req_{uuid.uuid4().hex[:12]}"


def get_user_from_token(token: str) -> UserInfo:
    if not token:
        if USER_AUTH_MODE == "mock":
            return get_mock_user()
        return None
    user_info = verify_jwt_token(token)
    if not user_info and USER_AUTH_MODE == "mock":
        return get_mock_user()
    return user_info


def ensure_user_exists(user_info: UserInfo):
    service = get_user_service()
    try:
        service.get_or_create_user(user_info)
        return service.get_user_summary(user_info.user_id)
    finally:
        service.db.close()


def check_user_consent(user_id: int) -> bool:
    with get_db_session() as db:
        user = db.query(User).filter(User.id == user_id).first()
        return user.consent_data_storage if user else None


def get_usage_records(user_id: int, limit: int = 20):
    """获取用户使用记录"""
    with get_db_session() as db:
        records = db.query(UsageRecord).filter(
            UsageRecord.user_id == user_id
        ).order_by(UsageRecord.created_at.desc()).limit(limit).all()
        return [{
            "time": r.created_at.strftime("%Y-%m-%d %H:%M"),
            "operation": r.operation,
            "model": r.model,
            "cost": float(r.cost or 0)
        } for r in records]


def get_match_history(user_id: int, limit: int = 10):
    """获取匹配历史"""
    with get_db_session() as db:
        records = db.query(MatchRecord).filter(
            MatchRecord.user_id == user_id
        ).order_by(MatchRecord.created_at.desc()).limit(limit).all()
        return [{
            "time": r.created_at.strftime("%Y-%m-%d %H:%M"),
            "score": r.match_score,
            "filename": r.resume_filename or "未命名",
            "cost": float(r.cost or 0)
        } for r in records]


# ========== 自定义 CSS ==========
LIGHT_THEME_CSS = """
:root {
    --bg-primary: #ffffff;
    --bg-secondary: #f8fafc;
    --bg-card: #ffffff;
    --text-primary: #1e293b;
    --text-secondary: #64748b;
    --border-color: #e2e8f0;
    --accent-color: #6366f1;
    --accent-gradient: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
}
"""

DARK_THEME_CSS = """
:root {
    --bg-primary: #0f172a;
    --bg-secondary: #1e293b;
    --bg-card: #1e293b;
    --text-primary: #f1f5f9;
    --text-secondary: #94a3b8;
    --border-color: #334155;
    --accent-color: #818cf8;
    --accent-gradient: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
}
"""

CUSTOM_CSS = """
/* 基础样式 */
.gradio-container {
    max-width: 1200px !important;
    margin: 0 auto !important;
    background: var(--bg-primary) !important;
}

/* 顶部导航 */
.header-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 24px;
    background: var(--bg-card);
    border-bottom: 1px solid var(--border-color);
    border-radius: 12px;
    margin-bottom: 24px;
}

.header-logo {
    display: flex;
    align-items: center;
    gap: 12px;
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--text-primary);
}

.header-logo span {
    background: var(--accent-gradient);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

/* 用户菜单 */
.user-menu {
    position: relative;
    display: inline-block;
}

.user-avatar {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    cursor: pointer;
    border: 2px solid var(--border-color);
    transition: all 0.2s;
}

.user-avatar:hover {
    border-color: var(--accent-color);
}

.user-dropdown {
    display: none;
    position: absolute;
    right: 0;
    top: 48px;
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 12px 0;
    min-width: 200px;
    box-shadow: 0 10px 40px rgba(0,0,0,0.15);
    z-index: 1000;
}

.user-menu:hover .user-dropdown {
    display: block;
}

.dropdown-header {
    padding: 12px 16px;
    border-bottom: 1px solid var(--border-color);
}

.dropdown-name {
    font-weight: 600;
    color: var(--text-primary);
    font-size: 14px;
}

.dropdown-balance {
    font-size: 12px;
    color: var(--text-secondary);
    margin-top: 4px;
}

.dropdown-balance strong {
    color: var(--accent-color);
    font-size: 16px;
}

.dropdown-item {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 16px;
    color: var(--text-primary);
    text-decoration: none;
    font-size: 14px;
    cursor: pointer;
    transition: background 0.2s;
}

.dropdown-item:hover {
    background: var(--bg-secondary);
}

/* 卡片 */
.card {
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 20px;
}

.card-title {
    font-size: 16px;
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    gap: 8px;
}

/* 分析按钮 */
.analyze-btn {
    background: var(--accent-gradient) !important;
    border: none !important;
    color: white !important;
    font-weight: 600 !important;
    padding: 14px 32px !important;
    font-size: 16px !important;
    border-radius: 10px !important;
    cursor: pointer !important;
    transition: transform 0.2s, box-shadow 0.2s !important;
}

.analyze-btn:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 20px rgba(99, 102, 241, 0.3) !important;
}

/* 结果区域 */
.result-score {
    text-align: center;
    padding: 24px;
    background: var(--accent-gradient);
    border-radius: 12px;
    color: white;
}

.result-score .score-number {
    font-size: 48px;
    font-weight: 700;
}

.result-score .score-label {
    font-size: 14px;
    opacity: 0.9;
}

/* 三栏结果 */
.result-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
    margin-top: 20px;
}

.result-column {
    background: var(--bg-secondary);
    border-radius: 10px;
    padding: 16px;
}

.result-column h4 {
    font-size: 14px;
    font-weight: 600;
    margin-bottom: 12px;
    color: var(--text-primary);
}

.result-column ul {
    list-style: none;
    padding: 0;
    margin: 0;
}

.result-column li {
    font-size: 13px;
    color: var(--text-secondary);
    padding: 6px 0;
    border-bottom: 1px solid var(--border-color);
}

.result-column li:last-child {
    border-bottom: none;
}

/* 使用记录表格 */
.usage-table {
    width: 100%;
    border-collapse: collapse;
}

.usage-table th, .usage-table td {
    padding: 12px 16px;
    text-align: left;
    border-bottom: 1px solid var(--border-color);
    font-size: 13px;
}

.usage-table th {
    color: var(--text-secondary);
    font-weight: 500;
}

.usage-table td {
    color: var(--text-primary);
}
"""


# ========== 核心分析函数 ==========
def analyze_match(jd_text: str, resume_file, token: str, progress=gr.Progress()):
    """执行简历匹配分析"""
    
    user_info = get_user_from_token(token)
    if not user_info:
        return None, "❌ 请先登录", "", ""
    
    user_summary = ensure_user_exists(user_info)
    
    if user_summary["total_available"] <= 0:
        return None, "❌ 余额不足，请充值后使用", "", ""
    
    if not jd_text or not jd_text.strip():
        return None, "⚠️ 请输入职位描述", "", ""
    
    if resume_file is None:
        return None, "⚠️ 请上传简历文件", "", ""
    
    progress(0.1, desc="正在解析简历...")
    
    try:
        resume_text, ocr_usage = extract_text_from_upload(resume_file.name)
        if not resume_text:
            return None, "❌ 简历解析失败", "", ""
    except Exception as e:
        log.exception("resume_parse_failed")
        return None, f"❌ 简历解析错误: {str(e)}", "", ""
    
    progress(0.3, desc="正在分析匹配度...")
    
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
        
        service.record_usage(
            user_id=user_info.user_id,
            request_id=request_id,
            operation="analysis",
            model=token_usage.get("model", QWEN_MODEL),
            prompt_tokens=token_usage.get("prompt_tokens", 0),
            completion_tokens=token_usage.get("completion_tokens", 0),
            cost=analysis_cost
        )
        
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
        
        deduct_result = service.deduct_balance(
            user_id=user_info.user_id,
            cost=total_cost,
            reference_id=request_id,
            remark=f"简历匹配分析 (匹配度 {score}%)"
        )
        
        progress(0.9, desc="正在生成报告...")
        
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
            except Exception as e:
                log.warning("match_record_save_failed | error={}", str(e))
        
        ms = int((time.perf_counter() - t0) * 1000)
        
        # 格式化结果
        score_html = f"""
        <div class="result-score">
            <div class="score-number">{score}%</div>
            <div class="score-label">匹配度</div>
        </div>
        """
        
        strengths = result.get("strengths", [])
        risks = result.get("risks", [])
        suggestions = result.get("suggestions", [])
        
        result_html = f"""
        <div class="result-grid">
            <div class="result-column">
                <h4>✅ 优势</h4>
                <ul>{"".join([f'<li>{s}</li>' for s in strengths])}</ul>
            </div>
            <div class="result-column">
                <h4>⚠️ 风险</h4>
                <ul>{"".join([f'<li>{r}</li>' for r in risks])}</ul>
            </div>
            <div class="result-column">
                <h4>💡 建议</h4>
                <ul>{"".join([f'<li>{s}</li>' for s in suggestions])}</ul>
            </div>
        </div>
        """
        
        detail_md = f"""
### 📋 详细分析

{result.get("detail_analysis", "")}

---
*本次分析消耗: ¥{total_cost:.4f} | 耗时: {ms}ms*
"""
        
        return score, score_html, result_html, detail_md
        
    except Exception as e:
        log.exception("analysis_failed")
        return None, f"❌ 分析失败: {str(e)}", "", ""
    finally:
        service.db.close()


def render_header(user_info, user_summary):
    """渲染顶部导航"""
    if not user_info:
        return """
        <div class="header-bar">
            <div class="header-logo">🧲 <span>HireStream Match</span></div>
            <div style="color: var(--text-secondary);">未登录</div>
        </div>
        """
    
    avatar = user_info.avatar_url or f"https://api.dicebear.com/7.x/avataaars/svg?seed={user_info.user_id}"
    
    return f"""
    <div class="header-bar">
        <div class="header-logo">🧲 <span>HireStream Match</span></div>
        <div class="user-menu">
            <img src="{avatar}" alt="avatar" class="user-avatar" />
            <div class="user-dropdown">
                <div class="dropdown-header">
                    <div class="dropdown-name">{user_info.nickname}</div>
                    <div class="dropdown-balance">
                        可用余额 <strong>¥{user_summary['total_available']:.2f}</strong>
                    </div>
                </div>
                <div class="dropdown-item" onclick="document.querySelector('[data-tab-id=usage]')?.click()">
                    📊 使用记录
                </div>
                <div class="dropdown-item" onclick="document.querySelector('[data-tab-id=settings]')?.click()">
                    ⚙️ 设置
                </div>
                <div class="dropdown-item" onclick="window.location.href='https://intjtech.reallier.top'">
                    🚪 返回官网
                </div>
            </div>
        </div>
    </div>
    """


def render_usage_table(user_id: int):
    """渲染使用记录"""
    records = get_usage_records(user_id, 20)
    if not records:
        return "<p style='color: var(--text-secondary); text-align: center; padding: 40px;'>暂无使用记录</p>"
    
    rows = ""
    for r in records:
        rows += f"""
        <tr>
            <td>{r['time']}</td>
            <td>{r['operation']}</td>
            <td>{r['model']}</td>
            <td>¥{r['cost']:.4f}</td>
        </tr>
        """
    
    return f"""
    <table class="usage-table">
        <thead>
            <tr>
                <th>时间</th>
                <th>操作</th>
                <th>模型</th>
                <th>费用</th>
            </tr>
        </thead>
        <tbody>{rows}</tbody>
    </table>
    """


def render_history_table(user_id: int):
    """渲染匹配历史"""
    records = get_match_history(user_id, 10)
    if not records:
        return "<p style='color: var(--text-secondary); text-align: center; padding: 40px;'>暂无匹配历史</p>"
    
    rows = ""
    for r in records:
        rows += f"""
        <tr>
            <td>{r['time']}</td>
            <td>{r['filename']}</td>
            <td><strong>{r['score']}%</strong></td>
            <td>¥{r['cost']:.4f}</td>
        </tr>
        """
    
    return f"""
    <table class="usage-table">
        <thead>
            <tr>
                <th>时间</th>
                <th>简历</th>
                <th>匹配度</th>
                <th>费用</th>
            </tr>
        </thead>
        <tbody>{rows}</tbody>
    </table>
    """


# ========== 构建界面 ==========
def create_app():
    
    with gr.Blocks(
        title="HireStream Match - 简历智能匹配",
        css=LIGHT_THEME_CSS + CUSTOM_CSS,
        theme=gr.themes.Soft(
            primary_hue="indigo",
            secondary_hue="purple",
            neutral_hue="slate"
        )
    ) as demo:
        
        # 状态
        token_state = gr.State("")
        user_info_state = gr.State(None)
        user_summary_state = gr.State({})
        
        # 顶部导航
        header_html = gr.HTML("")
        
        # 标签页
        with gr.Tabs() as tabs:
            
            # ===== 匹配分析页 =====
            with gr.Tab("🧲 匹配分析", id="match"):
                with gr.Row(equal_height=True):
                    with gr.Column(scale=1):
                        gr.Markdown("### 📝 职位描述")
                        jd_input = gr.Textbox(
                            placeholder="请粘贴完整的职位描述 (JD)...\n\n包括：\n• 职位名称\n• 工作职责\n• 任职要求\n• 薪资福利",
                            lines=15,
                            max_lines=25,
                            show_label=False,
                            container=False
                        )
                    
                    with gr.Column(scale=1):
                        gr.Markdown("### 📄 简历上传")
                        resume_upload = gr.File(
                            label="",
                            file_types=[".pdf", ".png", ".jpg", ".jpeg", ".doc", ".docx"],
                            type="filepath"
                        )
                        gr.Markdown("*支持 PDF、图片、Word 格式，最大 10MB*")
                
                analyze_btn = gr.Button(
                    "🚀 开始匹配分析",
                    variant="primary",
                    size="lg",
                    elem_classes=["analyze-btn"]
                )
                
                gr.Markdown("---")
                gr.Markdown("### 📊 匹配结果")
                
                with gr.Row():
                    with gr.Column(scale=1):
                        score_output = gr.Slider(
                            label="匹配度",
                            minimum=0,
                            maximum=100,
                            value=0,
                            interactive=False,
                            visible=False
                        )
                        score_html = gr.HTML("")
                    
                with gr.Row():
                    result_html = gr.HTML("")
                
                report_md = gr.Markdown("*请上传简历并输入 JD 后点击分析*")
            
            # ===== 使用记录页 =====
            with gr.Tab("📊 使用记录", id="usage"):
                gr.Markdown("### 📊 使用记录")
                usage_html = gr.HTML("<p style='text-align: center; color: #888;'>加载中...</p>")
                refresh_usage_btn = gr.Button("🔄 刷新", size="sm")
                
                gr.Markdown("---")
                gr.Markdown("### 📋 匹配历史")
                history_html = gr.HTML("<p style='text-align: center; color: #888;'>加载中...</p>")
            
            # ===== 设置页 =====
            with gr.Tab("⚙️ 设置", id="settings"):
                gr.Markdown("### ⚙️ 设置")
                
                with gr.Group():
                    gr.Markdown("#### 🎨 主题")
                    theme_radio = gr.Radio(
                        choices=["浅色", "深色"],
                        value="浅色",
                        label="界面主题",
                        interactive=True
                    )
                
                with gr.Group():
                    gr.Markdown("#### 📋 数据存储")
                    consent_checkbox = gr.Checkbox(
                        label="同意存储匹配数据用于服务改进",
                        value=False,
                        interactive=True
                    )
                    gr.Markdown("*存储的数据包括：简历内容、JD、匹配报告。用于改进 AI 匹配准确度。*")
                
                with gr.Accordion("📋 隐私政策", open=False):
                    gr.Markdown(PRIVACY_POLICY)
        
        # ===== 事件绑定 =====
        
        def on_load(request: gr.Request):
            """页面加载"""
            token = request.query_params.get("token", "")
            user_info = None
            user_summary = {}
            header = ""
            consent = False
            
            if token:
                user_info = get_user_from_token(token)
            
            if not user_info and USER_AUTH_MODE == "mock":
                user_info = get_mock_user()
                token = "mock"
            
            if user_info:
                user_summary = ensure_user_exists(user_info)
                header = render_header(user_info, user_summary)
                consent = check_user_consent(user_info.user_id) or False
            else:
                header = render_header(None, {})
            
            return token, user_info, user_summary, header, consent
        
        demo.load(
            on_load,
            inputs=None,
            outputs=[token_state, user_info_state, user_summary_state, header_html, consent_checkbox]
        )
        
        # 分析按钮
        analyze_btn.click(
            analyze_match,
            inputs=[jd_input, resume_upload, token_state],
            outputs=[score_output, score_html, result_html, report_md]
        )
        
        # 刷新使用记录
        def refresh_usage(user_info):
            if not user_info:
                return "<p>请先登录</p>", "<p>请先登录</p>"
            return render_usage_table(user_info.user_id), render_history_table(user_info.user_id)
        
        refresh_usage_btn.click(
            refresh_usage,
            inputs=[user_info_state],
            outputs=[usage_html, history_html]
        )
        
        # 页面切换时加载数据
        tabs.select(
            lambda user_info, evt: refresh_usage(user_info) if evt.value == "usage" else (gr.skip(), gr.skip()),
            inputs=[user_info_state],
            outputs=[usage_html, history_html]
        )
        
        # 保存同意状态
        def save_consent(consent, user_info):
            if user_info:
                with get_db_session() as db:
                    user = db.query(User).filter(User.id == user_info.user_id).first()
                    if user:
                        user.consent_data_storage = consent
                        user.consent_updated_at = datetime.utcnow()
                        db.commit()
            return consent
        
        consent_checkbox.change(
            save_consent,
            inputs=[consent_checkbox, user_info_state],
            outputs=[consent_checkbox]
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
