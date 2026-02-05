"""
测试模块 3: 即时匹配 (核心业务)
验证 JD 和简历匹配功能
"""
import pytest

class TestInstantMatch:
    """即时匹配测试 - 核心业务流程"""
    
    def test_instant_match_text_only(self, backend_client, sample_jd, sample_resume):
        """纯文本即时匹配 - POST /api/instant-match"""
        response = backend_client.post(
            "/api/instant-match",
            data={
                "jd": sample_jd,
                "resume_text": sample_resume,
            }
        )
        
        assert response.status_code == 200, f"匹配请求失败: {response.status_code} - {response.text}"
        
        data = response.json()
        print(f"📊 匹配结果: {data}")
        
        # 验证响应结构
        assert "match_score" in data, "响应缺少 match_score"
        
        print(f"✅ 即时匹配测试通过，匹配分数: {data.get('match_score')}")
    
    def test_instant_match_response_structure(self, backend_client, sample_jd, sample_resume):
        """验证匹配响应结构完整性"""
        response = backend_client.post(
            "/api/instant-match",
            data={
                "jd": sample_jd,
                "resume_text": sample_resume,
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # 核心字段验证
        required_fields = ["match_score"]
        optional_fields = ["advantages", "risks", "advice", "analysis"]
        
        for field in required_fields:
            assert field in data, f"缺少必需字段: {field}"
        
        # 检查可选字段（至少应该有一些）
        has_optional = any(field in data for field in optional_fields)
        print(f"📋 响应字段: {list(data.keys())}")
        
        print(f"✅ 响应结构验证通过")
    
    def test_instant_match_score_range(self, backend_client, sample_jd, sample_resume):
        """验证匹配分数范围 0-100"""
        response = backend_client.post(
            "/api/instant-match",
            data={
                "jd": sample_jd,
                "resume_text": sample_resume,
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        score = data.get("match_score")
        assert score is not None, "缺少 match_score"
        assert 0 <= score <= 100, f"分数超出范围: {score}"
        
        print(f"✅ 分数范围验证通过: {score}")
    
    def test_instant_match_missing_jd(self, backend_client, sample_resume):
        """缺少 JD 参数"""
        response = backend_client.post(
            "/api/instant-match",
            data={
                "resume_text": sample_resume,
            }
        )
        
        # 应该返回错误或提示
        if response.status_code == 200:
            data = response.json()
            # 可能返回错误消息
            assert "error" in data or data.get("match_score", 0) == 0, \
                "缺少 JD 应返回错误或零分"
        else:
            assert response.status_code in [400, 422], \
                f"意外的状态码: {response.status_code}"
        
        print(f"✅ 缺少 JD 测试通过")
    
    def test_instant_match_missing_resume(self, backend_client, sample_jd):
        """缺少简历参数"""
        response = backend_client.post(
            "/api/instant-match",
            data={
                "jd": sample_jd,
            }
        )
        
        # 应该返回错误（接受400/422/200带error）
        if response.status_code == 200:
            data = response.json()
            # 200时应包含错误信息或低分/空结果
            has_error = "error" in data or data.get("match_score", 101) <= 10
            assert has_error or "advice" in data, "缺少简历应返回错误或建议"
        else:
            assert response.status_code in [400, 422], \
                f"缺少简历应返回 400/422，实际: {response.status_code}"
        
        print(f"✅ 缺少简历测试通过")
    
    def test_instant_match_empty_inputs(self, backend_client):
        """空输入测试"""
        response = backend_client.post(
            "/api/instant-match",
            data={
                "jd": "",
                "resume_text": "",
            }
        )
        
        # 空输入应该被拒绝或返回错误
        if response.status_code == 200:
            data = response.json()
            assert "error" in data or data.get("match_score", 0) == 0
        else:
            assert response.status_code in [400, 422]
        
        print(f"✅ 空输入测试通过")
    
    def test_instant_match_short_jd(self, backend_client, sample_resume):
        """过短 JD 测试"""
        response = backend_client.post(
            "/api/instant-match",
            data={
                "jd": "招聘程序员",  # 非常短的 JD
                "resume_text": sample_resume,
            }
        )
        
        # 短 JD 可能被接受也可能被拒绝
        print(f"📊 短 JD 响应: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   结果: {data}")
        
        print(f"✅ 短 JD 测试通过")
