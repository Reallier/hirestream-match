-- ============================================
-- TalentAI 数据库初始化脚本
-- 版本: 1.0.0 (与 ORM 模型对齐)
-- 更新: 2026-01-20
-- ============================================

-- 启用必要的扩展
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================
-- 1. 用户表 (与官网共享)
-- ============================================
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE,
    username VARCHAR(100) UNIQUE,
    password VARCHAR(255),
    name VARCHAR(100),
    avatar TEXT,
    openid VARCHAR(255) UNIQUE,
    unionid VARCHAR(255) UNIQUE,
    role VARCHAR(20) DEFAULT 'user',
    balance NUMERIC(12, 6) DEFAULT 0.0 NOT NULL,
    free_quota NUMERIC(12, 6) DEFAULT 0.0 NOT NULL,
    consent_data_storage BOOLEAN,
    consent_updated_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建默认管理员账号 (密码: admin123)
-- bcrypt hash for 'admin123'
INSERT INTO users (username, email, password, name, role, balance, free_quota)
VALUES (
    'admin',
    'admin@localhost',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X.VrPWGdlQjQhKH.G',
    '系统管理员',
    'admin',
    100.0,
    10.0
) ON CONFLICT (username) DO NOTHING;

-- ============================================
-- 2. 候选人表
-- ============================================
CREATE TABLE IF NOT EXISTS candidates (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(50),
    location VARCHAR(100),
    years_experience INTEGER,
    current_title VARCHAR(200),
    current_company VARCHAR(200),
    skills TEXT[],
    education_level VARCHAR(50),
    source VARCHAR(100),
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_candidates_user_id ON candidates(user_id);
CREATE INDEX IF NOT EXISTS idx_candidates_email ON candidates(email);
CREATE INDEX IF NOT EXISTS idx_candidates_phone ON candidates(phone);
CREATE INDEX IF NOT EXISTS idx_candidates_location ON candidates(location);
CREATE INDEX IF NOT EXISTS idx_candidates_status ON candidates(status);
CREATE INDEX IF NOT EXISTS idx_candidates_updated_at ON candidates(updated_at);

-- ============================================
-- 3. 简历表
-- ============================================
CREATE TABLE IF NOT EXISTS resumes (
    id SERIAL PRIMARY KEY,
    candidate_id INTEGER REFERENCES candidates(id) ON DELETE CASCADE,
    file_uri VARCHAR(500) NOT NULL,
    file_type VARCHAR(20),
    text_content TEXT,
    text_hash VARCHAR(64) UNIQUE,
    parsed_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_resumes_candidate_id ON resumes(candidate_id);
CREATE INDEX IF NOT EXISTS idx_resumes_text_hash ON resumes(text_hash);

-- ============================================
-- 4. 工作经历表
-- ============================================
CREATE TABLE IF NOT EXISTS experiences (
    id SERIAL PRIMARY KEY,
    candidate_id INTEGER REFERENCES candidates(id) ON DELETE CASCADE,
    company VARCHAR(200) NOT NULL,
    title VARCHAR(200) NOT NULL,
    start_date DATE,
    end_date DATE,
    skills TEXT[],
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_experiences_candidate_id ON experiences(candidate_id);
CREATE INDEX IF NOT EXISTS idx_experiences_end_date ON experiences(end_date);

-- ============================================
-- 5. 项目经历表
-- ============================================
CREATE TABLE IF NOT EXISTS projects (
    id SERIAL PRIMARY KEY,
    candidate_id INTEGER REFERENCES candidates(id) ON DELETE CASCADE,
    experience_id INTEGER REFERENCES experiences(id) ON DELETE SET NULL,
    project_name VARCHAR(200),
    role VARCHAR(100),
    start_date DATE,
    end_date DATE,
    skills TEXT[],
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_projects_candidate_id ON projects(candidate_id);

-- ============================================
-- 6. 教育经历表
-- ============================================
CREATE TABLE IF NOT EXISTS education (
    id SERIAL PRIMARY KEY,
    candidate_id INTEGER REFERENCES candidates(id) ON DELETE CASCADE,
    school VARCHAR(200),
    degree VARCHAR(100),
    major VARCHAR(200),
    start_date DATE,
    end_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_education_candidate_id ON education(candidate_id);

-- ============================================
-- 7. 候选人索引表 (向量检索)
-- ============================================
CREATE TABLE IF NOT EXISTS candidate_index (
    candidate_id INTEGER PRIMARY KEY REFERENCES candidates(id) ON DELETE CASCADE,
    lexical_tsv TSVECTOR,
    embedding vector(1536),
    filters_json JSONB,
    features_json JSONB,
    embedding_version INTEGER DEFAULT 1,
    index_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 8. 合并谱系表
-- ============================================
CREATE TABLE IF NOT EXISTS merge_lineage (
    id SERIAL PRIMARY KEY,
    candidate_id INTEGER REFERENCES candidates(id) ON DELETE CASCADE,
    from_resume_id INTEGER REFERENCES resumes(id) ON DELETE SET NULL,
    merge_rule VARCHAR(100),
    field_name VARCHAR(100),
    old_value TEXT,
    new_value TEXT,
    decided_by VARCHAR(100) DEFAULT 'system',
    decided_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_merge_lineage_candidate_id ON merge_lineage(candidate_id);
CREATE INDEX IF NOT EXISTS idx_merge_lineage_from_resume_id ON merge_lineage(from_resume_id);

-- ============================================
-- 9. 审计日志表
-- ============================================
CREATE TABLE IF NOT EXISTS audit_log (
    id SERIAL PRIMARY KEY,
    entity_type VARCHAR(50),
    entity_id INTEGER,
    action VARCHAR(50),
    changes JSONB,
    performed_by VARCHAR(100),
    performed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_audit_log_entity_type ON audit_log(entity_type);
CREATE INDEX IF NOT EXISTS idx_audit_log_entity_id ON audit_log(entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_performed_at ON audit_log(performed_at);

-- ============================================
-- 10. 技能新鲜度表
-- ============================================
CREATE TABLE IF NOT EXISTS skill_recency (
    id SERIAL PRIMARY KEY,
    candidate_id INTEGER REFERENCES candidates(id) ON DELETE CASCADE,
    skill VARCHAR(200),
    last_used_date DATE,
    source VARCHAR(100)
);

CREATE INDEX IF NOT EXISTS idx_skill_recency_candidate_id ON skill_recency(candidate_id);
CREATE INDEX IF NOT EXISTS idx_skill_recency_skill ON skill_recency(skill);

-- ============================================
-- 11. 使用记录表 (HireMatch)
-- ============================================
CREATE TABLE IF NOT EXISTS hm_usage_records (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    request_id VARCHAR(64) NOT NULL UNIQUE,
    operation VARCHAR(20) NOT NULL,
    model VARCHAR(50) NOT NULL,
    prompt_tokens INTEGER DEFAULT 0,
    completion_tokens INTEGER DEFAULT 0,
    cost NUMERIC(12, 6) DEFAULT 0.0 NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_usage_user_created ON hm_usage_records(user_id, created_at);

-- ============================================
-- 12. 交易流水表 (HireMatch)
-- ============================================
CREATE TABLE IF NOT EXISTS hm_transactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    type VARCHAR(20) NOT NULL,
    amount NUMERIC(12, 6) NOT NULL,
    balance_after NUMERIC(12, 6) NOT NULL,
    reference_id VARCHAR(64),
    remark TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_trans_user_created ON hm_transactions(user_id, created_at);

-- ============================================
-- 13. 匹配记录表 (HireMatch)
-- ============================================
CREATE TABLE IF NOT EXISTS hm_match_records (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    jd_text TEXT NOT NULL,
    resume_text TEXT NOT NULL,
    resume_filename VARCHAR(255),
    match_score INTEGER,
    report_json JSONB,
    prompt_tokens INTEGER DEFAULT 0,
    completion_tokens INTEGER DEFAULT 0,
    cost NUMERIC(12, 6) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_match_records_user ON hm_match_records(user_id, created_at);

-- ============================================
-- 14. 用户反馈表 (HireMatch)
-- ============================================
CREATE TABLE IF NOT EXISTS hm_feedbacks (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    type VARCHAR(50) DEFAULT 'suggestion',
    content TEXT NOT NULL,
    contact VARCHAR(255),
    page VARCHAR(255),
    status VARCHAR(50) DEFAULT 'pending',
    admin_note TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_feedbacks_user_id ON hm_feedbacks(user_id);

-- ============================================
-- 完成提示
-- ============================================
DO $$
BEGIN
    RAISE NOTICE '================================';
    RAISE NOTICE 'TalentAI 数据库初始化完成!';
    RAISE NOTICE '版本: 1.0.0 (私有化部署)';
    RAISE NOTICE '================================';
    RAISE NOTICE '默认管理员账号:';
    RAISE NOTICE '  用户名: admin';
    RAISE NOTICE '  密码: admin123';
    RAISE NOTICE '================================';
END $$;
