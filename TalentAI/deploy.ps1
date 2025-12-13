# TalentAI Deploy Script - Build and push images to Tencent Cloud (PowerShell)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# Image registry
$REGISTRY = "ccr.ccs.tencentyun.com/reallier"
$FRONTEND_IMAGE = "$REGISTRY/talentai-frontend:latest"
$BACKEND_IMAGE = "$REGISTRY/talentai-backend:latest"

Write-Host "===================================" -ForegroundColor Cyan
Write-Host "TalentAI Deploy Script" -ForegroundColor Cyan
Write-Host "===================================" -ForegroundColor Cyan

# 1. Copy shared module to backend directory
Write-Host ""
Write-Host "[1/5] Preparing shared module..." -ForegroundColor Yellow
if (Test-Path "backend\shared") {
    Remove-Item -Recurse -Force "backend\shared"
}
Copy-Item -Recurse "..\shared" "backend\shared"
Write-Host "Done: shared module copied to backend\shared" -ForegroundColor Green

# 2. Build frontend image
Write-Host ""
Write-Host "[2/5] Building frontend image..." -ForegroundColor Yellow
Set-Location "frontend"
docker build -t $FRONTEND_IMAGE .
if ($LASTEXITCODE -ne 0) { throw "Frontend image build failed" }
Write-Host "Done: $FRONTEND_IMAGE" -ForegroundColor Green
Set-Location ..

# 3. Build backend image
Write-Host ""
Write-Host "[3/5] Building backend image..." -ForegroundColor Yellow
Set-Location "backend"
docker build -t $BACKEND_IMAGE .
if ($LASTEXITCODE -ne 0) { throw "Backend image build failed" }
Write-Host "Done: $BACKEND_IMAGE" -ForegroundColor Green
Set-Location ..

# 4. Push images
Write-Host ""
Write-Host "[4/5] Pushing images to Tencent Cloud..." -ForegroundColor Yellow
docker push $FRONTEND_IMAGE
if ($LASTEXITCODE -ne 0) { throw "Frontend image push failed" }
docker push $BACKEND_IMAGE
if ($LASTEXITCODE -ne 0) { throw "Backend image push failed" }
Write-Host "Done: images pushed" -ForegroundColor Green

# 5. Cleanup
Write-Host ""
Write-Host "[5/5] Cleaning up..." -ForegroundColor Yellow
Remove-Item -Recurse -Force "backend\shared"
Write-Host "Done: cleanup complete" -ForegroundColor Green

Write-Host ""
Write-Host "===================================" -ForegroundColor Cyan
Write-Host "Deploy preparation complete!" -ForegroundColor Green
Write-Host "===================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps on server:"
Write-Host "  cd /data/app-stack/talentai"
Write-Host "  docker compose pull"
Write-Host "  docker compose up -d"
Write-Host ""
Write-Host "URLs:"
Write-Host "  Frontend: https://talentai.reallier.top:5443" -ForegroundColor Blue
Write-Host "  API:      https://api.talentai.reallier.top:5443" -ForegroundColor Blue
Write-Host ""
