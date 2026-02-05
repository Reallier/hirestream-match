"""
License API 路由

提供 License 管理相关的 HTTP 接口。
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from datetime import datetime, timezone

from .models import (
    MachineIdResponse,
    LicenseStatus,
    LicenseActivateRequest,
    LicenseActivateResponse,
)
from .machine_id import get_machine_info
from .validator import (
    get_license_status,
    verify_license,
    store_license,
    remove_license,
    get_stored_license,
)

# 创建路由
router = APIRouter(prefix="/api/license", tags=["License 授权"])


def get_public_key() -> Optional[str]:
    """
    获取 License 公钥
    
    优先级：
    1. 环境变量 LICENSE_PUBLIC_KEY
    2. 文件 /app/license_public_key.pem
    3. 配置中的 license_public_key
    """
    import os
    from pathlib import Path
    
    # 1. 环境变量
    public_key = os.getenv("LICENSE_PUBLIC_KEY")
    if public_key:
        # 处理可能的 \n 转义
        return public_key.replace("\\n", "\n")
    
    # 2. 文件读取
    key_paths = [
        Path("/app/license_public_key.pem"),
        Path("license_public_key.pem"),
        Path("/data/license_public_key.pem"),
    ]
    for key_path in key_paths:
        if key_path.exists():
            return key_path.read_text()
    
    # 3. 配置文件
    try:
        from config import settings
        return getattr(settings, "license_public_key", None)
    except Exception:
        return None


@router.get("/machine-id", response_model=MachineIdResponse)
async def get_machine_id_endpoint():
    """
    获取服务器机器指纹
    
    用于申请 License 时提交给 INTJsys。
    """
    info = get_machine_info()
    return MachineIdResponse(
        machine_id=info["machine_id"],
        platform=info["platform"],
        generated_at=info["generated_at"],
    )


@router.get("/status", response_model=LicenseStatus)
async def get_license_status_endpoint():
    """
    获取当前 License 状态
    
    返回授权是否有效、版本、功能模块、剩余天数等信息。
    """
    public_key = get_public_key()
    return get_license_status(public_key)


@router.post("/activate", response_model=LicenseActivateResponse)
async def activate_license(request: LicenseActivateRequest):
    """
    激活 License
    
    验证并存储 License Key。激活成功后，系统功能将根据授权解锁。
    """
    public_key = get_public_key()
    
    if not public_key:
        raise HTTPException(
            status_code=500,
            detail="服务器未配置 License 公钥，无法验证授权"
        )
    
    # 验证 License
    is_valid, license_data, error = verify_license(request.license_key, public_key)
    
    if not is_valid:
        return LicenseActivateResponse(
            success=False,
            message=f"License 验证失败: {error}",
            status=None,
        )
    
    # 存储 License
    if not store_license(request.license_key):
        raise HTTPException(
            status_code=500,
            detail="License 验证成功，但存储失败。请检查服务器文件权限。"
        )
    
    # 返回激活后的状态
    status = get_license_status(public_key)
    
    return LicenseActivateResponse(
        success=True,
        message=f"License 激活成功！欢迎 {license_data.customer}，{license_data.edition} 版授权已生效。",
        status=status,
    )


@router.post("/deactivate")
async def deactivate_license():
    """
    注销 License
    
    用于服务器迁移前解除授权绑定。
    
    ⚠️ 注销后需要重新申请 License 才能使用系统。
    """
    # 检查是否已激活
    if not get_stored_license():
        raise HTTPException(
            status_code=400,
            detail="当前未激活任何 License"
        )
    
    # 移除 License
    if not remove_license():
        raise HTTPException(
            status_code=500,
            detail="License 注销失败，请检查文件权限"
        )
    
    return {
        "success": True,
        "message": "License 已注销。如需迁移到新服务器，请使用新机器的 Machine ID 重新申请授权。"
    }


# ============ Admin API: License 生成 ============

from .models import LicenseGenerateRequest, LicenseGenerateResponse


def get_private_key() -> Optional[str]:
    """
    获取 License 私钥 (仅限 Admin 使用)
    
    优先级：
    1. 环境变量 LICENSE_PRIVATE_KEY
    2. 文件 /app/license_private_key.pem
    """
    import os
    from pathlib import Path
    
    # 1. 环境变量
    private_key = os.getenv("LICENSE_PRIVATE_KEY")
    if private_key:
        return private_key.replace("\\n", "\n")
    
    # 2. 文件读取
    key_paths = [
        Path("/app/license_private_key.pem"),
        Path("license_private_key.pem"),
        Path("/data/license_private_key.pem"),
    ]
    for key_path in key_paths:
        if key_path.exists():
            return key_path.read_text()
    
    return None


def generate_license_key(
    private_key: str,
    machine_id: str,
    customer: str,
    edition: str = "professional",
    max_users: int = None,
    max_concurrency: int = None,
    days: int = 365,
) -> tuple:
    """
    生成 License Key (核心逻辑)
    
    Returns:
        (license_key, payload_dict)
    """
    import jwt
    from datetime import timedelta
    
    # 版本默认配置
    edition_defaults = {
        "standard": {"max_users": 50, "max_concurrency": 5, "features": ["instant_match", "talent_pool"]},
        "professional": {"max_users": 200, "max_concurrency": 20, "features": ["instant_match", "talent_pool", "jd_search", "api_access"]},
        "enterprise": {"max_users": 1000, "max_concurrency": 50, "features": ["instant_match", "talent_pool", "jd_search", "api_access", "custom_model", "sso"]},
        "flagship": {"max_users": 99999, "max_concurrency": 100, "features": ["instant_match", "talent_pool", "jd_search", "api_access", "custom_model", "sso", "source_code"]},
    }
    
    defaults = edition_defaults.get(edition, edition_defaults["professional"])
    
    if max_users is None:
        max_users = defaults["max_users"]
    if max_concurrency is None:
        max_concurrency = defaults["max_concurrency"]
    
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(days=days)
    lic_id = f"LIC-{now.strftime('%Y%m%d')}-{machine_id[:8].upper()}"
    
    payload = {
        "lic_id": lic_id,
        "customer": customer,
        "machine_id": machine_id,
        "edition": edition,
        "max_users": max_users,
        "max_concurrency": max_concurrency,
        "features": defaults["features"],
        "issued_at": now.isoformat(),
        "expires_at": expires_at.isoformat(),
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    
    token = jwt.encode(payload, private_key, algorithm="RS256")
    return token, payload


@router.post("/generate", response_model=LicenseGenerateResponse)
async def generate_license_endpoint(request: LicenseGenerateRequest):
    """
    生成 License (Admin API)
    
    ⚠️ 仅限管理员使用。需要服务器配置私钥。
    
    生成指定客户和机器的 License Key，可选发送邮件通知。
    """
    # 获取私钥
    private_key = get_private_key()
    
    if not private_key:
        raise HTTPException(
            status_code=500,
            detail="服务器未配置 License 私钥，无法生成授权。请在环境变量或文件中配置 LICENSE_PRIVATE_KEY。"
        )
    
    try:
        # 生成 License
        license_key, payload = generate_license_key(
            private_key=private_key,
            machine_id=request.machine_id,
            customer=request.customer,
            edition=request.edition.value if hasattr(request.edition, 'value') else request.edition,
            max_users=request.max_users,
            max_concurrency=request.max_concurrency,
            days=request.days,
        )
        
        return LicenseGenerateResponse(
            success=True,
            message=f"License 生成成功！客户: {request.customer}, 版本: {request.edition}, 有效期: {request.days} 天",
            license_key=license_key,
            lic_id=payload["lic_id"],
            expires_at=datetime.fromisoformat(payload["expires_at"]),
            email_sent=False,  # 邮件发送由官网 Admin 处理
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"License 生成失败: {str(e)}"
        )
