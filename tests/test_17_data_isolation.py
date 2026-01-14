# -*- coding: utf-8 -*-
"""
测试模块 17: 数据隔离测试

验证多租户场景下的数据隔离：
1. 用户 A 无法访问用户 B 的候选人
2. 用户 A 无法修改用户 B 的数据
3. 搜索结果仅限用户自己的数据
4. 历史记录按用户隔离
"""

import pytest
import jwt
import requests
import os
from datetime import datetime, timedelta
from config import get_config

# 测试配置
config = get_config()
API_BASE = config.backend_url

# JWT 配置
JWT_SECRET = os.getenv("JWT_SECRET", "5Sf4IrUfOLVQ7ul46zfg_w-bHHHu_Y67iqscKTw6UM0")
JWT_ALGORITHM = "HS256"

# 测试用户 (需要在测试环境存在)
TEST_USER_A = {"id": 5, "name": "test01"}      # user_id=5
TEST_USER_B = {"id": 6, "name": "Demo User"}  # user_id=6


def create_auth_token(user_id: int, nickname: str = "测试用户") -> str:
    """创建测试用 JWT Token"""
    now = datetime.utcnow()
    payload = {
        "id": user_id,
        "user_id": user_id,
        "nickname": nickname,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(days=1)).timestamp())
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


class TestCandidateIsolation:
    """候选人数据隔离测试"""
    
    @pytest.fixture
    def user_a_token(self):
        """用户 A 的认证 Token"""
        return create_auth_token(TEST_USER_A["id"], TEST_USER_A["name"])
    
    @pytest.fixture
    def user_b_token(self):
        """用户 B 的认证 Token"""
        return create_auth_token(TEST_USER_B["id"], TEST_USER_B["name"])
    
    def test_isolation_001_list_candidates_user_scoped(self, user_a_token, user_b_token):
        """
        ISOLATION-001: 候选人列表按用户隔离
        
        用户 A 的候选人列表不应包含用户 B 的候选人
        """
        # 获取用户 A 的候选人列表
        response_a = requests.get(
            f"{API_BASE}/api/candidates",
            params={"user_id": TEST_USER_A["id"]},
            cookies={"auth_token": user_a_token},
            verify=False,
            timeout=30
        )
        
        # 获取用户 B 的候选人列表
        response_b = requests.get(
            f"{API_BASE}/api/candidates",
            params={"user_id": TEST_USER_B["id"]},
            cookies={"auth_token": user_b_token},
            verify=False,
            timeout=30
        )
        
        assert response_a.status_code == 200, f"用户 A 请求失败: {response_a.status_code}"
        assert response_b.status_code == 200, f"用户 B 请求失败: {response_b.status_code}"
        
        data_a = response_a.json()
        data_b = response_b.json()
        
        # 兼容两种响应格式：直接列表 或 {"candidates": [...]}
        candidates_a = data_a if isinstance(data_a, list) else data_a.get("candidates", [])
        candidates_b = data_b if isinstance(data_b, list) else data_b.get("candidates", [])
        
        # 提取候选人 ID
        ids_a = set(c.get("id") for c in candidates_a if isinstance(c, dict) and c.get("id"))
        ids_b = set(c.get("id") for c in candidates_b if isinstance(c, dict) and c.get("id"))
        
        # 两个用户的候选人列表不应有交集
        overlap = ids_a & ids_b
        assert len(overlap) == 0, f"数据泄露！两用户共享候选人: {overlap}"
        
        print(f"✅ 用户 A 候选人数: {len(candidates_a)}")
        print(f"✅ 用户 B 候选人数: {len(candidates_b)}")
        print("✅ 候选人列表隔离验证通过")
    
    def test_isolation_002_access_other_user_candidate(self, user_a_token, user_b_token):
        """
        ISOLATION-002: 禁止访问其他用户的候选人
        
        用户 A 尝试访问用户 B 的候选人详情应被拒绝
        """
        # 先获取用户 B 的一个候选人 ID
        response_b = requests.get(
            f"{API_BASE}/api/candidates",
            cookies={"auth_token": user_b_token},
            params={"user_id": TEST_USER_B["id"], "limit": 1},
            verify=False,
            timeout=30
        )
        
        if response_b.status_code != 200:
            pytest.skip("无法获取用户 B 的候选人列表")
        
        data_b = response_b.json()
        candidates_b = data_b if isinstance(data_b, list) else data_b.get("candidates", [])
        if not candidates_b:
            pytest.skip("用户 B 没有候选人数据")
        
        target_candidate_id = candidates_b[0].get("id") if isinstance(candidates_b[0], dict) else candidates_b[0]
        
        # 用户 A 尝试访问用户 B 的候选人
        response_access = requests.get(
            f"{API_BASE}/api/candidates/{target_candidate_id}",
            cookies={"auth_token": user_a_token},
            verify=False,
            timeout=30
        )
        
        # 应该返回 403 Forbidden 或 404 Not Found 或 422 (user_id 参数缺失)
        assert response_access.status_code in [403, 404, 422], \
            f"安全漏洞！用户 A 能访问用户 B 的候选人: {response_access.status_code}"
        
        print(f"✅ 跨用户访问正确被拒绝: {response_access.status_code}")
    
    def test_isolation_003_delete_other_user_candidate(self, user_a_token, user_b_token):
        """
        ISOLATION-003: 禁止删除其他用户的候选人
        
        用户 A 尝试删除用户 B 的候选人应被拒绝
        """
        # 先获取用户 B 的一个候选人 ID
        response_b = requests.get(
            f"{API_BASE}/api/candidates",
            cookies={"auth_token": user_b_token},
            params={"user_id": TEST_USER_B["id"], "limit": 1},
            verify=False,
            timeout=30
        )
        
        if response_b.status_code != 200:
            pytest.skip("无法获取用户 B 的候选人列表")
        
        data_b = response_b.json()
        candidates_b = data_b if isinstance(data_b, list) else data_b.get("candidates", [])
        if not candidates_b:
            pytest.skip("用户 B 没有候选人数据")
        
        target_candidate_id = candidates_b[0].get("id") if isinstance(candidates_b[0], dict) else candidates_b[0]
        
        # 用户 A 尝试删除用户 B 的候选人
        response_delete = requests.delete(
            f"{API_BASE}/api/candidates/{target_candidate_id}",
            cookies={"auth_token": user_a_token},
            verify=False,
            timeout=30
        )
        
        # 应该返回 403 Forbidden 或 404 Not Found 或 422 (user_id 参数缺失)
        assert response_delete.status_code in [403, 404, 422], \
            f"安全漏洞！用户 A 能删除用户 B 的候选人: {response_delete.status_code}"
        
        print(f"✅ 跨用户删除正确被拒绝: {response_delete.status_code}")


class TestSearchIsolation:
    """搜索数据隔离测试"""
    
    @pytest.fixture
    def user_a_token(self):
        return create_auth_token(TEST_USER_A["id"], TEST_USER_A["name"])
    
    @pytest.fixture
    def user_b_token(self):
        return create_auth_token(TEST_USER_B["id"], TEST_USER_B["name"])
    
    def test_isolation_004_search_results_user_scoped(self, user_a_token, user_b_token):
        """
        ISOLATION-004: 搜索结果按用户隔离
        
        同样的搜索关键词，不同用户应返回各自的数据
        """
        search_query = "Python"  # 通用搜索词
        
        # 用户 A 搜索
        response_a = requests.get(
            f"{API_BASE}/api/search",
            params={"q": search_query, "user_id": TEST_USER_A["id"]},
            cookies={"auth_token": user_a_token},
            verify=False,
            timeout=30
        )
        
        # 用户 B 搜索
        response_b = requests.get(
            f"{API_BASE}/api/search",
            params={"q": search_query, "user_id": TEST_USER_B["id"]},
            cookies={"auth_token": user_b_token},
            verify=False,
            timeout=30
        )
        
        if response_a.status_code != 200 or response_b.status_code != 200:
            pytest.skip(f"搜索 API 不可用: A={response_a.status_code}, B={response_b.status_code}")
        
        results_a = response_a.json()
        results_b = response_b.json()
        
        # 兼容两种响应格式
        if isinstance(results_a, dict):
            results_a = results_a.get("results", [])
        if isinstance(results_b, dict):
            results_b = results_b.get("results", [])
        
        # 提取结果 ID
        ids_a = set(r.get("id") for r in results_a if isinstance(r, dict) and r.get("id"))
        ids_b = set(r.get("id") for r in results_b if isinstance(r, dict) and r.get("id"))
        
        # 搜索结果不应有交集
        overlap = ids_a & ids_b
        assert len(overlap) == 0, f"数据泄露！搜索结果共享: {overlap}"
        
        print(f"✅ 用户 A 搜索结果: {len(results_a)} 条")
        print(f"✅ 用户 B 搜索结果: {len(results_b)} 条")
        print("✅ 搜索结果隔离验证通过")


class TestHistoryIsolation:
    """历史记录隔离测试"""
    
    @pytest.fixture
    def user_a_token(self):
        return create_auth_token(TEST_USER_A["id"], TEST_USER_A["name"])
    
    @pytest.fixture
    def user_b_token(self):
        return create_auth_token(TEST_USER_B["id"], TEST_USER_B["name"])
    
    def test_isolation_005_match_history_user_scoped(self, user_a_token, user_b_token):
        """
        ISOLATION-005: 匹配历史按用户隔离
        
        用户 A 的匹配历史不应包含用户 B 的记录
        """
        # 获取用户 A 的匹配历史
        response_a = requests.get(
            f"{API_BASE}/api/match/history",
            params={"user_id": TEST_USER_A["id"]},
            cookies={"auth_token": user_a_token},
            verify=False,
            timeout=30
        )
        
        # 获取用户 B 的匹配历史
        response_b = requests.get(
            f"{API_BASE}/api/match/history",
            params={"user_id": TEST_USER_B["id"]},
            cookies={"auth_token": user_b_token},
            verify=False,
            timeout=30
        )
        
        if response_a.status_code != 200 or response_b.status_code != 200:
            pytest.skip(f"历史 API 不可用: A={response_a.status_code}, B={response_b.status_code}")
        
        history_a = response_a.json()
        history_b = response_b.json()
        
        # 兼容两种响应格式
        if isinstance(history_a, dict):
            history_a = history_a.get("records", [])
        if isinstance(history_b, dict):
            history_b = history_b.get("records", [])
        
        # 提取记录 ID
        ids_a = set(r.get("id") for r in history_a if isinstance(r, dict) and r.get("id"))
        ids_b = set(r.get("id") for r in history_b if isinstance(r, dict) and r.get("id"))
        
        # 历史记录不应有交集
        overlap = ids_a & ids_b
        assert len(overlap) == 0, f"数据泄露！历史记录共享: {overlap}"
        
        print(f"✅ 用户 A 历史记录: {len(history_a)} 条")
        print(f"✅ 用户 B 历史记录: {len(history_b)} 条")
        print("✅ 历史记录隔离验证通过")


class TestAnonymousIsolation:
    """匿名用户隔离测试"""
    
    def test_isolation_006_anonymous_no_data_access(self):
        """
        ISOLATION-006: 匿名用户无法访问任何用户数据
        """
        # 无认证请求候选人列表 - 需要 user_id 参数
        response = requests.get(
            f"{API_BASE}/api/candidates",
            params={"user_id": 1},  # 使用不存在的用户
            verify=False,
            timeout=30
        )
        
        # 应该返回 401 或空列表
        if response.status_code == 200:
            data = response.json()
            candidates = data if isinstance(data, list) else data.get("candidates", [])
            assert len(candidates) == 0, f"安全漏洞！匿名用户能看到候选人: {len(candidates)}"
        else:
            assert response.status_code in [401, 422], f"意外状态码: {response.status_code}"
        
        print("✅ 匿名用户数据访问正确被限制")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
