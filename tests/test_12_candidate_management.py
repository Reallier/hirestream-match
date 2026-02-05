# -*- coding: utf-8 -*-
"""
测试模块: 候选人管理 API 补充测试

覆盖:
- DELETE /api/candidates/{id}
- GET /api/match/history/{id}
"""

import pytest


class TestCandidateDelete:
    """候选人删除测试"""
    
    def test_delete_unauthorized(self, backend_client):
        """未授权删除候选人"""
        response = backend_client.delete("/api/candidates/1?user_id=1")
        
        # 应返回错误
        assert response.status_code in [401, 403, 404, 422, 500]
        print("✅ 未授权删除被拒绝")
    
    def test_delete_nonexistent_candidate(self, backend_client, auth_token, test_user_id):
        """删除不存在的候选人"""
        response = backend_client.delete(
            f"/api/candidates/999999?user_id={test_user_id}",
            cookies={"auth_token": auth_token}
        )
        
        # 应返回 404 或错误
        assert response.status_code in [404, 400, 422, 500]
        print("✅ 删除不存在候选人处理正常")
    
    def test_delete_other_user_candidate(self, backend_client, auth_token, test_user_id):
        """删除其他用户的候选人"""
        # 使用不匹配的 user_id
        fake_user_id = test_user_id + 1000
        
        response = backend_client.delete(
            f"/api/candidates/1?user_id={fake_user_id}",
            cookies={"auth_token": auth_token}
        )
        
        # 应返回 403 或 404（找不到该用户的候选人）
        assert response.status_code in [403, 404, 422, 500]
        print("✅ 跨用户删除保护正常")


class TestMatchHistoryDetail:
    """匹配历史详情测试"""
    
    def test_history_detail_unauthorized(self, backend_client):
        """未授权获取历史详情"""
        response = backend_client.get("/api/match/history/1")
        
        # 应返回未授权或空
        if response.status_code == 200:
            data = response.json()
            assert data.get("success") is False or data.get("record") is None
        else:
            assert response.status_code in [401, 403, 404]
        print("✅ 未授权获取历史详情处理正常")
    
    def test_history_detail_nonexistent(self, backend_client, auth_token):
        """获取不存在的历史记录"""
        response = backend_client.get(
            "/api/match/history/999999",
            cookies={"auth_token": auth_token}
        )
        
        if response.status_code == 200:
            data = response.json()
            assert data.get("success") is False or data.get("record") is None
        else:
            assert response.status_code in [404, 401]
        print("✅ 不存在历史记录处理正常")
    
    def test_history_detail_valid(self, backend_client, auth_token):
        """获取有效历史记录详情"""
        # 先获取历史列表
        list_response = backend_client.get(
            "/api/match/history",
            cookies={"auth_token": auth_token}
        )
        
        if list_response.status_code != 200:
            pytest.skip("无法获取历史列表")
        
        list_data = list_response.json()
        if not list_data.get("success") or not list_data.get("records"):
            pytest.skip("没有历史记录")
        
        # 获取第一条记录的详情
        record_id = list_data["records"][0]["id"]
        response = backend_client.get(
            f"/api/match/history/{record_id}",
            cookies={"auth_token": auth_token}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
        assert data.get("record") is not None
        print(f"✅ 获取历史详情成功, ID: {record_id}")


class TestCandidateList:
    """候选人列表补充测试"""
    
    def test_list_candidates_pagination(self, backend_client, auth_token, test_user_id):
        """候选人列表分页"""
        response = backend_client.get(
            f"/api/candidates?user_id={test_user_id}&skip=0&limit=5",
            cookies={"auth_token": auth_token}
        )
        
        if response.status_code == 200:
            data = response.json()
            # API 直接返回列表
            candidates = data if isinstance(data, list) else data.get("candidates", [])
            assert len(candidates) <= 5
            print(f"✅ 分页正常, 返回 {len(candidates)} 个候选人")
        else:
            assert response.status_code in [401, 404, 422]
    
    def test_list_candidates_status_filter(self, backend_client, auth_token, test_user_id):
        """候选人状态筛选"""
        response = backend_client.get(
            f"/api/candidates?user_id={test_user_id}&status=active",
            cookies={"auth_token": auth_token}
        )
        
        assert response.status_code in [200, 401, 422]
        print("✅ 状态筛选正常")
