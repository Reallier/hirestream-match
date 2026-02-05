#!/bin/bash
# ============================================
# TalentAI 企业私有化部署 - 一键安装脚本
# ============================================
#
# 使用方式:
#   chmod +x install.sh && ./install.sh
#
# 系统要求:
#   - Ubuntu 20.04+ / CentOS 8+ / Debian 11+
#   - Docker 20.10+
#   - Docker Compose v2+
#   - 至少 4GB RAM, 2 核 CPU, 20GB 磁盘
#
# ============================================

set -e

VERSION="1.0.0"
INSTALL_DIR="${PWD}"

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

print_banner() {
    echo -e "${CYAN}"
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║                                                               ║"
    echo "║   ████████╗ █████╗ ██╗     ███████╗███╗   ██╗████████╗       ║"
    echo "║   ╚══██╔══╝██╔══██╗██║     ██╔════╝████╗  ██║╚══██╔══╝       ║"
    echo "║      ██║   ███████║██║     █████╗  ██╔██╗ ██║   ██║          ║"
    echo "║      ██║   ██╔══██║██║     ██╔══╝  ██║╚██╗██║   ██║          ║"
    echo "║      ██║   ██║  ██║███████╗███████╗██║ ╚████║   ██║          ║"
    echo "║      ╚═╝   ╚═╝  ╚═╝╚══════╝╚══════╝╚═╝  ╚═══╝   ╚═╝          ║"
    echo "║                                                               ║"
    echo "║           企业私有化部署 v${VERSION}                             ║"
    echo "║           Powered by INTJsys                                  ║"
    echo "║                                                               ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

check_docker() {
    echo -e "${YELLOW}[1/4] 检查 Docker 环境...${NC}"
    
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}✗ Docker 未安装${NC}"
        echo "  请先安装 Docker: https://docs.docker.com/engine/install/"
        exit 1
    fi
    
    if ! docker compose version &> /dev/null; then
        echo -e "${RED}✗ Docker Compose v2 未安装${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ Docker $(docker --version | grep -oP '\d+\.\d+\.\d+')${NC}"
    echo -e "${GREEN}✓ Docker Compose $(docker compose version --short)${NC}"
}

load_images() {
    echo -e "${YELLOW}[2/4] 加载 Docker 镜像...${NC}"
    
    if [ -d "./images" ]; then
        echo "  检测到离线镜像包，正在导入..."
        for img in ./images/*.tar; do
            if [ -f "$img" ]; then
                echo "    导入: $(basename $img)"
                docker load -i "$img" > /dev/null 2>&1
            fi
        done
        echo -e "${GREEN}✓ 离线镜像导入完成${NC}"
    else
        echo "  使用在线镜像，正在拉取..."
        docker compose -f compose.private.yml pull
        echo -e "${GREEN}✓ 镜像拉取完成${NC}"
    fi
}

setup_config() {
    echo -e "${YELLOW}[3/4] 配置环境变量...${NC}"
    
    if [ ! -f ".env" ]; then
        cp .env.private.example .env
        echo -e "${GREEN}✓ 已创建 .env 配置文件${NC}"
    else
        echo -e "${GREEN}✓ .env 配置文件已存在${NC}"
    fi
}

start_services() {
    echo -e "${YELLOW}[4/4] 启动服务...${NC}"
    
    docker compose -f compose.private.yml up -d
    
    echo ""
    echo "  等待服务启动..."
    sleep 10
    
    # 检查服务状态
    if docker compose -f compose.private.yml ps | grep -q "healthy\|running"; then
        echo -e "${GREEN}✓ 服务启动成功${NC}"
    else
        echo -e "${YELLOW}⚠ 服务正在启动中，请稍候...${NC}"
    fi
}

print_success() {
    echo ""
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}                    🎉 TalentAI 部署完成!                       ${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "  ${CYAN}访问地址:${NC}"
    echo "    前端: http://localhost:3000"
    echo "    API:  http://localhost:8000"
    echo ""
    echo -e "  ${CYAN}默认账号:${NC}"
    echo "    用户名: admin"
    echo "    密码:   admin123"
    echo ""
    echo -e "  ${CYAN}License 激活:${NC}"
    echo "    1. 获取机器指纹:"
    echo "       curl http://localhost:8000/api/license/machine-id"
    echo ""
    echo "    2. 联系 INTJsys 获取 License Key"
    echo "       邮箱: license@intjsys.com"
    echo ""
    echo "    3. 激活系统:"
    echo "       curl -X POST http://localhost:8000/api/license/activate \\"
    echo "         -H 'Content-Type: application/json' \\"
    echo "         -d '{\"license_key\": \"YOUR_KEY\"}'"
    echo ""
    echo -e "  ${CYAN}常用命令:${NC}"
    echo "    查看状态: docker compose -f compose.private.yml ps"
    echo "    查看日志: docker compose -f compose.private.yml logs -f"
    echo "    重启服务: docker compose -f compose.private.yml restart"
    echo "    停止服务: docker compose -f compose.private.yml down"
    echo ""
}

# 主流程
print_banner
check_docker
load_images
setup_config
start_services
print_success
