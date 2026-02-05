#!/usr/bin/env python3
"""
测试服数据生成脚本

生成模拟的候选人数据用于测试人才库和搜索功能
"""
import os
import sys
import random
from datetime import datetime, date, timedelta

# 模拟候选人数据
MOCK_CANDIDATES = [
    {
        "name": "张三",
        "email": "zhangsan@example.com",
        "phone": "13800138001",
        "location": "北京",
        "years_experience": 5,
        "current_title": "高级Python开发工程师",
        "current_company": "某科技公司",
        "skills": ["Python", "FastAPI", "Django", "PostgreSQL", "Redis", "Docker", "Kubernetes"],
        "summary": "5年Python后端开发经验，擅长高并发系统设计与优化",
        "raw_text": """张三 - 高级Python开发工程师
联系方式: zhangsan@example.com | 13800138001
现居住地: 北京

技能专长:
- Python, FastAPI, Django, Flask
- PostgreSQL, MySQL, Redis
- Docker, Kubernetes, CI/CD
- 消息队列: RabbitMQ, Kafka

工作经历:
2020-至今 某科技公司 高级后端开发
- 负责核心业务系统架构设计与开发
- 优化系统性能，QPS提升300%
- 带领3人团队完成多个项目交付

教育背景:
2015-2019 北京大学 计算机科学与技术 本科
"""
    },
    {
        "name": "李四",
        "email": "lisi@example.com",
        "phone": "13800138002",
        "location": "上海",
        "years_experience": 3,
        "current_title": "前端开发工程师",
        "current_company": "互联网公司",
        "skills": ["JavaScript", "TypeScript", "Vue.js", "React", "Node.js", "CSS", "HTML"],
        "summary": "3年前端开发经验，精通Vue和React框架",
        "raw_text": """李四 - 前端开发工程师
联系方式: lisi@example.com | 13800138002
现居住地: 上海

技能专长:
- JavaScript, TypeScript
- Vue.js, React, Angular
- Node.js, Express
- HTML5, CSS3, Sass

工作经历:
2021-至今 互联网公司 前端开发
- 负责公司产品前端开发
- 参与技术选型和架构设计
- 性能优化，首屏加载时间减少50%

教育背景:
2017-2021 上海交通大学 软件工程 本科
"""
    },
    {
        "name": "王五",
        "email": "wangwu@example.com",
        "phone": "13800138003",
        "location": "深圳",
        "years_experience": 8,
        "current_title": "技术总监",
        "current_company": "AI创业公司",
        "skills": ["Python", "Machine Learning", "TensorFlow", "PyTorch", "AWS", "团队管理"],
        "summary": "8年技术经验，3年团队管理经验，专注AI产品落地",
        "raw_text": """王五 - 技术总监
联系方式: wangwu@example.com | 13800138003
现居住地: 深圳

技能专长:
- Python, Machine Learning
- TensorFlow, PyTorch, Scikit-learn
- AWS, GCP云服务
- 团队管理, 项目管理

工作经历:
2022-至今 AI创业公司 技术总监
- 带领20人技术团队
- 负责AI产品技术架构
- 推动多个AI项目商业化落地

2018-2022 大厂 高级算法工程师
- 推荐算法优化
- 用户增长模型设计

教育背景:
2012-2016 清华大学 计算机科学 本科
2016-2018 清华大学 人工智能 硕士
"""
    },
    {
        "name": "赵六",
        "email": "zhaoliu@example.com",
        "phone": "13800138004",
        "location": "杭州",
        "years_experience": 4,
        "current_title": "Java开发工程师",
        "current_company": "电商平台",
        "skills": ["Java", "Spring Boot", "MySQL", "Redis", "RabbitMQ", "微服务"],
        "summary": "4年Java后端开发经验，擅长微服务架构和高并发处理",
        "raw_text": """赵六 - Java开发工程师
联系方式: zhaoliu@example.com | 13800138004
现居住地: 杭州

技能专长:
- Java, Spring Boot, Spring Cloud
- MySQL, Redis, MongoDB
- RabbitMQ, Kafka
- 微服务架构, 分布式系统

工作经历:
2020-至今 电商平台 Java开发
- 负责订单系统核心开发
- 参与双十一大促技术保障
- 系统重构，提升30%性能

教育背景:
2016-2020 浙江大学 软件工程 本科
"""
    },
    {
        "name": "孙七",
        "email": "sunqi@example.com",
        "phone": "13800138005",
        "location": "广州",
        "years_experience": 2,
        "current_title": "DevOps工程师",
        "current_company": "金融科技公司",
        "skills": ["Linux", "Docker", "Kubernetes", "Jenkins", "Ansible", "Prometheus", "Grafana"],
        "summary": "2年DevOps经验，专注于CI/CD和监控体系建设",
        "raw_text": """孙七 - DevOps工程师
联系方式: sunqi@example.com | 13800138005
现居住地: 广州

技能专长:
- Linux, Shell脚本
- Docker, Kubernetes, Helm
- Jenkins, GitLab CI, ArgoCD
- Prometheus, Grafana, ELK

工作经历:
2022-至今 金融科技公司 DevOps工程师
- 负责公司CI/CD流程优化
- 搭建监控告警体系
- 容器化改造，部署效率提升10倍

教育背景:
2018-2022 中山大学 网络工程 本科
"""
    },
]

def generate_embedding():
    """生成模拟的 1536 维 embedding（OpenAI 格式）"""
    return [random.uniform(-0.1, 0.1) for _ in range(1536)]

def main():
    """主函数：直接在测试服执行"""
    print("🚀 开始生成测试数据...")
    
    # 设置测试用户 ID
    TEST_USER_ID = 5
    
    # SQL 语句
    sql_statements = []
    
    for i, candidate in enumerate(MOCK_CANDIDATES, 1):
        # 1. 插入 candidates 表
        skills_array = "{" + ",".join(f'"{s}"' for s in candidate["skills"]) + "}"
        raw_text_escaped = candidate["raw_text"].replace("'", "''")
        
        insert_candidate = f"""
INSERT INTO candidates (user_id, name, email, phone, location, years_experience, current_title, current_company, skills, summary, raw_text, status, created_at, updated_at)
VALUES ({TEST_USER_ID}, '{candidate["name"]}', '{candidate["email"]}', '{candidate["phone"]}', '{candidate["location"]}', {candidate["years_experience"]}, '{candidate["current_title"]}', '{candidate["current_company"]}', '{skills_array}', '{candidate["summary"]}', '{raw_text_escaped}', 'active', NOW(), NOW())
RETURNING id;
"""
        sql_statements.append(insert_candidate)
        
        # 2. 插入 candidate_index 表（需要 candidate_id）
        lexical_text = f"{candidate['name']} {candidate['current_title']} {' '.join(candidate['skills'])} {candidate['summary']}"
        embedding = generate_embedding()
        embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"
        filters_json = f'{{"location": "{candidate["location"]}", "years_experience": {candidate["years_experience"]}}}'
        features_json = f'{{"title": "{candidate["current_title"]}", "top_skills": {candidate["skills"][:3]}}}'.replace("'", '"')
        
        insert_index = f"""
INSERT INTO candidate_index (candidate_id, lexical_tsv, embedding, filters_json, features_json, embedding_version, index_updated_at)
SELECT id, to_tsvector('simple', '{lexical_text}'), '{embedding_str}'::vector, '{filters_json}'::jsonb, '{features_json}'::jsonb, 1, NOW()
FROM candidates WHERE email = '{candidate["email"]}';
"""
        sql_statements.append(insert_index)
    
    # 输出 SQL
    full_sql = "\n".join(sql_statements)
    print(full_sql)

if __name__ == "__main__":
    main()
