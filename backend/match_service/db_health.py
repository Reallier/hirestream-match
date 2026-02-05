# -*- coding: utf-8 -*-
"""
数据库健康检查模块

启动时验证所有必要的表和列是否存在，防止 ORM 模型与数据库 schema 不同步导致的静默失败。
"""

from typing import List, Tuple, Dict, Any
from sqlalchemy import text
from sqlalchemy.engine import Engine

# 定义必须存在的表和列
REQUIRED_SCHEMA = {
    # 核心用户表
    "users": [
        "id", "email", "username", "password", "name", "avatar",
        "openid", "unionid", "role", "balance", "free_quota",
        "consent_data_storage", "consent_updated_at",
        "created_at", "updated_at"
    ],
    # HireMatch 使用记录表
    "hm_usage_records": [
        "id", "user_id", "request_id", "operation", "model",
        "prompt_tokens", "completion_tokens", "cost", "created_at"
    ],
    # HireMatch 交易流水表
    "hm_transactions": [
        "id", "user_id", "type", "amount", "balance_after",
        "reference_id", "remark", "created_at"
    ],
    # HireMatch 匹配记录表
    "hm_match_records": [
        "id", "user_id", "jd_text", "resume_text", "resume_filename",
        "match_score", "report_json", "prompt_tokens", "completion_tokens",
        "cost", "created_at"
    ],
    # HireMatch 反馈表
    "hm_feedbacks": [
        "id", "user_id", "type", "content", "contact", "page",
        "status", "admin_note", "created_at", "updated_at"
    ],
}


class DatabaseHealthChecker:
    """数据库健康检查器"""
    
    def __init__(self, engine: Engine):
        self.engine = engine
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def check_table_exists(self, table_name: str) -> bool:
        """检查表是否存在"""
        query = text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = :table_name
            )
        """)
        with self.engine.connect() as conn:
            result = conn.execute(query, {"table_name": table_name})
            return result.scalar()
    
    def check_column_exists(self, table_name: str, column_name: str) -> bool:
        """检查列是否存在"""
        query = text("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = :table_name 
                AND column_name = :column_name
            )
        """)
        with self.engine.connect() as conn:
            result = conn.execute(query, {"table_name": table_name, "column_name": column_name})
            return result.scalar()
    
    def get_table_columns(self, table_name: str) -> List[str]:
        """获取表的所有列名"""
        query = text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND table_name = :table_name
        """)
        with self.engine.connect() as conn:
            result = conn.execute(query, {"table_name": table_name})
            return [row[0] for row in result]
    
    def run_checks(self) -> Tuple[bool, List[str], List[str]]:
        """
        执行所有健康检查
        
        Returns:
            (is_healthy, errors, warnings)
        """
        self.errors = []
        self.warnings = []
        
        for table_name, required_columns in REQUIRED_SCHEMA.items():
            # 检查表是否存在
            if not self.check_table_exists(table_name):
                self.errors.append(f"❌ 缺少表: {table_name}")
                continue
            
            # 检查必要的列
            existing_columns = self.get_table_columns(table_name)
            for column in required_columns:
                if column not in existing_columns:
                    self.errors.append(f"❌ 表 {table_name} 缺少列: {column}")
        
        is_healthy = len(self.errors) == 0
        return is_healthy, self.errors, self.warnings
    
    def get_report(self) -> str:
        """获取检查报告"""
        lines = ["=" * 50, "数据库健康检查报告", "=" * 50, ""]
        
        if self.errors:
            lines.append("🔴 错误 (必须修复):")
            for err in self.errors:
                lines.append(f"   {err}")
            lines.append("")
        
        if self.warnings:
            lines.append("🟡 警告 (建议修复):")
            for warn in self.warnings:
                lines.append(f"   {warn}")
            lines.append("")
        
        if not self.errors and not self.warnings:
            lines.append("🟢 所有检查通过!")
        
        lines.append("=" * 50)
        return "\n".join(lines)


def check_database_health(engine: Engine, fail_on_error: bool = True) -> bool:
    """
    执行数据库健康检查
    
    Args:
        engine: SQLAlchemy 引擎
        fail_on_error: 如果为 True，检查失败时抛出异常
        
    Returns:
        是否健康
    """
    checker = DatabaseHealthChecker(engine)
    is_healthy, errors, warnings = checker.run_checks()
    
    print(checker.get_report())
    
    if not is_healthy and fail_on_error:
        raise RuntimeError(
            f"数据库 schema 不完整! 发现 {len(errors)} 个错误。\n"
            "请运行数据库迁移脚本修复问题。"
        )
    
    return is_healthy


def generate_fix_sql(engine: Engine) -> str:
    """
    生成修复缺失表/列的 SQL 语句
    
    Args:
        engine: SQLAlchemy 引擎
        
    Returns:
        修复 SQL 语句
    """
    checker = DatabaseHealthChecker(engine)
    checker.run_checks()
    
    sql_lines = ["-- 自动生成的修复 SQL", "-- 生成时间: " + __import__("datetime").datetime.now().isoformat(), ""]
    
    # 这里只生成添加缺失列的简单 SQL（表需要手动创建）
    for err in checker.errors:
        if "缺少列" in err:
            # 解析错误信息
            import re
            match = re.search(r"表 (\w+) 缺少列: (\w+)", err)
            if match:
                table_name, column_name = match.groups()
                # 添加默认类型（实际使用时需要根据模型调整）
                sql_lines.append(f"-- ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS {column_name} TEXT;")
        elif "缺少表" in err:
            sql_lines.append(f"-- {err} (请手动执行 init-db.sql 或迁移脚本)")
    
    return "\n".join(sql_lines)
