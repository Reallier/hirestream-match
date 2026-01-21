#!/bin/bash
# ============================================
# TalentAI 离线镜像打包脚本
# ============================================
#
# 用于生成离线部署包，包含所有 Docker 镜像
#
# 使用方式:
#   ./build_offline_package.sh [VERSION]
#
# 输出:
#   talentai-private-vX.X.X.tar.gz
#
# ============================================

set -e

VERSION=${1:-"1.0.0"}
OUTPUT_DIR="talentai-private-v${VERSION}"
PACKAGE_NAME="${OUTPUT_DIR}.tar.gz"

echo "============================================"
echo "TalentAI 离线部署包构建"
echo "版本: ${VERSION}"
echo "============================================"
echo ""

# 清理旧文件
rm -rf "$OUTPUT_DIR"
rm -f "$PACKAGE_NAME"

# 创建目录结构
echo "[1/6] 创建目录结构..."
mkdir -p "$OUTPUT_DIR"/{images,database,nginx,docs}

# 构建前端镜像
echo "[2/6] 构建前端镜像..."
cd ../frontend
docker build -t talentai-frontend:${VERSION} -t talentai-frontend:latest .
cd ../deploy

# 构建后端镜像
echo "[3/6] 构建后端镜像..."
cd ..
docker build -t talentai-backend:${VERSION} -t talentai-backend:latest .
cd deploy

# 导出镜像
echo "[4/6] 导出 Docker 镜像..."
docker save talentai-frontend:${VERSION} -o "$OUTPUT_DIR/images/talentai-frontend.tar"
docker save talentai-backend:${VERSION} -o "$OUTPUT_DIR/images/talentai-backend.tar"
docker save pgvector/pgvector:pg16 -o "$OUTPUT_DIR/images/postgres-vector.tar"
docker save nginx:alpine -o "$OUTPUT_DIR/images/nginx.tar"

# 复制配置文件
echo "[5/6] 复制配置文件..."
cp compose.private.yml "$OUTPUT_DIR/"
cp .env.private.example "$OUTPUT_DIR/"
cp install.sh "$OUTPUT_DIR/"
cp install.ps1 "$OUTPUT_DIR/"

# 复制数据库初始化脚本
if [ -f "../database/init.sql" ]; then
    cp ../database/init.sql "$OUTPUT_DIR/database/"
fi

# 复制文档
cp -r docs/* "$OUTPUT_DIR/docs/" 2>/dev/null || true

# 创建 Nginx 配置模板
cat > "$OUTPUT_DIR/nginx/nginx.conf" << 'EOF'
events {
    worker_connections 1024;
}

http {
    upstream frontend {
        server talentai-frontend:3000;
    }
    
    upstream backend {
        server talentai-backend:8000;
    }

    server {
        listen 80;
        server_name _;
        
        # 重定向到 HTTPS（如果启用）
        # return 301 https://$host$request_uri;
        
        location / {
            proxy_pass http://frontend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
        
        location /api/ {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
    }
    
    # HTTPS 配置（取消注释并配置证书）
    # server {
    #     listen 443 ssl;
    #     server_name _;
    #     
    #     ssl_certificate /etc/nginx/ssl/cert.pem;
    #     ssl_certificate_key /etc/nginx/ssl/key.pem;
    #     
    #     location / {
    #         proxy_pass http://frontend;
    #     }
    #     
    #     location /api/ {
    #         proxy_pass http://backend;
    #     }
    # }
}
EOF

# 创建 SSL 目录占位
mkdir -p "$OUTPUT_DIR/nginx/ssl"
touch "$OUTPUT_DIR/nginx/ssl/.gitkeep"

# 创建启动脚本
cat > "$OUTPUT_DIR/start.sh" << 'EOF'
#!/bin/bash
docker compose -f compose.private.yml up -d
echo "TalentAI 已启动"
echo "前端: http://localhost:3000"
echo "API:  http://localhost:8000"
EOF
chmod +x "$OUTPUT_DIR/start.sh"

cat > "$OUTPUT_DIR/stop.sh" << 'EOF'
#!/bin/bash
docker compose -f compose.private.yml down
echo "TalentAI 已停止"
EOF
chmod +x "$OUTPUT_DIR/stop.sh"

# 打包
echo "[6/6] 打包..."
tar -czf "$PACKAGE_NAME" "$OUTPUT_DIR"

# 计算大小和校验和
SIZE=$(du -h "$PACKAGE_NAME" | cut -f1)
SHA256=$(sha256sum "$PACKAGE_NAME" | cut -d' ' -f1)

echo ""
echo "============================================"
echo "✓ 离线部署包构建完成"
echo "============================================"
echo ""
echo "输出文件: $PACKAGE_NAME"
echo "文件大小: $SIZE"
echo "SHA256:   $SHA256"
echo ""
echo "包含内容:"
echo "  - Docker 镜像 (前端/后端/数据库/Nginx)"
echo "  - Docker Compose 配置"
echo "  - 安装脚本 (Linux/Windows)"
echo "  - 部署文档"
echo ""

# 清理临时目录
rm -rf "$OUTPUT_DIR"

echo "完成！"
