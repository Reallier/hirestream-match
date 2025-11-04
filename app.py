# -*- coding: utf-8 -*-
import os
import sys
import streamlit as st

from prompts import SYSTEM_PROMPT, USER_TEMPLATE
from match_engine import (
    extract_text_from_upload, call_qwen_json, render_markdown_report, hash_inputs
)

st.set_page_config(page_title="HireStream Match — 简历与JD智能匹配", page_icon="🧲", layout="centered")

# HERO = "# HireStream Match\n_极简 · 一页式 · 开箱即用_"
# st.markdown(HERO)
# # 使用 st.markdown 在页面上显示英雄标题

# Top small tip
st.caption("提示：粘贴JD + 上传简历后，会自动分析，无需点击按钮。")

# --- Layout: three blocks ---
with st.container(border=True):
    jd_text = st.text_area("职位描述（JD）", height=220, placeholder="在此粘贴JD文本……", key="jd_text")

with st.container(border=True):
    up = st.file_uploader("上传候选人简历（PDF / DOCX / TXT，≤ 2MB）", type=["pdf", "docx", "txt"], accept_multiple_files=False, key="resume_file")
    resume_text = ""
    if up is not None:
        # Size guard
        if up.size > 2 * 1024 * 1024:
            st.error("文件过大：需 ≤ 2MB。")
            up = None
        else:
            try:
                resume_text = extract_text_from_upload(up.name, up.read())
                st.success(f"文件已上传：{up.name}")
            except Exception as e:
                st.error(f"解析失败：{e}")

# --- Auto trigger ---
placeholder = st.container(border=True)
with placeholder:
    st.markdown("### 匹配结果")
    # Only analyze when both ready & non-empty
    if jd_text and resume_text:
        # Debounce by hashing inputs
        key = hash_inputs(jd_text, resume_text)
        if st.session_state.get("last_key") != key:
            st.session_state["last_key"] = key
            st.session_state["result"] = None
            with st.spinner("正在分析匹配度…"):
                try:
                    user_prompt = USER_TEMPLATE.format(job_description=jd_text.strip(), resume_content=resume_text.strip())
                    result = call_qwen_json(
                        system_prompt=SYSTEM_PROMPT,
                        user_prompt=user_prompt,
                        model=os.getenv("QWEN_MODEL") or "qwen3-max",  # 可通过环境变量覆盖
                        timeout=10,
                        retries=1,
                    )
                    st.session_state["result"] = result
                except Exception as e:
                    st.error(f"模型调用失败：{e}")
                    st.stop()

        # Render report if available
        result = st.session_state.get("result")
        if result:
            # Visual score meter
            score = int(result.get("match_score", 0))
            st.progress(score/100.0, text=f"匹配度 {score}%")
            st.markdown(render_markdown_report(result), unsafe_allow_html=False)

# Footer
# st.divider()
st.caption("© 2025 HireStream Match · Powered by Qwen-3 Max")
# Hide Streamlit default footer/menu for cleanliness
# st.markdown("""
# <style>
# #MainMenu {visibility: hidden;}
# footer {visibility: hidden;}
# .block-container {padding-top: 2.0rem;}
# </style>
# """, unsafe_allow_html=True)

# st.markdown("""
# <style>
# /* 去掉粘性顶栏本体与占位 */
# header[data-testid="stHeader"]{display:none;}
# /* 收紧主容器上边距 */
# .main .block-container{padding-top:0.4rem;}
# /* 首个 H1 顶部外边距压缩，避免再留空 */
# h1:first-child{margin-top:0.2rem;}
# /* 可选：隐藏菜单/页脚，同时不占位 */
# #MainMenu, footer{display:none;}
# </style>
# """, unsafe_allow_html=True)

st.markdown("""
<style>
header[data-testid="stHeader"]{display:none;}
/* 关键：把视图容器的顶边距清零（覆盖 header 预留的 offset）*/
div[data-testid="stAppViewContainer"]{padding-top:0 !important;}
/* 收紧首个区块与 H1 的距离 */
div.block-container{padding-top:1rem;}
h1:first-child{margin-top:0;}
#MainMenu, footer{display:none;}
</style>
""", unsafe_allow_html=True)