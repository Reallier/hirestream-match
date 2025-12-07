FROM python:3.13-slim
WORKDIR /app

RUN pip install -U uv
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY . .
ENV PATH="/app/.venv/bin:$PATH"

# 暴露端口：Streamlit (8501) 和 Admin API (8000)
EXPOSE 8501 8000

# 使用启动脚本同时运行两个服务
RUN chmod +x start.sh
CMD ["./start.sh"]
