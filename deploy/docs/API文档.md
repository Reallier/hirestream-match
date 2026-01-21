# TalentAI API 文档

> **版本**：1.0.0 | **更新时间**：2026-01-20

本文档面向需要与 TalentAI 系统进行接口对接的技术开发人员。

---

## 认证方式

所有 API 请求均需要携带 JWT Token 进行身份认证。

### 获取 Token

通过登录接口获取访问令牌：

```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@company.com",
  "password": "your_password"
}
```

**响应**：

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### 使用 Token

在所有后续请求的 Header 中携带 Token：

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

### Token 刷新

Access Token 过期前，使用 Refresh Token 换取新令牌：

```http
POST /api/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

---

## 接口列表

### 即时匹配

**接口**：`POST /api/instant-match`

**功能**：上传简历和职位描述，获取 AI 匹配评分和分析。

**请求格式**：`multipart/form-data`

| 参数 | 类型 | 必填 | 说明 |
|:----|:----|:-----|:-----|
| `jd` | string | ✅ | 职位描述文本 |
| `resume` | file | 二选一 | 简历文件（PDF/JPG/PNG/GIF/WEBP） |
| `resume_text` | string | 二选一 | 简历纯文本内容 |

**请求示例**：

```bash
curl -X POST "http://localhost:8000/api/instant-match" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "jd=我们招聘一位3年以上Python开发经验的后端工程师..." \
  -F "resume=@/path/to/resume.pdf"
```

**响应示例**：

```json
{
  "match_score": 85,
  "advantages": [
    "5年 Python 开发经验，超出岗位要求",
    "有大型互联网公司背景",
    "熟悉 FastAPI 和微服务架构"
  ],
  "risks": [
    "缺乏团队管理经验",
    "薪资预期可能较高"
  ],
  "advice": "候选人技术实力突出，建议优先安排技术面试，重点考察团队协作能力。",
  "token_usage": {
    "prompt_tokens": 2500,
    "completion_tokens": 800,
    "total_tokens": 3300,
    "cost": 0.15
  }
}
```

---

### 候选人管理

#### 简历入库

**接口**：`POST /api/candidates/ingest`

**功能**：将简历入库，自动解析结构化信息。

| 参数 | 类型 | 必填 | 说明 |
|:----|:----|:-----|:-----|
| `resume` | file | ✅ | 简历文件 |

**响应示例**：

```json
{
  "candidate_id": 12345,
  "name": "张三",
  "email": "zhangsan@example.com",
  "phone": "138****8888",
  "is_duplicate": false,
  "message": "简历入库成功"
}
```

#### 候选人列表

**接口**：`GET /api/candidates`

**参数**：

| 参数 | 类型 | 必填 | 说明 |
|:----|:----|:-----|:-----|
| `page` | int | 否 | 页码，默认 1 |
| `page_size` | int | 否 | 每页数量，默认 20 |

**响应示例**：

```json
{
  "total": 156,
  "page": 1,
  "page_size": 20,
  "items": [
    {
      "id": 12345,
      "name": "张三",
      "title": "高级后端工程师",
      "company": "某科技公司",
      "created_at": "2026-01-20T10:30:00Z"
    }
  ]
}
```

#### 候选人详情

**接口**：`GET /api/candidates/{id}`

**响应示例**：

```json
{
  "id": 12345,
  "name": "张三",
  "email": "zhangsan@example.com",
  "phone": "13812345678",
  "experiences": [
    {
      "company": "某科技公司",
      "title": "高级后端工程师",
      "start_date": "2022-03",
      "end_date": "至今",
      "description": "负责核心业务系统开发..."
    }
  ],
  "education": [
    {
      "school": "某大学",
      "degree": "本科",
      "major": "计算机科学",
      "graduation_year": 2018
    }
  ],
  "skills": ["Python", "FastAPI", "PostgreSQL", "Docker"]
}
```

#### 删除候选人

**接口**：`DELETE /api/candidates/{id}`

**响应示例**：

```json
{
  "success": true,
  "message": "候选人已删除"
}
```

---

### 智能搜索

**接口**：`GET /api/search`

**功能**：在人才库中搜索候选人（关键词 + 语义混合搜索）。

| 参数 | 类型 | 必填 | 说明 |
|:----|:----|:-----|:-----|
| `q` | string | ✅ | 搜索关键词 |
| `top_k` | int | 否 | 返回数量，默认 10 |

**请求示例**：

```bash
curl "http://localhost:8000/api/search?q=Python%20后端%205年&top_k=20" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**响应示例**：

```json
{
  "query": "Python 后端 5年",
  "results": [
    {
      "id": 12345,
      "name": "张三",
      "title": "高级后端工程师",
      "score": 0.92,
      "highlights": ["Python", "后端开发", "5年经验"]
    }
  ]
}
```

---

### License 管理

#### 查询授权状态

**接口**：`GET /api/license/status`

**响应示例**：

```json
{
  "is_valid": true,
  "edition": "professional",
  "customer": "某科技有限公司",
  "max_users": 200,
  "current_users": 45,
  "max_concurrency": 20,
  "expires_at": "2027-01-20T00:00:00Z",
  "days_remaining": 365
}
```

#### 获取机器指纹

**接口**：`GET /api/license/machine-id`

**响应示例**：

```json
{
  "machine_id": "a51baa3f4841673cffd3fcbc8052fdc8",
  "platform": "Linux 5.15.0",
  "generated_at": "2026-01-20T06:30:00Z"
}
```

---

### 系统状态

#### 健康检查

**接口**：`GET /health`

**响应示例**：

```json
{
  "status": "healthy",
  "database": "connected",
  "ai_service": "available"
}
```

#### 系统统计

**接口**：`GET /api/stats`

**响应示例**：

```json
{
  "total_candidates": 1560,
  "total_matches_today": 45,
  "token_usage_today": 125000
}
```

---

## 错误码参考

| HTTP 状态码 | 错误码 | 说明 |
|:-----------|:------|:-----|
| 400 | `INVALID_REQUEST` | 请求参数无效 |
| 401 | `UNAUTHORIZED` | 未认证或 Token 过期 |
| 403 | `FORBIDDEN` | 无权限访问该资源 |
| 403 | `LICENSE_EXPIRED` | License 已过期 |
| 403 | `USER_LIMIT_EXCEEDED` | 超出用户数上限 |
| 404 | `NOT_FOUND` | 资源不存在 |
| 422 | `VALIDATION_ERROR` | 数据验证失败 |
| 429 | `RATE_LIMITED` | 请求频率超限 |
| 500 | `INTERNAL_ERROR` | 服务器内部错误 |

**错误响应格式**：

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "职位描述不能为空",
    "details": {
      "field": "jd",
      "reason": "required"
    }
  }
}
```

---

## 请求限制

| 版本 | 并发限制 | 说明 |
|:----|:--------|:-----|
| 标准版 | 5 并发 | 超出将返回 429 错误 |
| 专业版 | 20 并发 | - |
| 企业版 | 50 并发 | - |

建议在客户端实现请求队列机制，避免触发限流。

---

## 技术支持

API 对接问题请联系：

- **邮箱**：support@intjsys.com
- **工单系统**：support.intjsys.com
