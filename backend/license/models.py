"""
License 数据模型
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum


class LicenseEdition(str, Enum):
    """授权版本"""
    STANDARD = "standard"       # 标准版
    PROFESSIONAL = "professional"  # 专业版
    ENTERPRISE = "enterprise"   # 企业版
    FLAGSHIP = "flagship"       # 旗舰版


class LicenseData(BaseModel):
    """License 解码后的载荷结构"""
    lic_id: str = Field(..., description="License ID")
    customer: str = Field(..., description="客户名称")
    machine_id: str = Field(..., description="绑定的机器指纹")
    edition: LicenseEdition = Field(..., description="授权版本")
    max_users: int = Field(default=50, description="用户数上限")
    max_concurrency: int = Field(default=5, description="并发数上限")
    features: List[str] = Field(default_factory=list, description="解锁的功能模块")
    issued_at: datetime = Field(..., description="签发时间")
    expires_at: datetime = Field(..., description="过期时间")
    
    class Config:
        use_enum_values = True


class LicenseStatus(BaseModel):
    """License 状态 API 响应"""
    is_valid: bool = Field(..., description="License 是否有效")
    is_activated: bool = Field(..., description="是否已激活")
    edition: Optional[str] = Field(None, description="当前版本")
    customer: Optional[str] = Field(None, description="客户名称")
    max_users: Optional[int] = Field(None, description="用户上限")
    max_concurrency: Optional[int] = Field(None, description="并发上限")
    features: List[str] = Field(default_factory=list, description="已解锁功能")
    expires_at: Optional[datetime] = Field(None, description="过期时间")
    days_remaining: Optional[int] = Field(None, description="剩余天数")
    error: Optional[str] = Field(None, description="错误信息")


class MachineIdResponse(BaseModel):
    """机器指纹 API 响应"""
    machine_id: str = Field(..., description="服务器机器指纹")
    platform: str = Field(..., description="操作系统平台")
    generated_at: datetime = Field(..., description="生成时间")


class LicenseActivateRequest(BaseModel):
    """License 激活请求"""
    license_key: str = Field(..., description="License 密钥 (JWT格式)")


class LicenseActivateResponse(BaseModel):
    """License 激活响应"""
    success: bool = Field(..., description="激活是否成功")
    message: str = Field(..., description="结果消息")
    status: Optional[LicenseStatus] = Field(None, description="激活后的状态")


class LicenseGenerateRequest(BaseModel):
    """License 生成请求 (Admin API)"""
    customer: str = Field(..., description="客户名称")
    machine_id: str = Field(..., description="客户服务器机器指纹")
    edition: LicenseEdition = Field(default=LicenseEdition.PROFESSIONAL, description="授权版本")
    days: int = Field(default=365, description="有效天数")
    max_users: Optional[int] = Field(None, description="用户数上限 (不填则使用版本默认值)")
    max_concurrency: Optional[int] = Field(None, description="并发数上限 (不填则使用版本默认值)")
    customer_email: Optional[str] = Field(None, description="客户邮箱 (用于发送授权邮件)")


class LicenseGenerateResponse(BaseModel):
    """License 生成响应 (Admin API)"""
    success: bool = Field(..., description="生成是否成功")
    message: str = Field(..., description="结果消息")
    license_key: Optional[str] = Field(None, description="生成的 License Key (JWT)")
    lic_id: Optional[str] = Field(None, description="License ID")
    expires_at: Optional[datetime] = Field(None, description="过期时间")
    email_sent: bool = Field(default=False, description="是否已发送邮件")
