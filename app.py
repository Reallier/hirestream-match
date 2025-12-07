# -*- coding: utf-8 -*-
import os
import uuid
import time
import streamlit as st
from dotenv import load_dotenv
import toml  # Import toml library

from match_engine import extract_text_from_upload, call_qwen_json
from utils import hash_inputs, render_markdown_report
from log import logger as log
from token_calculator import TokenCalculator
from pricing_config import get_model_display_name

# 用户模块
from database import init_db
from auth import authenticate_user, UserInfo
from user_service import UserService, get_user_service, generate_request_id


# -------- Env --------
load_dotenv()
USER_TEMPLATE = os.getenv("USER_TEMPLATE")
QWEN_MODEL = os.getenv("QWEN_MODEL")


# -------- 数据库初始化 --------
@st.cache_resource
def init_database():
    """初始化数据库（只执行一次）"""
    init_db()
    return True

init_database()


# -------- 用户认证 --------
def get_current_user() -> UserInfo | None:
    """
    获取当前登录用户
    
    优先从 session_state 获取，其次从 URL 参数或 Cookie 认证
    """
    # 如果已经认证过，直接返回
    if "current_user" in st.session_state and st.session_state["current_user"]:
        return st.session_state["current_user"]
    
    # 从 URL 参数获取 token 或 mock_user
    query_params = st.query_params
    token = query_params.get("token")
    mock_id = query_params.get("mock_user")
    
    # 认证用户
    user_info = authenticate_user(token=token, mock_id=mock_id)
    
    if user_info:
        st.session_state["current_user"] = user_info
        log.info("user_authenticated | user_id={}", user_info.user_id)
    
    return user_info


def ensure_user_exists(user_info: UserInfo) -> dict:
    """确保用户在数据库中存在，返回用户概览"""
    service = get_user_service()
    try:
        service.get_or_create_user(user_info)
        return service.get_user_summary(user_info.user_id)
    finally:
        service.db.close()


# -------- Page Config --------
st.set_page_config(page_title="HireStream Match — 简历与JD智能匹配", page_icon="🧲", layout="centered")


# -------- 用户状态检查 --------
current_user = get_current_user()

if not current_user:
    st.error("⚠️ 请先登录")
    st.markdown("""
    ### 如何使用
    
    1. 从官网登录后访问本服务
    2. 或在开发模式下，访问 `?mock_user=test_user_001` 进行测试
    
    [返回官网登录](#)
    """)
    st.stop()

# 获取/创建用户并加载概览
user_summary = ensure_user_exists(current_user)


# -------- 侧边栏：用户信息 --------
with st.sidebar:
    st.markdown("### 👤 用户信息")
    
    # 用户头像和昵称
    col1, col2 = st.columns([1, 3])
    with col1:
        if current_user.avatar_url:
            st.image(current_user.avatar_url, width=50)
        else:
            st.markdown("👤")
    with col2:
        st.markdown(f"**{current_user.nickname}**")
        st.caption(f"ID: {current_user.user_id[:8]}...")
    
    st.markdown("---")
    
    # 账户余额
    st.markdown("### 💰 账户余额")
    balance = user_summary.get("balance", 0)
    free_quota = user_summary.get("free_quota", 0)
    total_available = user_summary.get("total_available", 0)
    
    st.metric("可用余额", f"¥{total_available:.4f}")
    
    col1, col2 = st.columns(2)
    with col1:
        st.caption(f"充值余额: ¥{balance:.4f}")
    with col2:
        st.caption(f"免费额度: ¥{free_quota:.4f}")
    
    # 余额不足警告
    if total_available < 0.01:
        st.warning("⚠️ 余额不足，请充值")
    
    st.markdown("---")
    
    # 今日使用统计
    st.markdown("### 📊 今日统计")
    today = user_summary.get("today", {})
    col1, col2 = st.columns(2)
    with col1:
        st.metric("调用次数", today.get("count", 0))
    with col2:
        st.metric("消费金额", f"¥{today.get('cost', 0):.4f}")
    
    # 刷新按钮
    if st.button("🔄 刷新余额", use_container_width=True):
        # 清除缓存的用户概览
        if "user_summary_cache" in st.session_state:
            del st.session_state["user_summary_cache"]
        st.rerun()


# -------- 主内容区 --------
st.caption("提示：粘贴JD + 上传简历后，会自动分析，无需点击按钮。")

# --- JD Block ---
with st.container(border=True):
    jd_text = st.text_area(
        "职位描述（JD）",
        height=220,
        placeholder="在此粘贴JD文本……",
        key="jd_text"
    )

    # 若内容非空且刚刚变化，则自动处理
    if jd_text and st.session_state.get("jd_last") != jd_text:
        st.session_state["jd_last"] = jd_text
        st.toast("✅ JD 已自动更新！")  # 右上角弹出提示框（自动消失）

# --- Resume Block ---
resume_text = ""
with st.container(border=True):
    # 文件上传组件
    up = st.file_uploader(
        "上传候选人简历（PDF 或 图片格式 ≤ 2MB）",
        type=["pdf", "jpg", "jpeg", "png", "gif", "bmp", "webp"],
        accept_multiple_files=False,
        key="resume_file",
        help="支持 PDF 和常见图片格式（JPG/PNG/GIF/BMP/WEBP）"
    )

    # 添加分割线
    st.markdown("---")

    # 文本输入框
    resume_text_input = st.text_area(
        "或在此粘贴简历文本",
        height=220,
        placeholder="在此粘贴简历文本……",
        key="resume_text"
    )

    # 若文本内容非空且刚刚变化，则自动处理
    if resume_text_input and st.session_state.get("resume_text_last") != resume_text_input:
        st.session_state["resume_text_last"] = resume_text_input
        st.toast("✅ 简历文本已自动更新！")  # 右上角弹出提示框（自动消失）

    # 处理简历内容获取逻辑
    # 优先使用文本输入，其次使用文件上传
    if resume_text_input.strip():
        resume_text = resume_text_input.strip()
        st.session_state["ocr_usage"] = None  # 文本输入不需要 OCR
    elif up is not None:
        log.info("upload_received | name={} size={}", up.name, up.size)
        with st.status("正在识别…", expanded=True) as status:
            if up.size > 2 * 1024 * 1024:
                status.update(label="文件过大", state="error")
                st.error("文件过大：需 ≤ 2MB。")
                log.warning("upload_rejected | reason=file_too_large | size={}", up.size)
            else:
                try:
                    resume_text, ocr_usage = extract_text_from_upload(up.name, up.read())
                    # 计算 OCR 费用
                    ocr_prompt = ocr_usage.get("prompt_tokens", 0)
                    ocr_completion = ocr_usage.get("completion_tokens", 0)
                    ocr_model = ocr_usage.get("model", "qwen-vl-ocr-2025-11-20")
                    ocr_cost = TokenCalculator.calculate_cost(ocr_model, ocr_prompt, ocr_completion)
                    ocr_usage["cost"] = ocr_cost
                    ocr_usage["request_id"] = generate_request_id()  # 生成请求ID用于记录
                    st.session_state["ocr_usage"] = ocr_usage
                    log.info("ocr_completed | model={} tokens={} cost={}", ocr_model, ocr_prompt + ocr_completion, ocr_cost)
                except Exception as e:
                    status.update(label="解析失败", state="error")
                    st.error(f"解析失败：{e}")
                else:
                    status.update(label="完成 ✅", state="complete")
                    st.success(f"文件已上传并解析完成：{up.name}")
                    st.text(resume_text[:500] + ("…" if len(resume_text) > 500 else ""))  # 显示前500个字符


# --- Analyze Block ---
placeholder = st.container(border=True)  # 创建一个带边框的容器，用于显示匹配结果部分
with placeholder:  # 在该容器中绘制内容
    st.markdown("### 匹配结果")
    # 仅当职位描述和简历文本都存在且非空时才执行分析逻辑
    if jd_text and resume_text:
        # 计算两段文本的哈希值，用于判断内容是否变化（防抖）
        key = hash_inputs(jd_text, resume_text)
        cache_hit = st.session_state.get("last_key") == key and st.session_state.get("result") is not None
        log.info("analyze_trigger | cache_hit={}", cache_hit)

        if not cache_hit:
            # 检查余额是否足够（预估费用约 0.05 元）
            service = get_user_service()
            try:
                balance_check = service.check_balance(current_user.user_id, estimated_cost=0.05)
                
                if not balance_check.sufficient:
                    st.error(f"⚠️ {balance_check.message}")
                    st.info("请先充值后再使用服务")
                    st.stop()
                
                st.session_state["last_key"] = key  # 更新 session_state 中记录的哈希值
                st.session_state["result"] = None  # 清空旧的分析结果
                
                with st.spinner("正在分析匹配度…"):  # 显示加载动画提示用户模型正在运行
                    t0 = time.perf_counter()
                    request_id = generate_request_id()
                    
                    try:
                        # 构造用户提示词（将JD和简历内容填入模板）
                        log.info("model_request | model={} user_id={}", QWEN_MODEL, current_user.user_id)
                        user_prompt = USER_TEMPLATE.format(job_description=jd_text.strip(), resume_content=resume_text.strip())
                        # 调用千问模型API进行匹配度分析
                        result = call_qwen_json(user_prompt=user_prompt)
                        result["request_id"] = request_id
                        st.session_state["result"] = result
                        
                        score = int(result.get("match_score", 0))
                        ms = int((time.perf_counter() - t0) * 1000)
                        token_usage = result.get("token_usage", {})
                        
                        # 记录使用量
                        analysis_prompt = token_usage.get("prompt_tokens", 0)
                        analysis_completion = token_usage.get("completion_tokens", 0)
                        analysis_cost = token_usage.get("cost", 0)
                        
                        service.record_usage(
                            user_id=current_user.user_id,
                            request_id=request_id,
                            operation="analysis",
                            model=token_usage.get("model", QWEN_MODEL),
                            prompt_tokens=analysis_prompt,
                            completion_tokens=analysis_completion,
                            cost=analysis_cost
                        )
                        
                        # 记录 OCR 使用量（如果有）
                        ocr_usage = st.session_state.get("ocr_usage")
                        total_cost = analysis_cost
                        if ocr_usage and ocr_usage.get("request_id"):
                            ocr_request_id = ocr_usage["request_id"]
                            ocr_cost = ocr_usage.get("cost", 0)
                            service.record_usage(
                                user_id=current_user.user_id,
                                request_id=ocr_request_id,
                                operation="ocr",
                                model=ocr_usage.get("model", "qwen-vl-ocr-2025-11-20"),
                                prompt_tokens=ocr_usage.get("prompt_tokens", 0),
                                completion_tokens=ocr_usage.get("completion_tokens", 0),
                                cost=ocr_cost
                            )
                            total_cost += ocr_cost
                            # 清除 OCR request_id，避免重复记录
                            ocr_usage["request_id"] = None
                        
                        # 扣费
                        deduct_result = service.deduct_balance(
                            user_id=current_user.user_id,
                            cost=total_cost,
                            reference_id=request_id,
                            remark=f"简历匹配分析 (匹配度 {score}%)"
                        )
                        
                        if deduct_result.success:
                            log.info("deduct_success | user_id={} | cost={} | balance_after={}",
                                     current_user.user_id, total_cost, deduct_result.balance_after)
                        else:
                            log.warning("deduct_failed | user_id={} | message={}",
                                        current_user.user_id, deduct_result.message)
                        
                        log.info("model_ok | model={} score={} ms={} token_usage={}", QWEN_MODEL, score, ms, token_usage)
                        
                    except Exception as e:
                        log.exception("model_failed | model={}", QWEN_MODEL)
                        st.error(f"模型调用失败：{e}")
                        st.stop()
            finally:
                service.db.close()

        # Render report if available
        result = st.session_state.get("result")  # 从 session_state 读取当前分析结果
        if result:  # 如果结果存在，执行展示逻辑
            # Visual score meter
            score = int(result.get("match_score", 0))  # 获取匹配得分（默认0）
            st.progress(score/100.0, text=f"匹配度 {score}%")  # 绘制进度条形式的匹配度指示器
            st.markdown(render_markdown_report(result), unsafe_allow_html=False)  # 渲染报告的 Markdown 内容

            token_usage = result.get("token_usage", {})

# Get version from pyproject.toml
try:
    with open("pyproject.toml", "r", encoding="utf-8") as f:
        pyproject_data = toml.load(f)
    __version__ = pyproject_data["project"]["version"]
except Exception:
    __version__ = "N/A"


# --- Resource Consumption Block ---
if st.session_state.get("result"):
    analysis_usage = st.session_state["result"].get("token_usage", {})
    ocr_usage = st.session_state.get("ocr_usage", {})
    
    # 只有当有 token 使用数据时才显示
    if analysis_usage or ocr_usage:
        with st.container(border=True):
            st.markdown("### 💰 费用明细")
            
            # 计算各项费用
            total_cost = 0.0
            
            # OCR 费用（如果有）
            if ocr_usage:
                ocr_prompt = ocr_usage.get("prompt_tokens", 0)
                ocr_completion = ocr_usage.get("completion_tokens", 0)
                ocr_total = ocr_prompt + ocr_completion
                ocr_cost = ocr_usage.get("cost", 0)
                ocr_model = ocr_usage.get("model", "qwen-vl-ocr-2025-11-20")
                ocr_pages = ocr_usage.get("pages", 1)
                total_cost += ocr_cost
                
                st.markdown(f"""
**🔍 OCR 识别** ({get_model_display_name(ocr_model)})
- 页数: {ocr_pages}
- Token: 输入 {ocr_prompt:,} + 输出 {ocr_completion:,} = **{ocr_total:,}**
- 费用: **¥{ocr_cost:.6f}**
""")
            
            # 分析费用
            if analysis_usage:
                analysis_prompt = analysis_usage.get("prompt_tokens", 0)
                analysis_completion = analysis_usage.get("completion_tokens", 0)
                analysis_total = analysis_usage.get("total_tokens", analysis_prompt + analysis_completion)
                analysis_cost = analysis_usage.get("cost", 0)
                analysis_model = analysis_usage.get("model", QWEN_MODEL)
                total_cost += analysis_cost
                
                # 显示阶梯信息
                tier_info = ""
                if analysis_prompt <= 32000:
                    tier_info = "≤32k"
                elif analysis_prompt <= 128000:
                    tier_info = "32k~128k"
                else:
                    tier_info = "128k~256k"
                
                st.markdown(f"""
**📊 匹配分析** ({get_model_display_name(analysis_model)})
- 阶梯: {tier_info}
- Token: 输入 {analysis_prompt:,} + 输出 {analysis_completion:,} = **{analysis_total:,}**
- 费用: **¥{analysis_cost:.6f}**
""")
            
            # 总计
            st.markdown("---")
            st.markdown(f"**📈 总费用: ¥{total_cost:.6f}**")
            st.caption("费用已从账户余额中扣除")

st.caption(f"© 2025 HireStream Match v{__version__} · Powered by Qwen-3 Max")

st.markdown("""
<style>
header[data-testid="stHeader"]{display:none;}
/* 把视图容器的顶边距清零（覆盖 header 预留的 offset）*/
div[data-testid="stAppViewContainer"]{padding-top:0 !important;}
/* 收紧首个区块与 H1 的距离 */
div.block-container{padding-top:1rem;}
h1:first-child{margin-top:0;}
#MainMenu, footer{display:none;}
</style>
""", unsafe_allow_html=True)