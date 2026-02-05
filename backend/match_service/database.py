# -*- coding: utf-8 -*-
"""
数据库连接和初始化模块

默认使用 PostgreSQL（与 TalentAI 共享 talentai-db）
也兼容 SQLite 用于本地开发
"""

import os
from contextlib import contextmanager
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

# 数据库 URL，默认使用 PostgreSQL（与 TalentAI 共享）
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://talentai:talentai123@localhost:5432/talentai")

# 创建引擎
if DATABASE_URL.startswith("sqlite"):
    # SQLite 需要 check_same_thread=False 才能在多线程环境使用
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False
    )
else:
    # PostgreSQL - 添加连接池配置以支持高并发
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        echo=False
    )

# 创建 Session 工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 声明基类
Base = declarative_base()


def init_db(fail_on_schema_error: bool = False):
    """
    初始化数据库
    
    - SQLite: 自动创建表（开发用）
    - PostgreSQL: 仅验证连接，表由 init.sql 创建
    
    Args:
        fail_on_schema_error: 如果为 True，schema 不完整时抛出异常阻止启动
    """
    # 导入模型以注册
    from models import User, UsageRecord, Transaction  # noqa: F401
    
    if DATABASE_URL.startswith("sqlite"):
        # SQLite: 确保 data 目录存在并创建表
        import pathlib
        db_path = DATABASE_URL.replace("sqlite:///", "")
        pathlib.Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        Base.metadata.create_all(bind=engine)
        print(f"✅ SQLite 数据库初始化完成: {DATABASE_URL}")
    else:
        # PostgreSQL: 验证连接和 schema
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print(f"✅ PostgreSQL 连接成功: {DATABASE_URL.split('@')[-1]}")
            
            # 执行数据库健康检查
            try:
                from db_health import check_database_health
                is_healthy = check_database_health(engine, fail_on_error=fail_on_schema_error)
                if is_healthy:
                    print("✅ 数据库 Schema 检查通过")
                else:
                    print("⚠️ 数据库 Schema 存在问题，请检查日志")
            except ImportError:
                print("⚠️ 数据库健康检查模块未找到，跳过 Schema 验证")
            except Exception as e:
                if fail_on_schema_error:
                    raise
                print(f"⚠️ 数据库健康检查失败: {e}")
                
        except Exception as e:
            print(f"❌ PostgreSQL 连接失败: {e}")


@contextmanager
def get_db():
    """
    获取数据库 Session 的上下文管理器
    
    使用示例:
        with get_db() as db:
            user = db.query(User).first()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_db_session():
    """
    获取数据库 Session（用于 Streamlit 等需要手动管理的场景）
    
    注意：调用者需要自己处理 commit/rollback/close
    """
    return SessionLocal()
