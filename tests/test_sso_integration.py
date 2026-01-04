# -*- coding: utf-8 -*-
"""
SSO 跨应用认证集成测试

基于 2026-01-02 TalentAI 架构重构中发现的问题总结

问题清单：
1. CORS 配置未包含测试环境 URL（带端口）
2. JWT_SECRET 未在所有服务间同步
3. JWT Payload 格式统一（2026 标准：纯整数 user_id）
4. Cookie 域配置问题
5. 前端 API_BASE 配置缺少端口号
"""

import os
import pytest
import requests
import jwt
from datetime import datetime, timedelta

# ============= 测试配置 =============

# 测试环境
TEST_OFFICIAL_SITE = os.getenv("TEST_OFFICIAL_SITE", "https://test.intjtech.reallier.top:5443")
TEST_TALENTAI_FRONTEND = os.getenv("TEST_TALENTAI_FRONTEND", "https://test.talentai.reallier.top:5443")
TEST_TALENTAI_API = os.getenv("TEST_TALENTAI_API", "https://test.api.talentai.reallier.top:5443")

# 生产环境
PROD_OFFICIAL_SITE = os.getenv("PROD_OFFICIAL_SITE", "https://intjtech.cn")
PROD_TALENTAI_FRONTEND = os.getenv("PROD_TALENTAI_FRONTEND", "https://talentai.reallier.top")
PROD_TALENTAI_API = os.getenv("PROD_TALENTAI_API", "https://api.talentai.reallier.top")

# 测试用户
TEST_USERNAME = os.getenv("TEST_USERNAME", "demo")
TEST_PASSWORD = os.getenv("TEST_PASSWORD", "Test123")

# JWT 配置
JWT_SECRET = os.getenv("JWT_SECRET", "5Sf4IrUfOLVQ7ul46zfg_w-bHHHu_Y67iqscKTw6UM0")
JWT_ALGORITHM = "HS256"


# ============= 基础设施测试 =============

class TestInfrastructure:
    """基础设施配置测试"""
    
    def test_cors_001_test_env_origins(self):
        """
        CORS-001: 测试环境 CORS 白名单
        
        验证后端 CORS 配置包含测试环境的完整 URL（含端口）
        
        问题背景：
        - 测试环境使用端口 5443
        - CORS origins 必须精确匹配 origin（包括端口）
        - 遗漏端口会导致 preflight 请求失败
        """
        # Preflight 请求
        response = requests.options(
            f"{TEST_TALENTAI_API}/api/auth/login",
            headers={
                "Origin": TEST_TALENTAI_FRONTEND,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type"
            },
            verify=False,
            timeout=10
        )
        
        assert response.status_code == 200, f"Preflight 请求失败: {response.status_code}"
        assert response.headers.get("Access-Control-Allow-Origin") == TEST_TALENTAI_FRONTEND, \
            f"CORS origin 不匹配: {response.headers.get('Access-Control-Allow-Origin')}"
        assert "true" in response.headers.get("Access-Control-Allow-Credentials", "").lower(), \
            "未设置 Allow-Credentials"
    
    @pytest.mark.xfail(reason="生产环境 SSL 需要更完整配置")
    def test_cors_002_prod_env_origins(self):
        """
        CORS-002: 生产环境 CORS 白名单
        
        验证生产环境的 CORS 配置正确
        """
        response = requests.options(
            f"{PROD_TALENTAI_API}/api/auth/login",
            headers={
                "Origin": PROD_TALENTAI_FRONTEND,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type"
            },
            verify=False,
            timeout=10
        )
        
        assert response.status_code == 200, f"Preflight 请求失败: {response.status_code}"
        assert response.headers.get("Access-Control-Allow-Origin") == PROD_TALENTAI_FRONTEND
    
    def test_jwt_001_secret_consistency(self):
        """
        JWT-001: JWT 密钥一致性
        
        验证使用相同 JWT_SECRET 生成的 Token 能被后端识别
        
        当前 TalentAI JWT 格式:
        {
            "user_id": <int>,
            "nickname": <str>,
            "iat": <timestamp>,
            "exp": <timestamp>
        }
        """
        # 使用当前 TalentAI 格式生成 Token
        payload = {
            "user_id": 6,
            "nickname": "测试用户",
            "iat": int(datetime.now().timestamp()),
            "exp": int((datetime.now() + timedelta(days=7)).timestamp())
        }
        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        
        # 验证 TalentAI 后端能解析
        response = requests.get(
            f"{TEST_TALENTAI_API}/api/auth/me",
            cookies={"auth_token": token},
            verify=False,
            timeout=10
        )
        
        assert response.status_code == 200, f"Token 验证失败: {response.status_code}"
        data = response.json()
        assert data.get("success") is True, f"Token 验证失败: {data}"
        assert data.get("user", {}).get("id") == 6, "用户 ID 解析错误"


# ============= SSO 认证流程测试 =============

class TestSSOFlow:
    """SSO 单点登录流程测试"""
    
    def test_sso_001_official_login_sets_cookie(self):
        """
        SSO-001: 官网登录设置跨域 Cookie
        
        验证官网登录后设置的 Cookie 域为 .reallier.top
        """
        response = requests.post(
            f"{TEST_OFFICIAL_SITE}/api/auth/login",
            json={"username": TEST_USERNAME, "password": TEST_PASSWORD},
            verify=False,
            timeout=10,
            allow_redirects=False
        )
        
        assert response.status_code == 200, f"登录失败: {response.status_code}"
        
        # 检查 Set-Cookie header
        set_cookie = response.headers.get("Set-Cookie", "")
        assert "auth_token" in set_cookie, "未设置 auth_token Cookie"
        assert ".reallier.top" in set_cookie or "domain=.reallier.top" in set_cookie.lower(), \
            f"Cookie 域配置错误: {set_cookie}"
    
    def test_sso_002_talentai_recognizes_official_token(self):
        """
        SSO-002: TalentAI 识别官网 Token
        
        验证 TalentAI 后端能正确解析官网签发的 JWT Token
        
        2026 统一标准：
        - 官网和 TalentAI 统一使用纯整数 user_id
        - 无需兼容处理 intj_ 前缀
        """
        # 先从官网登录获取 Token
        login_response = requests.post(
            f"{TEST_OFFICIAL_SITE}/api/auth/login",
            json={"username": TEST_USERNAME, "password": TEST_PASSWORD},
            verify=False,
            timeout=10
        )
        
        assert login_response.status_code == 200
        
        # 提取 Cookie
        cookies = login_response.cookies
        auth_token = cookies.get("auth_token")
        assert auth_token, "未获取到 auth_token"
        
        # 使用官网的 Token 访问 TalentAI API
        me_response = requests.get(
            f"{TEST_TALENTAI_API}/api/auth/me",
            cookies={"auth_token": auth_token},
            verify=False,
            timeout=10
        )
        
        assert me_response.status_code == 200, f"TalentAI 验证失败: {me_response.status_code}"
        data = me_response.json()
        assert data.get("success") is True, f"Token 验证失败: {data}"
    
    def test_sso_003_talentai_login_sets_cookie(self):
        """
        SSO-003: TalentAI 登录设置跨域 Cookie
        
        验证 TalentAI 登录后设置的 Cookie 域为 .reallier.top
        """
        response = requests.post(
            f"{TEST_TALENTAI_API}/api/auth/login",
            json={"username": TEST_USERNAME, "password": TEST_PASSWORD},
            verify=False,
            timeout=10
        )
        
        assert response.status_code == 200, f"登录失败: {response.status_code}"
        
        # 检查 Set-Cookie header
        set_cookie = response.headers.get("Set-Cookie", "")
        assert "auth_token" in set_cookie, "未设置 auth_token Cookie"
        assert ".reallier.top" in set_cookie or "domain=.reallier.top" in set_cookie.lower(), \
            f"Cookie 域配置错误: {set_cookie}"
    
    @pytest.mark.xfail(reason="官网后端尚未实现解析 TalentAI Token")
    def test_sso_004_official_recognizes_talentai_token(self):
        """
        SSO-004: 官网识别 TalentAI Token
        
        验证官网能正确解析 TalentAI 签发的 JWT Token（反向 SSO）
        """
        # 从 TalentAI 登录获取 Token
        login_response = requests.post(
            f"{TEST_TALENTAI_API}/api/auth/login",
            json={"username": TEST_USERNAME, "password": TEST_PASSWORD},
            verify=False,
            timeout=10
        )
        
        assert login_response.status_code == 200
        
        # 提取 Cookie
        cookies = login_response.cookies
        auth_token = cookies.get("auth_token")
        assert auth_token, "未获取到 auth_token"
        
        # 使用 TalentAI 的 Token 访问官网 API
        me_response = requests.get(
            f"{TEST_OFFICIAL_SITE}/api/user/me",
            cookies={"auth_token": auth_token},
            verify=False,
            timeout=10
        )
        
        assert me_response.status_code == 200, f"官网验证失败: {me_response.status_code}"
        data = me_response.json()
        assert data.get("user") is not None, f"Token 验证失败: {data}"


# ============= JWT Token 格式兼容性测试 =============

class TestJWTCompatibility:
    """JWT Token 格式兼容性测试"""
    
    def test_jwt_format_001_official_format(self):
        """
        JWT-FORMAT-001: 官网 JWT 格式
        
        验证官网 JWT Payload 包含必要字段
        """
        # 登录获取 Token
        response = requests.post(
            f"{TEST_OFFICIAL_SITE}/api/auth/login",
            json={"username": TEST_USERNAME, "password": TEST_PASSWORD},
            verify=False,
            timeout=10
        )
        
        auth_token = response.cookies.get("auth_token")
        assert auth_token, "未获取到 auth_token"
        
        # 解析 Token（不验证签名）
        payload = jwt.decode(auth_token, options={"verify_signature": False})
        
        # 验证必要字段
        assert "id" in payload or "user_id" in payload, "缺少用户 ID 字段"
        assert "exp" in payload, "缺少过期时间"
    
    def test_jwt_format_002_talentai_format(self):
        """
        JWT-FORMAT-002: TalentAI JWT 格式
        
        验证 TalentAI JWT Payload 包含必要字段
        """
        response = requests.post(
            f"{TEST_TALENTAI_API}/api/auth/login",
            json={"username": TEST_USERNAME, "password": TEST_PASSWORD},
            verify=False,
            timeout=10
        )
        
        auth_token = response.cookies.get("auth_token")
        assert auth_token, "未获取到 auth_token"
        
        payload = jwt.decode(auth_token, options={"verify_signature": False})
        
        assert "user_id" in payload, "缺少 user_id 字段"
        assert "exp" in payload, "缺少过期时间"
    
    def test_jwt_format_003_unified_integer_user_id(self):
        """
        JWT-FORMAT-003: 统一整数 user_id 格式
        
        验证 2026 统一标准：所有服务使用纯整数 user_id
        
        历史变更：
        - 2026-01-04: 废弃 intj_ 前缀格式，统一使用纯整数
        """
        # 构造纯整数格式的 Token（2026 统一标准）
        payload = {
            "id": 6,
            "user_id": 6,  # 纯整数
            "nickname": "测试用户",
            "iat": int(datetime.now().timestamp()),
            "exp": int((datetime.now() + timedelta(days=7)).timestamp())
        }
        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        
        response = requests.get(
            f"{TEST_TALENTAI_API}/api/auth/me",
            cookies={"auth_token": token},
            verify=False,
            timeout=10
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
        assert data.get("user", {}).get("id") == 6, "用户 ID 解析失败"


# ============= API 端点测试 =============

class TestAuthEndpoints:
    """认证相关 API 端点测试"""
    
    def test_auth_001_login_success(self):
        """AUTH-001: 登录成功"""
        response = requests.post(
            f"{TEST_TALENTAI_API}/api/auth/login",
            json={"username": TEST_USERNAME, "password": TEST_PASSWORD},
            verify=False,
            timeout=10
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
        assert data.get("user") is not None
    
    def test_auth_002_login_wrong_password(self):
        """AUTH-002: 密码错误"""
        response = requests.post(
            f"{TEST_TALENTAI_API}/api/auth/login",
            json={"username": TEST_USERNAME, "password": "wrongpassword"},
            verify=False,
            timeout=10
        )
        
        assert response.status_code == 401
    
    def test_auth_003_logout(self):
        """AUTH-003: 登出"""
        # 先登录
        login_response = requests.post(
            f"{TEST_TALENTAI_API}/api/auth/login",
            json={"username": TEST_USERNAME, "password": TEST_PASSWORD},
            verify=False,
            timeout=10
        )
        
        cookies = login_response.cookies
        
        # 登出
        logout_response = requests.post(
            f"{TEST_TALENTAI_API}/api/auth/logout",
            cookies=cookies,
            verify=False,
            timeout=10
        )
        
        assert logout_response.status_code == 200
        
        # 验证 Cookie 被清除
        set_cookie = logout_response.headers.get("Set-Cookie", "")
        # Cookie 应该被设置为空或过期
        assert "auth_token" in set_cookie
    
    def test_auth_004_me_without_token(self):
        """AUTH-004: 未登录获取用户信息"""
        response = requests.get(
            f"{TEST_TALENTAI_API}/api/auth/me",
            verify=False,
            timeout=10
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is False or data.get("user") is None
    
    def test_auth_005_me_with_valid_token(self):
        """AUTH-005: 已登录获取用户信息"""
        # 登录
        login_response = requests.post(
            f"{TEST_TALENTAI_API}/api/auth/login",
            json={"username": TEST_USERNAME, "password": TEST_PASSWORD},
            verify=False,
            timeout=10
        )
        
        cookies = login_response.cookies
        
        # 获取用户信息
        me_response = requests.get(
            f"{TEST_TALENTAI_API}/api/auth/me",
            cookies=cookies,
            verify=False,
            timeout=10
        )
        
        assert me_response.status_code == 200
        data = me_response.json()
        assert data.get("success") is True
        assert data.get("user", {}).get("name") is not None


# ============= 运行测试 =============

if __name__ == "__main__":
    import warnings
    warnings.filterwarnings("ignore", message="Unverified HTTPS request")
    
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-x"  # 遇到第一个失败就停止
    ])
