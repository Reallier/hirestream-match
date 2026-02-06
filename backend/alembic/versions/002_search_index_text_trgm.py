"""搜索索引增强：search_text + pg_trgm

Revision ID: 002_search_index_text_trgm
Revises: 001_init_billing
Create Date: 2026-02-06
"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '002_search_index_text_trgm'
down_revision = '001_init_billing'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """添加 search_text 字段并重建触发器"""
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
    op.execute("ALTER TABLE candidate_index ADD COLUMN IF NOT EXISTS search_text TEXT;")

    # 替换触发器逻辑：由 search_text 生成 lexical_tsv
    op.execute("DROP TRIGGER IF EXISTS update_candidate_index_lexical ON candidate_index;")
    op.execute("DROP FUNCTION IF EXISTS update_candidate_lexical_tsv();")

    op.execute("""
        CREATE OR REPLACE FUNCTION update_candidate_lexical_tsv()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.lexical_tsv := to_tsvector('simple', COALESCE(NEW.search_text, ''));
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER update_candidate_index_lexical
        BEFORE INSERT OR UPDATE ON candidate_index
        FOR EACH ROW
        EXECUTE FUNCTION update_candidate_lexical_tsv();
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_candidate_index_search_text_trgm
        ON candidate_index USING GIN(search_text gin_trgm_ops);
    """)


def downgrade() -> None:
    """回滚 search_text 字段与 trigram 索引"""
    op.execute("DROP INDEX IF EXISTS idx_candidate_index_search_text_trgm;")
    op.execute("DROP TRIGGER IF EXISTS update_candidate_index_lexical ON candidate_index;")
    op.execute("DROP FUNCTION IF EXISTS update_candidate_lexical_tsv();")
    op.execute("ALTER TABLE candidate_index DROP COLUMN IF EXISTS search_text;")

    # 恢复旧的触发器逻辑（基于 candidates 字段）
    op.execute("""
        CREATE OR REPLACE FUNCTION update_candidate_lexical_tsv()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.lexical_tsv := to_tsvector('simple',
                COALESCE((
                    SELECT name || ' ' || current_title || ' ' || current_company || ' ' || array_to_string(skills, ' ')
                    FROM candidates WHERE id = NEW.candidate_id
                ), '')
            );
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER update_candidate_index_lexical
        BEFORE INSERT OR UPDATE ON candidate_index
        FOR EACH ROW
        EXECUTE FUNCTION update_candidate_lexical_tsv();
    """)
