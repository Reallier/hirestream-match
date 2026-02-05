# TalentAI SSO 问题复盘与测试用例

> 基于 2026-01-02 架构重构中发现的问题

---

## 问题清单

### 1. CORS 配置问题

**问题描述**：后端 CORS 白名单未包含测试环境的完整 URL（带端口 5443）

**现象**：
- 浏览器报错：`Access to fetch blocked by CORS policy: No 'Access-Control-Allow-Origin' header`
- preflight 请求被拒绝

**根因**：
```python
# 错误配置 - 缺少端口
CORS_ORIGINS = [
    "https://talentai.intjsys.com",
]

# 正确配置 - 必须包含端口
CORS_ORIGINS = [
    "https://test.talentai.intjsys.com",
    "https://test.api.talentai.intjsys.com",
]
```

**测试用例**：`TestInfrastructure.test_cors_001_test_env_origins`

---

### 2. JWT_SECRET 未同步

**问题描述**：TalentAI 后端未配置 JWT_SECRET 环境变量，使用默认值导致无法验证官网签发的 Token

**现象**：
- 官网登录后，跳转 TalentAI 显示"未登录"
- 控制台无明显错误

**根因**：
```yaml
# compose.staging.yml - 缺少 JWT_SECRET
environment:
  - DATABASE_URL=...
  # ❌ 缺少 JWT_SECRET
  
# 修复后
environment:
  - DATABASE_URL=...
  - JWT_SECRET=${JWT_SECRET}  # ⚠️ 从安全存储获取，切勿明文写入！
```

**测试用例**：`TestInfrastructure.test_jwt_001_secret_consistency`

---

### 3. JWT Payload 格式（2026 统一标准）

> ⚠️ **2026-01-04 更新**：`intj_` 前缀格式已废弃，统一使用纯整数 `user_id`

**统一格式（2026 标准）**：
```json
{
  "id": 6,
  "user_id": 6,
  "email": "demo@test.com",
  "nickname": "测试用户"
}
```

**解析逻辑（简化后）**：
```python
# 2026 统一标准：纯整数格式
user_id = payload.get("id") or payload.get("user_id")
```

**测试用例**：`TestJWTCompatibility.test_jwt_format_003_unified_integer_user_id`

---

### 4. Cookie 域配置问题

**问题描述**：Cookie 域未设置为 `.reallier.top`，导致跨子域共享失败

**现象**：
- 官网登录后 Cookie 只在当前域可见
- TalentAI 无法读取 Cookie

**正确配置**：
```python
# Python (FastAPI)
response.set_cookie(
    key="auth_token",
    value=token,
    domain=".reallier.top",  # 注意前面的点
    secure=True,
    samesite="lax"
)

# JavaScript (Nuxt)
setCookie(event, 'auth_token', token, {
    domain: '.reallier.top',
    secure: true,
    sameSite: 'lax'
})
```

**测试用例**：`TestSSOFlow.test_sso_001_official_login_sets_cookie`

---

### 5. 前端 API_BASE 配置错误

**问题描述**：前端的 `NUXT_PUBLIC_API_BASE` 缺少端口号

**现象**：
- API 请求发送到错误的地址
- 连接失败或 CORS 错误

**根因**：
```yaml
# 错误配置
- NUXT_PUBLIC_API_BASE=https://test.api.talentai.intjsys.com

# 正确配置
- NUXT_PUBLIC_API_BASE=https://test.api.talentai.intjsys.com
```

---

## 测试矩阵

| 测试场景 | 测试用例 | 验证点 |
|:---|:---|:---|
| CORS 配置 | `test_cors_001_test_env_origins` | Preflight 请求通过 |
| CORS 配置 | `test_cors_002_prod_env_origins` | 生产环境 CORS 正确 |
| JWT 密钥 | `test_jwt_001_secret_consistency` | Token 跨服务验证 |
| SSO 流程 | `test_sso_001_official_login_sets_cookie` | Cookie 域设置 |
| SSO 流程 | `test_sso_002_talentai_recognizes_official_token` | 官网 Token 被识别 |
| SSO 流程 | `test_sso_003_talentai_login_sets_cookie` | Cookie 域设置 |
| SSO 流程 | `test_sso_004_official_recognizes_talentai_token` | TalentAI Token 被识别 |
| JWT 格式 | `test_jwt_format_003_intj_prefix_parsing` | intj_ 前缀解析 |
| 登录 API | `test_auth_001_login_success` | 登录成功 |
| 登录 API | `test_auth_002_login_wrong_password` | 密码错误处理 |
| 登出 API | `test_auth_003_logout` | Cookie 清除 |
| 用户信息 | `test_auth_004_me_without_token` | 未登录返回 |
| 用户信息 | `test_auth_005_me_with_valid_token` | 已登录返回 |

---

## 运行测试

```bash
cd products/app01-hirestream-match

# 运行所有 SSO 测试
pytest tests/test_sso_integration.py -v

# 运行特定测试类
pytest tests/test_sso_integration.py::TestSSOFlow -v

# 运行特定测试
pytest tests/test_sso_integration.py::TestInfrastructure::test_cors_001_test_env_origins -v
```

---

## 环境变量

测试依赖以下环境变量（可选，有默认值）：

| 变量 | 默认值 | 说明 |
|:---|:---|:---|
| `TEST_OFFICIAL_SITE` | https://test.intjtech.reallier.top:5443 | 测试环境官网 |
| `TEST_TALENTAI_FRONTEND` | https://test.talentai.intjsys.com | 测试环境前端 |
| `TEST_TALENTAI_API` | https://test.api.talentai.intjsys.com | 测试环境 API |
| `TEST_USERNAME` | demo | 测试用户 |
| `TEST_PASSWORD` | Test123 | 测试密码 |
| `JWT_SECRET` | (见配置) | JWT 签名密钥 |

---

## 检查清单（部署前）

- [ ] 后端 CORS 配置包含目标域名（含端口）
- [ ] 所有服务使用相同的 JWT_SECRET
- [ ] Cookie 域设置为 `.reallier.top`
- [ ] 前端 API_BASE 配置正确（含端口）
- [ ] JWT Payload 解析兼容两种格式
- [ ] 运行 `pytest tests/test_sso_integration.py` 全部通过
