#!/usr/bin/env python3
"""
TalentAI 功能测试运行器

用法:
    # 测试环境 (默认)
    python run_tests.py

    # 生产环境 (只读模式)
    python run_tests.py --env prod

    # 本地环境
    python run_tests.py --env local

    # 带 HTML 报告
    python run_tests.py --html
"""
import subprocess
import sys
import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="TalentAI 功能测试运行器")
    parser.add_argument(
        "--env",
        choices=["test", "prod", "local"],
        default="test",
        help="测试环境"
    )
    parser.add_argument(
        "--readonly",
        action="store_true",
        help="只读模式"
    )
    parser.add_argument(
        "--html",
        action="store_true",
        help="生成 HTML 报告"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="详细输出"
    )
    parser.add_argument(
        "--module", "-m",
        help="只运行指定模块 (如: test_01_health)"
    )
    parser.add_argument(
        "--parallel", "-p",
        type=int,
        default=4,
        help="并发 worker 数量 (默认 4，设为 0 禁用)"
    )
    
    args = parser.parse_args()
    
    # 构建 pytest 命令
    cmd = ["pytest"]
    
    # 环境参数
    cmd.extend([f"--env={args.env}"])
    
    if args.readonly:
        cmd.append("--readonly")
    
    if args.verbose:
        cmd.append("-v")
    
    if args.html:
        cmd.extend(["--html=report.html", "--self-contained-html"])
    
    if args.module:
        cmd.append(f"{args.module}.py")
    
    # 并发执行
    if args.parallel > 0:
        cmd.extend(["-n", str(args.parallel)])
    
    # 禁用 SSL 警告
    cmd.extend(["-W", "ignore::urllib3.exceptions.InsecureRequestWarning"])
    
    # 显示命令
    print(f"🚀 运行测试: {' '.join(cmd)}")
    print(f"📍 环境: {args.env}")
    print("-" * 50)
    
    # 执行
    result = subprocess.run(cmd, cwd=Path(__file__).parent)
    
    return result.returncode

if __name__ == "__main__":
    sys.exit(main())
