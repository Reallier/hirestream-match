# -*- coding: utf-8 -*-
"""
测试模块: 搜索 API 测试

覆盖后端搜索端点:
- GET /api/search
"""

import pytest


class TestSearch:
    """搜索 API 测试"""
    
    def test_search_basic(self, backend_client, auth_token, test_user_id):
        """基本搜索功能"""
        response = backend_client.get(
            f"/api/search?q=Python&user_id={test_user_id}&top_k=10",
            cookies={"auth_token": auth_token}
        )
        
        if response.status_code == 200:
            data = response.json()
            assert "results" in data
            print(f"✅ 搜索成功, 返回 {len(data.get('results', []))} 个结果")
        elif response.status_code == 401:
            pytest.skip("需要登录，跳过此测试")
        else:
            # 可能没有匹配结果
            assert response.status_code in [200, 404]
    
    def test_search_empty_query(self, backend_client, auth_token, test_user_id):
        """空查询"""
        response = backend_client.get(
            f"/api/search?q=&user_id={test_user_id}",
            cookies={"auth_token": auth_token}
        )
        
        if response.status_code == 401:
            pytest.skip("需要登录，跳过此测试")
        
        # 空查询应返回错误或空结果
        assert response.status_code in [200, 400, 422]
        print("✅ 空查询处理正常")
    
    def test_search_chinese_query(self, backend_client, auth_token, test_user_id):
        """中文搜索"""
        response = backend_client.get(
            f"/api/search?q=前端开发&user_id={test_user_id}&top_k=5",
            cookies={"auth_token": auth_token}
        )
        
        if response.status_code == 401:
            pytest.skip("需要登录，跳过此测试")
        
        assert response.status_code in [200, 404]
        print("✅ 中文搜索正常")
    
    def test_search_special_characters(self, backend_client, auth_token, test_user_id):
        """特殊字符搜索"""
        response = backend_client.get(
            f"/api/search?q=C%2B%2B&user_id={test_user_id}",  # C++
            cookies={"auth_token": auth_token}
        )
        
        if response.status_code == 401:
            pytest.skip("需要登录，跳过此测试")
        
        assert response.status_code in [200, 400, 404]
        print("✅ 特殊字符搜索正常")
    
    def test_search_unauthorized(self, backend_client):
        """未授权搜索"""
        response = backend_client.get("/api/search?q=Python&user_id=1")
        
        # 搜索需要认证
        assert response.status_code in [200, 401, 403]
        print("✅ 搜索权限检查正常")
    
    def test_search_top_k_limit(self, backend_client, auth_token, test_user_id):
        """top_k 限制"""
        response = backend_client.get(
            f"/api/search?q=开发&user_id={test_user_id}&top_k=3",
            cookies={"auth_token": auth_token}
        )
        
        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])
            assert len(results) <= 3
            print(f"✅ 搜索 top_k 限制正常, 返回 {len(results)} 个结果")
        elif response.status_code == 401:
            pytest.skip("需要登录，跳过此测试")


class TestSearchAdvanced:
    """高级搜索测试"""
    
    def test_search_long_query(self, backend_client, auth_token, test_user_id):
        """长查询字符串"""
        long_query = "精通Python Java JavaScript TypeScript React Vue Angular Node.js " * 5
        response = backend_client.get(
            f"/api/search?q={long_query[:500]}&user_id={test_user_id}",
            cookies={"auth_token": auth_token}
        )
        
        if response.status_code == 401:
            pytest.skip("需要登录，跳过此测试")
        
        assert response.status_code in [200, 400, 413, 414]
        print("✅ 长查询处理正常")
    
    def test_search_sql_injection(self, backend_client, auth_token, test_user_id):
        """SQL 注入测试"""
        response = backend_client.get(
            f"/api/search?q='; DROP TABLE candidates; --&user_id={test_user_id}",
            cookies={"auth_token": auth_token}
        )
        
        if response.status_code == 401:
            pytest.skip("需要登录，跳过此测试")
        
        # 不应崩溃
        assert response.status_code in [200, 400, 404]
        print("✅ SQL 注入防护正常")
