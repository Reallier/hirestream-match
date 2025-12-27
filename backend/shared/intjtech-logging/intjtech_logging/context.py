"""
上下文管理模块 - 管理 trace_id 等请求级上下文
"""

import logging
import uuid
from contextvars import ContextVar
from typing import Optional
from contextlib import contextmanager

# 上下文变量
_trace_id: ContextVar[Optional[str]] = ContextVar('trace_id', default=None)
_user_id: ContextVar[Optional[str]] = ContextVar('user_id', default=None)
_request_id: ContextVar[Optional[str]] = ContextVar('request_id', default=None)


def generate_trace_id() -> str:
    """生成新的 trace_id"""
    return uuid.uuid4().hex[:16]


def get_trace_id() -> Optional[str]:
    """获取当前 trace_id"""
    return _trace_id.get()


def set_trace_id(trace_id: str) -> None:
    """设置 trace_id"""
    _trace_id.set(trace_id)


def get_user_id() -> Optional[str]:
    """获取当前 user_id"""
    return _user_id.get()


def set_user_id(user_id: str) -> None:
    """设置 user_id"""
    _user_id.set(user_id)


def get_request_id() -> Optional[str]:
    """获取当前 request_id"""
    return _request_id.get()


def set_request_id(request_id: str) -> None:
    """设置 request_id"""
    _request_id.set(request_id)


class ContextFilter(logging.Filter):
    """将上下文信息注入日志记录"""
    
    def filter(self, record: logging.LogRecord) -> bool:
        record.trace_id = get_trace_id()
        record.user_id = get_user_id()
        record.request_id = get_request_id()
        return True


@contextmanager
def LogContext(
    trace_id: Optional[str] = None,
    user_id: Optional[str] = None,
    request_id: Optional[str] = None,
):
    """
    日志上下文管理器
    
    在上下文内的所有日志都会自动包含指定的字段
    
    Example:
        >>> with LogContext(trace_id="abc123", user_id="user_001"):
        ...     logger.info("Processing request")  # 自动包含 trace_id 和 user_id
    """
    # 保存旧值
    old_trace_id = _trace_id.get()
    old_user_id = _user_id.get()
    old_request_id = _request_id.get()
    
    try:
        # 设置新值
        if trace_id is not None:
            _trace_id.set(trace_id)
        if user_id is not None:
            _user_id.set(user_id)
        if request_id is not None:
            _request_id.set(request_id)
        
        yield
    finally:
        # 恢复旧值
        _trace_id.set(old_trace_id)
        _user_id.set(old_user_id)
        _request_id.set(old_request_id)
