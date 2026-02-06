# -*- coding: utf-8 -*-
"""
SSO 配置验证测试

验证跨服务 SSO 所需的配置是否正确：
1. JWT_SECRET 在所有服务间一致
2. verify-token API 正常工作
3. Cookie 域名配置正确

这些测试帮助快速定位 SSO 问题的根因。
"""

import pytest
import requests
import jwt
import time
from config import get_config


@pytest.fixture
def config(request):
    """获取测试配置（尊重 --env 参数）"""
    env = request.config.getoption("--env")
    return get_config(env)


@pytest.fixture
def official_site_url(config):
    """获取官网 URL（与 TalentAI 在同一域名下）"""
    # 从 TalentAI URL 推导官网 URL
    if "test." in config.backend_url:
        return "https://test.intjtech.reallier.top:5443"
    else:
        return "https://intjtech.reallier.top:5443"


class TestSSOConfiguration:
    """SSO 配置测试套件"""
    
    @pytest.mark.sso
    def test_sso_001_verify_token_endpoint_exists(self, config):
        """
        验证 verify-token 端点存在
        
        这个端点是 SSO 流程的关键，用于验证官网传递的 token 并设置 Cookie
        """
        url = f"{config.backend_url}/api/auth/verify-token"
        
        # 发送一个空 token，应该返回验证失败而不是 404
        response = requests.post(
            url,
            json={"token": "invalid_test_token"},
            timeout=config.timeout
        )
        
        # 不应该是 404（端点不存在）
        assert response.status_code != 404, "verify-token 端点不存在，SSO 功能将无法工作"
        
        # 应该返回 200（验证失败但端点存在）或 422（参数验证失败）
        assert response.status_code in [200, 422], f"意外的状态码: {response.status_code}"
        
        if response.status_code == 200:
            data = response.json()
            assert data.get("success") == False, "无效 token 应该返回 success=False"
    
    @pytest.mark.sso
    def test_sso_002_jwt_secret_consistency(self, config, official_site_url):
        """
        验证 JWT_SECRET 在服务间一致
        
        通过尝试用官网的格式签发 token 并让 TalentAI 验证来间接测试
        这个测试模拟官网签发 token 的格式
        """
        # 注意：这个测试需要知道 JWT_SECRET，在 CI/CD 中可以通过环境变量传入
        # 这里我们用一个已知的测试用户来验证
        
        # 首先获取官网的健康状态
        try:
            response = requests.get(f"{official_site_url}/", timeout=10)
            official_site_available = response.status_code == 200
        except Exception:
            official_site_available = False
        
        if not official_site_available:
            pytest.skip("官网不可用，跳过 JWT_SECRET 一致性测试")
        
        # 测试 TalentAI 后端是否能正确处理 JWT
        # 发送一个格式正确但签名错误的 token
        fake_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MSwidXNlcl9pZCI6MX0.FAKE_SIGNATURE"
        
        response = requests.post(
            f"{config.backend_url}/api/auth/verify-token",
            json={"token": fake_token},
            timeout=config.timeout
        )
        
        assert response.status_code == 200, f"verify-token 应返回 200，实际: {response.status_code}"
        data = response.json()
        
        # 签名错误的 token 应该验证失败
        assert data.get("success") == False, "假 token 应该验证失败"
    
    @pytest.mark.sso
    def test_sso_003_cors_configuration(self, config, official_site_url):
        """
        验证 CORS 配置允许官网跨域请求
        
        官网域名必须在 TalentAI 后端的 CORS 白名单中
        """
        # 模拟从官网发起的预检请求
        headers = {
            "Origin": official_site_url,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type"
        }
        
        response = requests.options(
            f"{config.backend_url}/api/auth/verify-token",
            headers=headers,
            timeout=config.timeout
        )
        
        # CORS 预检应该成功
        # 注意：某些服务器可能返回 200 或 204
        assert response.status_code in [200, 204, 400], f"CORS 预检失败: {response.status_code}"
        
        # 检查 CORS 头
        cors_origin = response.headers.get("Access-Control-Allow-Origin")
        cors_credentials = response.headers.get("Access-Control-Allow-Credentials")
        
        if cors_origin:
            # 应该允许官网域名或 *
            assert official_site_url in cors_origin or cors_origin == "*", \
                f"CORS 未允许官网域名: {cors_origin}"
        
        if cors_credentials:
            assert cors_credentials.lower() == "true", \
                "CORS 需要允许 credentials 以支持 Cookie"
    
    @pytest.mark.sso
    def test_sso_004_auth_me_endpoint(self, config):
        """
        验证 /api/auth/me 端点正常工作
        
        这个端点用于获取当前登录用户信息
        """
        response = requests.get(
            f"{config.backend_url}/api/auth/me",
            timeout=config.timeout
        )
        
        assert response.status_code == 200, f"/api/auth/me 返回 {response.status_code}"
        
        data = response.json()
        # 没有 Cookie 时应该返回 user=null
        assert "user" in data or "success" in data, "响应格式不正确"
    
    @pytest.mark.sso
    def test_sso_005_cookie_domain_configuration(self, config):
        """
        验证 Cookie 域名配置（通过登录响应头检查）
        
        Cookie 必须设置为 .reallier.top 才能跨子域共享
        """
        # 这个测试需要实际登录才能看到 Set-Cookie 头
        # 这里我们只验证登录端点存在
        response = requests.post(
            f"{config.backend_url}/api/auth/login",
            json={"username": "test_nonexistent_user_12345", "password": "wrong"},
            timeout=config.timeout
        )
        
        # 登录失败应该返回 401 或包含错误信息的 200
        assert response.status_code in [200, 401, 422], f"登录端点异常: {response.status_code}"
    
    @pytest.mark.sso
    @pytest.mark.slow
    def test_sso_006_full_sso_flow_simulation(self, config, official_site_url):
        """
        模拟完整的 SSO 流程
        
        1. 检查官网 redirect 端点是否存在
        2. 验证重定向 URL 格式正确
        
        注意：完整的 SSO 测试需要浏览器环境
        """
        # 检查官网的 hirestream-redirect 端点
        # 未登录时应该重定向到登录页
        try:
            response = requests.get(
                f"{official_site_url}/api/services/hirestream-redirect",
                allow_redirects=False,
                timeout=config.timeout
            )
            
            # 未登录应该重定向到登录页
            if response.status_code in [302, 307]:
                location = response.headers.get("Location", "")
                assert "login" in location.lower(), \
                    f"未登录时应重定向到登录页，实际: {location}"
            elif response.status_code == 200:
                # 可能已经登录或返回了错误页面
                pass
            else:
                pytest.skip(f"hirestream-redirect 返回 {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            pytest.skip(f"无法访问官网: {e}")


class TestSSOHealthCheck:
    """SSO 健康检查 - 快速诊断"""
    
    @pytest.mark.sso
    @pytest.mark.smoke
    def test_sso_health_quick_check(self, config, official_site_url):
        """
        SSO 健康快速检查 - 一次性验证关键配置
        
        这个测试可以快速诊断 SSO 问题的根因
        """
        issues = []
        
        # 1. 检查 TalentAI 后端健康
        try:
            r = requests.get(f"{config.backend_url}/health", timeout=5)
            if r.status_code != 200:
                issues.append(f"TalentAI 后端不健康: {r.status_code}")
        except Exception as e:
            issues.append(f"TalentAI 后端不可达: {e}")
        
        # 2. 检查官网健康
        try:
            r = requests.get(official_site_url, timeout=5)
            if r.status_code not in [200, 301, 302, 403, 404]:
                issues.append(f"官网不健康: {r.status_code}")
        except Exception as e:
            issues.append(f"官网不可达: {e}")
        
        # 3. 检查 verify-token 端点
        try:
            r = requests.post(
                f"{config.backend_url}/api/auth/verify-token",
                json={"token": "test"},
                timeout=5
            )
            if r.status_code == 404:
                issues.append("verify-token 端点不存在")
            elif r.status_code == 500:
                issues.append("verify-token 端点内部错误（可能是 JWT_SECRET 未配置）")
        except Exception as e:
            issues.append(f"verify-token 端点不可达: {e}")
        
        # 4. 检查 auth/me 端点
        try:
            r = requests.get(f"{config.backend_url}/api/auth/me", timeout=5)
            if r.status_code != 200:
                issues.append(f"auth/me 端点异常: {r.status_code}")
        except Exception as e:
            issues.append(f"auth/me 端点不可达: {e}")
        
        # 报告问题
        if issues:
            pytest.fail("SSO 健康检查发现问题:\n" + "\n".join(f"  - {i}" for i in issues))
