# -*- coding: utf-8 -*-
"""
数据库模型定义

包含用户、使用记录、交易流水三个核心模型
用户表与官网共享（统一 users 表）
"""

from datetime import datetime
from sqlalchemy import Column, String, Integer, Numeric, DateTime, Text, ForeignKey, Index, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from database import Base


class User(Base):
    """用户模型（与官网共享）"""
    __tablename__ = "users"
    
    # 主键：与官网统一的自增 ID
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 官网用户信息
    email = Column(String(255), unique=True, nullable=True)
    username = Column(String(100), unique=True, nullable=True)
    password = Column(String(255), nullable=True)
    name = Column(String(100), nullable=True, comment="用户昵称")
    avatar = Column(Text, nullable=True, comment="头像URL")
    openid = Column(String(255), unique=True, nullable=True)
    unionid = Column(String(255), unique=True, nullable=True)
    role = Column(String(20), default="user")
    
    # 计费信息
    balance = Column(Numeric(12, 6), default=0.0, nullable=False, comment="账户余额（元）")
    free_quota = Column(Numeric(12, 6), default=0.0, nullable=False, comment="剩余免费额度（元）")
    
    # 数据存储同意
    consent_data_storage = Column(Boolean, nullable=True, comment="同意存储简历/JD数据")
    consent_updated_at = Column(DateTime, nullable=True, comment="同意更新时间")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    
    # 关联
    usage_records = relationship("UsageRecord", back_populates="user", lazy="dynamic")
    transactions = relationship("Transaction", back_populates="user", lazy="dynamic")
    match_records = relationship("MatchRecord", back_populates="user", lazy="dynamic")
    
    def __repr__(self):
        return f"<User(id={self.id}, name={self.name}, balance={self.balance})>"
    
    @property
    def user_id(self) -> int:
        """兼容旧代码的 user_id 属性"""
        return self.id
    
    @property
    def nickname(self) -> str:
        """兼容旧代码的 nickname 属性"""
        return self.name or f"用户{self.id}"
    
    @property
    def avatar_url(self) -> str:
        """兼容旧代码的 avatar_url 属性"""
        return self.avatar
    
    @property
    def total_available(self) -> float:
        """可用总额 = 余额 + 免费额度"""
        return float(self.balance or 0) + float(self.free_quota or 0)


class UsageRecord(Base):
    """使用记录模型"""
    __tablename__ = "hm_usage_records"
    
    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 用户关联（现在是 Integer）
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # 请求信息
    request_id = Column(String(64), nullable=False, unique=True, index=True, comment="请求唯一ID，用于幂等")
    operation = Column(String(20), nullable=False, comment="操作类型：ocr/analysis")
    
    # 模型和 Token 信息
    model = Column(String(50), nullable=False, comment="使用的模型")
    prompt_tokens = Column(Integer, default=0, comment="输入Token数")
    completion_tokens = Column(Integer, default=0, comment="输出Token数")
    
    # 费用
    cost = Column(Numeric(12, 6), default=0.0, nullable=False, comment="本次花费（元）")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="使用时间")
    
    # 关联
    user = relationship("User", back_populates="usage_records")
    
    # 索引：按用户+时间查询
    __table_args__ = (
        Index("idx_usage_user_created", "user_id", "created_at"),
    )
    
    def __repr__(self):
        return f"<UsageRecord(id={self.id}, user_id={self.user_id}, operation={self.operation}, cost={self.cost})>"
    
    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens


class Transaction(Base):
    """交易流水模型"""
    __tablename__ = "hm_transactions"
    
    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 用户关联（现在是 Integer）
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # 交易信息
    type = Column(String(20), nullable=False, comment="类型：recharge/deduct/refund/free_grant")
    amount = Column(Numeric(12, 6), nullable=False, comment="金额（充值正数，扣费负数）")
    balance_after = Column(Numeric(12, 6), nullable=False, comment="交易后余额")
    
    # 关联信息
    reference_id = Column(String(64), nullable=True, comment="关联ID（充值单号/usage_record.request_id）")
    remark = Column(Text, nullable=True, comment="备注")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="交易时间")
    
    # 关联
    user = relationship("User", back_populates="transactions")
    
    # 索引：按用户+时间查询
    __table_args__ = (
        Index("idx_trans_user_created", "user_id", "created_at"),
    )
    
    def __repr__(self):
        return f"<Transaction(id={self.id}, user_id={self.user_id}, type={self.type}, amount={self.amount})>"


class MatchRecord(Base):
    """匹配记录模型 - 存储用户同意后的简历匹配数据"""
    __tablename__ = "hm_match_records"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # 输入内容
    jd_text = Column(Text, nullable=False, comment="职位描述")
    resume_text = Column(Text, nullable=False, comment="简历文本")
    resume_filename = Column(String(255), nullable=True, comment="简历文件名")
    
    # 输出结果
    match_score = Column(Integer, nullable=True, comment="匹配分数 0-100")
    report_json = Column(JSONB, nullable=True, comment="完整报告 JSON")
    
    # Token 用量
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    cost = Column(Numeric(12, 6), default=0)
    
    # 时间
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关联
    user = relationship("User", back_populates="match_records")
    
    __table_args__ = (
        Index("idx_match_records_user", "user_id", "created_at"),
    )
    
    def __repr__(self):
        return f"<MatchRecord(id={self.id}, user_id={self.user_id}, score={self.match_score})>"


class Feedback(Base):
    """用户反馈模型"""
    __tablename__ = "hm_feedbacks"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    
    # 反馈内容
    type = Column(String(50), default="suggestion", comment="suggestion, bug, other")
    content = Column(Text, nullable=False)
    contact = Column(String(255), nullable=True, comment="联系方式")
    page = Column(String(255), nullable=True, comment="来源页面")
    
    # 状态
    status = Column(String(50), default="pending", comment="pending, reviewed, resolved")
    admin_note = Column(Text, nullable=True)
    
    # 时间
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联
    user = relationship("User", backref="feedbacks")
    
    def __repr__(self):
        return f"<Feedback(id={self.id}, type={self.type}, status={self.status})>"
