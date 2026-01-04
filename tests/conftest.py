"""
Pytest 配置和共享 Fixtures
"""
import pytest
import httpx
import os
from config import get_config, TestConfig

def pytest_addoption(parser):
    """添加命令行选项"""
    parser.addoption(
        "--env",
        action="store",
        default="test",
        help="测试环境: test, prod, local"
    )
    parser.addoption(
        "--readonly",
        action="store_true",
        default=False,
        help="只读模式（跳过写入操作）"
    )

@pytest.fixture(scope="session")
def test_config(request) -> TestConfig:
    """获取测试配置"""
    env = request.config.getoption("--env")
    config = get_config(env)
    
    # 命令行参数覆盖
    if request.config.getoption("--readonly"):
        config.readonly = True
    
    return config

@pytest.fixture(scope="session")
def backend_client(test_config) -> httpx.Client:
    """后端 API 客户端"""
    client = httpx.Client(
        base_url=test_config.backend_url,
        timeout=test_config.timeout,
        verify=False,  # 测试环境可能使用自签名证书
    )
    yield client
    client.close()

@pytest.fixture(scope="session")
def frontend_client(test_config) -> httpx.Client:
    """前端 API 客户端"""
    client = httpx.Client(
        base_url=test_config.frontend_url,
        timeout=test_config.timeout,
        verify=False,
    )
    yield client
    client.close()

@pytest.fixture
def skip_if_readonly(test_config):
    """跳过只读模式下的写入测试"""
    if test_config.readonly:
        pytest.skip("跳过写入操作（只读模式）")

# 测试数据
@pytest.fixture
def sample_jd():
    """示例职位描述"""
    return """
职位：Python 后端开发工程师
公司：某科技公司
要求：
- 3年以上 Python 开发经验
- 熟悉 FastAPI/Django/Flask 框架
- 熟悉 MySQL/PostgreSQL 数据库
- 了解 Docker/Kubernetes
- 良好的沟通能力和团队协作能力
薪资：20-35K
"""

@pytest.fixture
def sample_resume():
    """示例简历"""
    return """
张三
Python 开发工程师 | 5年经验

联系方式：zhangsan@example.com / 138-xxxx-xxxx

技能专长：
- Python, FastAPI, Django, Flask
- MySQL, PostgreSQL, Redis
- Docker, Kubernetes, CI/CD
- Git, Linux

工作经历：
2020-至今 某科技公司 高级后端开发
- 负责核心业务系统架构设计与开发
- 优化系统性能，QPS 提升 300%
- 带领3人小团队完成多个项目交付

2018-2020 某互联网公司 后端开发
- 参与电商平台后端开发
- 负责支付模块和订单模块

教育背景：
2014-2018 北京大学 计算机科学与技术 本科
"""


@pytest.fixture(scope="session")
def auth_token(test_config, backend_client) -> str:
    """获取认证 Token"""
    import os
    
    username = os.getenv("TEST_USERNAME", "demo")
    password = os.getenv("TEST_PASSWORD", "Test123")
    
    response = backend_client.post("/api/auth/login", json={
        "username": username,
        "password": password
    })
    
    if response.status_code == 200:
        return response.cookies.get("auth_token", "")
    return ""


@pytest.fixture(scope="session")
def admin_auth_token(test_config, backend_client) -> str:
    """获取管理员认证 Token"""
    import os
    
    username = os.getenv("ADMIN_USERNAME", "admin")
    password = os.getenv("ADMIN_PASSWORD", "admin123")
    
    response = backend_client.post("/api/auth/login", json={
        "username": username,
        "password": password
    })
    
    if response.status_code == 200:
        return response.cookies.get("auth_token", "")
    return ""


@pytest.fixture
def test_user_id() -> int:
    """测试用户 ID"""
    import os
    return int(os.getenv("TEST_USER_ID", "6"))
