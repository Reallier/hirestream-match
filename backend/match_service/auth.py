# -*- coding: utf-8 -*-
"""
JWT Token 验证模块

支持从官网传递的 JWT Token 验证用户身份，
同时支持 Mock 模式用于开发测试。
"""

import os
from dataclasses import dataclass
from typing import Optional
import jwt
from dotenv import load_dotenv
from loguru import logger as log

load_dotenv()

# JWT 配置
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-key-change-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

# 认证模式：mock / jwt
USER_AUTH_MODE = os.getenv("USER_AUTH_MODE", "mock")


@dataclass
class UserInfo:
    """用户信息"""
    user_id: int  # 统一使用 Integer ID
    nickname: str
    avatar_url: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "nickname": self.nickname,
            "avatar_url": self.avatar_url
        }


def verify_jwt_token(token: str) -> Optional[UserInfo]:
    """
    验证 JWT Token 并解析用户信息
    
    Args:
        token: JWT Token 字符串
        
    Returns:
        UserInfo 如果验证成功，否则 None
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        
        # 统一使用 Integer user_id（2026 标准：纯整数格式）
        # 优先 id，其次 user_id
        user_id = payload.get("id") or payload.get("user_id")
        
        if not user_id:
            log.warning("jwt_verify_failed | reason=missing_user_id")
            return None
        
        return UserInfo(
            user_id=int(user_id),
            nickname=payload.get("nickname", payload.get("name", f"用户{user_id}")),
            avatar_url=payload.get("avatar_url", payload.get("avatar"))
        )
    except jwt.ExpiredSignatureError:
        log.warning("jwt_verify_failed | reason=token_expired")
        return None
    except jwt.InvalidTokenError as e:
        log.warning("jwt_verify_failed | reason=invalid_token | error={}", str(e))
        return None


def get_mock_user(mock_id: Optional[str] = None) -> UserInfo:
    """
    获取 Mock 用户（开发测试用）
    
    Args:
        mock_id: 可选的 mock 用户 ID，默认使用 id=1
        
    Returns:
        Mock 用户信息
    """
    # 支持数字或 "test_user_001" 等格式
    if mock_id and mock_id.isdigit():
        user_id = int(mock_id)
    else:
        user_id = 1  # 默认使用 id=1
    
    return UserInfo(
        user_id=user_id,
        nickname=f"测试用户 ({user_id})",
        avatar_url=None
    )


def authenticate_user(
    token: Optional[str] = None, 
    mock_id: Optional[str] = None
) -> Optional[UserInfo]:
    """
    认证用户
    
    根据 USER_AUTH_MODE 配置决定使用 JWT 还是 Mock 模式。
    
    Args:
        token: JWT Token（jwt 模式时需要）
        mock_id: Mock 用户 ID（mock 模式时可选）
        
    Returns:
        UserInfo 如果认证成功，否则 None
    """
    if USER_AUTH_MODE == "mock":
        log.info("auth_mode=mock | mock_id={}", mock_id)
        return get_mock_user(mock_id)
    
    elif USER_AUTH_MODE == "jwt":
        if not token:
            log.warning("auth_failed | reason=no_token")
            return None
        return verify_jwt_token(token)
    
    else:
        log.error("auth_failed | reason=unknown_mode | mode={}", USER_AUTH_MODE)
        return None


def generate_jwt_token(user_info: UserInfo, expires_in: int = 86400, email: str = None) -> str:
    """
    生成 JWT Token（用于测试或官网集成）
    
    Args:
        user_info: 用户信息
        expires_in: 过期时间（秒），默认 24 小时
        email: 可选的邮箱地址
        
    Returns:
        JWT Token 字符串
    """
    import time
    
    payload = {
        "id": user_info.user_id,  # 官网兼容
        "user_id": user_info.user_id,  # TalentAI 标准
        "nickname": user_info.nickname,
        "name": user_info.nickname,  # 官网兼容
        "avatar_url": user_info.avatar_url,
        "avatar": user_info.avatar_url,  # 官网兼容
        "email": email,  # 官网兼容
        "type": "access",  # 官网兼容 - 关键字段！
        "iat": int(time.time()),
        "exp": int(time.time()) + expires_in
    }
    
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
