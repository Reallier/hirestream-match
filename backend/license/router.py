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
