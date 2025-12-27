"""
FastAPI 中间件 - 自动注入 trace_id 和请求日志
"""

import time
from typing import Callable
from .context import generate_trace_id, set_trace_id, set_user_id, get_trace_id
from .config import get_logger

logger = get_logger(__name__)


class LoggingMiddleware:
    """
    FastAPI 日志中间件
    
    功能:
    - 自动生成/传递 trace_id
    - 记录请求开始/结束
    - 计算请求耗时
    - 从 JWT 中提取 user_id（可选）
    
    Usage:
        >>> from fastapi import FastAPI
        >>> from intjtech_logging.middleware import LoggingMiddleware
        >>> 
        >>> app = FastAPI()
        >>> app.add_middleware(LoggingMiddleware)
    """
    
    def __init__(self, app, extract_user_id: bool = True):
        self.app = app
        self.extract_user_id = extract_user_id
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # 从 header 获取或生成 trace_id
        headers = dict(scope.get("headers", []))
        trace_id = headers.get(b"x-trace-id", b"").decode() or generate_trace_id()
        set_trace_id(trace_id)
        
        # 提取 user_id（如果启用）
        if self.extract_user_id:
            auth_header = headers.get(b"authorization", b"").decode()
            if auth_header.startswith("Bearer "):
                user_id = self._extract_user_from_jwt(auth_header[7:])
                if user_id:
                    set_user_id(user_id)
        
        # 记录请求信息
        method = scope.get("method", "")
        path = scope.get("path", "")
        start_time = time.time()
        
        logger.info(
            "Request started",
            extra={
                "method": method,
                "path": path,
                "event": "request_start",
            }
        )
        
        # 捕获响应状态码
        status_code = 500
        
        async def send_wrapper(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
                # 添加 trace_id 到响应头
                headers = list(message.get("headers", []))
                headers.append((b"x-trace-id", trace_id.encode()))
                message["headers"] = headers
            await send(message)
        
        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as e:
            logger.error(
                f"Request failed: {e}",
                extra={
                    "method": method,
                    "path": path,
                    "error": str(e),
                    "event": "request_error",
                }
            )
            raise
        finally:
            duration_ms = (time.time() - start_time) * 1000
            logger.info(
                "Request completed",
                extra={
                    "method": method,
                    "path": path,
                    "status_code": status_code,
                    "duration_ms": round(duration_ms, 2),
                    "event": "request_end",
                }
            )
    
    def _extract_user_from_jwt(self, token: str) -> str | None:
        """从 JWT 中提取 user_id（简单解码，不验证签名）"""
        try:
            import base64
            import json
            
            # JWT 格式: header.payload.signature
            parts = token.split(".")
            if len(parts) != 3:
                return None
            
            # Base64 解码 payload
            payload = parts[1]
            # 补齐 padding
            padding = 4 - len(payload) % 4
            if padding != 4:
                payload += "=" * padding
            
            decoded = base64.urlsafe_b64decode(payload)
            data = json.loads(decoded)
            
            # 尝试常见的 user_id 字段
            return data.get("sub") or data.get("user_id") or data.get("id")
        except Exception:
            return None
