# TalentAI 密钥与敏感信息管理

## ⚠️ 安全须知

本项目涉及以下敏感信息，**绝对不能提交到 Git 仓库**：

### 1. RSA 私钥 (`license_private_key.pem`)
- **用途**：签发私有化部署 License
- **风险**：泄露后任何人都能伪造有效 License
- **存放位置**：`~/.talentai-secrets/license_private_key.pem`（不在仓库目录内）
- **备份**：加密存储在安全的密码管理器中

### 2. 环境变量 (`.env`)
- **包含内容**：
  - `DASHSCOPE_API_KEY` - 阿里云 DashScope API 密钥
  - `JWT_SECRET` - JWT 签名密钥（与官网共享）
  - `DATABASE_PASSWORD` - 数据库密码
  - `ADMIN_API_KEY` - 管理员 API 密钥
- **风险**：泄露后可滥用 API、伪造用户身份、访问所有数据
- **正确做法**：
  1. 使用 `.env.example` 作为模板
  2. 复制为 `.env` 并填入实际值
  3. 确保 `.env` 在 `.gitignore` 中

### 3. 认证模式 (`USER_AUTH_MODE`)
- `mock` - **仅限开发测试**，自动信任任何请求
- `jwt` - **生产环境必须**，从 Cookie 验证 JWT
- **风险**：生产环境使用 `mock` 模式将导致任何人都能访问所有数据

## 生产环境检查清单

部署前请确认：

- [ ] `USER_AUTH_MODE=jwt`（不是 `mock`）
- [ ] `JWT_SECRET` 是随机生成的 32+ 位字符串
- [ ] `ADMIN_API_KEY` 已配置且足够复杂
- [ ] 私钥不在仓库目录或任何可公开访问的位置
- [ ] 所有 API Key 与开发环境不同

## 密钥轮换

如果怀疑密钥泄露，立即执行：

1. **DashScope API Key**：在阿里云控制台重新生成
2. **JWT_SECRET**：更换后所有用户需重新登录
3. **RSA 私钥**：重新生成密钥对，更新公钥到所有私有化部署客户端
4. **ADMIN_API_KEY**：更换后更新所有调用方

```bash
# 生成新的 JWT Secret
openssl rand -hex 32

# 生成新的 RSA 密钥对
openssl genrsa -out license_private_key.pem 2048
openssl rsa -in license_private_key.pem -pubout -out license_public_key.pem
```

## 文件位置参考

| 文件 | 开发环境 | 生产环境 |
|------|---------|---------|
| `.env` | `backend/.env` | Docker Compose 环境变量 |
| 私钥 | `~/.talentai-secrets/` | 不部署（仅用于签发） |
| 公钥 | `backend/license/license_public_key.pem` | 打包到镜像中 |
