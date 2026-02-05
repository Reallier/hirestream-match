# 使用 uv 官方镜像作为基础，包含预装的 uv
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

WORKDIR /app

# 安装系统依赖（保持原有的，不改动以利用缓存）
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 使用 uv 安装 Python 依赖（比 pip 快 10-100 倍）
RUN uv pip install --system --no-cache -r requirements.txt

# 复制应用代码（包含 shared 目录，由构建脚本预先复制）
COPY . .

# 创建上传目录
RUN mkdir -p /app/uploads

# 暴露端口
EXPOSE 8000

# 启动命令 (通过环境变量控制 worker 数量，默认 2)
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port 8000 --workers ${UVICORN_WORKERS:-2}"]