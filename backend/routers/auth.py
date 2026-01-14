# -*- coding: utf-8 -*-
"""
用户认证相关 API

提供登录、登出、获取用户信息等功能
"""

from fastapi import APIRouter, HTTPException, Response, Cookie, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
import bcrypt

from database import get_auth_db
from match_service.auth import generate_jwt_token, verify_jwt_token, UserInfo
from loguru import logger


router = APIRouter(prefix="/api/auth", tags=["认证"])


# ============= 请求模型 =============

class LoginRequest(BaseModel):
    """登录请求"""
    username: str
    password: str


class UserResponse(BaseModel):
    """用户信息响应"""
    id: int
    name: Optional[str] = None
    email: Optional[str] = None
    avatar: Optional[str] = None
    balance: float = 0
    freeQuota: float = 0
    totalAvailable: float = 0
    role: str = "user"


# ============= API 端点 =============

@router.post("/login")
async def login(
    request: LoginRequest,
    response: Response,
    auth_db: Session = Depends(get_auth_db)
):
    """
    用户登录
    
    验证用户名密码，返回用户信息并设置 JWT Cookie
    """
    from sqlalchemy import text
    
    # 查询用户
    result = auth_db.execute(
        text("SELECT id, username, password, name, email, avatar, balance, free_quota, role FROM users WHERE username = :username OR email = :username"),
        {"username": request.username}
    ).fetchone()
    
    if not result:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    user_id, username, password_hash, name, email, avatar, balance, free_quota, role = result
    
    # 验证密码
    if not password_hash or not bcrypt.checkpw(request.password.encode('utf-8'), password_hash.encode('utf-8')):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    # 生成 JWT Token
    user_info = UserInfo(
        user_id=user_id,
        nickname=name or username,
        avatar_url=avatar
    )
    token = generate_jwt_token(user_info, expires_in=86400 * 7)  # 7天
    
    # 设置 Cookie（跨子域共享）
    response.set_cookie(
        key="auth_token",
        value=token,
        max_age=86400 * 7,
        path="/",
        domain=".reallier.top",
        secure=True,
        httponly=True,  # 防止 XSS 窃取 Token
        samesite="lax"
    )
    
    logger.info("user_login | user_id={} | username={}", user_id, username)
    
    balance_val = float(balance or 0)
    free_quota_val = float(free_quota or 0)
    
    return {
        "success": True,
        "user": {
            "id": user_id,
            "name": name,
            "email": email,
            "avatar": avatar,
            "balance": balance_val,
            "freeQuota": free_quota_val,
            "totalAvailable": balance_val + free_quota_val,
            "role": role or "user"
        }
    }


@router.post("/logout")
async def logout(response: Response):
    """
    用户登出
    
    清除认证 Cookie
    """
    response.delete_cookie(
        key="auth_token",
        path="/",
        domain=".reallier.top"
    )
    
    return {"success": True, "message": "已登出"}


class VerifyTokenRequest(BaseModel):
    """Token 验证请求"""
    token: str


@router.post("/verify-token")
async def verify_token(
    request: VerifyTokenRequest,
    response: Response,
    auth_db: Session = Depends(get_auth_db)
):
    """
    验证 JWT Token 并设置 Cookie（用于 SSO 登录回调）
    
    从官网跳转过来时，URL 中携带 token，前端调用此接口验证并设置 Cookie
    """
    from sqlalchemy import text
    
    user_info = verify_jwt_token(request.token)
    if not user_info:
        return {"success": False, "message": "Token 无效或已过期"}
    
    # 查询用户信息
    result = auth_db.execute(
        text("SELECT id, username, name, email, avatar, balance, free_quota, role FROM users WHERE id = :user_id"),
        {"user_id": user_info.user_id}
    ).fetchone()
    
    if not result:
        return {"success": False, "message": "用户不存在"}
    
    user_id, username, name, email, avatar, balance, free_quota, role = result
    
    # 设置 Cookie（跨子域共享）
    response.set_cookie(
        key="auth_token",
        value=request.token,
        max_age=86400 * 7,
        path="/",
        domain=".reallier.top",
        secure=True,
        httponly=True,
        samesite="lax"
    )
    
    logger.info("sso_login | user_id={} | username={}", user_id, username)
    
    balance_val = float(balance or 0)
    free_quota_val = float(free_quota or 0)
    
    return {
        "success": True,
        "user": {
            "id": user_id,
            "name": name or username,
            "email": email,
            "avatar": avatar,
            "balance": balance_val,
            "freeQuota": free_quota_val,
            "totalAvailable": balance_val + free_quota_val,
            "role": role or "user"
        }
    }


@router.get("/me")
async def get_current_user(
    auth_token: Optional[str] = Cookie(None),
    auth_db: Session = Depends(get_auth_db)
):
    """
    获取当前用户信息
    
    从 Cookie 中读取 JWT Token 并验证
    """
    if not auth_token:
        return {"success": False, "user": None}
    
    user_info = verify_jwt_token(auth_token)
    if not user_info:
        return {"success": False, "user": None}
    
    from sqlalchemy import text
    
    # 查询最新用户信息
    result = auth_db.execute(
        text("SELECT id, username, name, email, avatar, balance, free_quota, role FROM users WHERE id = :user_id"),
        {"user_id": user_info.user_id}
    ).fetchone()
    
    if not result:
        return {"success": False, "user": None}
    
    user_id, username, name, email, avatar, balance, free_quota, role = result
    
    balance_val = float(balance or 0)
    free_quota_val = float(free_quota or 0)
    
    return {
        "success": True,
        "user": {
            "id": user_id,
            "name": name or username,
            "email": email,
            "avatar": avatar,
            "balance": balance_val,
            "freeQuota": free_quota_val,
            "totalAvailable": balance_val + free_quota_val,
            "role": role or "user"
        }
    }
