# -*- coding: utf-8 -*-
"""
FastAPI 依赖注入模块

提供统一的用户认证依赖，确保所有受保护接口从 JWT Token 获取用户身份。
"""

from fastapi import Cookie, HTTPException, Depends, Header
from typing import Optional

from match_service.auth import verify_jwt_token, UserInfo


async def get_current_user(
    auth_token: Optional[str] = Cookie(None)
) -> UserInfo:
    """
    获取当前登录用户（必须登录）
    
    从 Cookie 中获取 auth_token 并验证 JWT，返回用户信息。
    如果未登录或 token 无效，抛出 401 异常。
    
    Usage:
        @app.get("/api/candidates")
        async def list_candidates(user: UserInfo = Depends(get_current_user)):
            user_id = user.user_id
    """
    if not auth_token:
        raise HTTPException(status_code=401, detail="未登录，请先登录")
    
    user_info = verify_jwt_token(auth_token)
    if not user_info:
        raise HTTPException(status_code=401, detail="登录已过期，请重新登录")
    
    return user_info


async def get_current_user_optional(
    auth_token: Optional[str] = Cookie(None)
) -> Optional[UserInfo]:
    """
    获取当前用户（可选，允许匿名访问）
    
    用于匿名也可使用但登录用户有额外功能的接口。
    """
    if not auth_token:
        return None
    
    return verify_jwt_token(auth_token)


async def verify_admin_api_key(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key")
) -> str:
    """
    验证管理员 API Key（从请求头获取）
    
    用于内部管理接口，如 /api/reindex。
    """
    import os
    expected_key = os.environ.get("ADMIN_API_KEY", "")
    
    if not expected_key:
        raise HTTPException(status_code=500, detail="服务器未配置管理员 API Key")
    
    if not x_api_key or x_api_key != expected_key:
        raise HTTPException(status_code=403, detail="此 API 需要有效的管理员 API Key")
    
    return x_api_key
