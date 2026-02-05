"""
License 中间件

用于在私有化部署模式下验证 License 有效性。
"""
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional
from enum import Enum

from .validator import get_license_status, get_stored_license, verify_license


class AuthMode(str, Enum):
    """认证模式"""
    SAAS = "saas"       # SaaS模式：使用 Identity HUB，无需本地 License
    PRIVATE = "private"  # 私有化模式：使用本地 License + 本地认证
    OFFLINE = "offline"  # 离线模式：使用本地 License + 完全离线


def get_auth_mode() -> AuthMode:
    """获取当前认证模式"""
    import os
    mode = os.getenv("AUTH_MODE", "saas").lower()
    try:
        return AuthMode(mode)
    except ValueError:
        return AuthMode.SAAS


# 不需要 License 校验的路径白名单
LICENSE_EXEMPT_PATHS = {
    "/",
    "/health",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/api/license/machine-id",
    "/api/license/status",
    "/api/license/activate",
}


class LicenseMiddleware(BaseHTTPMiddleware):
    """
    License 验证中间件
    
    在私有化/离线模式下，验证 License 有效性。
    未激活或过期的 License 将阻止 API 访问。
    """
    
    def __init__(self, app, public_key: Optional[str] = None):
        super().__init__(app)
        self.public_key = public_key
    
    async def dispatch(self, request: Request, call_next):
        # 获取认证模式
        mode = get_auth_mode()
        
        # SaaS 模式不需要 License 校验
        if mode == AuthMode.SAAS:
            return await call_next(request)
        
        # 检查白名单路径
        path = request.url.path
        if path in LICENSE_EXEMPT_PATHS:
            return await call_next(request)
        
        # 静态资源跳过
        if path.startswith("/static") or path.startswith("/_nuxt"):
            return await call_next(request)
        
        # 私有化/离线模式需要验证 License
        status = get_license_status(self.public_key)
        
        if not status.is_activated:
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "LICENSE_NOT_ACTIVATED",
                    "message": "系统未激活，请联系管理员导入 License",
                    "machine_id_endpoint": "/api/license/machine-id",
                    "activate_endpoint": "/api/license/activate",
                }
            )
        
        if not status.is_valid:
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "LICENSE_INVALID",
                    "message": status.error or "License 无效或已过期",
                    "expires_at": str(status.expires_at) if status.expires_at else None,
                }
            )
        
        # License 有效，继续处理请求
        # 将 License 信息附加到请求状态
        request.state.license = status
        
        return await call_next(request)


def require_license_feature(feature: str):
    """
    装饰器：要求特定 License 功能
    
    用法:
        @router.get("/api/some-feature")
        @require_license_feature("api_access")
        async def some_feature():
            ...
    """
    def decorator(func):
        async def wrapper(request: Request, *args, **kwargs):
            # 检查 License 功能
            license_status = getattr(request.state, "license", None)
            
            if license_status and feature not in license_status.features:
                raise HTTPException(
                    status_code=403,
                    detail={
                        "error": "FEATURE_NOT_LICENSED",
                        "message": f"当前 License 不包含 '{feature}' 功能",
                        "current_features": license_status.features,
                        "required_feature": feature,
                    }
                )
            
            return await func(request, *args, **kwargs)
        
        # 保留原函数的元数据
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        
        return wrapper
    return decorator


def get_license_limits(request: Request) -> dict:
    """
    获取当前 License 限制
    
    Args:
        request: FastAPI 请求对象
        
    Returns:
        dict: 包含 max_users, max_concurrency 等限制
    """
    license_status = getattr(request.state, "license", None)
    
    if not license_status:
        # 未激活或 SaaS 模式，返回默认值
        return {
            "max_users": float("inf"),
            "max_concurrency": float("inf"),
            "features": [],
        }
    
    return {
        "max_users": license_status.max_users or float("inf"),
        "max_concurrency": license_status.max_concurrency or float("inf"),
        "features": license_status.features or [],
    }
