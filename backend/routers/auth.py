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
import re
import uuid
from datetime import datetime, timedelta

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
    token = generate_jwt_token(user_info, expires_in=86400 * 7, email=email)  # 7天
    
    # 设置 Cookie（跨子域共享）
    response.set_cookie(
        key="auth_token",
        value=token,
        max_age=86400 * 7,
        path="/",
        domain=".intjsys.com",
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
    
    清除认证 Cookie（同时清除 auth_token 和 refresh_token 实现跨系统统一退出）
    """
    # 删除 Access Token
    response.delete_cookie(
        key="auth_token",
        path="/",
        domain=".intjsys.com"
    )
    
    # 删除 Refresh Token（官网使用双 Token 机制）
    response.delete_cookie(
        key="refresh_token",
        path="/",
        domain=".intjsys.com"
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
        domain=".intjsys.com",
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


# ============= 邮箱验证码登录 =============

# 邮箱格式验证
EMAIL_REGEX = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')

# 发送频率限制（秒）
SEND_INTERVAL = 60

# 验证码有效期（分钟）
CODE_EXPIRY = 5


class EmailSendRequest(BaseModel):
    """发送验证码请求"""
    email: str


class EmailVerifyRequest(BaseModel):
    """验证码登录请求"""
    email: str
    code: str


@router.post("/email/send")
async def send_email_code_api(
    request: EmailSendRequest,
    auth_db: Session = Depends(get_auth_db)
):
    """
    发送邮箱验证码
    
    POST /api/auth/email/send
    Body: { "email": "user@example.com" }
    """
    from sqlalchemy import text
    from utils.email import send_email_code, generate_code
    
    email = request.email.lower().strip()
    
    # 验证邮箱格式
    if not email or not EMAIL_REGEX.match(email):
        return {"success": False, "message": "请输入正确的邮箱地址"}
    
    logger.info(f"[Email Send] 请求发送验证码: {email}")
    
    # 检查发送频率（1分钟内不能重复发送）
    recent_code = auth_db.execute(
        text("""
            SELECT id, created_at FROM sms_codes 
            WHERE phone = :email 
            AND created_at > :min_time
            ORDER BY created_at DESC 
            LIMIT 1
        """),
        {"email": email, "min_time": datetime.utcnow() - timedelta(seconds=SEND_INTERVAL)}
    ).fetchone()
    
    if recent_code:
        wait_seconds = SEND_INTERVAL - int((datetime.utcnow() - recent_code[1]).total_seconds())
        if wait_seconds > 0:
            return {"success": False, "message": f"请{wait_seconds}秒后再试"}
    
    # 生成验证码
    code = generate_code()
    expires_at = datetime.utcnow() + timedelta(minutes=CODE_EXPIRY)
    
    # 生成唯一 ID
    code_id = str(uuid.uuid4())
    
    # 保存到数据库（复用 sms_codes 表，phone 字段存储邮箱）
    auth_db.execute(
        text("""
            INSERT INTO sms_codes (id, phone, code, expires_at, used, created_at)
            VALUES (:id, :email, :code, :expires_at, false, :created_at)
        """),
        {"id": code_id, "email": email, "code": code, "expires_at": expires_at, "created_at": datetime.utcnow()}
    )
    auth_db.commit()
    
    # 发送邮件
    result = send_email_code(email, code)
    
    if not result["success"]:
        logger.error(f"[Email Send] 发送失败: {result['message']}")
        return {"success": False, "message": "验证码发送失败，请稍后重试"}
    
    logger.info(f"[Email Send] 验证码已发送: {email}")
    
    return {"success": True, "message": "验证码已发送到您的邮箱"}


@router.post("/email/verify")
async def verify_email_code(
    request: EmailVerifyRequest,
    response: Response,
    auth_db: Session = Depends(get_auth_db)
):
    """
    验证邮箱验证码并登录
    
    POST /api/auth/email/verify
    Body: { "email": "user@example.com", "code": "123456" }
    
    用户不存在时自动注册
    """
    from sqlalchemy import text
    
    email = request.email.lower().strip()
    code = request.code.strip()
    
    # 验证参数
    if not email or not EMAIL_REGEX.match(email):
        return {"success": False, "message": "请输入正确的邮箱地址"}
    
    if not code or not re.match(r'^\d{6}$', code):
        return {"success": False, "message": "请输入6位验证码"}
    
    logger.info(f"[Email Verify] 验证登录: {email}")
    
    # 查找有效的验证码
    email_code = auth_db.execute(
        text("""
            SELECT id, code FROM sms_codes 
            WHERE phone = :email 
            AND code = :code 
            AND used = false 
            AND expires_at > :now
            ORDER BY created_at DESC 
            LIMIT 1
        """),
        {"email": email, "code": code, "now": datetime.utcnow()}
    ).fetchone()
    
    if not email_code:
        logger.warning(f"[Email Verify] 验证码无效或已过期: {email}")
        return {"success": False, "message": "验证码错误或已过期"}
    
    # 标记验证码已使用
    auth_db.execute(
        text("UPDATE sms_codes SET used = true WHERE id = :id"),
        {"id": email_code[0]}
    )
    
    # 查找或创建用户
    user = auth_db.execute(
        text("SELECT id, username, name, email, avatar, balance, free_quota, role FROM users WHERE email = :email"),
        {"email": email}
    ).fetchone()
    
    is_new_user = False
    
    if not user:
        # 新用户自动注册
        logger.info(f"[Email Verify] 新用户注册: {email}")
        is_new_user = True
        
        # 用邮箱前缀作为默认昵称
        default_name = email.split('@')[0]
        
        auth_db.execute(
            text("""
                INSERT INTO users (email, name, balance, free_quota, role, created_at, updated_at)
                VALUES (:email, :name, 0, 5.0, 'user', :now, :now)
            """),
            {"email": email, "name": default_name, "now": datetime.utcnow()}
        )
        auth_db.commit()
        
        # 重新查询获取 ID
        user = auth_db.execute(
            text("SELECT id, username, name, email, avatar, balance, free_quota, role FROM users WHERE email = :email"),
            {"email": email}
        ).fetchone()
    
    auth_db.commit()
    
    user_id, username, name, user_email, avatar, balance, free_quota, role = user
    
    # 生成 JWT Token
    user_info = UserInfo(
        user_id=user_id,
        nickname=name or email.split('@')[0],
        avatar_url=avatar
    )
    token = generate_jwt_token(user_info, expires_in=86400 * 7, email=user_email)  # 7天
    
    # 设置 Cookie（跨子域共享）
    response.set_cookie(
        key="auth_token",
        value=token,
        max_age=86400 * 7,
        path="/",
        domain=".intjsys.com",
        secure=True,
        httponly=True,
        samesite="lax"
    )
    
    logger.info(f"[Email Verify] 登录成功: user_id={user_id}, is_new={is_new_user}")
    
    balance_val = float(balance or 0)
    free_quota_val = float(free_quota or 0)
    
    return {
        "success": True,
        "message": "注册成功" if is_new_user else "登录成功",
        "user": {
            "id": user_id,
            "name": name or email.split('@')[0],
            "email": user_email,
            "avatar": avatar,
            "balance": balance_val,
            "freeQuota": free_quota_val,
            "totalAvailable": balance_val + free_quota_val,
            "role": role or "user"
        }
    }
