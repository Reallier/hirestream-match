from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from pathlib import Path
import shutil
from datetime import datetime
from models import Candidate, Resume, Experience, Project, Education, AuditLog
from services.resume_parser import ResumeParser
from services.deduplication import DeduplicationService
from services.indexing_service import IndexingService
from config import settings
from match_service.log import logger
import os


class IngestService:
    """简历入库服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.parser = ResumeParser()
        self.dedup_service = DeduplicationService(db)
        self.indexing_service = IndexingService(db)
        self.upload_dir = Path(settings.upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    def ingest_resume(
        self,
        file_path: str,
        user_id: int,
        source: str = 'upload',
        merge_strategy: str = 'new_priority'
    ) -> Dict[str, Any]:
        """入库简历"""
        try:
            # 1. 解析简历
            parsed_result = self.parser.parse_file(file_path)
            text_content = parsed_result['text_content']
            text_hash = parsed_result['text_hash']
            parsed_data = parsed_result['parsed_data']
            
            # 序列化 date 对象为字符串（避免 JSON 序列化错误）
            parsed_data = self._serialize_dates(parsed_data)
            
            # 2. 提取关键信息用于判重
            personal_info = parsed_data.get('personal', {})
            email = personal_info.get('email')
            phone = personal_info.get('phone')
            name = personal_info.get('name')
            
            if not name and parsed_data.get('experiences'):
                name = text_content.split('\n')[0][:20]
            
            # 3. 判重 (加上 user_id 限制)
            existing_candidate, match_type = self.dedup_service.find_duplicates(
                user_id=user_id,
                email=email,
                phone=phone,
                name=name,
                text_hash=text_hash,
                current_company=parsed_data.get('experiences', [{}])[0].get('company') if parsed_data.get('experiences') else None
            )
            
            # 4. 保存文件
            file_uri = self._save_file(file_path, text_hash)
            
            # 5. 创建或更新
            if existing_candidate:
                # 合并...
                candidate_id = existing_candidate.id
                is_new = False
                
                # 检查 text_hash 是否已存在（避免唯一约束冲突）
                existing_resume = self.db.query(Resume).filter(Resume.text_hash == text_hash).first()
                if existing_resume:
                    # 简历内容完全相同，跳过
                    return {
                        'success': True,
                        'candidate_id': candidate_id,
                        'resume_id': existing_resume.id,
                        'is_new': False,
                        'merged_with': candidate_id,
                        'message': f'简历内容与已有记录相同，已跳过 (候选人 ID: {candidate_id})'
                    }
                
                resume = Resume(
                    candidate_id=candidate_id,
                    file_uri=file_uri,
                    file_type=Path(file_path).suffix.lower(),
                    text_content=text_content,
                    text_hash=text_hash,
                    parsed_data=parsed_data
                )
                self.db.add(resume)
                self.db.flush()
                
                # ...合并逻辑略...
                
                message = f"简历已合并到现有候选人 (ID: {candidate_id})"
            
            else:
                # 创建新候选人
                candidate_data = self._build_candidate_data(parsed_data)
                candidate = Candidate(
                    user_id=user_id,  # SaaS Update
                    name=name or '未知',
                    email=email,
                    phone=phone,
                    source=source,
                    **{k: v for k, v in candidate_data.items() 
                       if k in ['location', 'years_experience', 'current_title', 
                                'current_company', 'skills', 'education_level']}
                )
                self.db.add(candidate)
                self.db.flush()
                
                candidate_id = candidate.id
                is_new = True
                
                # 创建简历记录
                resume = Resume(
                    candidate_id=candidate_id,
                    file_uri=file_uri,
                    file_type=Path(file_path).suffix.lower(),
                    text_content=text_content,
                    text_hash=text_hash,
                    parsed_data=parsed_data
                )
                self.db.add(resume)
                self.db.flush()
                
                # 创建工作经历
                for exp_data in parsed_data.get('experiences', []):
                    # 处理 description 可能是列表的情况
                    desc = exp_data.get('description', '')
                    if isinstance(desc, list):
                        desc = '\n'.join(str(d) for d in desc)
                    # 确保 skills 是列表
                    exp_skills = exp_data.get('skills', [])
                    if not isinstance(exp_skills, list):
                        exp_skills = [exp_skills] if exp_skills else []
                    
                    experience = Experience(
                        candidate_id=candidate_id,
                        company=exp_data.get('company', ''),
                        title=exp_data.get('title', ''),
                        start_date=exp_data.get('start_date'),
                        end_date=exp_data.get('end_date'),
                        skills=exp_skills,
                        description=desc
                    )
                    self.db.add(experience)
                
                # 创建项目经历
                for proj_data in parsed_data.get('projects', []):
                    # 处理 description 可能是列表的情况
                    proj_desc = proj_data.get('description', '')
                    if isinstance(proj_desc, list):
                        proj_desc = '\n'.join(str(d) for d in proj_desc)
                    # 确保 skills 是列表
                    proj_skills = proj_data.get('skills', [])
                    if not isinstance(proj_skills, list):
                        proj_skills = [proj_skills] if proj_skills else []
                    
                    project = Project(
                        candidate_id=candidate_id,
                        project_name=proj_data.get('project_name'),
                        role=proj_data.get('role'),
                        start_date=proj_data.get('start_date'),
                        end_date=proj_data.get('end_date'),
                        skills=proj_skills,
                        description=proj_desc
                    )
                    self.db.add(project)
                
                # 创建教育经历
                for edu_data in parsed_data.get('education', []):
                    education = Education(
                        candidate_id=candidate_id,
                        school=edu_data.get('school'),
                        degree=edu_data.get('degree'),
                        major=edu_data.get('major'),
                        start_date=edu_data.get('start_date'),
                        end_date=edu_data.get('end_date')
                    )
                    self.db.add(education)
                
                # 记录审计日志
                self._log_audit('candidate', candidate_id, 'create', {
                    'resume_id': resume.id,
                    'source': source
                })
                
                message = f"已创建新候选人 (ID: {candidate_id})"
            
            # 6. 提交事务
            self.db.commit()
            
            # 7. 后台异步建立索引（避免阻塞请求）
            import threading
            
            def delayed_index():
                import time
                time.sleep(settings.index_delay_seconds)
                try:
                    self.indexing_service.index_candidate(candidate_id, force=True)
                except Exception as e:
                    # 索引失败不影响主流程，仅记录日志
                    logger.error(f"后台索引失败 (candidate_id={candidate_id}): {e}")
            
            # 在后台线程执行，不阻塞当前请求
            threading.Thread(target=delayed_index, daemon=True).start()
            
            return {
                'success': True,
                'candidate_id': candidate_id,
                'resume_id': resume.id,
                'is_new': is_new,
                'merged_with': existing_candidate.id if existing_candidate else None,
                'message': message
            }
        
        except Exception as e:
            self.db.rollback()
            return {
                'success': False,
                'candidate_id': 0,
                'resume_id': 0,
                'is_new': False,
                'merged_with': None,
                'message': f'入库失败: {str(e)}'
            }
    
    def _serialize_dates(self, obj: Any) -> Any:
        """递归将 date/datetime 对象转换为 ISO 格式字符串"""
        from datetime import date, datetime as dt
        
        if isinstance(obj, (date, dt)):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {k: self._serialize_dates(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._serialize_dates(item) for item in obj]
        return obj
    
    def _build_candidate_data(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """从解析数据构建候选人数据"""
        personal = parsed_data.get('personal', {})
        experiences = parsed_data.get('experiences', [])
        education = parsed_data.get('education', [])
        skills = parsed_data.get('skills', [])
        
        # 提取当前职位和公司
        current_title = None
        current_company = None
        if experiences:
            latest_exp = experiences[0]
            current_title = latest_exp.get('title')
            current_company = latest_exp.get('company')
        
        # 计算工作年限
        years_experience = self._calculate_years_experience(experiences)
        
        # 提取教育水平
        education_level = self._extract_education_level(education)
        
        return {
            'email': personal.get('email'),
            'phone': personal.get('phone'),
            'location': personal.get('location'),
            'years_experience': years_experience,
            'current_title': current_title,
            'current_company': current_company,
            'skills': skills,
            'education_level': education_level
        }
    
    def _calculate_years_experience(self, experiences: list) -> Optional[int]:
        """计算工作年限"""
        if not experiences:
            return None
        
        # 简单计算：最早开始日期到现在
        earliest_date = None
        for exp in experiences:
            start_date = exp.get('start_date')
            if start_date:
                if earliest_date is None or start_date < earliest_date:
                    earliest_date = start_date
        
        if earliest_date:
            from datetime import date
            today = date.today()
            if isinstance(earliest_date, str):
                from datetime import datetime
                earliest_date = datetime.strptime(earliest_date, '%Y-%m-%d').date()
            
            years = (today - earliest_date).days / 365.25
            return int(years)
        
        return None
    
    def _extract_education_level(self, education: list) -> Optional[str]:
        """提取最高学历"""
        if not education:
            return None
        
        # 学历等级
        levels = {
            '博士': 5,
            'PhD': 5,
            'Doctor': 5,
            '硕士': 4,
            'Master': 4,
            'MBA': 4,
            '本科': 3,
            'Bachelor': 3,
            '学士': 3,
            '专科': 2,
            'Associate': 2
        }
        
        highest_level = 0
        highest_degree = None
        
        for edu in education:
            degree = edu.get('degree', '')
            for key, level in levels.items():
                if key in degree:
                    if level > highest_level:
                        highest_level = level
                        highest_degree = key
                        break
        
        return highest_degree
    
    def _save_file(self, source_path: str, text_hash: str) -> str:
        """保存文件到永久存储"""
        # 使用哈希作为文件名避免重复
        file_ext = Path(source_path).suffix
        dest_filename = f"{text_hash}{file_ext}"
        dest_path = self.upload_dir / dest_filename
        
        # 如果文件已存在，不重复保存
        if not dest_path.exists():
            shutil.copy2(source_path, dest_path)
        
        # 返回相对路径
        return str(dest_path.relative_to(self.upload_dir.parent))
    
    def _log_audit(
        self,
        entity_type: str,
        entity_id: int,
        action: str,
        changes: Dict[str, Any]
    ):
        """记录审计日志"""
        import json
        log = AuditLog(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            changes=changes,
            performed_by='system',
            performed_at=datetime.utcnow()
        )
        self.db.add(log)