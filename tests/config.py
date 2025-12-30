"""
TalentAI 功能测试配置
支持多环境切换: 测试服 / 生产服
"""
import os
from dataclasses import dataclass

@dataclass
class TestConfig:
    """测试环境配置"""
    # API 基础地址
    backend_url: str
    frontend_url: str
    # 测试模式
    readonly: bool = False
    # 超时设置 (秒)
    timeout: int = 60
    # 测试数据
    test_user_id: int = 5
    
# 环境配置
CONFIGS = {
    "test": TestConfig(
        backend_url="https://test.api.talentai.reallier.top:5443",
        frontend_url="https://test.talentai.reallier.top:5443",
        readonly=False,
    ),
    "prod": TestConfig(
        backend_url="https://api.talentai.reallier.top:5443",
        frontend_url="https://talentai.reallier.top:5443",
        readonly=True,  # 生产环境默认只读
    ),
    "local": TestConfig(
        backend_url="http://localhost:8000",
        frontend_url="http://localhost:3000",
        readonly=False,
    ),
}

def get_config(env: str = None) -> TestConfig:
    """获取测试配置"""
    env = env or os.getenv("TEST_ENV", "test")
    return CONFIGS.get(env, CONFIGS["test"])

# 默认配置
config = get_config()
