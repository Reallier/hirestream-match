# -*- coding: utf-8 -*-
"""
HireStream Match 核心逻辑：
- 在内存中完整解析文件（PDF/DOCX/TXT）
- 通过 DashScope（优先）或兼容 OpenAI 的 DashScope 接口调用 LLM
- 最少次数的重试与超时控制
- 将结果后处理为整洁的 Markdown 报告
"""
from __future__ import annotations # 延迟解析类型注解为字符串，避免循环引用/前置声明问题，并减少运行期开销。

import json
import os
import re
import time
from typing import Dict, Any, List, Optional
from qwen_pdf_ocr import QwenPDFOCR
from openai import OpenAI
from log import logger as log

# --- 轻量级、纯内存文件解析 ---
def _read_pdf_bytes_to_text(data: bytes) -> str:
    api_key = os.getenv("DASHSCOPE_API_KEY", "").strip()
    return QwenPDFOCR.from_bytes(data, api_key=api_key, region="cn", verbose=False).run().strip()

def _read_image_bytes_to_text(data: bytes) -> str:
    """处理图片格式的简历（JPG/PNG等）"""
    api_key = os.getenv("DASHSCOPE_API_KEY", "").strip()
    return QwenPDFOCR.from_image_bytes(data, api_key=api_key, region="cn", verbose=False)

def extract_text_from_upload(filename: str, data: bytes) -> str:
    name = (filename or "").lower()
    if name.endswith(".pdf"):
        return _read_pdf_bytes_to_text(data)
    elif name.endswith((".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp")):
        return _read_image_bytes_to_text(data)
    raise ValueError("不支持的文件类型，仅支持 PDF 和常见图片格式（JPG/PNG/GIF/BMP/WEBP）")

# --- LLM 调用（通过 DashScope 或兼容 OpenAI 的 DashScope 接口） ---
def _call_dashscope_via_openai(messages: List[Dict[str, str]], model: str, timeout: int) -> str:
    """
    通过 OpenAI Python SDK 调用 DashScope 的 OpenAI 兼容接口。

    前提要求：
      - 环境变量中存在 OPENAI_API_KEY 或 DASHSCOPE_API_KEY（两者任选其一）
      - 可选环境变量 OPENAI_BASE_URL（未设置则默认使用 DashScope 中国区兼容端点）
    """
    client = OpenAI(
        api_key=os.getenv("DASHSCOPE_API_KEY"),
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
    )

    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.2,
        max_tokens=800,
        stream=False,
    )
    # 提取返回内容。DashScope 兼容 OpenAI 格式，因此结构为：
    # resp.choices[0].message.content
    content = resp.choices[0].message.content or ""
    return content

def call_qwen_json(
    user_prompt: str,
    retries: int = 1
) -> Dict[str, Any]:
    """
    调用 Qwen（通义千问）模型生成 JSON 格式的结构化分析结果。

    本函数是调用大模型服务并进行数据处理的核心封装。它通过尝试不同的
    客户端（优先使用 DashScope SDK）与模型通信，并执行多次重试以提高
    调用成功率。最重要的是，它对模型的原始输出进行鲁棒的 JSON 提取和
    数据规范化，以确保返回的结果符合预期的结构和约束。
    """
    # 确定模型名称：优先使用传入参数，其次是环境变量，最后是默认值
    model = os.getenv("QWEN_MODEL")
    system_prompt = os.getenv("SYSTEM_PROMPT")

    # 构造标准的消息列表 (Messages)，用于 API 调用
    messages = [{"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}]

    log.info("2222222222222222222222222222model_request | model={} user_prompt={}", model, messages)

    last_err: Optional[Exception] = None  # 存储最后一次发生的异常

    # 开始重试循环：总共尝试 retries + 1 次
    for attempt in range(retries + 1):
        try:
            # --- 1. API 调用 ---
            content = _call_dashscope_via_openai(messages, model=model, timeout=10)
            # 加个日志输出返回内容
            log.info("！！！！！！！！！！！！！！！！model_response | model={} content={}", model, content)

            json_str = _extract_json(content)
            result = json.loads(json_str)
            result = _normalize_result(result)
            return result
        except Exception as e:
            last_err = e
            if attempt < retries:
                time.sleep(0.8)
                continue
            raise

    assert False, f"Unreachable, last_err={last_err}"

_JSON_BLOCK_RE = re.compile(r'```(?:json)?\s*(\{.*?\})\s*```', re.S)

def _extract_json(text: str) -> str:
    if not text:
        raise ValueError("模型返回为空")
    m = _JSON_BLOCK_RE.search(text)
    if m:
        return m.group(1)
    text = text.strip()
    if text.startswith("{") and text.endswith("}"):
        return text
    start = text.find("{")
    end = text.rfind("}")
    if 0 <= start < end:
        return text[start:end+1]
    raise ValueError("未能在模型输出中找到JSON，请调整提示词或重试。")

def _normalize_result(d: Dict[str, Any]) -> Dict[str, Any]:
    def to_int(x: Any) -> int:
        try:
            v = int(round(float(x)))
        except Exception:
            v = 0
        return max(0, min(100, v))

    out = {
        "match_score": to_int(d.get("match_score", 0)),
        "advantages": list(_ensure_list_of_str(d.get("advantages", [])))[:10],
        "risks": list(_ensure_list_of_str(d.get("risks", [])))[:10],
        "advice": str(d.get("advice", "")).strip()[:120],
    }
    return out

def _ensure_list_of_str(x: Any) -> List[str]:
    if isinstance(x, list):
        return [str(i).strip() for i in x if str(i).strip()]
    if isinstance(x, str) and x.strip():
        # split bullets
        parts = re.split(r"[;\n•·\-]+", x)
        return [p.strip() for p in parts if p.strip()]
    return []