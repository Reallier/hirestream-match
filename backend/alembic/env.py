# -*- coding: utf-8 -*-
"""
Alembic 环境配置

自动从项目配置读取数据库连接，并导入所有模型用于自动生成迁移。
"""

import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# ============================================
# 添加项目路径以支持模型导入
# ============================================
# 获取当前文件所在目录 (alembic/)
current_dir = os.path.dirname(os.path.abspath(__file__))
# 获取 backend 目录
backend_dir = os.path.dirname(current_dir)
# 添加到 Python 路径
sys.path.insert(0, backend_dir)
sys.path.insert(0, os.path.join(backend_dir, "match_service"))

# 加载环境变量
from dotenv import load_dotenv
load_dotenv(os.path.join(backend_dir, ".env"))

# ============================================
# 导入项目模型
# ============================================
# 导入 match_service 的模型 (使用 hm_* 表)
from match_service.database import Base as MatchServiceBase
from match_service.models import User, UsageRecord, Transaction, MatchRecord, Feedback

# 导入主应用的模型 (candidates, resumes 等)
from models import Base as MainBase, Candidate, Resume, Experience, Project, Education

# ============================================
# Alembic 配置
# ============================================
config = context.config

# 从环境变量设置数据库 URL
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://talentai:talentai123@localhost:5432/talentai"
)
config.set_main_option("sqlalchemy.url", DATABASE_URL)

# 配置日志
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ============================================
# 合并所有模型的 metadata
# ============================================
# 由于 match_service 和 main 使用不同的 Base，需要合并 metadata
# 这里使用 match_service 的 Base 作为主 metadata（包含 hm_* 表）
target_metadata = MatchServiceBase.metadata

# 可选：如果需要同时管理 main 的表，可以合并：
# from sqlalchemy import MetaData
# combined_metadata = MetaData()
# for meta in [MatchServiceBase.metadata, MainBase.metadata]:
#     for table in meta.tables.values():
#         table.tometadata(combined_metadata)
# target_metadata = combined_metadata

# ============================================
# 迁移运行函数
# ============================================

def run_migrations_offline() -> None:
    """
    以 'offline' 模式运行迁移。
    
    只生成 SQL 脚本，不实际连接数据库。
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    以 'online' 模式运行迁移。
    
    实际连接数据库并执行迁移。
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata,
            # 启用自动生成比对
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
