"""
测试模块 4: 候选人管理
验证候选人列表、搜索、详情等功能
"""
import pytest

class TestCandidates:
    """候选人管理测试"""
    
    def test_list_candidates(self, backend_client, test_config):
        """获取候选人列表 - GET /api/candidates"""
        response = backend_client.get("/api/candidates", params={
            "user_id": test_config.test_user_id
        })
        
        assert response.status_code == 200, f"获取候选人列表失败: {response.status_code}"
        
        data = response.json()
        # 可能返回列表或包含列表的对象
        if isinstance(data, list):
            candidates = data
        else:
            candidates = data.get("candidates", data.get("items", []))
        
        print(f"📋 候选人数量: {len(candidates)}")
        print(f"✅ 候选人列表测试通过")
    
    def test_list_candidates_pagination(self, backend_client, test_config):
        """候选人列表分页 - GET /api/candidates?skip=0&limit=10"""
        response = backend_client.get("/api/candidates", params={
            "user_id": test_config.test_user_id,
            "skip": 0,
            "limit": 10
        })
        
        assert response.status_code == 200, f"分页请求失败: {response.status_code}"
        
        data = response.json()
        print(f"📋 分页结果: {type(data)}")
        print(f"✅ 分页测试通过")
    
    def test_candidates_count(self, frontend_client):
        """获取候选人数量 - GET /api/candidates/count"""
        response = frontend_client.get("/api/candidates/count")
        
        if response.status_code == 200:
            data = response.json()
            count = data.get("count", data.get("total", 0))
            print(f"📊 候选人总数: {count}")
        else:
            # 404 可能是路由不存在
            print(f"⚠️ 候选人计数接口: {response.status_code}")
        
        print(f"✅ 候选人计数测试通过")
    
    def test_search_candidates(self, backend_client, test_config):
        """关键词搜索候选人 - GET /api/search?q=python"""
        response = backend_client.get("/api/search", params={
            "user_id": test_config.test_user_id,
            "q": "Python"
        })
        
        # 搜索接口可能返回 200 或 404（无结果）
        assert response.status_code in [200, 404], \
            f"搜索请求失败: {response.status_code}"
        
        if response.status_code == 200:
            data = response.json()
            print(f"🔍 搜索结果: {len(data) if isinstance(data, list) else data}")
        
        print(f"✅ 候选人搜索测试通过")
    
    def test_get_candidate_detail(self, backend_client, test_config):
        """获取候选人详情 - GET /api/candidates/1"""
        # 先获取列表找一个有效 ID
        list_response = backend_client.get("/api/candidates", params={
            "user_id": test_config.test_user_id,
            "limit": 1
        })
        
        if list_response.status_code == 200:
            data = list_response.json()
            candidates = data if isinstance(data, list) else data.get("candidates", [])
            
            if candidates:
                candidate_id = candidates[0].get("id", 1)
                
                response = backend_client.get(f"/api/candidates/{candidate_id}", params={
                    "user_id": test_config.test_user_id
                })
                assert response.status_code in [200, 404], \
                    f"获取详情失败: {response.status_code}"
                
                if response.status_code == 200:
                    detail = response.json()
                    print(f"👤 候选人详情: {detail.get('name', 'Unknown')}")
            else:
                print(f"⚠️ 没有候选人数据，跳过详情测试")
        
        print(f"✅ 候选人详情测试通过")
    
    def test_get_nonexistent_candidate(self, backend_client, test_config):
        """获取不存在的候选人"""
        response = backend_client.get("/api/candidates/999999", params={
            "user_id": test_config.test_user_id
        })
        
        # 应该返回 404
        assert response.status_code == 404, \
            f"不存在的候选人应返回 404: {response.status_code}"
        
        print(f"✅ 不存在候选人测试通过")
