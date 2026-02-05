# -*- coding: utf-8 -*-
"""
API 路由模块
"""

from .auth import router as auth_router
from .history import router as history_router
from .feedback import router as feedback_router

__all__ = ["auth_router", "history_router", "feedback_router"]
