# -*- coding: utf-8 -*-
"""
Admin API 模块

为官网后台提供管理接口，使用 FastAPI 实现。
"""

import os
import secrets
from datetime import datetime, timedelta
from typing import Optional, List
from dataclasses import dataclass

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import jwt

from database import get_db_session
from models import User, Transaction
from user_service import UserService
from log import logger as log
from dotenv import load_dotenv

load_dotenv()

# 管理员凭证（从环境变量读取）
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "INTJ@Admin2024")
ADMIN_JWT_SECRET = os.getenv("ADMIN_JWT_SECRET", os.getenv("JWT_SECRET", "admin-secret-key"))

# Admin API 实例
admin_app = FastAPI(
    title="HireStream Admin API",
    description="管理后台接口",
    version="1.0.0",
    docs_url="/api/admin/docs",
    redoc_url=None
)

# CORS 配置
admin_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制为官网域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============ 数据模型 ============

class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    success: bool
    token: Optional[str] = None
    message: str


class UserResponse(BaseModel):
    user_id: str
    nickname: str
    avatar_url: Optional[str]
    balance: float
    free_quota: float
    total_available: float
    created_at: str
    updated_at: str


class UserListResponse(BaseModel):
    total: int
    users: List[UserResponse]


class RechargeRequest(BaseModel):
    amount: float
    remark: Optional[str] = None


class RechargeResponse(BaseModel):
    success: bool
    message: str
    new_balance: float


class StatsResponse(BaseModel):
    total_users: int
    total_balance: float
    total_transactions: int
    today_new_users: int


class CreateUserRequest(BaseModel):
    """创建用户请求"""
    nickname: str
    initial_balance: float = 0.0
    initial_free_quota: float = 1.0


class CreateUserResponse(BaseModel):
    """创建用户响应"""
    success: bool
    message: str
    user_id: Optional[str] = None
    password: Optional[str] = None  # 随机生成的密码，只返回一次


class ResetPasswordRequest(BaseModel):
    """重置密码请求"""
    pass  # 无需传参，自动生成新密码


class ResetPasswordResponse(BaseModel):
    """重置密码响应"""
    success: bool
    message: str
    new_password: Optional[str] = None


# ============ 认证相关 ============

def create_admin_token(username: str) -> str:
    """生成管理员 JWT Token"""
    payload = {
        "sub": username,
        "role": "admin",
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=24)
    }
    return jwt.encode(payload, ADMIN_JWT_SECRET, algorithm="HS256")


def verify_admin_token(authorization: str = Header(None)) -> str:
    """验证管理员 Token"""
    if not authorization:
        raise HTTPException(status_code=401, detail="未提供认证 Token")
    
    # 支持 "Bearer xxx" 格式
    token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
    
    try:
        payload = jwt.decode(token, ADMIN_JWT_SECRET, algorithms=["HS256"])
        if payload.get("role") != "admin":
            raise HTTPException(status_code=403, detail="权限不足")
        return payload.get("sub")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token 已过期")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="无效的 Token")


# ============ API 接口 ============

@admin_app.post("/api/admin/login", response_model=LoginResponse)
async def admin_login(request: LoginRequest):
    """管理员登录"""
    if request.username == ADMIN_USERNAME and request.password == ADMIN_PASSWORD:
        token = create_admin_token(request.username)
        log.info("admin_login_success | username={}", request.username)
        return LoginResponse(success=True, token=token, message="登录成功")
    
    log.warning("admin_login_failed | username={}", request.username)
    return LoginResponse(success=False, token=None, message="用户名或密码错误")


@admin_app.get("/api/admin/users", response_model=UserListResponse)
async def get_users(
    skip: int = 0,
    limit: int = 50,
    search: Optional[str] = None,
    admin: str = Depends(verify_admin_token)
):
    """获取用户列表"""
    with get_db_session() as db:
        query = db.query(User)
        
        if search:
            query = query.filter(
                (User.user_id.contains(search)) | 
                (User.nickname.contains(search))
            )
        
        total = query.count()
        users = query.order_by(User.created_at.desc()).offset(skip).limit(limit).all()
        
        user_list = [
            UserResponse(
                user_id=u.user_id,
                nickname=u.nickname or "",
                avatar_url=u.avatar_url,
                balance=u.balance,
                free_quota=u.free_quota,
                total_available=u.total_available,
                created_at=u.created_at.isoformat() if u.created_at else "",
                updated_at=u.updated_at.isoformat() if u.updated_at else ""
            )
            for u in users
        ]
        
        return UserListResponse(total=total, users=user_list)


@admin_app.get("/api/admin/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: str, admin: str = Depends(verify_admin_token)):
    """获取用户详情"""
    with get_db_session() as db:
        user = db.query(User).filter(User.user_id == user_id).first()
        
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        return UserResponse(
            user_id=user.user_id,
            nickname=user.nickname or "",
            avatar_url=user.avatar_url,
            balance=user.balance,
            free_quota=user.free_quota,
            total_available=user.total_available,
            created_at=user.created_at.isoformat() if user.created_at else "",
            updated_at=user.updated_at.isoformat() if user.updated_at else ""
        )


@admin_app.post("/api/admin/users/{user_id}/recharge", response_model=RechargeResponse)
async def recharge_user(
    user_id: str, 
    request: RechargeRequest,
    admin: str = Depends(verify_admin_token)
):
    """给用户充值"""
    if request.amount <= 0:
        raise HTTPException(status_code=400, detail="充值金额必须大于 0")
    
    with get_db_session() as db:
        user = db.query(User).filter(User.user_id == user_id).first()
        
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        old_balance = user.balance
        user.balance += request.amount
        user.updated_at = datetime.utcnow()
        
        # 记录交易
        transaction = Transaction(
            user_id=user_id,
            type="admin_recharge",
            amount=request.amount,
            balance_after=user.balance,
            remark=request.remark or f"管理员充值 (by {admin})",
            created_at=datetime.utcnow()
        )
        db.add(transaction)
        db.commit()
        
        log.info(
            "admin_recharge | user_id={} | amount={} | new_balance={} | admin={}",
            user_id, request.amount, user.balance, admin
        )
        
        return RechargeResponse(
            success=True,
            message=f"充值成功，已为用户充值 ¥{request.amount:.2f}",
            new_balance=user.balance
        )


@admin_app.get("/api/admin/stats", response_model=StatsResponse)
async def get_stats(admin: str = Depends(verify_admin_token)):
    """获取统计数据"""
    from sqlalchemy import func
    
    with get_db_session() as db:
        total_users = db.query(User).count()
        total_balance = db.query(func.sum(User.balance)).scalar() or 0.0
        total_transactions = db.query(Transaction).count()
        
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_new_users = db.query(User).filter(User.created_at >= today_start).count()
        
        return StatsResponse(
            total_users=total_users,
            total_balance=float(total_balance),
            total_transactions=total_transactions,
            today_new_users=today_new_users
        )


# 健康检查
@admin_app.get("/api/admin/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "service": "admin-api"}


def generate_password(length: int = 12) -> str:
    """生成随机密码"""
    import string
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def generate_user_id() -> str:
    """生成用户 ID"""
    import uuid
    return f"user_{uuid.uuid4().hex[:8]}"


@admin_app.post("/api/admin/users", response_model=CreateUserResponse)
async def create_user(
    request: CreateUserRequest,
    admin: str = Depends(verify_admin_token)
):
    """创建新用户（随机生成密码）"""
    # 生成用户 ID 和密码
    user_id = generate_user_id()
    password = generate_password()
    
    with get_db_session() as db:
        # 检查用户 ID 是否已存在
        existing = db.query(User).filter(User.user_id == user_id).first()
        if existing:
            user_id = generate_user_id()  # 重新生成
        
        # 创建用户
        user = User(
            user_id=user_id,
            nickname=request.nickname,
            balance=request.initial_balance,
            free_quota=request.initial_free_quota,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(user)
        
        # 记录初始余额交易
        if request.initial_balance > 0:
            tx = Transaction(
                user_id=user_id,
                type="admin_recharge",
                amount=request.initial_balance,
                balance_after=request.initial_balance,
                remark=f"新用户初始余额 (by {admin})",
                created_at=datetime.utcnow()
            )
            db.add(tx)
        
        # 记录免费额度
        if request.initial_free_quota > 0:
            tx = Transaction(
                user_id=user_id,
                type="free_grant",
                amount=request.initial_free_quota,
                balance_after=request.initial_balance,
                remark="新用户免费额度",
                created_at=datetime.utcnow()
            )
            db.add(tx)
        
        db.commit()
        
        log.info(
            "user_created | user_id={} | nickname={} | admin={}",
            user_id, request.nickname, admin
        )
        
        return CreateUserResponse(
            success=True,
            message=f"用户创建成功",
            user_id=user_id,
            password=password
        )


@admin_app.post("/api/admin/users/{user_id}/reset-password", response_model=ResetPasswordResponse)
async def reset_user_password(
    user_id: str,
    admin: str = Depends(verify_admin_token)
):
    """重置用户密码（随机生成新密码）"""
    new_password = generate_password()
    
    with get_db_session() as db:
        user = db.query(User).filter(User.user_id == user_id).first()
        
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        # 注意：HireStream 的 User 模型没有 password 字段
        # 密码存储在官网的数据库中
        # 这里只是生成密码，需要在官网数据库中更新
        
        log.info(
            "password_reset | user_id={} | admin={}",
            user_id, admin
        )
        
        return ResetPasswordResponse(
            success=True,
            message=f"密码已重置，请在官网后台更新",
            new_password=new_password
        )


class DeleteUserResponse(BaseModel):
    """删除用户响应"""
    success: bool
    message: str


@admin_app.delete("/api/admin/users/{user_id}", response_model=DeleteUserResponse)
async def delete_user(
    user_id: str,
    admin: str = Depends(verify_admin_token)
):
    """删除用户及其所有相关数据"""
    from models import UsageRecord
    
    with get_db_session() as db:
        user = db.query(User).filter(User.user_id == user_id).first()
        
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        # 记录用户信息用于日志
        nickname = user.nickname or user_id
        
        # 删除用户的使用记录
        usage_count = db.query(UsageRecord).filter(UsageRecord.user_id == user_id).delete()
        
        # 删除用户的交易记录
        tx_count = db.query(Transaction).filter(Transaction.user_id == user_id).delete()
        
        # 删除用户
        db.delete(user)
        db.commit()
        
        log.info(
            "user_deleted | user_id={} | nickname={} | usage_records={} | transactions={} | admin={}",
            user_id, nickname, usage_count, tx_count, admin
        )
        
        return DeleteUserResponse(
            success=True,
            message=f"用户 {nickname} 已删除，同时清理了 {usage_count} 条使用记录和 {tx_count} 条交易记录"
        )
