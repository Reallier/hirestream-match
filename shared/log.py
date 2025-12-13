# -*- coding: utf-8 -*-
"""
共享日志模块

提供统一的日志记录功能
"""

import logging
import sys

# 创建 logger
logger = logging.getLogger("shared")
logger.setLevel(logging.INFO)

# 创建控制台处理器
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

__all__ = ['logger']
