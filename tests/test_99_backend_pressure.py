"""
TalentAI 后端服务器抗压能力测试
测试 /api/instant-match 接口在不同并发级别下的表现
"""
import asyncio
import httpx
import time
import statistics
from dataclasses import dataclass
from typing import List, Tuple

# 配置
BACKEND_URL = "https://api.talentai.reallier.top:5443"
ENDPOINT = "/api/instant-match"

# 测试数据
TEST_JD = """
职位：Python 后端开发
要求：3年经验，熟悉 FastAPI
"""

TEST_RESUME = """
张三 | Python 开发 | 5年经验
技能：Python, FastAPI, PostgreSQL
"""


@dataclass
class RequestResult:
    """单次请求结果"""
    request_id: int
    status_code: int
    elapsed: float
    error: str = None


async def send_match_request(client: httpx.AsyncClient, request_id: int) -> RequestResult:
    """发送匹配请求"""
    start = time.time()
    try:
        response = await client.post(
            f"{BACKEND_URL}{ENDPOINT}",
            data={  # 使用 Form Data 而非 JSON
                "jd": TEST_JD,
                "resume_text": TEST_RESUME
            },
            timeout=60.0
        )
        elapsed = time.time() - start
        return RequestResult(request_id, response.status_code, elapsed)
    except Exception as e:
        elapsed = time.time() - start
        return RequestResult(request_id, 0, elapsed, str(e))


async def run_concurrency_test(concurrency: int, total_requests: int = None) -> List[RequestResult]:
    """
    运行并发测试
    
    Args:
        concurrency: 并发数
        total_requests: 总请求数（默认等于并发数）
    """
    if total_requests is None:
        total_requests = concurrency
    
    print(f"\n{'='*60}")
    print(f"🔥 并发测试: {concurrency} 并发 / {total_requests} 请求")
    print(f"{'='*60}")
    
    results = []
    
    async with httpx.AsyncClient(verify=False) as client:
        start_time = time.time()
        
        # 分批发送请求
        for batch_start in range(0, total_requests, concurrency):
            batch_end = min(batch_start + concurrency, total_requests)
            batch_size = batch_end - batch_start
            
            tasks = [
                send_match_request(client, i)
                for i in range(batch_start, batch_end)
            ]
            batch_results = await asyncio.gather(*tasks)
            results.extend(batch_results)
            
            # 打印进度
            success = sum(1 for r in batch_results if r.status_code == 200)
            failed = batch_size - success
            print(f"  批次 {batch_start//concurrency + 1}: {success}✅ {failed}❌")
        
        total_time = time.time() - start_time
    
    return results, total_time


def analyze_results(results: List[RequestResult], total_time: float, concurrency: int):
    """分析测试结果"""
    success_results = [r for r in results if r.status_code == 200]
    failed_results = [r for r in results if r.status_code != 200]
    
    print(f"\n📊 结果分析:")
    print(f"  总请求: {len(results)}")
    print(f"  成功: {len(success_results)} ({len(success_results)/len(results)*100:.1f}%)")
    print(f"  失败: {len(failed_results)} ({len(failed_results)/len(results)*100:.1f}%)")
    
    if failed_results:
        # 统计失败原因
        error_codes = {}
        for r in failed_results:
            key = f"HTTP {r.status_code}" if r.status_code else r.error[:30]
            error_codes[key] = error_codes.get(key, 0) + 1
        print(f"  失败详情: {error_codes}")
    
    if success_results:
        times = [r.elapsed for r in success_results]
        print(f"\n⏱️ 延迟统计 (成功请求):")
        print(f"  最小: {min(times):.2f}s")
        print(f"  最大: {max(times):.2f}s")
        print(f"  平均: {statistics.mean(times):.2f}s")
        print(f"  中位数: {statistics.median(times):.2f}s")
        if len(times) > 1:
            print(f"  标准差: {statistics.stdev(times):.2f}s")
    
    print(f"\n🚀 吞吐量:")
    print(f"  总耗时: {total_time:.2f}s")
    print(f"  RPS: {len(results)/total_time:.2f} 请求/秒")
    print(f"  成功 RPS: {len(success_results)/total_time:.2f} 请求/秒")
    
    return len(success_results), len(failed_results)


async def find_breaking_point():
    """逐步增加并发找到服务器极限"""
    print("\n" + "="*60)
    print("🎯 TalentAI 后端抗压能力测试")
    print(f"   目标: {BACKEND_URL}{ENDPOINT}")
    print("="*60)
    
    # 先做健康检查
    print("\n🏥 健康检查...")
    async with httpx.AsyncClient(verify=False) as client:
        try:
            resp = await client.get(f"{BACKEND_URL}/health", timeout=10.0)
            print(f"   /health: {resp.status_code}")
        except Exception as e:
            print(f"   ❌ 健康检查失败: {e}")
            return
    
    # 测试不同并发级别
    concurrency_levels = [1, 2, 4, 8, 12, 16, 20]
    summary = []
    
    for concurrency in concurrency_levels:
        results, total_time = await run_concurrency_test(concurrency)
        success, failed = analyze_results(results, total_time, concurrency)
        summary.append((concurrency, success, failed, total_time))
        
        # 如果失败率超过 50%，停止测试
        if failed > success:
            print(f"\n⚠️ 失败率超过 50%，停止测试")
            break
        
        # 短暂休息，让服务器恢复
        await asyncio.sleep(2)
    
    # 打印汇总
    print("\n" + "="*60)
    print("📋 抗压能力汇总")
    print("="*60)
    print(f"{'并发数':<10} {'成功':<10} {'失败':<10} {'成功率':<12} {'RPS':<10}")
    print("-"*60)
    
    max_stable_concurrency = 0
    for concurrency, success, failed, total_time in summary:
        total = success + failed
        success_rate = success / total * 100
        rps = total / total_time
        
        status = "✅" if failed == 0 else "⚠️" if success_rate >= 80 else "❌"
        print(f"{concurrency:<10} {success:<10} {failed:<10} {success_rate:<10.1f}% {rps:<10.2f} {status}")
        
        if failed == 0:
            max_stable_concurrency = concurrency
    
    print("-"*60)
    print(f"🏆 最大稳定并发: {max_stable_concurrency}")
    print(f"💡 建议 pytest-xdist worker 数: {max(1, max_stable_concurrency // 2)}")


if __name__ == "__main__":
    asyncio.run(find_breaking_point())
