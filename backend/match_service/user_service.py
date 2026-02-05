# -*- coding: utf-8 -*-
"""
用户服务层

提供用户管理、余额检查、扣费、使用记录等核心业务逻辑
"""

import os
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func

# 处理模块导入路径问题 - 同时支持直接运行和被外部导入
try:
    from .database import get_db, get_db_session
    from .models import User, UsageRecord, Transaction
    from .auth import UserInfo
    from .log import logger as log
except ImportError:
    from database import get_db, get_db_session
    from models import User, UsageRecord, Transaction
    from auth import UserInfo
    from log import logger as log

from dotenv import load_dotenv

load_dotenv()

# 新用户默认免费额度（元）
DEFAULT_FREE_QUOTA = float(os.getenv("DEFAULT_FREE_QUOTA", "1.0"))


@dataclass
class BalanceCheckResult:
    """余额检查结果"""
    sufficient: bool
    balance: float
    free_quota: float
    total_available: float
    estimated_cost: float
    message: str


@dataclass
class DeductResult:
    """扣费结果"""
    success: bool
    deducted_from_free: float
    deducted_from_balance: float
    total_deducted: float
    balance_after: float
    free_quota_after: float
    message: str


class UserService:
    """用户服务类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_or_create_user(self, user_info: UserInfo) -> User:
        """
        获取或创建用户
        
        Args:
            user_info: 用户信息（来自 JWT 或 Mock）
            
        Returns:
            User 模型实例
        """
        user = self.db.query(User).filter(User.id == user_info.user_id).first()
        
        if user:
            # 更新用户信息（如果有变化）
            if user_info.nickname and user.name != user_info.nickname:
                user.name = user_info.nickname
            if user_info.avatar_url and user.avatar != user_info.avatar_url:
                user.avatar = user_info.avatar_url
            user.updated_at = datetime.utcnow()
            log.info("user_updated | user_id={}", user.id)
        else:
            # 创建新用户（注意：正常情况下用户应该在官网已创建）
            user = User(
                id=user_info.user_id,
                name=user_info.nickname,
                avatar=user_info.avatar_url,
                balance=0.0,
                free_quota=DEFAULT_FREE_QUOTA,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            self.db.add(user)
            
            # 记录免费额度发放
            if DEFAULT_FREE_QUOTA > 0:
                grant_tx = Transaction(
                    user_id=user_info.user_id,
                    type="free_grant",
                    amount=DEFAULT_FREE_QUOTA,
                    balance_after=0.0,
                    reference_id=None,
                    remark=f"新用户免费额度 ¥{DEFAULT_FREE_QUOTA}",
                    created_at=datetime.utcnow()
                )
                self.db.add(grant_tx)
            
            log.info("user_created | user_id={} | free_quota={}", user.id, DEFAULT_FREE_QUOTA)
        
        self.db.commit()
        return user
    
    def get_user(self, user_id: int) -> Optional[User]:
        """获取用户"""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def check_balance(self, user_id: int, estimated_cost: float = 0.0) -> BalanceCheckResult:
        """
        检查用户余额是否足够
        
        Args:
            user_id: 用户 ID
            estimated_cost: 预估费用（元），用于预检查
            
        Returns:
            BalanceCheckResult 余额检查结果
        """
        user = self.get_user(user_id)
        
        if not user:
            return BalanceCheckResult(
                sufficient=False,
                balance=0.0,
                free_quota=0.0,
                total_available=0.0,
                estimated_cost=estimated_cost,
                message="用户不存在"
            )
        
        total_available = user.total_available
        sufficient = total_available >= estimated_cost
        
        if sufficient:
            message = f"余额充足（可用 ¥{total_available:.4f}）"
        else:
            message = f"余额不足（可用 ¥{total_available:.4f}，需要 ¥{estimated_cost:.4f}）"
        
        return BalanceCheckResult(
            sufficient=sufficient,
            balance=user.balance,
            free_quota=user.free_quota,
            total_available=total_available,
            estimated_cost=estimated_cost,
            message=message
        )
    
    def record_usage(
        self,
        user_id: int,
        request_id: str,
        operation: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        cost: float
    ) -> UsageRecord:
        """
        记录使用量
        
        Args:
            user_id: 用户 ID
            request_id: 请求唯一 ID
            operation: 操作类型（ocr/analysis）
            model: 模型名称
            prompt_tokens: 输入 Token 数
            completion_tokens: 输出 Token 数
            cost: 费用（元）
            
        Returns:
            UsageRecord 使用记录
        """
        # 检查是否已存在（幂等）
        existing = self.db.query(UsageRecord).filter(UsageRecord.request_id == request_id).first()
        if existing:
            log.info("usage_record_exists | request_id={}", request_id)
            return existing
        
        record = UsageRecord(
            user_id=user_id,
            request_id=request_id,
            operation=operation,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost=cost,
            created_at=datetime.utcnow()
        )
        self.db.add(record)
        self.db.commit()
        
        log.info("usage_recorded | user_id={} | request_id={} | operation={} | cost={}", 
                 user_id, request_id, operation, cost)
        
        return record
    
    def deduct_balance(self, user_id: int, cost: float, reference_id: str, remark: str = "") -> DeductResult:
        """
        扣除余额
        
        优先从免费额度扣除，不足部分从余额扣除
        
        Args:
            user_id: 用户 ID
            cost: 扣费金额（元）
            reference_id: 关联 ID（通常是 request_id）
            remark: 备注
            
        Returns:
            DeductResult 扣费结果
        """
        # 将 cost 转换为 Decimal 以匹配数据库字段类型
        cost = Decimal(str(cost))
        
        user = self.get_user(user_id)
        
        if not user:
            return DeductResult(
                success=False,
                deducted_from_free=0.0,
                deducted_from_balance=0.0,
                total_deducted=0.0,
                balance_after=0.0,
                free_quota_after=0.0,
                message="用户不存在"
            )
        
        if user.total_available < cost:
            return DeductResult(
                success=False,
                deducted_from_free=0.0,
                deducted_from_balance=0.0,
                total_deducted=0.0,
                balance_after=user.balance,
                free_quota_after=user.free_quota,
                message=f"余额不足（可用 ¥{user.total_available:.4f}，需要 ¥{cost:.4f}）"
            )
        
        # 优先从免费额度扣除
        deducted_from_free = 0.0
        deducted_from_balance = 0.0
        
        if user.free_quota >= cost:
            # 免费额度足够
            deducted_from_free = cost
            user.free_quota -= cost
        elif user.free_quota > 0:
            # 免费额度部分覆盖
            deducted_from_free = user.free_quota
            deducted_from_balance = cost - user.free_quota
            user.free_quota = 0.0
            user.balance -= deducted_from_balance
        else:
            # 全部从余额扣除
            deducted_from_balance = cost
            user.balance -= cost
        
        user.updated_at = datetime.utcnow()
        
        # 记录交易流水
        tx = Transaction(
            user_id=user_id,
            type="deduct",
            amount=-cost,  # 扣费为负数
            balance_after=user.balance,
            reference_id=reference_id,
            remark=remark or f"服务使用扣费",
            created_at=datetime.utcnow()
        )
        self.db.add(tx)
        self.db.commit()
        
        log.info("balance_deducted | user_id={} | cost={} | from_free={} | from_balance={} | balance_after={}",
                 user_id, cost, deducted_from_free, deducted_from_balance, user.balance)
        
        return DeductResult(
            success=True,
            deducted_from_free=deducted_from_free,
            deducted_from_balance=deducted_from_balance,
            total_deducted=cost,
            balance_after=user.balance,
            free_quota_after=user.free_quota,
            message="扣费成功"
        )
    
    def add_balance(self, user_id: int, amount: float, reference_id: str, remark: str = "") -> bool:
        """
        充值余额
        
        Args:
            user_id: 用户 ID
            amount: 充值金额（元，正数）
            reference_id: 充值单号
            remark: 备注
            
        Returns:
            是否成功
        """
        if amount <= 0:
            return False
        
        user = self.get_user(user_id)
        if not user:
            return False
        
        user.balance += amount
        user.updated_at = datetime.utcnow()
        
        # 记录交易流水
        tx = Transaction(
            user_id=user_id,
            type="recharge",
            amount=amount,
            balance_after=user.balance,
            reference_id=reference_id,
            remark=remark or f"账户充值",
            created_at=datetime.utcnow()
        )
        self.db.add(tx)
        self.db.commit()
        
        log.info("balance_added | user_id={} | amount={} | balance_after={}", 
                 user_id, amount, user.balance)
        
        return True
    
    def get_user_summary(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        获取用户概览信息
        
        Args:
            user_id: 用户 ID
            
        Returns:
            用户概览字典
        """
        user = self.get_user(user_id)
        if not user:
            return None
        
        # 今日使用统计
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_usage = self.db.query(
            func.count(UsageRecord.id).label("count"),
            func.sum(UsageRecord.cost).label("cost"),
            func.sum(UsageRecord.prompt_tokens).label("prompt_tokens"),
            func.sum(UsageRecord.completion_tokens).label("completion_tokens")
        ).filter(
            UsageRecord.user_id == user_id,
            UsageRecord.created_at >= today_start
        ).first()
        
        # 总使用统计
        total_usage = self.db.query(
            func.count(UsageRecord.id).label("count"),
            func.sum(UsageRecord.cost).label("cost")
        ).filter(UsageRecord.user_id == user_id).first()
        
        return {
            "user_id": user.user_id,
            "nickname": user.nickname,
            "avatar_url": user.avatar_url,
            "balance": user.balance,
            "free_quota": user.free_quota,
            "total_available": user.total_available,
            "today": {
                "count": today_usage.count or 0,
                "cost": today_usage.cost or 0.0,
                "tokens": (today_usage.prompt_tokens or 0) + (today_usage.completion_tokens or 0)
            },
            "total": {
                "count": total_usage.count or 0,
                "cost": total_usage.cost or 0.0
            },
            "created_at": user.created_at.isoformat() if user.created_at else None
        }
    
    def get_recent_usage(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取最近的使用记录
        
        Args:
            user_id: 用户 ID
            limit: 返回数量限制
            
        Returns:
            使用记录列表
        """
        records = self.db.query(UsageRecord).filter(
            UsageRecord.user_id == user_id
        ).order_by(UsageRecord.created_at.desc()).limit(limit).all()
        
        return [
            {
                "id": r.id,
                "request_id": r.request_id,
                "operation": r.operation,
                "model": r.model,
                "tokens": r.total_tokens,
                "cost": r.cost,
                "created_at": r.created_at.isoformat()
            }
            for r in records
        ]


# 便捷函数
def get_user_service() -> UserService:
    """获取 UserService 实例"""
    db = get_db_session()
    return UserService(db)


def generate_request_id() -> str:
    """生成唯一请求 ID"""
    return str(uuid.uuid4())
