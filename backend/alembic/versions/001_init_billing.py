"""初始化 - 创建计费系统表

Revision ID: 001_init_billing
Revises: 
Create Date: 2026-01-27

这是基线迁移，将现有的 hm_* 表结构记录为 Alembic 基线。
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_init_billing'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """创建计费系统所需的所有表"""
    
    # 1. 添加 users 表缺失的列（如不存在）
    # 注意：users 表由官网创建，这里只添加 TalentAI 需要的额外列
    op.execute("""
        ALTER TABLE users ADD COLUMN IF NOT EXISTS consent_data_storage BOOLEAN;
        ALTER TABLE users ADD COLUMN IF NOT EXISTS consent_updated_at TIMESTAMP;
    """)
    
    # 2. 创建 hm_usage_records 表
    op.execute("""
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
    """)
    
    # 3. 创建 hm_transactions 表
    op.execute("""
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
    """)
    
    # 4. 创建 hm_match_records 表
    op.execute("""
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
    """)
    
    # 5. 创建 hm_feedbacks 表
    op.execute("""
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
    """)


def downgrade() -> None:
    """回滚：删除计费系统表"""
    # 注意：这会删除所有数据，谨慎使用！
    op.execute("DROP TABLE IF EXISTS hm_feedbacks CASCADE;")
    op.execute("DROP TABLE IF EXISTS hm_match_records CASCADE;")
    op.execute("DROP TABLE IF EXISTS hm_transactions CASCADE;")
    op.execute("DROP TABLE IF EXISTS hm_usage_records CASCADE;")
    
    # 不删除 users 表的列，因为可能影响其他系统
