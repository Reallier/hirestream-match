FROM python:3.13-slim
WORKDIR /app

# 安装构建工具
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libc-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install -U uv
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY . .
ENV PATH="/app/.venv/bin:$PATH"

# Gradio 端口
EXPOSE 7860

CMD ["python", "app_gradio.py"]
