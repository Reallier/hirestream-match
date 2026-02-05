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
    
    # 执行数据库健康检查
    try:
        import sys
        import os
        # 添加 match_service 到路径
        match_service_path = os.path.join(os.path.dirname(__file__), 'match_service')
        if match_service_path not in sys.path:
            sys.path.insert(0, match_service_path)
        
        from db_health import check_database_health
        is_healthy = check_database_health(engine, fail_on_error=False)
        if is_healthy:
            print("✅ 数据库 Schema 检查通过")
        else:
            print("⚠️ 数据库 Schema 存在问题，请检查日志")
    except ImportError as e:
        print(f"⚠️ 数据库健康检查模块未找到，跳过 Schema 验证: {e}")
    except Exception as e:
        print(f"⚠️ 数据库健康检查失败: {e}")