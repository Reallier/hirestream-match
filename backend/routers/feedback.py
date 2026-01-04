# -*- coding: utf-8 -*-
"""
反馈 API

用户反馈提交和管理
"""

from fastapi import APIRouter, Depends, Cookie, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
from loguru import logger

from database import get_db
from match_service.models import Feedback, User
from match_service.auth import verify_jwt_token


router = APIRouter(prefix="/api/feedback", tags=["Feedback"])


class FeedbackSubmitRequest(BaseModel):
    """提交反馈请求"""
    type: str = "suggestion"  # suggestion, bug, other
    content: str
    contact: Optional[str] = None
    page: Optional[str] = None


class FeedbackUpdateRequest(BaseModel):
    """更新反馈请求"""
    status: Optional[str] = None
    admin_note: Optional[str] = None


@router.post("/submit")
async def submit_feedback(
    request: FeedbackSubmitRequest,
    auth_token: Optional[str] = Cookie(None),
    db: Session = Depends(get_db)
):
    """
    提交用户反馈
    
    可以匿名提交，登录用户会关联用户 ID
    """
    if not request.content or not request.content.strip():
        raise HTTPException(status_code=400, detail="反馈内容不能为空")
    
    # 尝试获取用户 ID
    user_id = None
    if auth_token:
        user_info = verify_jwt_token(auth_token)
        if user_info:
            user_id = user_info.user_id
    
    # 创建反馈记录
    feedback = Feedback(
        user_id=user_id,
        type=request.type or "suggestion",
        content=request.content.strip(),
        contact=request.contact.strip() if request.contact else None,
        page=request.page,
        status="pending"
    )
    
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    
    logger.info("feedback_submitted | id={} | type={} | user_id={}", 
                feedback.id, feedback.type, user_id)
    
    return {
        "success": True,
        "feedbackId": feedback.id,
        "message": "感谢您的反馈！我们会认真阅读每一条建议。"
    }


@router.get("/list")
async def list_feedbacks(
    auth_token: Optional[str] = Cookie(None),
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db)
):
    """
    获取反馈列表（管理员）
    
    需要管理员权限
    """
    # 验证管理员权限
    if not auth_token:
        raise HTTPException(status_code=401, detail="未登录")
    
    user_info = verify_jwt_token(auth_token)
    if not user_info:
        raise HTTPException(status_code=401, detail="登录已过期")
    
    # 检查管理员权限
    user = db.query(User).filter(User.id == user_info.user_id).first()
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="权限不足")
    
    # 构建查询
    query = db.query(Feedback)
    if status:
        query = query.filter(Feedback.status == status)
    
    # 统计总数
    total = query.count()
    
    # 分页查询
    feedbacks = query.order_by(Feedback.created_at.desc()) \
        .offset((page - 1) * page_size) \
        .limit(page_size) \
        .all()
    
    # 转换响应
    data = []
    for fb in feedbacks:
        data.append({
            "id": fb.id,
            "userId": fb.user_id,
            "type": fb.type,
            "content": fb.content,
            "contact": fb.contact,
            "page": fb.page,
            "status": fb.status,
            "adminNote": fb.admin_note,
            "createdAt": fb.created_at.isoformat() if fb.created_at else None,
            "updatedAt": fb.updated_at.isoformat() if fb.updated_at else None
        })
    
    return {
        "success": True,
        "data": data,
        "total": total,
        "page": page,
        "pageSize": page_size,
        "totalPages": (total + page_size - 1) // page_size
    }


@router.patch("/{feedback_id}")
async def update_feedback(
    feedback_id: int,
    request: FeedbackUpdateRequest,
    auth_token: Optional[str] = Cookie(None),
    db: Session = Depends(get_db)
):
    """
    更新反馈状态（管理员）
    """
    # 验证管理员权限
    if not auth_token:
        raise HTTPException(status_code=401, detail="未登录")
    
    user_info = verify_jwt_token(auth_token)
    if not user_info:
        raise HTTPException(status_code=401, detail="登录已过期")
    
    user = db.query(User).filter(User.id == user_info.user_id).first()
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="权限不足")
    
    # 查找反馈
    feedback = db.query(Feedback).filter(Feedback.id == feedback_id).first()
    if not feedback:
        raise HTTPException(status_code=404, detail="反馈不存在")
    
    # 更新
    if request.status:
        feedback.status = request.status
    if request.admin_note is not None:
        feedback.admin_note = request.admin_note
    
    db.commit()
    db.refresh(feedback)
    
    logger.info("feedback_updated | id={} | status={}", feedback_id, feedback.status)
    
    return {
        "success": True,
        "data": {
            "id": feedback.id,
            "status": feedback.status,
            "adminNote": feedback.admin_note
        }
    }
