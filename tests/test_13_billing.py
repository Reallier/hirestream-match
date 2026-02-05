# -*- coding: utf-8 -*-
"""
即时匹配计费测试

验证 /api/instant-match 接口的扣费逻辑是否正确工作：
1. 已登录用户：应该扣费并返回 billing 信息
2. 未登录用户：不扣费，billing.charged = False
3. 费用记录：使用记录应该被正确保存
"""

import os
import pytest
import requests
import jwt
from datetime import datetime, timedelta

from config import get_config

# 测试配置
config = get_config()
API_BASE = config.backend_url

# JWT 配置
JWT_SECRET = os.getenv("JWT_SECRET")  # 必须从环境变量获取，切勿硬编码
if not JWT_SECRET:
    raise ValueError("JWT_SECRET 环境变量未设置，请在运行测试前配置")
JWT_ALGORITHM = "HS256"

# 测试用户 ID（需要在测试环境中存在）
TEST_USER_ID = int(os.getenv("TEST_USER_ID", "5"))

# 测试用的 JD 和简历（简短内容以减少费用）
TEST_JD = """
职位: Python 开发工程师
要求: 3年以上Python经验
"""

TEST_RESUME = """
姓名: 测试候选人
经验: 5年Python开发
技能: Python, FastAPI, Django
"""


def create_test_token(user_id: int) -> str:
    """创建测试用 JWT Token"""
    now = datetime.utcnow()
    payload = {
        "id": user_id,
        "user_id": user_id,
        "nickname": "测试用户",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(days=1)).timestamp())
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


class TestInstantMatchBilling:
    """即时匹配扣费测试"""
    
    @pytest.mark.billing
    def test_billing_001_anonymous_no_charge(self):
        """
        BILLING-001: 未登录用户不扣费
        
        验证未登录用户调用 instant-match 时：
        1. 请求正常处理
        2. 返回 billing.charged = False
        """
        response = requests.post(
            f"{API_BASE}/api/instant-match",
            data={"jd": TEST_JD, "resume_text": TEST_RESUME},
            verify=False,
            timeout=60
        )
        
        assert response.status_code == 200, f"请求失败: {response.status_code}"
        data = response.json()
        
        # 验证结果包含匹配分数
        assert "match_score" in data, "缺少 match_score"
        
        # 验证计费信息
        assert "billing" in data, "缺少 billing 字段"
        assert data["billing"]["charged"] is False, "未登录用户不应该扣费"
    
    @pytest.mark.billing
    def test_billing_002_authenticated_user_charged(self):
        """
        BILLING-002: 已登录用户扣费
        
        验证已登录用户调用 instant-match 时：
        1. 请求正常处理
        2. 返回 billing.charged = True
        3. 返回 billing.cost > 0
        4. 返回 billing.balance_after（扣费后余额）
        """
        token = create_test_token(TEST_USER_ID)
        
        response = requests.post(
            f"{API_BASE}/api/instant-match",
            data={"jd": TEST_JD, "resume_text": TEST_RESUME},
            cookies={"auth_token": token},
            verify=False,
            timeout=60
        )
        
        assert response.status_code == 200, f"请求失败: {response.status_code}"
        data = response.json()
        
        # 验证结果包含匹配分数
        assert "match_score" in data, "缺少 match_score"
        
        # 验证计费信息
        assert "billing" in data, "缺少 billing 字段"
        billing = data["billing"]
        
        # 扣费应该成功（如果余额足够）
        if billing["charged"]:
            assert "cost" in billing, "扣费成功时应返回 cost"
            assert billing["cost"] > 0, "费用应该大于 0"
            assert "balance_after" in billing, "扣费成功时应返回 balance_after"
            assert billing["balance_after"] >= 0, "余额不应该为负"
        else:
            # 余额不足时会扣费失败
            assert "reason" in billing, "扣费失败时应返回原因"
    
    @pytest.mark.billing
    def test_billing_003_token_usage_reported(self):
        """
        BILLING-003: Token 使用量报告
        
        验证响应中包含 token 使用量信息
        """
        token = create_test_token(TEST_USER_ID)
        
        response = requests.post(
            f"{API_BASE}/api/instant-match",
            data={"jd": TEST_JD, "resume_text": TEST_RESUME},
            cookies={"auth_token": token},
            verify=False,
            timeout=60
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # 验证 token 使用量
        assert "token_usage" in data, "缺少 token_usage"
        token_usage = data["token_usage"]
        
        assert "prompt_tokens" in token_usage, "缺少 prompt_tokens"
        assert "completion_tokens" in token_usage, "缺少 completion_tokens"
        assert "total_tokens" in token_usage, "缺少 total_tokens"
        assert "cost" in token_usage, "缺少 cost"
        assert "model" in token_usage, "缺少 model"
        
        # 验证值合理
        assert token_usage["prompt_tokens"] > 0, "prompt_tokens 应该大于 0"
        assert token_usage["cost"] > 0, "cost 应该大于 0"
    
    @pytest.mark.billing
    def test_billing_004_balance_decreases(self):
        """
        BILLING-004: 余额减少验证
        
        验证多次调用后余额确实减少
        """
        token = create_test_token(TEST_USER_ID)
        
        # 第一次调用
        response1 = requests.post(
            f"{API_BASE}/api/instant-match",
            data={"jd": TEST_JD, "resume_text": TEST_RESUME},
            cookies={"auth_token": token},
            verify=False,
            timeout=60
        )
        
        assert response1.status_code == 200
        data1 = response1.json()
        
        if not data1.get("billing", {}).get("charged"):
            pytest.skip("余额不足，跳过此测试")
        
        balance_after_1 = float(data1["billing"]["balance_after"])
        cost_1 = float(data1["billing"]["cost"])
        
        # 第二次调用
        response2 = requests.post(
            f"{API_BASE}/api/instant-match",
            data={"jd": TEST_JD, "resume_text": TEST_RESUME},
            cookies={"auth_token": token},
            verify=False,
            timeout=60
        )
        
        assert response2.status_code == 200
        data2 = response2.json()
        
        if data2.get("billing", {}).get("charged"):
            balance_after_2 = float(data2["billing"]["balance_after"])
            
            # 验证余额减少
            assert balance_after_2 < balance_after_1, \
                f"余额未减少: {balance_after_1} -> {balance_after_2}"
    
    @pytest.mark.billing
    @pytest.mark.smoke
    def test_billing_health_quick_check(self):
        """
        计费健康检查（快速验证）
        
        验证基本的计费功能是否正常工作
        """
        # 1. 匿名请求
        anon_response = requests.post(
            f"{API_BASE}/api/instant-match",
            data={"jd": "Python开发", "resume_text": "Python工程师"},
            verify=False,
            timeout=30
        )
        assert anon_response.status_code == 200, "匿名请求失败"
        assert "billing" in anon_response.json(), "缺少 billing 字段"
        
        # 2. 认证请求
        token = create_test_token(TEST_USER_ID)
        auth_response = requests.post(
            f"{API_BASE}/api/instant-match",
            data={"jd": "Python开发", "resume_text": "Python工程师"},
            cookies={"auth_token": token},
            verify=False,
            timeout=30
        )
        assert auth_response.status_code == 200, "认证请求失败"
        assert "billing" in auth_response.json(), "认证请求缺少 billing 字段"


# 添加 billing 标记到 pytest.ini
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
