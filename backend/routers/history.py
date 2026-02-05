# -*- coding: utf-8 -*-
"""
匹配历史 API

获取用户的匹配历史记录
"""

from fastapi import APIRouter, Depends, Cookie
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel
from loguru import logger

from database import get_db
from match_service.models import MatchRecord
from match_service.auth import verify_jwt_token


router = APIRouter(prefix="/api/match", tags=["Match History"])


class MatchRecordResponse(BaseModel):
    """匹配记录响应模型"""
    id: int
    jd_text: str
    resume_text: str
    resume_filename: Optional[str]
    match_score: Optional[int]
    created_at: datetime
    
    class Config:
        from_attributes = True


@router.get("/history")
async def get_match_history(
    auth_token: Optional[str] = Cookie(None),
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    获取当前用户的匹配历史记录
    
    返回最近的 N 条匹配记录（默认 20 条）
    """
    # 验证 Token
    if not auth_token:
        return {"success": False, "records": [], "message": "请先登录"}
    
    user_info = verify_jwt_token(auth_token)
    if not user_info:
        return {"success": False, "records": [], "message": "Token 无效"}
    
    try:
        # 查询匹配历史
        records = db.query(MatchRecord).filter(
            MatchRecord.user_id == user_info.user_id
        ).order_by(
            MatchRecord.created_at.desc()
        ).limit(limit).all()
        
        # 转换为响应格式
        result = []
        for r in records:
            result.append({
                "id": r.id,
                "jd_text": r.jd_text[:200] + "..." if len(r.jd_text) > 200 else r.jd_text,
                "resume_text": r.resume_text[:200] + "..." if len(r.resume_text) > 200 else r.resume_text,
                "resume_filename": r.resume_filename,
                "match_score": r.match_score,
                "created_at": r.created_at.isoformat() if r.created_at else None
            })
        
        logger.info("match_history | user_id={} | count={}", user_info.user_id, len(result))
        
        return {
            "success": True,
            "records": result
        }
        
    except Exception as e:
        logger.error("match_history_error | user_id={} | error={}", user_info.user_id, str(e))
        return {"success": False, "records": [], "message": str(e)}


@router.get("/history/{record_id}")
async def get_match_record_detail(
    record_id: int,
    auth_token: Optional[str] = Cookie(None),
    db: Session = Depends(get_db)
):
    """
    获取单条匹配记录详情
    
    包含完整的 JD、简历文本和匹配报告
    """
    if not auth_token:
        return {"success": False, "message": "请先登录"}
    
    user_info = verify_jwt_token(auth_token)
    if not user_info:
        return {"success": False, "message": "Token 无效"}
    
    record = db.query(MatchRecord).filter(
        MatchRecord.id == record_id,
        MatchRecord.user_id == user_info.user_id
    ).first()
    
    if not record:
        return {"success": False, "message": "记录不存在"}
    
    return {
        "success": True,
        "record": {
            "id": record.id,
            "jd_text": record.jd_text,
            "resume_text": record.resume_text,
            "resume_filename": record.resume_filename,
            "match_score": record.match_score,
            "report": record.report_json,
            "created_at": record.created_at.isoformat() if record.created_at else None
        }
    }
