# TalentAI 数据库迁移与健康检查

## 概述

为防止类似 2026-01-27 计费系统静默失败的严重事故，TalentAI 现已实现：

1. **Alembic 数据库迁移** - 版本化管理 schema 变更
2. **启动时健康检查** - 验证所有必要的表和列是否存在

## 迁移命令

```bash
# 在 backend 目录执行
cd products/app01-hirestream-match/backend

# 查看当前版本
alembic current

# 升级到最新版本
alembic upgrade head

# 回滚一个版本
alembic downgrade -1

# 查看迁移历史
alembic history --verbose

# 自动生成新迁移（基于模型变更）
alembic revision --autogenerate -m "描述变更内容"
```

## 健康检查

启动时自动执行，也可手动运行：

```bash
cd backend/match_service
python -c "
from database import engine
from db_health import check_database_health
check_database_health(engine)
"
```

## 必需的表和列

健康检查验证以下 schema：

### users (与官网共享)
- id, email, username, password, name, avatar
- openid, unionid, role, balance, free_quota
- **consent_data_storage**, **consent_updated_at** (新增)
- created_at, updated_at

### hm_usage_records (使用记录)
- id, user_id, request_id, operation, model
- prompt_tokens, completion_tokens, cost, created_at

### hm_transactions (交易流水)
- id, user_id, type, amount, balance_after
- reference_id, remark, created_at

### hm_match_records (匹配记录)
- id, user_id, jd_text, resume_text, resume_filename
- match_score, report_json, prompt_tokens, completion_tokens
- cost, created_at

### hm_feedbacks (用户反馈)
- id, user_id, type, content, contact, page
- status, admin_note, created_at, updated_at

## 部署新迁移

1. 创建迁移文件：
   ```bash
   alembic revision --autogenerate -m "添加新功能"
   ```

2. 检查生成的迁移文件

3. 本地测试：
   ```bash
   alembic upgrade head
   ```

4. 部署到生产：
   ```bash
   # 方法 1：通过 Docker 执行
   docker exec talentai_backend alembic upgrade head
   
   # 方法 2：直接在数据库执行 SQL
   docker exec -i talentai_db psql -U talentai -d talentai < migration.sql
   ```

## 故障排查

如果启动时健康检查失败：

1. 查看具体缺失的表/列
2. 运行迁移命令补齐 schema
3. 或手动执行 SQL 添加缺失部分

```sql
-- 示例：添加缺失的列
ALTER TABLE users ADD COLUMN IF NOT EXISTS consent_data_storage BOOLEAN;
ALTER TABLE users ADD COLUMN IF NOT EXISTS consent_updated_at TIMESTAMP;
```
