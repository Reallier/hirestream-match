"""
机器指纹生成模块

用于生成服务器唯一标识，绑定 License 授权。
"""
import hashlib
import platform
import uuid
import os
from pathlib import Path
from datetime import datetime, timezone


# 持久化 UUID 文件路径（兜底策略）
_FALLBACK_UUID_FILE = Path("/app/.machine_uuid")


def _get_mac_address() -> str:
    """获取 MAC 地址"""
    try:
        mac = uuid.getnode()
        # 验证 MAC 地址有效性（非随机生成）
        if (mac >> 40) % 2:  # 检查是否为随机生成
            return ""
        return hex(mac)
    except Exception:
        return ""


def _get_platform_info() -> str:
    """获取平台信息"""
    return f"{platform.system()}-{platform.machine()}-{platform.processor()}"


def _get_or_create_fallback_uuid() -> str:
    """
    获取或创建兜底 UUID
    
    在容器环境中可能无法获取硬件信息，此时使用持久化文件存储的 UUID。
    """
    fallback_path = _FALLBACK_UUID_FILE
    
    # 尝试多个可能的路径
    possible_paths = [
        Path("/app/.machine_uuid"),
        Path.home() / ".talentai_machine_uuid",
        Path(".machine_uuid"),
    ]
    
    for path in possible_paths:
        try:
            if path.exists():
                return path.read_text().strip()
        except Exception:
            continue
    
    # 如果都不存在，创建新的 UUID
    new_uuid = str(uuid.uuid4())
    for path in possible_paths:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(new_uuid)
            return new_uuid
        except Exception:
            continue
    
    # 最后兜底：返回临时 UUID（每次重启会变化，不推荐）
    return new_uuid


def get_machine_id() -> str:
    """
    生成机器指纹
    
    组合 MAC 地址、平台信息等生成唯一 hash。
    如果硬件信息不可用，使用持久化 UUID 兜底。
    
    Returns:
        str: 32位十六进制字符串（MD5 hash）
    """
    mac = _get_mac_address()
    platform_info = _get_platform_info()
    
    # 如果 MAC 地址可用，使用硬件信息组合
    if mac:
        raw = f"{mac}:{platform_info}"
    else:
        # 兜底：使用持久化 UUID
        fallback_uuid = _get_or_create_fallback_uuid()
        raw = f"fallback:{fallback_uuid}:{platform_info}"
    
    # 生成 MD5 hash
    return hashlib.md5(raw.encode()).hexdigest()


def get_platform_name() -> str:
    """获取平台友好名称"""
    return f"{platform.system()} {platform.release()}"


def get_machine_info() -> dict:
    """
    获取完整的机器信息
    
    Returns:
        dict: 包含 machine_id, platform, generated_at
    """
    return {
        "machine_id": get_machine_id(),
        "platform": get_platform_name(),
        "generated_at": datetime.now(timezone.utc),
    }
