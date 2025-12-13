#!/bin/bash
# TalentAI 部署脚本 - 构建并推送镜像到腾讯云

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 镜像仓库
REGISTRY="ccr.ccs.tencentyun.com/reallier"
FRONTEND_IMAGE="$REGISTRY/talentai-frontend:latest"
BACKEND_IMAGE="$REGISTRY/talentai-backend:latest"

echo "==================================="
echo "TalentAI 部署脚本"
echo "==================================="

# 1. 复制共享模块到后端目录
echo ""
echo "📦 准备共享模块..."
rm -rf backend/shared
cp -r ../shared backend/shared
echo "✓ 共享模块已复制到 backend/shared"

# 2. 构建前端镜像
echo ""
echo "🔨 构建前端镜像..."
cd frontend
docker build -t "$FRONTEND_IMAGE" .
echo "✓ 前端镜像构建完成: $FRONTEND_IMAGE"
cd ..

# 3. 构建后端镜像
echo ""
echo "🔨 构建后端镜像..."
cd backend
docker build -t "$BACKEND_IMAGE" .
echo "✓ 后端镜像构建完成: $BACKEND_IMAGE"
cd ..

# 4. 推送镜像
echo ""
echo "📤 推送镜像到腾讯云..."
docker push "$FRONTEND_IMAGE"
docker push "$BACKEND_IMAGE"
echo "✓ 镜像推送完成"

# 5. 清理临时文件
echo ""
echo "🧹 清理临时文件..."
rm -rf backend/shared
echo "✓ 清理完成"

echo ""
echo "==================================="
echo "✅ 部署准备完成！"
echo "==================================="
echo ""
echo "接下来请在服务器上执行："
echo "  cd /data/app-stack/talentai"
echo "  docker compose pull"
echo "  docker compose up -d"
echo ""
echo "访问地址："
echo "  前端: https://talentai.reallier.top:5443"
echo "  API:  https://api.talentai.reallier.top:5443"
echo ""
