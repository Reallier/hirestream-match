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
# with st.container(border=True):
#     jd_text = st.text_area("职位描述（JD）", height=220, placeholder="在此粘贴JD文本……", key="jd_text")
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
        st.success("JD 已自动更新！")  # 这里写你的处理逻辑，比如解析、分析等


with st.container(border=True):  # 创建一个带边框的容器，以下组件都显示在这个容器中
    up = st.file_uploader(  # 文件上传组件
        "上传候选人简历（PDF ≤ 2MB）",  # 上传提示文字
        type=["pdf"],  # 只允许上传 PDF 文件
        accept_multiple_files=False,  # 仅允许单文件上传
        key="resume_file"  # 组件唯一键值，避免状态冲突
    )
    resume_text = ""  # 初始化简历文本变量，默认空字符串
    if up is not None:  # 判断是否有文件被上传
        if up.size > 2 * 1024 * 1024:
            st.error("文件过大：需 ≤ 2MB。")
            up = None
        else:
            # 调用自定义函数提取上传文件的文本内容
            # up.read() 读取文件的全部二进制数据
            resume_text = extract_text_from_upload(up.name, up.read())
            # 显示上传成功信息，并提示文件名
            st.success(f"文件已上传：{up.name}")


# --- Auto trigger ---
placeholder = st.container(border=True)  # 创建一个带边框的容器，用于显示匹配结果部分
with placeholder:  # 在该容器中绘制内容
    st.markdown("### 匹配结果")
    # 仅当职位描述和简历文本都存在且非空时才执行分析逻辑
    if jd_text and resume_text:
        # 计算两段文本的哈希值，用于判断内容是否变化（防抖）
        key = hash_inputs(jd_text, resume_text)
        if st.session_state.get("last_key") != key:  # 如果当前哈希与上次不同，说明输入内容发生了变化
            st.session_state["last_key"] = key  # 更新 session_state 中记录的哈希值
            st.session_state["result"] = None  # 清空旧的分析结果
            with st.spinner("正在分析匹配度…"):  # 显示加载动画提示用户模型正在运行
                try:
                    # 构造用户提示词（将JD和简历内容填入模板）
                    user_prompt = USER_TEMPLATE.format(job_description=jd_text.strip(), resume_content=resume_text.strip())
                    # 调用千问模型API进行匹配度分析
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
        result = st.session_state.get("result")  # 从 session_state 读取当前分析结果
        if result:  # 如果结果存在，执行展示逻辑
            # Visual score meter
            score = int(result.get("match_score", 0))  # 获取匹配得分（默认0）
            st.progress(score/100.0, text=f"匹配度 {score}%")  # 绘制进度条形式的匹配度指示器
            st.markdown(render_markdown_report(result), unsafe_allow_html=False)  # 渲染报告的 Markdown 内容


st.caption("© 2025 HireStream Match · Powered by Qwen-3 Max")

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