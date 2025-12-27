"""
App01 TalentAI 压力测试脚本
使用 Locust 进行并发性能测试

运行方式:
    cd app01-hirestream-match
    pip install locust
    locust -f stress_test.py --host=http://localhost:8001 --web-host=0.0.0.0 --web-port=8089

然后打开浏览器访问 http://localhost:8089 配置并发用户数和启动测试
"""

import json
import random
from locust import HttpUser, task, between, events
from locust.runners import MasterRunner

# 测试数据
SAMPLE_JDS = [
    """
    职位：Python 后端开发工程师
    要求：
    - 3年以上 Python 开发经验
    - 熟悉 FastAPI/Django/Flask 框架
    - 熟悉 MySQL/PostgreSQL 数据库
    - 了解 Docker/Kubernetes
    - 良好的沟通能力
    """,
    """
    职位：前端开发工程师
    要求：
    - 3年以上前端开发经验
    - 精通 Vue.js 或 React
    - 熟悉 TypeScript
    - 了解 Node.js
    - 有移动端开发经验优先
    """,
    """
    职位：AI 算法工程师
    要求：
    - 硕士及以上学历，计算机/数学相关专业
    - 熟悉深度学习框架 PyTorch/TensorFlow
    - 有 NLP/CV 项目经验
    - 发表过顶会论文优先
    """,
]

SAMPLE_RESUMES = [
    """
    张三
    Python 开发工程师 | 5年经验
    
    技能：Python, FastAPI, Django, MySQL, Redis, Docker
    
    工作经历：
    2020-至今 某科技公司 高级后端开发
    - 负责核心业务系统开发
    - 优化系统性能，QPS 提升 300%
    
    教育背景：
    2016-2020 北京大学 计算机科学 本科
    """,
    """
    李四
    前端开发工程师 | 4年经验
    
    技能：Vue.js, React, TypeScript, Node.js, Webpack
    
    工作经历：
    2021-至今 某互联网公司 前端开发
    - 负责公司官网和管理后台开发
    - 优化首屏加载时间，提升 50%
    
    教育背景：
    2017-2021 清华大学 软件工程 本科
    """,
    """
    王五
    AI 算法工程师 | 3年经验
    
    技能：PyTorch, TensorFlow, NLP, CV, Transformers
    
    工作经历：
    2022-至今 某AI公司 算法工程师
    - 负责大语言模型微调
    - 发表 ACL 2023 论文一篇
    
    教育背景：
    2019-2022 北京大学 人工智能 硕士
    """,
]


class TalentAIUser(HttpUser):
    """模拟 TalentAI 用户行为"""
    
    # 用户请求间隔：1-3秒
    wait_time = between(1, 3)
    
    def on_start(self):
        """用户启动时的初始化"""
        self.session_id = f"stress_test_{random.randint(1000, 9999)}"
    
    @task(10)
    def health_check(self):
        """健康检查 - 高频率"""
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")
    
    @task(5)
    def api_match(self):
        """调用匹配 API - 核心业务"""
        jd = random.choice(SAMPLE_JDS)
        resume = random.choice(SAMPLE_RESUMES)
        
        payload = {
            "jd": jd,
            "resume": resume,
            "session_id": self.session_id,
        }
        
        with self.client.post(
            "/api/match",
            json=payload,
            catch_response=True,
            timeout=60,  # LLM 调用可能较慢
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "match_score" in data or "score" in data:
                        response.success()
                    else:
                        response.failure("Invalid response format")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            elif response.status_code == 429:
                response.failure("Rate limited")
            else:
                response.failure(f"Match failed: {response.status_code}")
    
    @task(3)
    def get_usage_stats(self):
        """获取用量统计"""
        with self.client.get("/api/usage/stats", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Usage stats failed: {response.status_code}")
    
    @task(2)
    def get_history(self):
        """获取历史记录"""
        with self.client.get(
            f"/api/history?session_id={self.session_id}",
            catch_response=True
        ) as response:
            if response.status_code in [200, 404]:  # 404 表示无历史记录也是正常
                response.success()
            else:
                response.failure(f"History failed: {response.status_code}")


class StressTestUser(HttpUser):
    """高压力测试用户 - 模拟攻击场景"""
    
    wait_time = between(0.1, 0.5)  # 更快的请求频率
    weight = 1  # 权重较低，只占少量用户
    
    @task
    def rapid_health_check(self):
        """快速健康检查"""
        self.client.get("/health")
    
    @task
    def rapid_match(self):
        """快速匹配请求 - 测试限流"""
        payload = {
            "jd": "测试职位",
            "resume": "测试简历",
        }
        self.client.post("/api/match", json=payload, timeout=30)


# 测试统计收集
@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """记录请求统计"""
    if exception:
        print(f"[ERROR] {request_type} {name}: {exception}")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """测试开始时的回调"""
    print("=" * 50)
    print("App01 TalentAI 压力测试开始")
    print("=" * 50)
    if isinstance(environment.runner, MasterRunner):
        print(f"Running in distributed mode with {environment.runner.worker_count} workers")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """测试结束时的回调"""
    print("=" * 50)
    print("压力测试结束")
    print("=" * 50)


if __name__ == "__main__":
    import os
    os.system("locust -f stress_test.py --host=http://localhost:8001 --web-host=0.0.0.0 --web-port=8089")
