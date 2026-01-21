"""
License 验证模块

负责验证 License 密钥的有效性（JWT + RSA 签名）
"""
import jwt
from datetime import datetime, timezone
from typing import Optional, Tuple
from pathlib import Path

from .models import LicenseData, LicenseStatus
from .machine_id import get_machine_id

# License 存储文件路径
_LICENSE_FILE_PATHS = [
    Path("/app/.license"),
    Path.home() / ".talentai_license",
    Path(".license"),
]


class LicenseValidationError(Exception):
    """License 验证错误"""
    pass


def _get_license_file_path() -> Path:
    """获取可用的 License 文件路径"""
    for path in _LICENSE_FILE_PATHS:
        try:
            if path.exists():
                return path
            # 检查是否可写
            path.parent.mkdir(parents=True, exist_ok=True)
            return path
        except Exception:
            continue
    return _LICENSE_FILE_PATHS[-1]  # 使用当前目录作为最后选项


def get_stored_license() -> Optional[str]:
    """
    获取已存储的 License Key
    
    Returns:
        Optional[str]: License Key 或 None（如未激活）
    """
    for path in _LICENSE_FILE_PATHS:
        try:
            if path.exists():
                return path.read_text().strip()
        except Exception:
            continue
    return None


def store_license(license_key: str) -> bool:
    """
    存储 License Key 到本地文件
    
    Args:
        license_key: 要存储的 License Key
        
    Returns:
        bool: 是否存储成功
    """
    path = _get_license_file_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(license_key)
        return True
    except Exception:
        return False


def remove_license() -> bool:
    """
    移除已存储的 License
    
    Returns:
        bool: 是否移除成功
    """
    for path in _LICENSE_FILE_PATHS:
        try:
            if path.exists():
                path.unlink()
                return True
        except Exception:
            continue
    return False


def decode_license(license_key: str, public_key: str) -> LicenseData:
    """
    解码并验证 License Key
    
    Args:
        license_key: JWT 格式的 License Key
        public_key: RSA 公钥（PEM 格式）
        
    Returns:
        LicenseData: 解码后的 License 数据
        
    Raises:
        LicenseValidationError: 验证失败时抛出
    """
    try:
        # 解码 JWT
        payload = jwt.decode(
            license_key,
            public_key,
            algorithms=["RS256"],
            options={"require": ["exp", "iat"]}
        )
        
        # 解析日期字段
        issued_at = datetime.fromisoformat(payload["issued_at"]) if isinstance(payload.get("issued_at"), str) else datetime.fromtimestamp(payload.get("iat", 0), tz=timezone.utc)
        expires_at = datetime.fromisoformat(payload["expires_at"]) if isinstance(payload.get("expires_at"), str) else datetime.fromtimestamp(payload.get("exp", 0), tz=timezone.utc)
        
        return LicenseData(
            lic_id=payload["lic_id"],
            customer=payload["customer"],
            machine_id=payload["machine_id"],
            edition=payload["edition"],
            max_users=payload.get("max_users", 50),
            max_concurrency=payload.get("max_concurrency", 5),
            features=payload.get("features", []),
            issued_at=issued_at,
            expires_at=expires_at,
        )
        
    except jwt.ExpiredSignatureError:
        raise LicenseValidationError("License 已过期")
    except jwt.InvalidSignatureError:
        raise LicenseValidationError("License 签名无效")
    except jwt.DecodeError as e:
        raise LicenseValidationError(f"License 格式错误: {str(e)}")
    except KeyError as e:
        raise LicenseValidationError(f"License 缺少必要字段: {str(e)}")
    except Exception as e:
        raise LicenseValidationError(f"License 验证失败: {str(e)}")


def verify_license(license_key: str, public_key: str) -> Tuple[bool, Optional[LicenseData], Optional[str]]:
    """
    完整验证 License
    
    包括：JWT 解码、签名验证、机器指纹匹配、过期检查。
    
    Args:
        license_key: JWT 格式的 License Key
        public_key: RSA 公钥（PEM 格式）
        
    Returns:
        Tuple[bool, Optional[LicenseData], Optional[str]]: 
            (是否有效, License数据, 错误信息)
    """
    try:
        # 1. 解码并验证签名
        license_data = decode_license(license_key, public_key)
        
        # 2. 验证机器指纹
        current_machine_id = get_machine_id()
        if license_data.machine_id != current_machine_id:
            return False, None, f"机器指纹不匹配 (期望: {license_data.machine_id[:8]}..., 当前: {current_machine_id[:8]}...)"
        
        # 3. 检查是否过期
        now = datetime.now(timezone.utc)
        if license_data.expires_at.tzinfo is None:
            expires_at = license_data.expires_at.replace(tzinfo=timezone.utc)
        else:
            expires_at = license_data.expires_at
            
        if now > expires_at:
            return False, license_data, "License 已过期"
        
        return True, license_data, None
        
    except LicenseValidationError as e:
        return False, None, str(e)
    except Exception as e:
        return False, None, f"未知错误: {str(e)}"


def get_license_status(public_key: Optional[str]) -> LicenseStatus:
    """
    获取当前 License 状态
    
    Args:
        public_key: RSA 公钥（如果为 None，返回未配置状态）
        
    Returns:
        LicenseStatus: 当前状态
    """
    stored_key = get_stored_license()
    
    # 检查是否已激活
    if not stored_key:
        return LicenseStatus(
            is_valid=False,
            is_activated=False,
            error="未激活：请导入 License Key"
        )
    
    # 检查公钥是否配置
    if not public_key:
        return LicenseStatus(
            is_valid=False,
            is_activated=True,
            error="公钥未配置：无法验证 License"
        )
    
    # 验证 License
    is_valid, license_data, error = verify_license(stored_key, public_key)
    
    if not is_valid:
        return LicenseStatus(
            is_valid=False,
            is_activated=True,
            error=error
        )
    
    # 计算剩余天数
    now = datetime.now(timezone.utc)
    expires_at = license_data.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    days_remaining = (expires_at - now).days
    
    return LicenseStatus(
        is_valid=True,
        is_activated=True,
        edition=license_data.edition,
        customer=license_data.customer,
        max_users=license_data.max_users,
        max_concurrency=license_data.max_concurrency,
        features=license_data.features,
        expires_at=license_data.expires_at,
        days_remaining=max(0, days_remaining),
    )
