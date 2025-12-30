"""
DashScope 单 Key 并发能力测试
验证注释中 "单 Key 同时只能处理 1 个请求" 是否正确
"""
import asyncio
import httpx
import time
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('DASHSCOPE_API_KEY', '')
API_URL = 'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions'

print(f"API Key 长度: {len(API_KEY)}")
print(f"API URL: {API_URL}")

async def send_request(session, request_id):
    """发送单个请求并返回耗时"""
    start = time.time()
    try:
        response = await session.post(
            API_URL,
            headers={
                'Authorization': f'Bearer {API_KEY}',
                'Content-Type': 'application/json'
            },
            json={
                'model': 'qwen-turbo',
                'messages': [{'role': 'user', 'content': f'Say hello #{request_id}'}],
                'max_tokens': 10
            },
            timeout=30.0
        )
        elapsed = time.time() - start
        status = response.status_code
        return request_id, status, elapsed, None
    except Exception as e:
        elapsed = time.time() - start
        return request_id, 0, elapsed, str(e)


async def test_concurrency(n):
    """测试 N 个并发请求"""
    print(f'\n{"="*50}')
    print(f'测试 {n} 并发请求 (单 Key)')
    print(f'{"="*50}')
    
    async with httpx.AsyncClient() as client:
        start = time.time()
        tasks = [send_request(client, i) for i in range(n)]
        results = await asyncio.gather(*tasks)
        total = time.time() - start
    
    # 打印结果
    for req_id, status, elapsed, error in results:
        if error:
            print(f'  [{req_id}] ERROR: {error} ({elapsed:.2f}s)')
        else:
            print(f'  [{req_id}] HTTP {status} ({elapsed:.2f}s)')
    
    # 分析
    times = [r[2] for r in results]
    avg_time = sum(times) / len(times)
    
    print(f'\n📊 结果分析:')
    print(f'  总耗时: {total:.2f}s')
    print(f'  平均单请求: {avg_time:.2f}s')
    
    if n > 1:
        expected_serial = avg_time * n
        print(f'  如果真串行: 预期 ~{expected_serial:.1f}s')
        print(f'  实际并发比: {expected_serial / total:.1f}x')
        
        if total < expected_serial * 0.7:
            print(f'  ✅ 结论: 支持真并发!')
        else:
            print(f'  ❌ 结论: 可能是串行处理')


async def main():
    # 先测 1 个建立基线
    await test_concurrency(1)
    
    # 测试 4 并发
    await test_concurrency(4)
    
    # 测试 8 并发
    await test_concurrency(8)
    
    # 测试 12 并发
    await test_concurrency(12)


if __name__ == '__main__':
    asyncio.run(main())
