"""
日志配置模块 - 统一日志初始化和格式化
"""

import logging
import sys
import os
from typing import Optional
from pythonjsonlogger import jsonlogger

from .context import ContextFilter

# 默认日志格式
DEFAULT_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
JSON_FORMAT = "%(timestamp)s %(level)s %(name)s %(message)s"


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """自定义 JSON 格式化器，添加服务名和 trace_id"""
    
    def __init__(self, service_name: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service_name = service_name
    
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        
        # 标准字段
        log_record['timestamp'] = self.formatTime(record)
        log_record['level'] = record.levelname
        log_record['service'] = self.service_name
        log_record['logger'] = record.name
        
        # 上下文字段（从 ContextFilter 注入）
        if hasattr(record, 'trace_id') and record.trace_id:
            log_record['trace_id'] = record.trace_id
        if hasattr(record, 'user_id') and record.user_id:
            log_record['user_id'] = record.user_id
        if hasattr(record, 'request_id') and record.request_id:
            log_record['request_id'] = record.request_id


def setup_logging(
    service_name: str,
    log_level: str = "INFO",
    enable_json: bool = True,
    loki_url: Optional[str] = None,
) -> None:
    """
    初始化日志配置
    
    Args:
        service_name: 服务名称，用于标识日志来源
        log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR)
        enable_json: 是否使用 JSON 格式（生产环境推荐）
        loki_url: Loki 推送地址（可选）
    
    Example:
        >>> from intjtech_logging import setup_logging
        >>> setup_logging("app01-hirestream", log_level="INFO")
    """
    # 获取根 logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # 清除现有 handlers
    root_logger.handlers.clear()
    
    # 添加上下文 filter
    context_filter = ContextFilter()
    
    # 控制台 handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.addFilter(context_filter)
    
    if enable_json:
        formatter = CustomJsonFormatter(service_name)
    else:
        formatter = logging.Formatter(
            f"%(asctime)s | %(levelname)-8s | {service_name} | %(name)s | %(message)s"
        )
    
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Loki handler（可选）
    if loki_url:
        try:
            import logging_loki
            loki_handler = logging_loki.LokiHandler(
                url=f"{loki_url}/loki/api/v1/push",
                tags={"service": service_name},
                version="1",
            )
            loki_handler.addFilter(context_filter)
            root_logger.addHandler(loki_handler)
        except ImportError:
            logging.warning("python-logging-loki not installed, Loki handler disabled")
    
    # 设置第三方库日志级别
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    获取命名 logger
    
    Args:
        name: Logger 名称，通常使用 __name__
    
    Returns:
        配置好的 Logger 实例
    
    Example:
        >>> from intjtech_logging import get_logger
        >>> logger = get_logger(__name__)
        >>> logger.info("Hello", extra={"user_id": "123"})
    """
    return logging.getLogger(name)
