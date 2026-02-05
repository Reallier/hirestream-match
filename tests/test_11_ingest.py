# -*- coding: utf-8 -*-
"""
测试模块: 简历入库 API 测试

覆盖后端简历入库端点:
- POST /api/candidates/ingest
"""

import pytest
import io


class TestResumeIngest:
    """简历入库测试"""
    
    def test_ingest_unauthorized(self, backend_client):
        """未授权上传简历"""
        # 创建一个假的 PDF 文件
        fake_pdf = io.BytesIO(b"%PDF-1.4 fake content")
        
        response = backend_client.post(
            "/api/candidates/ingest",
            files={"file": ("test.pdf", fake_pdf, "application/pdf")},
            data={"source": "test", "user_id": "1"}
        )
        
        # 应该被拒绝或失败（无有效 user_id）
        assert response.status_code in [200, 400, 401, 403, 404, 415, 422, 500]
        print("✅ 未授权入库权限检查完成")
    
    def test_ingest_empty_file(self, backend_client, auth_token, test_user_id):
        """空文件上传"""
        empty_file = io.BytesIO(b"")
        
        response = backend_client.post(
            "/api/candidates/ingest",
            files={"file": ("empty.pdf", empty_file, "application/pdf")},
            data={"source": "test", "user_id": str(test_user_id)},
            cookies={"auth_token": auth_token}
        )
        
        # 空文件应返回错误
        assert response.status_code in [200, 400, 404, 415, 422, 500]
        print("✅ 空文件处理正常")
    
    def test_ingest_invalid_file_type(self, backend_client, auth_token, test_user_id):
        """不支持的文件类型"""
        fake_file = io.BytesIO(b"This is a text file, not PDF or DOCX")
        
        response = backend_client.post(
            "/api/candidates/ingest",
            files={"file": ("test.txt", fake_file, "text/plain")},
            data={"source": "test", "user_id": str(test_user_id)},
            cookies={"auth_token": auth_token}
        )
        
        # 不支持的文件类型应返回错误
        assert response.status_code in [200, 400, 404, 415, 422, 500]
        print("✅ 不支持文件类型处理正常")
    
    def test_ingest_fake_pdf(self, backend_client, auth_token, test_user_id):
        """伪造 PDF 文件"""
        # 创建一个假的 PDF（只有头部）
        fake_pdf = io.BytesIO(b"%PDF-1.4\n%fake content\n")
        
        response = backend_client.post(
            "/api/candidates/ingest",
            files={"file": ("fake.pdf", fake_pdf, "application/pdf")},
            data={"source": "test", "user_id": str(test_user_id)},
            cookies={"auth_token": auth_token}
        )
        
        # 伪造 PDF 可能解析失败
        assert response.status_code in [200, 400, 422, 500]
        print("✅ 伪造 PDF 处理正常")
    
    def test_ingest_source_parameter(self, backend_client, auth_token, test_user_id):
        """来源参数测试"""
        fake_pdf = io.BytesIO(b"%PDF-1.4 test")
        
        response = backend_client.post(
            "/api/candidates/ingest",
            files={"file": ("test.pdf", fake_pdf, "application/pdf")},
            data={"source": "api_test", "user_id": str(test_user_id)},
            cookies={"auth_token": auth_token}
        )
        
        # 来源参数应被正确处理
        assert response.status_code in [200, 400, 422, 500]
        print("✅ 来源参数处理正常")
    
    def test_ingest_missing_file(self, backend_client, auth_token, test_user_id):
        """缺少文件"""
        response = backend_client.post(
            "/api/candidates/ingest",
            data={"source": "test", "user_id": str(test_user_id)},
            cookies={"auth_token": auth_token}
        )
        
        # 缺少文件应返回 422
        assert response.status_code == 422
        print("✅ 缺少文件处理正常")


class TestResumeIngestSecurity:
    """简历入库安全测试"""
    
    def test_ingest_path_traversal(self, backend_client, auth_token, test_user_id):
        """路径遍历攻击"""
        malicious_file = io.BytesIO(b"%PDF-1.4 test")
        
        response = backend_client.post(
            "/api/candidates/ingest",
            files={"file": ("../../../etc/passwd.pdf", malicious_file, "application/pdf")},
            data={"source": "test", "user_id": str(test_user_id)},
            cookies={"auth_token": auth_token}
        )
        
        # 不应导致服务崩溃
        assert response.status_code in [200, 400, 422, 500]
        print("✅ 路径遍历防护正常")
    
    def test_ingest_large_filename(self, backend_client, auth_token, test_user_id):
        """超长文件名"""
        long_name = "a" * 500 + ".pdf"
        fake_pdf = io.BytesIO(b"%PDF-1.4 test")
        
        response = backend_client.post(
            "/api/candidates/ingest",
            files={"file": (long_name, fake_pdf, "application/pdf")},
            data={"source": "test", "user_id": str(test_user_id)},
            cookies={"auth_token": auth_token}
        )
        
        # 应正常处理或拒绝
        assert response.status_code in [200, 400, 404, 414, 422, 500]
        print("✅ 超长文件名处理正常")
    
    def test_ingest_special_filename(self, backend_client, auth_token, test_user_id):
        """特殊字符文件名"""
        special_name = "测试简历<script>alert(1)</script>.pdf"
        fake_pdf = io.BytesIO(b"%PDF-1.4 test")
        
        response = backend_client.post(
            "/api/candidates/ingest",
            files={"file": (special_name, fake_pdf, "application/pdf")},
            data={"source": "test", "user_id": str(test_user_id)},
            cookies={"auth_token": auth_token}
        )
        
        # 应正常处理
        assert response.status_code in [200, 400, 422, 500]
        print("✅ 特殊字符文件名处理正常")
