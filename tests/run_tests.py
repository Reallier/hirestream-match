#!/usr/bin/env python3
"""
TalentAI 测试运行器 (带历史记录)

用法:
    # 测试环境 (默认)
    python run_tests.py

    # 生产环境 (只读模式)
    python run_tests.py --env prod

    # 指定并发数
    python run_tests.py -p 8
    
    # 查看历史记录
    python run_tests.py --history
"""
import subprocess
import sys
import argparse
import json
from pathlib import Path
from datetime import datetime

HISTORY_FILE = Path(__file__).parent / "test_history.json"

def load_history() -> dict:
    """加载历史记录"""
    if HISTORY_FILE.exists():
        return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    return {"runs": [], "tests": {}}

def save_history(history: dict):
    """保存历史记录"""
    HISTORY_FILE.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")

def parse_pytest_output(output: str) -> dict:
    """解析 pytest 输出获取测试结果"""
    result = {"passed": 0, "failed": 0, "total": 0, "details": []}
    
    # 解析 "X passed, Y failed" 格式
    for line in output.split("\n"):
        if "passed" in line and ("failed" in line or "=" in line):
            parts = line.split()
            for i, part in enumerate(parts):
                if part == "passed" and i > 0:
                    try:
                        result["passed"] = int(parts[i-1])
                    except ValueError:
                        pass
                if part == "failed" and i > 0:
                    try:
                        result["failed"] = int(parts[i-1].rstrip(","))
                    except ValueError:
                        pass
        
        # 解析失败的测试名
        if "FAILED" in line:
            test_name = line.split("FAILED")[-1].strip().split(" ")[0].strip()
            if test_name:
                result["details"].append(test_name)
    
    result["total"] = result["passed"] + result["failed"]
    return result

def show_history():
    """显示历史记录"""
    history = load_history()
    
    if not history["runs"]:
        print("📭 暂无测试历史记录")
        return
    
    print("\n📊 测试历史记录")
    print("=" * 60)
    
    # 最近 5 次运行
    print("\n🕐 最近运行:")
    for run in history["runs"][-5:][::-1]:
        status = "✅" if run["failed"] == 0 else "❌"
        rate = run["passed"] / run["total"] * 100 if run["total"] > 0 else 0
        print(f"  {status} {run['time']} | {run['passed']}/{run['total']} ({rate:.1f}%) | {run['env']}")
    
    # 问题测试统计
    if history["tests"]:
        print("\n📌 测试状态:")
        for test_name, info in sorted(history["tests"].items(), key=lambda x: -x[1].get("fail_count", 0)):
            if info.get("fail_count", 0) > 0:
                last = "✅" if info.get("last_status") == "passed" else "❌"
                print(f"  {last} {test_name.split('::')[-1][:40]:<40} | 失败 {info['fail_count']} 次")
    
    print()

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
    parser.add_argument(
        "--history",
        action="store_true",
        help="显示历史记录"
    )
    parser.add_argument(
        "--cov",
        action="store_true",
        help="生成覆盖率报告 (输出到 reports/coverage/)"
    )
    
    args = parser.parse_args()
    
    # 显示历史
    if args.history:
        show_history()
        return 0
    
    # 构建 pytest 命令
    cmd = ["pytest"]
    
    # 环境参数
    cmd.extend([f"--env={args.env}"])
    
    if args.readonly:
        cmd.append("--readonly")
    
    if args.verbose:
        cmd.append("-v")
    else:
        cmd.append("-q")  # 简洁输出便于解析
    
    cmd.append("--tb=no")  # 不显示 traceback
    
    if args.module:
        cmd.append(f"{args.module}.py")
    
    # 并发执行
    if args.parallel > 0:
        cmd.extend(["-n", str(args.parallel)])
    
    # 覆盖率报告
    if args.cov:
        cmd.extend([
            "--cov=../backend",
            "--cov-report=html:reports/coverage",
            "--cov-report=term-missing"
        ])
    
    # 禁用 SSL 警告
    cmd.extend(["-W", "ignore::urllib3.exceptions.InsecureRequestWarning"])
    
    # 显示命令
    print(f"🚀 运行测试: pytest --env={args.env} -n {args.parallel}")
    print(f"📍 环境: {args.env}")
    print("-" * 50)
    
    # 执行
    result = subprocess.run(
        cmd, 
        cwd=Path(__file__).parent,
        capture_output=True,
        text=True
    )
    
    # 输出结果
    print(result.stdout)
    if result.stderr:
        print(result.stderr)
    
    # 解析结果并保存历史
    test_result = parse_pytest_output(result.stdout + result.stderr)
    
    history = load_history()
    
    # 记录本次运行
    run_record = {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "env": args.env,
        "passed": test_result["passed"],
        "failed": test_result["failed"],
        "total": test_result["total"],
        "failed_tests": test_result["details"]
    }
    history["runs"].append(run_record)
    
    # 只保留最近 20 次
    history["runs"] = history["runs"][-20:]
    
    # 更新测试状态
    for test_name in test_result["details"]:
        if test_name not in history["tests"]:
            history["tests"][test_name] = {"fail_count": 0, "last_status": "passed"}
        history["tests"][test_name]["fail_count"] += 1
        history["tests"][test_name]["last_status"] = "failed"
        history["tests"][test_name]["last_fail"] = run_record["time"]
    
    save_history(history)
    
    # 显示摘要
    rate = test_result["passed"] / test_result["total"] * 100 if test_result["total"] > 0 else 0
    status = "✅ 全部通过" if test_result["failed"] == 0 else f"❌ {test_result['failed']} 个失败"
    print("-" * 50)
    print(f"📊 结果: {test_result['passed']}/{test_result['total']} ({rate:.1f}%) {status}")
    
    return result.returncode

if __name__ == "__main__":
    sys.exit(main())
