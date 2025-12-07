#!/bin/bash
# 启动脚本：同时运行 Streamlit 和 FastAPI Admin API

# 启动 FastAPI Admin API (后台运行)
uvicorn admin_api:admin_app --host 0.0.0.0 --port 8000 &

# 启动 Streamlit (前台运行)
streamlit run app.py --server.port=8501 --server.address=0.0.0.0
