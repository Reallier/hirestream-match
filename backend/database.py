from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import settings

# 创建业务数据库引擎 (candidates, resumes, etc.)
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

# 创建用户主库引擎 (users)
auth_database_url = settings.auth_database_url or settings.database_url
auth_engine = create_engine(
    auth_database_url,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
AuthSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=auth_engine)

# 创建基类
Base = declarative_base()
AuthBase = declarative_base()


def get_db():
    """获取业务数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_auth_db():
    """获取用户主库会话"""
    db = AuthSessionLocal()
    try:
        yield db
    finally:
        db.close()


async def init_db():
    """初始化数据库（创建表）"""
    Base.metadata.create_all(bind=engine)