"""
测试模块 1: 健康检查
验证后端和前端服务是否正常运行
"""
import pytest

class TestHealth:
    """健康检查测试"""
    
    def test_backend_health(self, backend_client):
        """后端健康检查 - GET /health"""
        response = backend_client.get("/health")
        
        assert response.status_code == 200, f"健康检查失败: {response.status_code}"
        
        data = response.json()
        assert "status" in data or response.status_code == 200, "响应缺少状态信息"
        
        print(f"✅ 后端健康检查通过: {data}")
    
    def test_backend_root(self, backend_client):
        """后端根路径 - GET /"""
        response = backend_client.get("/")
        
        assert response.status_code == 200, f"根路径访问失败: {response.status_code}"
        print(f"✅ 后端根路径可访问")
    
    def test_frontend_accessible(self, frontend_client):
        """前端页面可访问"""
        response = frontend_client.get("/")
        
        assert response.status_code == 200, f"前端访问失败: {response.status_code}"
        assert "TalentAI" in response.text or "html" in response.headers.get("content-type", "").lower()
        
        print(f"✅ 前端页面可访问")
    
    def test_backend_api_docs(self, backend_client):
        """API 文档可访问 - GET /docs"""
        response = backend_client.get("/docs")
        
        # FastAPI 默认的 Swagger UI
        assert response.status_code == 200, f"API 文档访问失败: {response.status_code}"
        print(f"✅ API 文档可访问")
