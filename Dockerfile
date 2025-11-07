# 1. 使用官方 Python 3.12 轻量级基础镜像
FROM python:3.12-slim

# 2. 设置容器内的工作目录
WORKDIR /app

# 3. 复制依赖文件到容器中
COPY requirements.txt .

# 4. 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 5. 复制项目当前目录下的所有文件到容器工作目录
COPY . .

# 6. 暴露应用运行的端口 (如果是 Streamlit 默认是 8501)
EXPOSE 8501

# 7. 启动命令
# 如果是 Streamlit 应用：
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
# 如果是普通 Python 脚本 (如 main.py)：
# CMD ["python", "main.py"]