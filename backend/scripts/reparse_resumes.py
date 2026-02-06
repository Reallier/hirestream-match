#!/usr/bin/env python
"""重新解析所有简历，使用 LLM 提取结构化信息"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Candidate, Resume
from services.resume_parser import ResumeParser
import os

# 连接数据库
engine = create_engine(os.environ.get("DATABASE_URL", "postgresql://talentai:talentai@talentai_db:5432/talentai"))
Session = sessionmaker(bind=engine)
db = Session()

parser = ResumeParser()

# 获取所有简历
resumes = db.query(Resume).all()
print(f"找到 {len(resumes)} 份简历待重新解析")

success_count = 0
fail_count = 0

for resume in resumes:
    print(f"\n解析简历 ID: {resume.id}, 候选人 ID: {resume.candidate_id}")
    
    # 检查文件是否存在
    file_path = f"/app/{resume.file_uri}"
    if not os.path.exists(file_path):
        print(f"  文件不存在: {file_path}")
        fail_count += 1
        continue
    
    try:
        # 重新解析
        result = parser.parse_file(file_path)
        parsed = result["parsed_data"]
        
        # 更新候选人信息
        candidate = db.query(Candidate).filter(Candidate.id == resume.candidate_id).first()
        if candidate:
            name = parsed.get("personal", {}).get("name")
            if name:
                candidate.name = name
                print(f"  姓名: {name}")
            
            title = parsed.get("current_title")
            if title:
                candidate.current_title = title
                print(f"  职位: {title}")
            
            company = parsed.get("current_company")
            if company:
                candidate.current_company = company
                print(f"  公司: {company}")
            
            exp = parsed.get("years_experience")
            if exp:
                candidate.years_experience = exp
                print(f"  经验: {exp}年")
            
            skills = parsed.get("skills")
            if skills:
                candidate.skills = skills[:20]
                print(f"  技能: {skills[:5]}...")
            
            edu = parsed.get("education_level")
            if edu:
                candidate.education_level = edu
                print(f"  学历: {edu}")
            
            email = parsed.get("personal", {}).get("email")
            if email:
                candidate.email = email
            
            phone = parsed.get("personal", {}).get("phone")
            if phone:
                candidate.phone = phone
            
            location = parsed.get("personal", {}).get("location")
            if location:
                candidate.location = location
            
            db.commit()
            print(f"  ✅ 更新成功")
            success_count += 1
    except Exception as e:
        print(f"  ❌ 解析失败: {e}")
        fail_count += 1
        db.rollback()

db.close()
print(f"\n解析完成: 成功 {success_count}, 失败 {fail_count}")
