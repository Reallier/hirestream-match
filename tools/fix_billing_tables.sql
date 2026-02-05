-- 紧急修复 - 创建计费所需的表
-- 2026-01-27 计费系统故障修复

-- 1. 使用记录表
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

-- 2. 交易流水表
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

-- 3. 匹配记录表
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
