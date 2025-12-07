# -*- coding: utf-8 -*-
"""
数据库连接和初始化模块

支持 SQLite（开发）和 PostgreSQL（生产）
"""

import os
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

# 数据库 URL，默认使用 SQLite
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/hirestream.db")

# 创建引擎
# SQLite 需要 check_same_thread=False 才能在多线程环境使用
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False  # 设为 True 可以看到 SQL 语句
    )
else:
    engine = create_engine(DATABASE_URL, echo=False)

# 创建 Session 工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 声明基类
Base = declarative_base()


def init_db():
    """
    初始化数据库，创建所有表
    
    需要先 import models 以注册所有模型
    """
    # 确保 data 目录存在
    if DATABASE_URL.startswith("sqlite"):
        import pathlib
        db_path = DATABASE_URL.replace("sqlite:///", "")
        pathlib.Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    
    # 导入模型以注册
    from models import User, UsageRecord, Transaction  # noqa: F401
    
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    print(f"✅ 数据库初始化完成: {DATABASE_URL}")


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
