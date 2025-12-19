#!/bin/bash
# 启动脚本：同时运行 Gradio 和 FastAPI Admin API

# 启动 FastAPI Admin API (后台运行)
uvicorn admin_api:admin_app --host 0.0.0.0 --port 8000 &

# 启动 Gradio (前台运行)
python app_gradio.py
