#!/bin/bash
# TalentAI 统一部署脚本
# 用法: ./deploy.sh [backend|frontend|all] [staging|prod]

set -e

# ============ 环境配置 ============
ENV=${2:-"prod"}  # 默认部署到生产环境

# SSH 选项（禁用主机密钥检查以避免交互式提示）
SSH_OPTS="-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"

# Windows 兼容路径处理
if [ -n "$USERPROFILE" ]; then
    # Windows 环境 (Git Bash / PowerShell)
    WIN_HOME=$(cygpath -u "$USERPROFILE" 2>/dev/null || echo "/c/Users/admin")
else
    WIN_HOME="$HOME"
fi

if [ "$ENV" == "staging" ]; then
    SSH_KEY="$WIN_HOME/Downloads/test.pem"
    SSH_HOST="root@111.230.19.24"
    DEPLOY_PATH="/data/app-stack/talentai"
    IMAGE_TAG="staging"
    echo "🧪 目标环境: STAGING (111.230.19.24)"
else
    SSH_KEY="$WIN_HOME/Downloads/reallier.pem"
    SSH_HOST="root@119.29.166.51"
    DEPLOY_PATH="/data/app-stack/talentai"
    IMAGE_TAG="prod"
    echo "🚀 目标环境: PRODUCTION (119.29.166.51)"
fi

REGISTRY="ccr.ccs.tencentyun.com/reallier"


echo "========================================="
echo "  TalentAI - 统一部署脚本"
echo "  镜像标签: $IMAGE_TAG"
echo "========================================="

# 选择要部署的服务
SERVICE=${1:-"all"}

update_compose() {
    echo ""
    echo "[0/4] 更新服务器 compose.yml..."
    scp -i $SSH_KEY $SSH_OPTS deploy/compose.yml $SSH_HOST:$DEPLOY_PATH/compose.yml
}

deploy_backend() {
    echo ""
    echo "[1/5] 复制 shared 目录到 backend..."
    cp -r ../shared backend/shared 2>/dev/null || echo "  (shared 目录不存在，跳过)"
    
    echo ""
    echo "[2/5] 构建 talentai-backend 镜像..."
    cd backend
    docker buildx build --platform linux/amd64 -t talentai-backend:$IMAGE_TAG --load .
    
    # 清理复制的 shared 目录
    rm -rf shared 2>/dev/null || true
    cd ..
    
    echo ""
    echo "[3/5] 标记镜像..."
    docker tag talentai-backend:$IMAGE_TAG $REGISTRY/talentai-backend:$IMAGE_TAG
    
    echo ""
    echo "[4/5] 推送镜像 ($IMAGE_TAG)..."
    docker push $REGISTRY/talentai-backend:$IMAGE_TAG
    
    echo ""
    echo "[5/5] 更新服务器 ($SSH_HOST)..."
    if [ "$ENV" == "staging" ]; then
        ssh -i $SSH_KEY $SSH_OPTS $SSH_HOST "cd $DEPLOY_PATH && \
            docker pull $REGISTRY/talentai-backend:$IMAGE_TAG && \
            docker compose -f compose.staging.yml up -d talentai-backend"
    else
        ssh -i $SSH_KEY $SSH_OPTS $SSH_HOST "cd $DEPLOY_PATH && \
            docker pull $REGISTRY/talentai-backend:$IMAGE_TAG && \
            docker compose up -d talentai-backend"
    fi
}

deploy_frontend() {
    echo ""
    echo "[1/4] 构建 talentai-frontend 镜像..."
    cd frontend
    docker buildx build --platform linux/amd64 -t talentai-frontend:$IMAGE_TAG --load .
    cd ..
    
    echo ""
    echo "[2/4] 标记镜像..."
    docker tag talentai-frontend:$IMAGE_TAG $REGISTRY/talentai-frontend:$IMAGE_TAG
    
    echo ""
    echo "[3/4] 推送镜像 ($IMAGE_TAG)..."
    docker push $REGISTRY/talentai-frontend:$IMAGE_TAG
    
    echo ""
    echo "[4/4] 更新服务器 ($SSH_HOST)..."
    ssh -i $SSH_KEY $SSH_OPTS $SSH_HOST "cd $DEPLOY_PATH && \
        docker pull $REGISTRY/talentai-frontend:$IMAGE_TAG && \
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
        echo "用法: ./deploy.sh [backend|frontend|all] [staging|prod]"
        echo ""
        echo "示例:"
        echo "  ./deploy.sh backend staging   # 部署后端到测试服"
        echo "  ./deploy.sh backend prod      # 部署后端到生产服"
        echo "  ./deploy.sh backend           # 默认部署到生产服"
        exit 1
        ;;
esac

echo ""
echo "========================================="
echo "  部署完成！环境: $ENV"
echo "========================================="
echo ""
if [ "$ENV" == "staging" ]; then
    echo "测试服: https://test.api.talentai.intjsys.com"
else
    echo "生产服: https://talentai.intjsys.com"
fi

