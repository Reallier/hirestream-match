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

deploy_match() {
    echo ""
    echo "[1/4] 构建 talentai-match 镜像..."
    cd backend/match_service
    docker buildx build --platform linux/amd64 -t talentai-match:latest --load .
    
    echo ""
    echo "[2/4] 标记镜像..."
    docker tag talentai-match:latest $REGISTRY/talentai-match:latest
    
    echo ""
    echo "[3/4] 推送镜像..."
    docker push $REGISTRY/talentai-match:latest
    
    echo ""
    echo "[4/4] 更新服务器..."
    ssh -i $SSH_KEY $SSH_HOST "cd /data/app-stack/talentai && docker compose pull talentai-match && docker compose up -d talentai-match"
    
    cd ../..
}

deploy_backend() {
    echo ""
    echo "[1/4] 构建 talentai-backend 镜像..."
    cd backend
    docker buildx build --platform linux/amd64 -t talentai-backend:latest --load .
    
    echo ""
    echo "[2/4] 标记镜像..."
    docker tag talentai-backend:latest $REGISTRY/talentai-backend:latest
    
    echo ""
    echo "[3/4] 推送镜像..."
    docker push $REGISTRY/talentai-backend:latest
    
    echo ""
    echo "[4/4] 更新服务器..."
    ssh -i $SSH_KEY $SSH_HOST "cd /data/app-stack/talentai && docker compose pull talentai-backend && docker compose up -d talentai-backend"
    
    cd ..
}

deploy_frontend() {
    echo ""
    echo "[1/4] 构建 talentai-frontend 镜像..."
    cd frontend
    docker buildx build --platform linux/amd64 -t talentai-frontend:latest --load .
    
    echo ""
    echo "[2/4] 标记镜像..."
    docker tag talentai-frontend:latest $REGISTRY/talentai-frontend:latest
    
    echo ""
    echo "[3/4] 推送镜像..."
    docker push $REGISTRY/talentai-frontend:latest
    
    echo ""
    echo "[4/4] 更新服务器..."
    ssh -i $SSH_KEY $SSH_HOST "cd /data/app-stack/talentai && docker compose pull talentai-frontend && docker compose up -d talentai-frontend"
    
    cd ..
}

case $SERVICE in
    match)
        deploy_match
        ;;
    backend)
        deploy_backend
        ;;
    frontend)
        deploy_frontend
        ;;
    all)
        deploy_match
        deploy_backend
        deploy_frontend
        ;;
    *)
        echo "用法: ./deploy.sh [match|backend|frontend|all]"
        exit 1
        ;;
esac

echo ""
echo "========================================"
echo "  部署完成！"
echo "========================================"
echo ""
echo "TalentAI: https://talentai.reallier.top:5443"
echo "匹配服务: https://talentai.reallier.top:5443/match"
