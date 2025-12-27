#!/bin/bash
# TalentAI 统一部署脚本

set -e

SSH_KEY="$HOME/Downloads/reallier.pem"
SSH_HOST="root@119.29.166.51"
REGISTRY="ccr.ccs.tencentyun.com/reallier"

echo "========================================"
echo "  TalentAI - 统一部署脚本"
echo "========================================"

# 选择要部署的服务
SERVICE=${1:-"all"}

update_compose() {
    echo ""
    echo "[0/4] 更新服务器 compose.yml..."
    scp -i $SSH_KEY deploy/compose.yml $SSH_HOST:/data/app-stack/talentai/compose.yml
}

deploy_backend() {
    echo ""
    echo "[1/5] 复制 shared 目录到 backend..."
    cp -r ../shared backend/shared
    
    echo ""
    echo "[2/5] 构建 talentai-backend 镜像..."
    cd backend
    docker buildx build --platform linux/amd64 -t talentai-backend:latest --load .
    
    # 清理复制的 shared 目录
    rm -rf shared
    cd ..
    
    echo ""
    echo "[3/5] 标记镜像..."
    docker tag talentai-backend:latest $REGISTRY/talentai-backend:latest
    
    echo ""
    echo "[4/5] 推送镜像..."
    docker push $REGISTRY/talentai-backend:latest
    
    echo ""
    echo "[5/5] 更新服务器..."
    ssh -i $SSH_KEY $SSH_HOST "cd /data/app-stack/talentai && \
        docker compose pull talentai-backend && \
        docker compose up -d talentai-backend"
}

deploy_frontend() {
    echo ""
    echo "[1/4] 构建 talentai-frontend 镜像..."
    cd frontend
    docker buildx build --platform linux/amd64 -t talentai-frontend:latest --load .
    cd ..
    
    echo ""
    echo "[2/4] 标记镜像..."
    docker tag talentai-frontend:latest $REGISTRY/talentai-frontend:latest
    
    echo ""
    echo "[3/4] 推送镜像..."
    docker push $REGISTRY/talentai-frontend:latest
    
    echo ""
    echo "[4/4] 更新服务器..."
    ssh -i $SSH_KEY $SSH_HOST "cd /data/app-stack/talentai && \
        docker compose pull talentai-frontend && \
        docker compose up -d talentai-frontend"
}

case $SERVICE in
    backend)
        deploy_backend
        ;;
    frontend)
        deploy_frontend
        ;;
    all)
        update_compose
        deploy_backend
        deploy_frontend
        ;;
    *)
        echo "用法: ./deploy.sh [backend|frontend|all]"
        exit 1
        ;;
esac

echo ""
echo "========================================"
echo "  部署完成！"
echo "========================================"
echo ""
echo "TalentAI: https://talentai.reallier.top"
