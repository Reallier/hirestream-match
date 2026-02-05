"""
License 模块单元测试

测试覆盖：
1. 机器指纹生成
2. License JWT 解码与验证
3. License 状态管理
4. API 端点
"""
import pytest
import sys
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

# 添加 backend 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))


class TestMachineId:
    """测试机器指纹生成"""
    
    def test_get_machine_id_returns_string(self):
        """测试 get_machine_id 返回非空字符串"""
        from license.machine_id import get_machine_id
        
        machine_id = get_machine_id()
        
        assert isinstance(machine_id, str)
        assert len(machine_id) == 32  # MD5 hash 长度
        assert machine_id.isalnum()  # 只包含字母和数字
    
    def test_get_machine_id_is_consistent(self):
        """测试 get_machine_id 返回一致的值"""
        from license.machine_id import get_machine_id
        
        id1 = get_machine_id()
        id2 = get_machine_id()
        
        assert id1 == id2
    
    def test_get_machine_info_structure(self):
        """测试 get_machine_info 返回正确结构"""
        from license.machine_id import get_machine_info
        
        info = get_machine_info()
        
        assert "machine_id" in info
        assert "platform" in info
        assert "generated_at" in info
        assert isinstance(info["generated_at"], datetime)


class TestLicenseValidation:
    """测试 License 验证逻辑"""
    
    @pytest.fixture
    def rsa_key_pair(self):
        """生成临时 RSA 密钥对用于测试"""
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.backends import default_backend
        
        # 生成私钥
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        
        # 导出 PEM 格式
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode()
        
        public_pem = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode()
        
        return private_pem, public_pem
    
    @pytest.fixture
    def create_test_license(self, rsa_key_pair):
        """创建测试 License 的工厂函数"""
        import jwt
        from license.machine_id import get_machine_id
        
        private_key, public_key = rsa_key_pair
        
        def _create(
            machine_id=None,
            expires_days=365,
            edition="professional",
            max_users=200,
            max_concurrency=20,
            features=None
        ):
            if machine_id is None:
                machine_id = get_machine_id()
            if features is None:
                features = ["instant_match", "talent_pool", "api_access"]
            
            now = datetime.now(timezone.utc)
            expires_at = now + timedelta(days=expires_days)
            
            payload = {
                "lic_id": "LIC-TEST-00001",
                "customer": "测试公司",
                "machine_id": machine_id,
                "edition": edition,
                "max_users": max_users,
                "max_concurrency": max_concurrency,
                "features": features,
                "issued_at": now.isoformat(),
                "expires_at": expires_at.isoformat(),
                "iat": int(now.timestamp()),
                "exp": int(expires_at.timestamp()),
            }
            
            token = jwt.encode(payload, private_key, algorithm="RS256")
            return token, public_key
        
        return _create
    
    def test_decode_valid_license(self, create_test_license):
        """测试解码有效 License"""
        from license.validator import decode_license
        
        license_key, public_key = create_test_license()
        
        data = decode_license(license_key, public_key)
        
        assert data.lic_id == "LIC-TEST-00001"
        assert data.customer == "测试公司"
        assert data.edition == "professional"
        assert data.max_users == 200
    
    def test_verify_license_valid(self, create_test_license):
        """测试验证有效 License（机器指纹匹配）"""
        from license.validator import verify_license
        
        license_key, public_key = create_test_license()
        
        is_valid, data, error = verify_license(license_key, public_key)
        
        assert is_valid is True
        assert data is not None
        assert error is None
    
    def test_verify_license_wrong_machine_id(self, create_test_license):
        """测试验证失败：机器指纹不匹配"""
        from license.validator import verify_license
        
        license_key, public_key = create_test_license(machine_id="wrong_machine_id")
        
        is_valid, data, error = verify_license(license_key, public_key)
        
        assert is_valid is False
        assert "机器指纹不匹配" in error
    
    def test_verify_license_expired(self, create_test_license):
        """测试验证失败：License 已过期"""
        from license.validator import verify_license
        
        license_key, public_key = create_test_license(expires_days=-1)
        
        is_valid, data, error = verify_license(license_key, public_key)
        
        assert is_valid is False
        assert "过期" in error
    
    def test_verify_license_invalid_signature(self, rsa_key_pair, create_test_license):
        """测试验证失败：签名无效"""
        from license.validator import verify_license
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.backends import default_backend
        
        # 使用正确的密钥创建 License
        license_key, _ = create_test_license()
        
        # 使用另一个公钥验证
        another_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        wrong_public_key = another_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode()
        
        is_valid, data, error = verify_license(license_key, wrong_public_key)
        
        assert is_valid is False
        assert "签名" in error or "验证失败" in error


class TestLicenseStorage:
    """测试 License 存储功能"""
    
    def test_store_and_retrieve_license(self, tmp_path, monkeypatch):
        """测试存储和读取 License"""
        from license import validator
        
        # 修改存储路径为临时目录
        test_license_file = tmp_path / ".license"
        monkeypatch.setattr(validator, "_LICENSE_FILE_PATHS", [test_license_file])
        
        test_key = "test_license_key_12345"
        
        # 存储
        result = validator.store_license(test_key)
        assert result is True
        
        # 读取
        retrieved = validator.get_stored_license()
        assert retrieved == test_key
        
        # 删除
        result = validator.remove_license()
        assert result is True
        
        # 确认已删除
        assert validator.get_stored_license() is None


class TestLicenseAPI:
    """测试 License API 端点"""
    
    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        from fastapi.testclient import TestClient
        from main import app
        return TestClient(app)
    
    def test_get_machine_id_endpoint(self, client):
        """测试获取机器指纹端点"""
        response = client.get("/api/license/machine-id")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "machine_id" in data
        assert "platform" in data
        assert "generated_at" in data
        assert len(data["machine_id"]) == 32
    
    def test_get_license_status_not_activated(self, client, tmp_path, monkeypatch):
        """测试获取状态：未激活"""
        from license import validator
        
        # 确保没有 License 文件
        test_license_file = tmp_path / ".license"
        monkeypatch.setattr(validator, "_LICENSE_FILE_PATHS", [test_license_file])
        
        response = client.get("/api/license/status")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["is_valid"] is False
        assert data["is_activated"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
