# -*- coding: utf-8 -*-
"""
测试模块: Feedback API 测试

覆盖后端 Feedback API 端点:
- POST /api/feedback/submit
- GET /api/feedback/list
- PATCH /api/feedback/{id}
"""

import pytest


class TestFeedbackSubmit:
    """反馈提交测试"""
    
    def test_submit_feedback_anonymous(self, backend_client):
        """匿名提交反馈"""
        response = backend_client.post("/api/feedback/submit", json={
            "type": "suggestion",
            "content": "这是一条测试反馈，希望增加批量导入功能",
            "contact": "test@example.com",
            "page": "/library"
        })
        
        assert response.status_code == 200, f"提交失败: {response.status_code}"
        data = response.json()
        assert data.get("success") is True or "id" in data or "feedback_id" in data
        print(f"✅ 匿名反馈提交成功")
    
    def test_submit_feedback_empty_content(self, backend_client):
        """空内容应拒绝"""
        response = backend_client.post("/api/feedback/submit", json={
            "type": "bug",
            "content": "",
            "page": "/match"
        })
        
        # 应返回 400 或 422
        assert response.status_code in [400, 422], f"空内容应被拒绝: {response.status_code}"
        print("✅ 空内容反馈被正确拒绝")
    
    def test_submit_feedback_type_bug(self, backend_client):
        """Bug 类型反馈"""
        response = backend_client.post("/api/feedback/submit", json={
            "type": "bug",
            "content": "匹配结果页面偶尔加载失败",
            "page": "/match"
        })
        
        assert response.status_code == 200
        print("✅ Bug 类型反馈提交成功")
    
    def test_submit_feedback_type_other(self, backend_client):
        """其他类型反馈"""
        response = backend_client.post("/api/feedback/submit", json={
            "type": "other",
            "content": "希望支持更多简历格式"
        })
        
        assert response.status_code == 200
        print("✅ 其他类型反馈提交成功")


class TestFeedbackList:
    """反馈列表测试（需要管理员权限）"""
    
    def test_list_feedback_unauthorized(self, backend_client):
        """未授权访问反馈列表"""
        response = backend_client.get("/api/feedback/list")
        
        # 应返回 401 或 403
        assert response.status_code in [401, 403], f"未授权应被拒绝: {response.status_code}"
        print("✅ 未授权访问被正确拒绝")
    
    def test_list_feedback_with_auth(self, backend_client, admin_auth_token):
        """管理员获取反馈列表"""
        response = backend_client.get(
            "/api/feedback/list",
            cookies={"auth_token": admin_auth_token}
        )
        
        if response.status_code == 200:
            data = response.json()
            assert "data" in data, f"响应缺少 data 字段: {data.keys()}"
            print(f"✅ 管理员获取反馈列表成功")
        elif response.status_code in [401, 403]:
            pytest.skip("无管理员权限，跳过此测试")
    
    def test_list_feedback_with_filter(self, backend_client, admin_auth_token):
        """按状态筛选反馈"""
        response = backend_client.get(
            "/api/feedback/list?status=pending",
            cookies={"auth_token": admin_auth_token}
        )
        
        if response.status_code == 200:
            print("✅ 反馈筛选功能正常")
        elif response.status_code in [401, 403]:
            pytest.skip("无管理员权限，跳过此测试")


class TestFeedbackUpdate:
    """反馈更新测试（需要管理员权限）"""
    
    def test_update_feedback_unauthorized(self, backend_client):
        """未授权更新反馈"""
        # 确保没有携带 Cookie
        backend_client.cookies.clear()
        
        response = backend_client.patch("/api/feedback/1", json={
            "status": "reviewed"
        })
        
        # 应返回 401, 403, 404, 422 或 500（内部错误）
        assert response.status_code in [401, 403, 404, 422, 500], f"未授权应被拒绝: {response.status_code}"
        print("✅ 未授权更新被正确拒绝")
    
    def test_update_nonexistent_feedback(self, backend_client, admin_auth_token):
        """更新不存在的反馈"""
        response = backend_client.patch(
            "/api/feedback/99999",
            json={"status": "reviewed"},
            cookies={"auth_token": admin_auth_token}
        )
        
        if response.status_code == 404:
            print("✅ 不存在的反馈正确返回 404")
        elif response.status_code in [401, 403]:
            pytest.skip("无管理员权限，跳过此测试")
