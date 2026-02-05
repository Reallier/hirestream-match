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

from database import get_db, get_auth_db
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
    
    # 发送邮件通知管理员（仅 Bug 反馈）
    if feedback.type == "bug":
        try:
            await send_feedback_notification(feedback, user_id)
        except Exception as e:
            logger.warning("feedback_email_failed | id={} | error={}", feedback.id, str(e))
    
    return {
        "success": True,
        "feedbackId": feedback.id,
        "message": "感谢您的反馈！我们会认真阅读每一条建议。"
    }


async def send_feedback_notification(feedback, user_id):
    """发送反馈通知邮件给管理员"""
    import httpx
    import os
    from datetime import datetime
    
    resend_api_key = os.getenv("RESEND_API_KEY")
    admin_email = os.getenv("ADMIN_EMAIL", "icey123580@gmail.com")
    
    if not resend_api_key:
        logger.warning("RESEND_API_KEY not configured, skipping feedback email")
        return
    
    type_names = {
        "suggestion": "功能建议",
        "bug": "Bug 反馈",
        "other": "其他"
    }
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    html_content = f"""
    <div style="font-family: -apple-system, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #111; border-bottom: 2px solid #eee; padding-bottom: 12px;">
            📬 新用户反馈
        </h2>
        <table style="width: 100%; border-collapse: collapse; margin: 16px 0;">
            <tr>
                <td style="padding: 8px 0; color: #666; width: 100px;">反馈 ID</td>
                <td style="padding: 8px 0; font-weight: 600;">#{feedback.id}</td>
            </tr>
            <tr>
                <td style="padding: 8px 0; color: #666;">类型</td>
                <td style="padding: 8px 0;">{type_names.get(feedback.type, feedback.type)}</td>
            </tr>
            <tr>
                <td style="padding: 8px 0; color: #666;">用户 ID</td>
                <td style="padding: 8px 0;">{user_id or '匿名用户'}</td>
            </tr>
            <tr>
                <td style="padding: 8px 0; color: #666;">提交时间</td>
                <td style="padding: 8px 0;">{timestamp}</td>
            </tr>
            <tr>
                <td style="padding: 8px 0; color: #666;">来源页面</td>
                <td style="padding: 8px 0;">{feedback.page or '未知'}</td>
            </tr>
            <tr>
                <td style="padding: 8px 0; color: #666;">联系方式</td>
                <td style="padding: 8px 0;">{feedback.contact or '未提供'}</td>
            </tr>
        </table>
        <div style="background: #f9f9f9; padding: 16px; border-left: 4px solid #333; margin: 16px 0;">
            <p style="margin: 0; color: #333; white-space: pre-wrap;">{feedback.content}</p>
        </div>
        <p style="font-size: 12px; color: #999; margin-top: 24px;">
            此邮件由 TalentAI 系统自动发送
        </p>
    </div>
    """
    
    async with httpx.AsyncClient() as client:
        await client.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {resend_api_key}",
                "Content-Type": "application/json"
            },
            json={
                "from": "TalentAI 反馈通知 <noreply@auth.intjsys.com>",
                "to": admin_email,
                "subject": f"[TalentAI] 新反馈 #{feedback.id}: {type_names.get(feedback.type, feedback.type)}",
                "html": html_content
            }
        )
    
    logger.info("feedback_email_sent | id={} | to={}", feedback.id, admin_email)


@router.get("/list")
async def list_feedbacks(
    auth_token: Optional[str] = Cookie(None),
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    auth_db: Session = Depends(get_auth_db)
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
    
    # 检查管理员权限（从用户主库查询）
    user = auth_db.query(User).filter(User.id == user_info.user_id).first()
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
    db: Session = Depends(get_db),
    auth_db: Session = Depends(get_auth_db)
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
    
    # 检查管理员权限（从用户主库查询）
    user = auth_db.query(User).filter(User.id == user_info.user_id).first()
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
