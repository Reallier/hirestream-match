#!/bin/bash
echo "========================================"
echo "  HireStream Match - Deployment Script"
echo "========================================"
echo

set -e  # 遇到错误立即退出

# SSH 密钥路径（Mac）
SSH_KEY="${SSH_KEY:-$HOME/Downloads/reallier.pem}"

echo "[1/4] Building Docker image (linux/amd64)..."
docker buildx build --platform linux/amd64 --no-cache -t hirestream:latest --load .

echo
echo "[2/4] Tagging Docker image..."
docker tag hirestream:latest ccr.ccs.tencentyun.com/reallier/hirestream:latest

echo
echo "[3/4] Pushing Docker image to registry..."
docker push ccr.ccs.tencentyun.com/reallier/hirestream:latest

echo
echo "[4/4] Connecting to server and updating containers..."
ssh -i "$SSH_KEY" root@119.29.166.51 "cd /data/app-stack/hirestream && docker compose pull && docker compose up -d"

echo
echo "========================================"
echo "  Deployment completed successfully!"
echo "========================================"
echo
echo "HireStream is now available at: https://app.reallier.top"
