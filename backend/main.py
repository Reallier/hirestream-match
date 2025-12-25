from fastapi import FastAPI, File, UploadFile, Depends, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Optional
import tempfile
import os

from database import get_db, init_db
from schemas import (
    MatchRequest, MatchResponse, SearchRequest, SearchResponse,
    CandidateResponse, CandidateDetail, ReindexRequest, ReindexResponse,
    IngestResponse
)
from models import Candidate
from services.matching_service import MatchingService
from services.ingest_service import IngestService
from services.indexing_service import IndexingService
from config import settings

# 统一日志系统
try:
    from intjtech_logging import setup_logging, get_logger
    from intjtech_logging.middleware import LoggingMiddleware
    setup_logging(
        service_name="app01-hirestream-match",
        log_level="INFO",
        enable_json=True,
        loki_url="http://43.136.53.213:3100",
    )
    logger = get_logger(__name__)
    LOGGING_ENABLED = True
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    LOGGING_ENABLED = False

# 创建 FastAPI 应用
app = FastAPI(
    title="TalentAI - 智能招聘匹配系统",
    description="基于 RAG 的人才匹配与简历管理系统",
    version="1.0.0"
)

# 日志中间件（优先添加）
if LOGGING_ENABLED:
    app.add_middleware(LoggingMiddleware)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """启动事件"""
    await init_db()
    print("✓ 数据库初始化完成")


@app.get("/")
async def root():
    """根路径"""
    return {
        "name": "TalentAI API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


# ============= 即时匹配 API（来自 HireStream 融合） =============

@app.post("/api/instant-match")
async def instant_match(
    jd: str = Form(...),
    resume: UploadFile = File(None),
    resume_text: str = Form(None)
):
    """
    即时匹配（不入库）
    
    上传简历文件或提供简历文本，加上职位描述，AI 立即分析匹配度并返回结果。
    此 API 不会将简历入库到人才库。
    
    参数：
    - jd: 职位描述文本 (必需)
    - resume: 简历文件 (PDF/JPG/PNG等，与 resume_text 二选一)
    - resume_text: 简历文本 (与 resume 二选一，优先使用)
    """
    import sys
    import os
    
    # 添加共享模块路径
    shared_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))
    if shared_path not in sys.path:
        sys.path.insert(0, shared_path)
    
    from shared.llm_client import LLMClient
    from shared.token_calculator import TokenCalculator
    
    ocr_usage = None
    final_resume_text = None
    
    try:
        # 优先使用文本输入
        if resume_text and resume_text.strip():
            final_resume_text = resume_text.strip()
            print(f"[instant-match] 使用文本输入，长度: {len(final_resume_text)}")
        elif resume and resume.filename:
            # 使用文件上传
            filename = resume.filename.lower()
            if not filename.endswith(('.pdf', '.jpg', '.jpeg', '.png', '.gif', '.webp')):
                raise HTTPException(
                    status_code=400,
                    detail="不支持的文件格式。支持 PDF 和常见图片格式（JPG/PNG/GIF/WEBP）"
                )
            
            # 读取文件内容
            file_data = await resume.read()
            
            # OCR 提取简历文本
            from shared.qwen_pdf_ocr import QwenPDFOCR
            
            api_key = os.getenv("DASHSCOPE_API_KEY", "")
            
            # 根据文件类型选择 OCR 方式
            if filename.endswith('.pdf'):
                ocr = QwenPDFOCR.from_bytes(file_data, api_key=api_key, verbose=False)
                final_resume_text, ocr_usage = ocr.run()
            else:
                final_resume_text, ocr_usage = QwenPDFOCR.from_image_bytes(file_data, api_key=api_key, verbose=False)
            
            print(f"[instant-match] OCR 完成，文本长度: {len(final_resume_text) if final_resume_text else 0}")
            
            if not final_resume_text or final_resume_text.startswith("["):
                raise HTTPException(status_code=400, detail="无法识别简历内容，请确保文件清晰可读")
        else:
            raise HTTPException(status_code=400, detail="请提供简历文件或简历文本")
        
        # 构建匹配分析 prompt
        user_prompt = f"""请分析以下简历与职位描述的匹配度。

## 职位描述 (JD)
{jd}

## 候选人简历
{final_resume_text[:8000]}

请以 JSON 格式返回分析结果，包含以下字段：
- match_score: 匹配度评分 (0-100)
- advantages: 匹配优势列表 (数组，3-5项)
- risks: 潜在风险/不足列表 (数组，2-4项)
- advice: 综合建议 (字符串，不超过100字)"""

        system_prompt = os.getenv("SYSTEM_PROMPT", """你是一位资深的HR招聘专家和人才评估师。你的任务是分析候选人简历与职位描述的匹配程度，提供专业、客观的评估意见。

评估时请关注：
1. 技能匹配度：候选人的技术栈与岗位要求的契合程度
2. 经验相关性：工作经历与目标岗位的关联度
3. 教育背景：学历和专业是否符合要求
4. 潜在风险：识别可能的不足或风险点

请务必返回有效的 JSON 格式。""")
        
        # 调用 LLM 进行匹配分析
        llm = LLMClient()
        result = llm.call_json(user_prompt, system_prompt=system_prompt)
        
        # 合并 OCR 的 token 使用量（如果有）
        if "token_usage" in result and ocr_usage:
            result["token_usage"]["ocr_tokens"] = ocr_usage.get("prompt_tokens", 0) + ocr_usage.get("completion_tokens", 0)
            # 计算 OCR 费用
            ocr_cost = TokenCalculator.calculate_cost(
                ocr_usage.get("model", "qwen-vl-ocr"),
                ocr_usage.get("prompt_tokens", 0),
                ocr_usage.get("completion_tokens", 0)
            )
            result["token_usage"]["cost"] = result["token_usage"].get("cost", 0) + ocr_cost
            result["token_usage"]["total_tokens"] = (
                result["token_usage"].get("total_tokens", 0) + 
                result["token_usage"]["ocr_tokens"]
            )
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"匹配分析失败: {str(e)}")


# ============= 匹配相关 API =============

@app.post("/api/match", response_model=MatchResponse)
async def match_candidates(
    request: MatchRequest,
    db: Session = Depends(get_db)
):
    """
    JD 匹配候选人
    
    根据职位描述匹配最合适的候选人，返回排序结果和证据
    """
    try:
        matching_service = MatchingService(db)
        
        result = matching_service.match_candidates(
            jd_text=request.jd,
            filters=request.filters.dict() if request.filters else None,
            top_k=request.top_k,
            explain=request.explain
        )
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"匹配失败: {str(e)}")


@app.get("/api/search", response_model=SearchResponse)
async def search_candidates(
    q: str,
    top_k: int = 20,
    db: Session = Depends(get_db)
):
    """
    关键词搜索候选人
    
    使用关键词进行全文搜索
    """
    try:
        matching_service = MatchingService(db)
        
        results = matching_service.search_candidates(
            query=q,
            top_k=top_k
        )
        
        return {
            "results": results,
            "total": len(results),
            "query": q
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")


# ============= 简历入库 API =============

@app.post("/api/candidates/ingest", response_model=IngestResponse)
async def ingest_resume(
    file: UploadFile = File(...),
    source: str = Form("upload"),
    user_id: int = Form(...),
    db: Session = Depends(get_db)
):
    """
    上传并入库简历
    
    支持 PDF 和 DOCX 格式，自动解析、判重、合并
    """
    # 检查文件类型
    if not file.filename.lower().endswith(('.pdf', '.docx', '.doc')):
        raise HTTPException(
            status_code=400,
            detail="不支持的文件格式，仅支持 PDF 和 DOCX"
        )
    
    # 检查文件大小
    file_size = 0
    chunk_size = 1024 * 1024  # 1MB
    temp_file = None
    
    try:
        # 保存到临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp:
            temp_file = temp.name
            while chunk := await file.read(chunk_size):
                file_size += len(chunk)
                if file_size > settings.max_file_size_mb * 1024 * 1024:
                    raise HTTPException(
                        status_code=400,
                        detail=f"文件大小超过限制 ({settings.max_file_size_mb}MB)"
                    )
                temp.write(chunk)
        
        # 入库处理
        ingest_service = IngestService(db)
        result = ingest_service.ingest_resume(
            file_path=temp_file,
            source=source,
            user_id=user_id
        )
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"入库失败: {str(e)}")
    
    finally:
        # 清理临时文件
        if temp_file and os.path.exists(temp_file):
            os.remove(temp_file)


# ============= 候选人管理 API =============

@app.get("/api/candidates/{candidate_id}", response_model=CandidateDetail)
async def get_candidate(
    candidate_id: int,
    db: Session = Depends(get_db)
):
    """
    获取候选人详细信息
    
    包含基本信息、工作经历、项目经历、教育背景等
    """
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    
    if not candidate:
        raise HTTPException(status_code=404, detail="候选人不存在")
    
    # 构建详细响应
    from schemas import (
        ResumeResponse, ExperienceResponse, 
        ProjectResponse, EducationResponse
    )
    
    detail = {
        "id": candidate.id,
        "name": candidate.name,
        "email": candidate.email,
        "phone": candidate.phone,
        "location": candidate.location,
        "years_experience": candidate.years_experience,
        "current_title": candidate.current_title,
        "current_company": candidate.current_company,
        "skills": candidate.skills or [],
        "education_level": candidate.education_level,
        "source": candidate.source,
        "status": candidate.status,
        "created_at": candidate.created_at,
        "updated_at": candidate.updated_at,
        "resumes": [
            ResumeResponse(
                id=r.id,
                candidate_id=r.candidate_id,
                file_uri=r.file_uri,
                file_type=r.file_type,
                text_hash=r.text_hash,
                created_at=r.created_at
            ) for r in candidate.resumes
        ],
        "experiences": [
            ExperienceResponse(
                id=e.id,
                candidate_id=e.candidate_id,
                company=e.company,
                title=e.title,
                start_date=e.start_date,
                end_date=e.end_date,
                skills=e.skills or [],
                description=e.description,
                created_at=e.created_at
            ) for e in candidate.experiences
        ],
        "projects": [
            ProjectResponse(
                id=p.id,
                candidate_id=p.candidate_id,
                project_name=p.project_name,
                role=p.role,
                start_date=p.start_date,
                end_date=p.end_date,
                skills=p.skills or [],
                description=p.description
            ) for p in candidate.projects
        ],
        "education": [
            EducationResponse(
                id=e.id,
                candidate_id=e.candidate_id,
                school=e.school,
                degree=e.degree,
                major=e.major,
                start_date=e.start_date,
                end_date=e.end_date
            ) for e in candidate.education
        ]
    }
    
    # 添加索引信息
    if candidate.index:
        detail["index_updated_at"] = candidate.index.index_updated_at
        detail["embedding_version"] = candidate.index.embedding_version
    
    return detail


@app.get("/api/candidates", response_model=list)
async def list_candidates(
    skip: int = 0,
    limit: int = 20,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    列出候选人
    
    支持分页和状态过滤
    """
    query = db.query(Candidate)
    
    if status:
        query = query.filter(Candidate.status == status)
    
    candidates = query.offset(skip).limit(limit).all()
    
    return [
        CandidateResponse(
            id=c.id,
            name=c.name,
            email=c.email,
            phone=c.phone,
            location=c.location,
            years_experience=c.years_experience,
            current_title=c.current_title,
            current_company=c.current_company,
            skills=c.skills or [],
            education_level=c.education_level,
            source=c.source,
            status=c.status,
            created_at=c.created_at,
            updated_at=c.updated_at
        )
        for c in candidates
    ]


# ============= 索引管理 API =============

@app.post("/api/reindex", response_model=ReindexResponse)
async def reindex_candidates(
    request: ReindexRequest,
    db: Session = Depends(get_db)
):
    """
    重建索引
    
    可以指定候选人ID列表或时间范围
    """
    try:
        indexing_service = IndexingService(db)
        
        result = indexing_service.reindex_all(
            candidate_ids=request.candidate_ids,
            updated_since=request.updated_since
        )
        
        return {
            "success": True,
            "reindexed_count": result['success'],
            "failed_count": result['failed'],
            "errors": []
        }
    
    except Exception as e:
        return {
            "success": False,
            "reindexed_count": 0,
            "failed_count": 0,
            "errors": [str(e)]
        }


@app.delete("/api/candidates/{candidate_id}")
async def delete_candidate(
    candidate_id: int,
    db: Session = Depends(get_db)
):
    """
    删除候选人
    
    会同时删除相关的简历、索引等数据，并记录审计日志
    """
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    
    if not candidate:
        raise HTTPException(status_code=404, detail="候选人不存在")
    
    try:
        # 记录审计日志
        from models import AuditLog
        audit = AuditLog(
            entity_type='candidate',
            entity_id=candidate_id,
            action='delete',
            changes={'name': candidate.name},
            performed_by='api',
            performed_at=datetime.utcnow()
        )
        db.add(audit)
        
        # 删除候选人（级联删除相关数据）
        db.delete(candidate)
        db.commit()
        
        return {"success": True, "message": f"候选人 {candidate_id} 已删除"}
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


# ============= 统计 API =============

@app.get("/api/stats")
async def get_stats(db: Session = Depends(get_db)):
    """获取系统统计信息"""
    from models import Resume, Experience
    from sqlalchemy import func
    
    total_candidates = db.query(func.count(Candidate.id)).scalar()
    total_resumes = db.query(func.count(Resume.id)).scalar()
    active_candidates = db.query(func.count(Candidate.id)).filter(
        Candidate.status == 'active'
    ).scalar()
    
    return {
        "total_candidates": total_candidates,
        "total_resumes": total_resumes,
        "active_candidates": active_candidates
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    )