"""
INTJTech Unified Logging Library

统一日志库 - 为所有 INTJTech 服务提供结构化日志支持
"""

from .config import setup_logging, get_logger
from .context import LogContext, get_trace_id, set_trace_id

__version__ = "0.1.0"
__all__ = [
    "setup_logging",
    "get_logger", 
    "LogContext",
    "get_trace_id",
    "set_trace_id",
]
