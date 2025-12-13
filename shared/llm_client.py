# -*- coding: utf-8 -*-
"""
统一 LLM 调用客户端

提供统一的 LLM 调用接口，支持 Qwen 系列模型。
"""

import os
import json
import re
import time
from typing import Dict, Any, List, Optional
from openai import OpenAI
from .log import logger
from .token_calculator import TokenCalculator


class LLMClient:
    """统一的 LLM 调用客户端"""
    
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1",
        default_model: str = "qwen3-max"
    ):
        """
        初始化 LLM 客户端
        
        Args:
            api_key: DashScope API Key，如果不传则从环境变量获取
            base_url: API 基础 URL
            default_model: 默认使用的模型
        """
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY", "")
        self.base_url = base_url
        self.default_model = default_model
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
    
    def call(
        self,
        messages: List[Dict[str, str]],
        model: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 800,
        timeout: int = 60
    ) -> tuple[str, dict]:
        """
        调用 LLM
        
        Args:
            messages: 消息列表
            model: 模型名称，默认使用初始化时设置的模型
            temperature: 温度参数
            max_tokens: 最大输出 token 数
            timeout: 超时时间（秒）
            
        Returns:
            (响应文本, token使用量字典)
        """
        model = model or self.default_model
        
        resp = self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=False,
        )
        
        content = resp.choices[0].message.content or ""
        token_usage = {
            "prompt_tokens": resp.usage.prompt_tokens,
            "completion_tokens": resp.usage.completion_tokens,
            "total_tokens": resp.usage.total_tokens,
            "model": model
        }
        
        return content, token_usage
    
    def call_json(
        self,
        user_prompt: str,
        system_prompt: str | None = None,
        model: str | None = None,
        retries: int = 1
    ) -> Dict[str, Any]:
        """
        调用 LLM 并解析 JSON 响应
        
        Args:
            user_prompt: 用户提示词
            system_prompt: 系统提示词
            model: 模型名称
            retries: 重试次数
            
        Returns:
            解析后的 JSON 字典（包含 token_usage 字段）
        """
        model = model or self.default_model
        system_prompt = system_prompt or os.getenv("SYSTEM_PROMPT", "")
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})
        
        logger.info(f"LLM 请求 | model={model}")
        
        last_err: Optional[Exception] = None
        
        for attempt in range(retries + 1):
            try:
                content, token_usage = self.call(messages, model=model)
                logger.info(f"LLM 响应 | model={model} content_length={len(content)}")
                
                json_str = self._extract_json(content)
                result = json.loads(json_str)
                result = self._normalize_result(result)
                
                # 添加 token 使用量和费用计算
                prompt_tokens = token_usage.get("prompt_tokens", 0)
                completion_tokens = token_usage.get("completion_tokens", 0)
                cost = TokenCalculator.calculate_cost(model, prompt_tokens, completion_tokens)
                
                result["token_usage"] = {
                    **token_usage,
                    "cost": cost
                }
                return result
            except Exception as e:
                last_err = e
                if attempt < retries:
                    time.sleep(0.8)
                    continue
                raise
        
        assert False, f"Unreachable, last_err={last_err}"
    
    _JSON_BLOCK_RE = re.compile(r'```(?:json)?\s*(\{.*?\})\s*```', re.S)
    
    def _extract_json(self, text: str) -> str:
        """从文本中提取 JSON"""
        if not text:
            raise ValueError("模型返回为空")
        
        m = self._JSON_BLOCK_RE.search(text)
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
    
    def _normalize_result(self, d: Dict[str, Any]) -> Dict[str, Any]:
        """规范化结果"""
        def to_int(x: Any) -> int:
            try:
                v = int(round(float(x)))
            except Exception:
                v = 0
            return max(0, min(100, v))
        
        out = {
            "match_score": to_int(d.get("match_score", 0)),
            "advantages": list(self._ensure_list_of_str(d.get("advantages", [])))[:10],
            "risks": list(self._ensure_list_of_str(d.get("risks", [])))[:10],
            "advice": str(d.get("advice", "")).strip()[:1200],
        }
        return out
    
    def _ensure_list_of_str(self, x: Any) -> List[str]:
        """确保返回字符串列表"""
        if isinstance(x, list):
            return [str(i).strip() for i in x if str(i).strip()]
        if isinstance(x, str) and x.strip():
            parts = re.split(r"[;\n•·\-]+", x)
            return [p.strip() for p in parts if p.strip()]
        return []


# 便捷函数
def get_llm_client() -> LLMClient:
    """获取默认的 LLM 客户端实例"""
    return LLMClient()
