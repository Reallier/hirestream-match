"""
License API 自动化测试
测试 License 生成、验证等核心功能
"""
import pytest
import httpx
import os
from datetime import datetime, timedelta

# 测试环境配置
API_BASE_URL = os.getenv("TEST_API_URL", "https://api.talentai.intjsys.com")

# 测试数据
TEST_CUSTOMER = "自动化测试公司"
TEST_MACHINE_ID = "test-machine-id-12345678"


class TestLicenseAPI:
    """License API 测试套件"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """测试前准备"""
        self.client = httpx.Client(base_url=API_BASE_URL, timeout=30.0)
        yield
        self.client.close()
    
    def test_01_get_machine_id(self):
        """测试获取服务器机器指纹"""
        response = self.client.get("/api/license/machine-id")
        
        assert response.status_code == 200, f"获取机器指纹失败: {response.text}"
        
        data = response.json()
        assert "machine_id" in data, "响应缺少 machine_id 字段"
        assert "platform" in data, "响应缺少 platform 字段"
        assert "generated_at" in data, "响应缺少 generated_at 字段"
        
        # 验证 machine_id 格式 (32位十六进制)
        machine_id = data["machine_id"]
        assert len(machine_id) == 32, f"machine_id 长度应为 32，实际为 {len(machine_id)}"
        assert machine_id.isalnum(), "machine_id 应为字母数字"
        
        print(f"✓ 机器指纹: {machine_id}")
        print(f"✓ 平台: {data['platform']}")
        
        # 保存 machine_id 供后续测试使用
        self.__class__.server_machine_id = machine_id
    
    def test_02_get_license_status_not_activated(self):
        """测试未激活状态下的 License 状态查询"""
        response = self.client.get("/api/license/status")
        
        assert response.status_code == 200, f"获取 License 状态失败: {response.text}"
        
        data = response.json()
        assert "is_valid" in data, "响应缺少 is_valid 字段"
        assert "is_activated" in data, "响应缺少 is_activated 字段"
        
        print(f"✓ License 状态: is_valid={data['is_valid']}, is_activated={data['is_activated']}")
    
    def test_03_generate_license_success(self):
        """测试生成 License（核心功能）"""
        payload = {
            "customer": TEST_CUSTOMER,
            "machine_id": TEST_MACHINE_ID,
            "edition": "professional",
            "days": 365
        }
        
        response = self.client.post("/api/license/generate", json=payload)
        
        assert response.status_code == 200, f"生成 License 失败: {response.text}"
        
        data = response.json()
        assert data.get("success") is True, f"生成失败: {data.get('message')}"
        assert "license_key" in data, "响应缺少 license_key 字段"
        assert "lic_id" in data, "响应缺少 lic_id 字段"
        assert "expires_at" in data, "响应缺少 expires_at 字段"
        
        # 验证 License Key 是 JWT 格式 (三段，点分隔)
        license_key = data["license_key"]
        parts = license_key.split(".")
        assert len(parts) == 3, f"License Key 应为 JWT 格式 (3段)，实际为 {len(parts)} 段"
        
        # 验证 License ID 格式
        lic_id = data["lic_id"]
        assert lic_id.startswith("LIC-"), f"License ID 应以 LIC- 开头，实际为: {lic_id}"
        
        # 验证过期时间
        expires_at = datetime.fromisoformat(data["expires_at"].replace("Z", "+00:00"))
        expected_expires = datetime.now().astimezone() + timedelta(days=365)
        delta = abs((expires_at - expected_expires).days)
        assert delta <= 1, f"过期时间偏差超过 1 天: {delta} 天"
        
        print(f"✓ License ID: {lic_id}")
        print(f"✓ 过期时间: {expires_at.strftime('%Y-%m-%d')}")
        print(f"✓ License Key 长度: {len(license_key)} 字符")
        
        # 保存供后续测试使用
        self.__class__.generated_license_key = license_key
        self.__class__.generated_lic_id = lic_id
    
    def test_04_generate_license_with_email(self):
        """测试生成 License 并指定客户邮箱"""
        payload = {
            "customer": "邮件测试公司",
            "machine_id": "email-test-machine-id",
            "edition": "standard",
            "days": 30,
            "customer_email": "test@example.com"  # 不会真的发送（需要有效邮箱）
        }
        
        response = self.client.post("/api/license/generate", json=payload)
        
        assert response.status_code == 200, f"生成 License 失败: {response.text}"
        
        data = response.json()
        assert data.get("success") is True, f"生成失败: {data.get('message')}"
        # email_sent 可能为 False（因为是测试邮箱）
        assert "email_sent" in data, "响应缺少 email_sent 字段"
        
        print(f"✓ 邮件发送状态: {data.get('email_sent')}")
    
    def test_05_generate_license_missing_fields(self):
        """测试生成 License 缺少必填字段"""
        # 缺少 customer
        payload = {
            "machine_id": TEST_MACHINE_ID,
            "edition": "professional",
            "days": 365
        }
        
        response = self.client.post("/api/license/generate", json=payload)
        
        assert response.status_code == 422, f"应返回 422 错误，实际返回: {response.status_code}"
        print("✓ 缺少 customer 字段正确返回 422 错误")
    
    def test_06_generate_license_invalid_edition(self):
        """测试生成 License 使用无效版本"""
        payload = {
            "customer": TEST_CUSTOMER,
            "machine_id": TEST_MACHINE_ID,
            "edition": "invalid_edition",  # 无效版本
            "days": 365
        }
        
        response = self.client.post("/api/license/generate", json=payload)
        
        assert response.status_code == 422, f"应返回 422 错误，实际返回: {response.status_code}"
        print("✓ 无效版本正确返回 422 错误")
    
    def test_07_generate_license_all_editions(self):
        """测试所有版本的 License 生成"""
        editions = ["standard", "professional", "enterprise", "flagship"]
        
        for edition in editions:
            payload = {
                "customer": f"{edition.capitalize()} 测试客户",
                "machine_id": f"test-{edition}-machine",
                "edition": edition,
                "days": 90
            }
            
            response = self.client.post("/api/license/generate", json=payload)
            
            assert response.status_code == 200, f"生成 {edition} 版 License 失败: {response.text}"
            
            data = response.json()
            assert data.get("success") is True, f"{edition} 版生成失败"
            
            print(f"✓ {edition.upper()} 版本生成成功")
    
    def test_08_health_check(self):
        """测试健康检查接口"""
        response = self.client.get("/health")
        
        assert response.status_code == 200, f"健康检查失败: {response.text}"
        
        data = response.json()
        assert data.get("status") == "healthy", f"服务状态异常: {data}"
        
        print("✓ 服务健康检查通过")


class TestLicenseAPIPerformance:
    """License API 性能测试"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """测试前准备"""
        self.client = httpx.Client(base_url=API_BASE_URL, timeout=30.0)
        yield
        self.client.close()
    
    def test_generate_license_response_time(self):
        """测试 License 生成响应时间"""
        import time
        
        payload = {
            "customer": "性能测试公司",
            "machine_id": "perf-test-machine-id",
            "edition": "professional",
            "days": 365
        }
        
        start_time = time.time()
        response = self.client.post("/api/license/generate", json=payload)
        elapsed = time.time() - start_time
        
        assert response.status_code == 200, f"请求失败: {response.text}"
        assert elapsed < 5.0, f"响应时间超过 5 秒: {elapsed:.2f}s"
        
        print(f"✓ License 生成响应时间: {elapsed:.2f}s")


if __name__ == "__main__":
    # 直接运行时使用 pytest
    pytest.main([__file__, "-v", "--tb=short"])
