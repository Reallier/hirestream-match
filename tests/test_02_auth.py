"""
测试模块 2: 认证流程
验证用户认证相关功能
"""
import pytest

class TestAuth:
    """认证流程测试"""
    
    def test_auth_me_unauthorized(self, frontend_client):
        """未授权访问 /api/auth/me"""
        response = frontend_client.get("/api/auth/me")
        
        # 未登录时应返回错误或空用户
        if response.status_code == 200:
            data = response.json()
            # 可能返回 success: false 或 user: null
            assert not data.get("success") or data.get("user") is None, \
                "未授权请求不应返回有效用户"
        else:
            # 401/403 都是合理的
            assert response.status_code in [401, 403, 500], \
                f"意外的状态码: {response.status_code}"
        
        print(f"✅ 未授权访问测试通过")
    
    def test_auth_callback_missing_token(self, frontend_client):
        """回调缺少 token"""
        response = frontend_client.post(
            "/api/auth/callback",
            json={}
        )
        
        # 应该返回 400 或相关错误
        assert response.status_code in [400, 401, 422], \
            f"缺少 token 应返回错误: {response.status_code}"
        
        print(f"✅ 缺少 token 测试通过")
    
    def test_auth_callback_invalid_token(self, frontend_client):
        """无效 token 回调"""
        response = frontend_client.post(
            "/api/auth/callback",
            json={"token": "invalid_token_12345"}
        )
        
        # 应该返回 401
        assert response.status_code == 401, \
            f"无效 token 应返回 401: {response.status_code}"
        
        print(f"✅ 无效 token 测试通过")
    
    def test_auth_logout(self, frontend_client):
        """登出接口可访问"""
        response = frontend_client.post("/api/auth/logout")
        
        # 登出应该总是成功（即使没登录）
        assert response.status_code in [200, 204], \
            f"登出应返回成功: {response.status_code}"
        
        print(f"✅ 登出测试通过")
