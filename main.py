import sys, os, pathlib, subprocess

def main():
    # 确定 app.py 路径
    app_path = str(pathlib.Path(__file__).with_name("app.py"))

    # 关闭热重载等耗资源功能
    os.environ["STREAMLIT_SERVER_FILEWATCHER_TYPE"] = "none"
    os.environ["STREAMLIT_GLOBAL_DEVELOPMENT_MODE"] = "false"
    os.environ["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"

    # 启动命令：使用独立进程运行 streamlit
    cmd = [sys.executable, "-m", "streamlit", "run", app_path, "--server.headless", "true"]
    subprocess.Popen(cmd)  # 异步启动，让 GUI 不卡死

if __name__ == "__main__":
    main()