#!/bin/bash
# ============================================
# TalentAI 数据库迁移脚本
# ============================================
# 
# 使用方法:
#   ./migrate.sh upgrade      # 升级到最新版本
#   ./migrate.sh downgrade -1 # 回滚一个版本
#   ./migrate.sh current      # 查看当前版本
#   ./migrate.sh history      # 查看迁移历史
#   ./migrate.sh check        # 检查数据库健康状态
#
# ============================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR"

# 加载环境变量
if [ -f "$BACKEND_DIR/.env" ]; then
    export $(cat "$BACKEND_DIR/.env" | grep -v '^#' | xargs)
fi

# 默认数据库 URL
DATABASE_URL="${DATABASE_URL:-postgresql://talentai:talentai123@localhost:5432/talentai}"
export DATABASE_URL

cd "$BACKEND_DIR"

case "$1" in
    upgrade)
        echo "🔄 执行数据库迁移..."
        alembic upgrade ${2:-head}
        echo "✅ 迁移完成"
        ;;
    downgrade)
        if [ -z "$2" ]; then
            echo "❌ 请指定回滚版本，如: ./migrate.sh downgrade -1"
            exit 1
        fi
        echo "⚠️  回滚数据库到版本: $2"
        read -p "确定要回滚吗? (y/N) " confirm
        if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
            alembic downgrade $2
            echo "✅ 回滚完成"
        else
            echo "取消操作"
        fi
        ;;
    current)
        echo "📍 当前数据库版本:"
        alembic current
        ;;
    history)
        echo "📜 迁移历史:"
        alembic history --verbose
        ;;
    check)
        echo "🔍 检查数据库健康状态..."
        python -c "
import os, sys
sys.path.insert(0, 'match_service')
from database import engine
from db_health import check_database_health
check_database_health(engine, fail_on_error=False)
"
        ;;
    revision)
        if [ -z "$2" ]; then
            echo "❌ 请指定迁移说明，如: ./migrate.sh revision '添加新字段'"
            exit 1
        fi
        echo "📝 创建新迁移: $2"
        alembic revision --autogenerate -m "$2"
        echo "✅ 迁移文件已创建，请检查 alembic/versions/ 目录"
        ;;
    *)
        echo "TalentAI 数据库迁移工具"
        echo ""
        echo "使用方法:"
        echo "  $0 upgrade [version]   升级到指定版本(默认 head)"
        echo "  $0 downgrade <version> 回滚到指定版本"
        echo "  $0 current             查看当前版本"
        echo "  $0 history             查看迁移历史"
        echo "  $0 check               检查数据库健康状态"
        echo "  $0 revision '<desc>'   自动生成新迁移"
        ;;
esac
