# -*- coding: utf-8 -*-
"""
数据库模型定义

包含用户、使用记录、交易流水三个核心模型
"""

from datetime import datetime
from sqlalchemy import Column, String, Integer, Numeric, DateTime, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from database import Base


class User(Base):
    """用户模型"""
    __tablename__ = "hm_users"
    
    # 主键：来自官网的用户 ID
    user_id = Column(String(64), primary_key=True, index=True)
    
    # 用户信息
    nickname = Column(String(100), nullable=True, comment="用户昵称")
    avatar_url = Column(Text, nullable=True, comment="头像URL")
    
    # 账户信息
    balance = Column(Numeric(12, 6), default=0.0, nullable=False, comment="账户余额（元）")
    free_quota = Column(Numeric(12, 6), default=0.0, nullable=False, comment="剩余免费额度（元）")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    
    # 关联
    usage_records = relationship("UsageRecord", back_populates="user", lazy="dynamic")
    transactions = relationship("Transaction", back_populates="user", lazy="dynamic")
    
    def __repr__(self):
        return f"<User(user_id={self.user_id}, nickname={self.nickname}, balance={self.balance})>"
    
    @property
    def total_available(self) -> float:
        """可用总额 = 余额 + 免费额度"""
        return float(self.balance) + float(self.free_quota)


class UsageRecord(Base):
    """使用记录模型"""
    __tablename__ = "hm_usage_records"
    
    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 用户关联
    user_id = Column(String(64), ForeignKey("users.user_id"), nullable=False, index=True)
    
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
        Index("idx_user_created", "user_id", "created_at"),
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
    
    # 用户关联
    user_id = Column(String(64), ForeignKey("users.user_id"), nullable=False, index=True)
    
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
