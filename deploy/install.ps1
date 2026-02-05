# ============================================
# TalentAI 企业私有化部署 - Windows 安装脚本
# ============================================
#
# 使用方式:
#   以管理员身份运行 PowerShell
#   .\install.ps1
#
# 系统要求:
#   - Windows Server 2019+ 或 Windows 10/11 Pro
#   - Docker Desktop 或 Docker Engine
#   - 至少 4GB RAM, 2 核 CPU, 20GB 磁盘
#
# ============================================

$ErrorActionPreference = "Stop"

# 版本
$VERSION = "1.0.0"
$INSTALL_DIR = "C:\TalentAI"

Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════════╗" -ForegroundColor Blue
Write-Host "║                                                           ║" -ForegroundColor Blue
Write-Host "║          TalentAI 企业私有化部署安装程序                  ║" -ForegroundColor Blue
Write-Host "║                    版本: $VERSION                          ║" -ForegroundColor Blue
Write-Host "║                                                           ║" -ForegroundColor Blue
Write-Host "╚═══════════════════════════════════════════════════════════╝" -ForegroundColor Blue
Write-Host ""

# 检查管理员权限
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")
if (-not $isAdmin) {
    Write-Host "错误: 请以管理员身份运行此脚本" -ForegroundColor Red
    exit 1
}

# 检查 Docker
Write-Host "[1/6] 检查 Docker 环境..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version
    Write-Host "✓ Docker 已安装: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "错误: Docker 未安装或未运行" -ForegroundColor Red
    Write-Host "请先安装 Docker Desktop: https://www.docker.com/products/docker-desktop/"
    exit 1
}

# 检查 Docker Compose
Write-Host "[2/6] 检查 Docker Compose..." -ForegroundColor Yellow
try {
    $composeVersion = docker compose version --short
    Write-Host "✓ Docker Compose 已安装: $composeVersion" -ForegroundColor Green
} catch {
    Write-Host "错误: Docker Compose 不可用" -ForegroundColor Red
    exit 1
}

# 创建安装目录
Write-Host "[3/6] 创建安装目录..." -ForegroundColor Yellow
if (-not (Test-Path $INSTALL_DIR)) {
    New-Item -ItemType Directory -Path $INSTALL_DIR -Force | Out-Null
}
Set-Location $INSTALL_DIR
Write-Host "✓ 安装目录: $INSTALL_DIR" -ForegroundColor Green

# 检查镜像文件
Write-Host "[4/6] 检查 Docker 镜像..." -ForegroundColor Yellow
$imagesDir = Join-Path $INSTALL_DIR "images"
if (Test-Path $imagesDir) {
    Write-Host "检测到离线镜像包，正在导入..."
    Get-ChildItem -Path $imagesDir -Filter "*.tar" | ForEach-Object {
        Write-Host "  导入: $($_.Name)"
        docker load -i $_.FullName
    }
    Write-Host "✓ 镜像导入完成" -ForegroundColor Green
} else {
    Write-Host "⚠ 未检测到离线镜像，将使用在线拉取模式" -ForegroundColor Yellow
}

# 配置环境变量
Write-Host "[5/6] 配置环境变量..." -ForegroundColor Yellow
$envFile = Join-Path $INSTALL_DIR ".env"
$envTemplate = Join-Path $INSTALL_DIR ".env.private.example"

if (-not (Test-Path $envFile)) {
    if (Test-Path $envTemplate) {
        Copy-Item $envTemplate $envFile
        Write-Host "⚠ 已创建 .env 文件，请编辑配置后重新运行" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "必须配置的项目:"
        Write-Host "  - DATABASE_PASSWORD: 数据库密码"
        Write-Host "  - DASHSCOPE_API_KEY: 阿里云 DashScope API Key"
        Write-Host "  - JWT_SECRET: JWT 密钥"
        Write-Host "  - LICENSE_PUBLIC_KEY: License 公钥"
        Write-Host ""
        Write-Host "编辑配置: notepad $envFile"
        Write-Host "完成后运行: $INSTALL_DIR\start.ps1"
        exit 0
    } else {
        Write-Host "错误: 找不到环境变量模板文件" -ForegroundColor Red
        exit 1
    fi
} else {
    Write-Host "✓ 环境变量已配置" -ForegroundColor Green
}

# 启动服务
Write-Host "[6/6] 启动服务..." -ForegroundColor Yellow
docker compose -f compose.private.yml up -d

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "✓ TalentAI 安装完成！" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host ""
Write-Host "访问地址:"
Write-Host "  - 前端: http://localhost:3000"
Write-Host "  - API:  http://localhost:8000"
Write-Host ""
Write-Host "License 激活:"
Write-Host "  1. 获取机器指纹: Invoke-RestMethod http://localhost:8000/api/license/machine-id"
Write-Host "  2. 联系 INTJsys 获取 License Key"
Write-Host "  3. 激活系统"
Write-Host ""
Write-Host "查看日志: docker compose -f compose.private.yml logs -f"
Write-Host "停止服务: docker compose -f compose.private.yml down"
Write-Host ""
