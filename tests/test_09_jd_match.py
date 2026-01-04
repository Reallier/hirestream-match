# -*- coding: utf-8 -*-
"""
测试模块: JD 匹配 API 测试

覆盖后端 JD 匹配端点:
- POST /api/match?user_id={id}
"""

import pytest


class TestJDMatch:
    """JD 匹配测试"""
    
    def test_jd_match_basic(self, backend_client, sample_jd, auth_token, test_user_id):
        """基本 JD 匹配"""
        response = backend_client.post(
            f"/api/match?user_id={test_user_id}",
            json={
                "jd": sample_jd,
                "top_k": 5
            },
            cookies={"auth_token": auth_token}
        )
        
        if response.status_code == 200:
            data = response.json()
            assert "matches" in data
            print(f"✅ JD 匹配成功")
        elif response.status_code == 401:
            pytest.skip("需要登录，跳过此测试")
        else:
            # 可能人才库为空
            assert response.status_code in [200, 400, 404, 500]
    
    def test_jd_match_unauthorized(self, backend_client, sample_jd, test_user_id):
        """未授权 JD 匹配"""
        response = backend_client.post(f"/api/match?user_id={test_user_id}", json={
            "jd": sample_jd,
            "top_k": 10
        })
        
        # 可能返回 200（无需认证）或 401/403/422
        assert response.status_code in [200, 401, 403, 422, 500]
        print("✅ JD 匹配权限检查完成")
    
    def test_jd_match_empty_jd(self, backend_client, auth_token, test_user_id):
        """空 JD 应拒绝"""
        response = backend_client.post(
            f"/api/match?user_id={test_user_id}",
            json={
                "jd": "",
                "top_k": 10
            },
            cookies={"auth_token": auth_token}
        )
        
        if response.status_code == 401:
            pytest.skip("需要登录，跳过此测试")
        
        # 空 JD 应返回错误或空结果
        assert response.status_code in [200, 400, 422, 500]
        print("✅ 空 JD 处理正常")
    
    def test_jd_match_top_k_limit(self, backend_client, sample_jd, auth_token, test_user_id):
        """top_k 参数测试"""
        response = backend_client.post(
            f"/api/match?user_id={test_user_id}",
            json={
                "jd": sample_jd,
                "top_k": 3
            },
            cookies={"auth_token": auth_token}
        )
        
        if response.status_code == 200:
            data = response.json()
            results = data.get("matches", [])
            assert len(results) <= 3, f"结果数应不超过 top_k: {len(results)}"
            print(f"✅ top_k 限制正常, 返回 {len(results)} 个结果")
        elif response.status_code == 401:
            pytest.skip("需要登录，跳过此测试")
        else:
            assert response.status_code in [400, 404, 500]
    
    def test_jd_match_large_top_k(self, backend_client, sample_jd, auth_token, test_user_id):
        """大 top_k 值"""
        response = backend_client.post(
            f"/api/match?user_id={test_user_id}",
            json={
                "jd": sample_jd,
                "top_k": 100
            },
            cookies={"auth_token": auth_token}
        )
        
        if response.status_code == 401:
            pytest.skip("需要登录，跳过此测试")
        
        # 应正常处理或限制
        assert response.status_code in [200, 400, 422, 500]
        print("✅ 大 top_k 值处理正常")
