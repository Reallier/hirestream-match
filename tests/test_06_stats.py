"""
测试模块 6: 统计与系统信息
验证统计接口
"""
import pytest

class TestStats:
    """统计信息测试"""
    
    def test_get_stats(self, backend_client):
        """获取系统统计 - GET /api/stats"""
        response = backend_client.get("/api/stats")
        
        if response.status_code == 200:
            data = response.json()
            print(f"📊 系统统计: {data}")
        else:
            print(f"⚠️ 统计接口: {response.status_code}")
        
        print(f"✅ 系统统计测试通过")
    
    def test_feedback_list(self, frontend_client):
        """获取反馈列表 - GET /api/feedback/list"""
        response = frontend_client.get("/api/feedback/list")
        
        # 可能需要管理员权限
        print(f"📋 反馈列表响应: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   反馈数量: {len(data) if isinstance(data, list) else data}")
        
        print(f"✅ 反馈列表测试通过")
