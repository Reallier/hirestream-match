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

# --- 轻量级、纯内存文件解析 ---
def _read_pdf_bytes_to_text(data: bytes) -> str:
    api_key = os.getenv("DASHSCOPE_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("未配置 DASHSCOPE_API_KEY 环境变量。")
    return QwenPDFOCR.from_bytes(data, api_key=api_key, region="cn", verbose=False).run().strip()

def extract_text_from_upload(filename: str, data: bytes) -> str:
    name = (filename or "").lower()
    if name.endswith(".pdf"):
        return _read_pdf_bytes_to_text(data)
    raise ValueError("不支持的文件类型，仅支持 PDF")

# --- LLM 调用（通过 DashScope 或兼容 OpenAI 的 DashScope 接口） ---
def _call_dashscope_via_openai(messages: List[Dict[str, str]], model: str, timeout: int) -> str:
    """
    通过 OpenAI Python SDK 调用 DashScope 的 OpenAI 兼容接口。

    前提要求：
      - 环境变量中存在 OPENAI_API_KEY 或 DASHSCOPE_API_KEY（两者任选其一）
      - 可选环境变量 OPENAI_BASE_URL（未设置则默认使用 DashScope 中国区兼容端点）
    """

    from openai import OpenAI  # type: ignore


    # load_dotenv()  # 必须在读取环境变量之前调用
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise RuntimeError("未检测到 OPENAI_API_KEY 或 DASHSCOPE_API_KEY 环境变量。")

    base_url = os.getenv("OPENAI_BASE_URL") or "https://dashscope.aliyuncs.com/compatible-mode/v1"
    client = OpenAI(api_key=api_key, base_url=base_url)
    # 在 OpenAI SDK >=1.40 版本中可通过 with_options 设置请求超时
    try:
        client = client.with_options(timeout=timeout)
    except Exception:
        # 兼容旧版 SDK（无 with_options 方法时忽略）
        pass

    # 发起 ChatCompletion 调用
    # 关键参数：
    #   - model: 指定使用的模型（如 "qwen-plus"）
    #   - messages: 聊天消息列表，格式与 OpenAI 一致 [{"role": "user", "content": "..."}]
    #   - temperature: 控制随机性，0.2 较为稳定
    #   - max_tokens: 限制返回最大 token 数，防止生成过长
    #   - stream=False: 关闭流式输出，直接一次性返回结果
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

def _call_dashscope_sdk(messages: List[Dict[str, str]], model: str, timeout: int) -> str:
    """
    通过 DashScope 原生 SDK 调用模型（非 OpenAI 兼容模式）。
    说明：
      - DashScope 不同版本的 SDK 接口略有差异。
      - 较新版本支持直接传入 "messages"（类似 OpenAI 格式）；
        旧版可能只接受单字符串 "prompt"。
      - 因此代码会先尝试使用 "messages" 调用，如失败则回退到 "prompt" 方式。
    """
    import dashscope  # type: ignore
    from dashscope import Generation  # type: ignore

    # API key
    api_key = os.getenv("DASHSCOPE_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("未检测到 DASHSCOPE_API_KEY 或 OPENAI_API_KEY 环境变量。")
    dashscope.api_key = api_key  # type: ignore

    # Some versions accept 'messages' directly, others accept 'input' dict.
    # We try 'input' schema first.
    try:
        resp = Generation.call(
            model=model,
            input={"messages": messages},
            timeout=timeout,
        )
        # resp.output.text in newer SDKs; older: 'output' may contain 'choices'
        content = ""
        if hasattr(resp, "output") and resp.output:
            out = resp.output
            if isinstance(out, dict):
                # Try modern choices format
                try:
                    content = out["choices"][0]["message"]["content"]
                except Exception:
                    content = out.get("text", "")
        if not content and hasattr(resp, "output_text"):
            content = getattr(resp, "output_text")
        if not content:
            content = str(resp)
        return content
    except Exception:
        # Fallback: concatenate into a single prompt
        prompt = "\n\n".join([m.get("content", "") for m in messages])
        resp = Generation.call(model=model, prompt=prompt, timeout=timeout)
        if hasattr(resp, "output_text"):
            return resp.output_text
        if hasattr(resp, "output") and isinstance(resp.output, dict):
            try:
                return resp.output.get("text", "") or resp.output["choices"][0]["message"]["content"]
            except Exception:
                pass
        return str(resp)

def call_qwen_json(
    system_prompt: str, user_prompt: str,
    model: str = None, timeout: int = 10, retries: int = 1
) -> Dict[str, Any]:
    """
    Call Qwen and parse JSON as required by our template.
    Returns a dict with keys: match_score, advantages, risks, advice
    """
    model = model or os.getenv("QWEN_MODEL") or os.getenv("OPENAI_MODEL") or "qwen-max"
    messages = [{"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}]
    last_err: Optional[Exception] = None
    for attempt in range(retries + 1):
        try:
            # Prefer native DashScope SDK; if not installed, use OpenAI-compatible client
            try:
                content = _call_dashscope_sdk(messages, model=model, timeout=timeout)
            except Exception:
                content = _call_dashscope_via_openai(messages, model=model, timeout=timeout)

            # Extract JSON payload robustly (handles code fences)
            json_str = _extract_json(content)
            result = json.loads(json_str)
            # Validate fields
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
    # If the whole text looks like JSON
    text = text.strip()
    if text.startswith("{") and text.endswith("}"):
        return text
    # Try to salvage by finding first { ... }
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

