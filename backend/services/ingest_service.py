from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from pathlib import Path
import shutil
from datetime import datetime, date
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
            logger.info(f"开始入库简历: user_id={user_id}, file={file_path}")
            
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
                
                # 去重（同一候选人重复上传相同内容的简历时直接跳过）
                # 注意：text_hash 已移除全局 UNIQUE，仅在业务层做用户/候选人级别去重
                existing_resume = self.db.query(Resume).filter(
                    Resume.text_hash == text_hash,
                    Resume.candidate_id == candidate_id
                ).first()
                if existing_resume:
                    # 简历内容完全相同，跳过
                    return {
                        'success': True,
                        'candidate_id': candidate_id,
                        'resume_id': existing_resume.id,
                        'is_new': False,
                        'merged_with': candidate_id,
                        'index_required': False,
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
                
                # 创建工作经历（容错：单条失败不影响其他）
                for exp_data in parsed_data.get('experiences', []):
                    try:
                        desc = exp_data.get('description', '')
                        if isinstance(desc, list):
                            desc = '\n'.join(str(d) for d in desc)
                        exp_skills = exp_data.get('skills', [])
                        if not isinstance(exp_skills, list):
                            exp_skills = [exp_skills] if exp_skills else []
                        
                        experience = Experience(
                            candidate_id=candidate_id,
                            company=exp_data.get('company', ''),
                            title=exp_data.get('title', ''),
                            start_date=self._safe_parse_date(exp_data.get('start_date')),
                            end_date=self._safe_parse_date(exp_data.get('end_date')),
                            skills=exp_skills,
                            description=desc
                        )
                        self.db.add(experience)
                    except Exception as e:
                        logger.warning(f"创建工作经历失败: {e}")
                
                # 创建项目经历（容错）
                for proj_data in parsed_data.get('projects', []):
                    try:
                        proj_desc = proj_data.get('description', '')
                        if isinstance(proj_desc, list):
                            proj_desc = '\n'.join(str(d) for d in proj_desc)
                        proj_skills = proj_data.get('skills', [])
                        if not isinstance(proj_skills, list):
                            proj_skills = [proj_skills] if proj_skills else []
                        
                        project = Project(
                            candidate_id=candidate_id,
                            project_name=proj_data.get('project_name'),
                            role=proj_data.get('role'),
                            start_date=self._safe_parse_date(proj_data.get('start_date')),
                            end_date=self._safe_parse_date(proj_data.get('end_date')),
                            skills=proj_skills,
                            description=proj_desc
                        )
                        self.db.add(project)
                    except Exception as e:
                        logger.warning(f"创建项目经历失败: {e}")
                
                # 创建教育经历（容错）
                for edu_data in parsed_data.get('education', []):
                    try:
                        education = Education(
                            candidate_id=candidate_id,
                            school=edu_data.get('school'),
                            degree=edu_data.get('degree'),
                            major=edu_data.get('major'),
                            start_date=self._safe_parse_date(edu_data.get('start_date')),
                            end_date=self._safe_parse_date(edu_data.get('end_date'))
                        )
                        self.db.add(education)
                    except Exception as e:
                        logger.warning(f"创建教育经历失败: {e}")
                
                # 记录审计日志
                self._log_audit('candidate', candidate_id, 'create', {
                    'resume_id': resume.id,
                    'source': source
                })
                
                message = f"已创建新候选人 (ID: {candidate_id})"
            
            # 6. 提交事务
            self.db.commit()
            
            return {
                'success': True,
                'candidate_id': candidate_id,
                'resume_id': resume.id,
                'is_new': is_new,
                'merged_with': existing_candidate.id if existing_candidate else None,
                'index_required': True,
                'message': message
            }
        
        except Exception as e:
            self.db.rollback()
            logger.error("入库失败: user_id=%s, error=%s" % (user_id, repr(e)), exc_info=True)
            return {
                'success': False,
                'candidate_id': 0,
                'resume_id': 0,
                'is_new': False,
                'merged_with': None,
                'index_required': False,
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
    
    def _safe_parse_date(self, date_str: Any) -> Optional[str]:
        """安全解析日期，支持多种格式，返回标准格式或 None"""
        if date_str is None:
            return None
        if isinstance(date_str, (date, datetime)):
            return date_str.isoformat()
        if not isinstance(date_str, str):
            return None
        
        # 支持多种格式
        for fmt in ['%Y-%m-%d', '%Y-%m', '%Y', '%Y/%m/%d', '%Y/%m', '%d/%m/%Y', '%m/%d/%Y']:
            try:
                parsed = datetime.strptime(date_str.strip(), fmt)
                return parsed.date().isoformat()
            except ValueError:
                continue
        
        # 无法解析，返回原字符串让数据库处理
        logger.warning(f"无法解析日期: {date_str}")
        return None
    
    def _build_candidate_data(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """从解析数据构建候选人数据（容错处理）"""
        try:
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
            
            # 计算工作年限（容错）
            try:
                years_experience = self._calculate_years_experience(experiences)
            except Exception as e:
                logger.warning(f"计算工作年限失败: {e}")
                years_experience = None
            
            # 提取教育水平（容错）
            try:
                education_level = self._extract_education_level(education)
            except Exception as e:
                logger.warning(f"提取教育水平失败: {e}")
                education_level = None
            
            return {
                'email': personal.get('email'),
                'phone': personal.get('phone'),
                'location': personal.get('location'),
                'years_experience': years_experience,
                'current_title': current_title,
                'current_company': current_company,
                'skills': skills if isinstance(skills, list) else [],
                'education_level': education_level
            }
        except Exception as e:
            logger.warning(f"构建候选人数据失败: {e}")
            return {}
    
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
                # 支持多种日期格式
                for fmt in ['%Y-%m-%d', '%Y-%m', '%Y']:
                    try:
                        earliest_date = datetime.strptime(earliest_date, fmt).date()
                        break
                    except ValueError:
                        continue
                else:
                    # 无法解析，跳过
                    return None
            
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
