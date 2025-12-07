# -*- coding: utf-8 -*-
import os
import uuid
import time
import streamlit as st
from dotenv import load_dotenv
import toml # Import toml library

from match_engine import extract_text_from_upload, call_qwen_json
from utils import hash_inputs, render_markdown_report
from log import logger as log
from token_calculator import TokenCalculator
from pricing_config import get_model_display_name


# -------- Env --------
load_dotenv()
USER_TEMPLATE = os.getenv("USER_TEMPLATE")
QWEN_MODEL = os.getenv("QWEN_MODEL")


# -------- Page --------
st.set_page_config(page_title="HireStream Match — 简历与JD智能匹配", page_icon="🧲", layout="centered")
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
            st.session_state["last_key"] = key  # 更新 session_state 中记录的哈希值
            st.session_state["result"] = None  # 清空旧的分析结果
            with st.spinner("正在分析匹配度…"):  # 显示加载动画提示用户模型正在运行
                t0 = time.perf_counter()
                try:
                    # 构造用户提示词（将JD和简历内容填入模板）
                    log.info("11111111111111model_request | model={} user_prompt={}", QWEN_MODEL, USER_TEMPLATE)
                    user_prompt = USER_TEMPLATE.format(job_description=jd_text.strip(), resume_content=resume_text.strip())
                    # 调用千问模型API进行匹配度分析
                    result = call_qwen_json(user_prompt=user_prompt)
                    st.session_state["result"] = result
                    score = int(result.get("match_score", 0))
                    ms = int((time.perf_counter() - t0) * 1000)
                    token_usage = result.get("token_usage", {})
                    log.info("model_ok | model={} score={} ms={} token_usage={}", QWEN_MODEL, score, ms, token_usage)
                except Exception as e:
                    log.exception("model_failed | model={}", QWEN_MODEL)
                    st.error(f"模型调用失败：{e}")
                    st.stop()

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