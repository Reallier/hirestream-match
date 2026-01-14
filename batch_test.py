# -*- coding: utf-8 -*-
"""
TalentAI 批量匹配测试脚本

简单的批量测试工具，用于测试 instant-match API

用法:
    python batch_test.py                    # 测试测试服
    python batch_test.py --env prod         # 测试生产
    python batch_test.py --count 20         # 运行 20 次测试
    python batch_test.py --concurrent 5     # 5 并发
"""

import argparse
import time
import requests
import urllib3
from concurrent.futures import ThreadPoolExecutor, as_completed

urllib3.disable_warnings()

# 环境配置
ENVS = {
    "test": "https://test.api.talentai.reallier.top:5443",
    "prod": "https://api.talentai.reallier.top:5443",
    "local": "http://localhost:8000"
}

# 测试数据 - 简单的 JD 和简历组合
TEST_CASES = [
    {
        "name": "Python后端 vs Python工程师",
        "jd": """职位: Python 后端开发
要求: 3年以上Python经验，熟悉FastAPI/Django，熟悉MySQL/PostgreSQL""",
        "resume": """姓名: 测试候选人A
经验: 5年Python开发
技能: Python, FastAPI, Django, MySQL, Redis, Docker
工作经历: 2019-至今 某科技公司 后端开发工程师"""
    },
    {
        "name": "前端开发 vs Vue工程师",
        "jd": """职位: 前端开发工程师
要求: 3年以上前端经验，精通Vue.js或React，熟悉TypeScript""",
        "resume": """姓名: 测试候选人B
经验: 4年前端开发
技能: Vue.js, React, TypeScript, Node.js, Webpack
工作经历: 2020-至今 某互联网公司 前端开发"""
    },
    {
        "name": "AI算法 vs NLP工程师",
        "jd": """职位: AI算法工程师
要求: 硕士及以上，熟悉PyTorch/TensorFlow，有NLP或CV经验""",
        "resume": """姓名: 测试候选人C
经验: 3年算法开发
技能: PyTorch, TensorFlow, NLP, Transformers, BERT
工作经历: 2022-至今 某AI公司 算法工程师
教育: 北京大学 人工智能硕士"""
    },
    {
        "name": "产品经理 vs 技术PM",
        "jd": """职位: 产品经理
要求: 3年以上产品经验，熟悉B端产品，有技术背景优先""",
        "resume": """姓名: 测试候选人D
经验: 5年产品管理
技能: 需求分析, 原型设计, 数据分析, SQL, Agile
工作经历: 2019-至今 某SaaS公司 高级产品经理"""
    },
    {
        "name": "Java后端 vs Python工程师 (不匹配)",
        "jd": """职位: Java 后端开发
要求: 5年以上Java经验，精通Spring Boot，微服务架构""",
        "resume": """姓名: 测试候选人E
经验: 4年Python开发
技能: Python, Django, Flask, Redis
工作经历: 2020-至今 某公司 Python开发"""
    },
]


def run_single_test(api_base: str, test_case: dict, test_id: int) -> dict:
    """运行单个测试"""
    start_time = time.time()
    
    try:
        response = requests.post(
            f"{api_base}/api/instant-match",
            data={
                "jd": test_case["jd"],
                "resume_text": test_case["resume"]
            },
            verify=False,
            timeout=60
        )
        
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            return {
                "id": test_id,
                "name": test_case["name"],
                "success": True,
                "status_code": 200,
                "score": data.get("match_score", data.get("score", "N/A")),
                "cost": data.get("token_usage", {}).get("cost", 0),
                "elapsed": elapsed,
                "billing": data.get("billing", {})
            }
        else:
            return {
                "id": test_id,
                "name": test_case["name"],
                "success": False,
                "status_code": response.status_code,
                "error": response.text[:200],
                "elapsed": elapsed
            }
    except Exception as e:
        return {
            "id": test_id,
            "name": test_case["name"],
            "success": False,
            "status_code": 0,
            "error": str(e),
            "elapsed": time.time() - start_time
        }


def run_batch_test(env: str, count: int, concurrent: int):
    """批量运行测试"""
    api_base = ENVS.get(env, ENVS["test"])
    
    print(f"\n{'='*60}")
    print(f"TalentAI 批量测试")
    print(f"{'='*60}")
    print(f"目标环境: {env} ({api_base})")
    print(f"测试次数: {count}")
    print(f"并发数: {concurrent}")
    print(f"{'='*60}\n")
    
    # 准备测试任务
    tasks = []
    for i in range(count):
        test_case = TEST_CASES[i % len(TEST_CASES)]
        tasks.append((api_base, test_case, i + 1))
    
    results = []
    success_count = 0
    total_cost = 0
    total_time = 0
    
    start_all = time.time()
    
    with ThreadPoolExecutor(max_workers=concurrent) as executor:
        futures = {executor.submit(run_single_test, t[0], t[1], t[2]): t for t in tasks}
        
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            
            # 实时输出
            if result["success"]:
                success_count += 1
                score = result.get("score", "N/A")
                cost = result.get("cost", 0)
                total_cost += cost
                print(f"✅ [{result['id']:3d}] {result['name'][:30]:30s} | 分数: {score:>5} | 耗时: {result['elapsed']:.2f}s | 费用: ¥{cost:.4f}")
            else:
                print(f"❌ [{result['id']:3d}] {result['name'][:30]:30s} | 错误: {result.get('error', '')[:40]}")
            
            total_time += result["elapsed"]
    
    elapsed_all = time.time() - start_all
    
    # 汇总统计
    print(f"\n{'='*60}")
    print("测试完成 - 统计汇总")
    print(f"{'='*60}")
    print(f"总测试数: {count}")
    print(f"成功: {success_count} ({success_count/count*100:.1f}%)")
    print(f"失败: {count - success_count}")
    print(f"总耗时: {elapsed_all:.2f}s")
    print(f"平均耗时: {total_time/count:.2f}s")
    print(f"总费用: ¥{total_cost:.4f}")
    print(f"QPS: {count/elapsed_all:.2f}")
    print(f"{'='*60}\n")
    
    return results


def main():
    parser = argparse.ArgumentParser(description="TalentAI 批量测试脚本")
    parser.add_argument("--env", choices=["test", "prod", "local"], default="test",
                       help="测试环境: test/prod/local (默认: test)")
    parser.add_argument("--count", type=int, default=10,
                       help="测试次数 (默认: 10)")
    parser.add_argument("--concurrent", type=int, default=3,
                       help="并发数 (默认: 3)")
    
    args = parser.parse_args()
    
    run_batch_test(args.env, args.count, args.concurrent)


if __name__ == "__main__":
    main()
