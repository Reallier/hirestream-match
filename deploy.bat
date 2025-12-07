@echo off
echo ========================================
echo   HireStream Match - Deployment Script
echo ========================================
echo.

echo [1/4] Building Docker image...
docker build --no-cache -t hirestream:latest .
if %ERRORLEVEL% neq 0 (
    echo ERROR: Docker build failed!
    pause
    exit /b 1
)

echo.
echo [2/4] Tagging Docker image...
docker tag hirestream:latest ccr.ccs.tencentyun.com/reallier/hirestream:latest
if %ERRORLEVEL% neq 0 (
    echo ERROR: Docker tag failed!
    pause
    exit /b 1
)

echo.
echo [3/4] Pushing Docker image to registry...
docker push ccr.ccs.tencentyun.com/reallier/hirestream:latest
if %ERRORLEVEL% neq 0 (
    echo ERROR: Docker push failed!
    pause
    exit /b 1
)

echo.
echo [4/4] Connecting to server and updating containers...
ssh -i "C:\Users\admin\Downloads\reallier.pem" root@119.29.166.51 "cd /data/app-stack/hirestream && docker compose pull && docker compose up -d"
if %ERRORLEVEL% neq 0 (
    echo ERROR: Server deployment failed!
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Deployment completed successfully!
echo ========================================
echo.
echo HireStream is now available at: https://app.reallier.top
echo.
pause
