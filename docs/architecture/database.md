# 数据库设计

本文档描述 HireStream Match 的数据库架构设计。

## 技术选型

| 环境 | 数据库 | 说明 |
|------|--------|------|
| 开发/测试 | SQLite | 轻量、零配置 |
| 生产环境 | PostgreSQL | 高性能、支持并发 |

使用 SQLAlchemy ORM，支持无缝迁移。

---

## ER 关系图

```mermaid
erDiagram
    users ||--o{ usage_records : "has"
    users ||--o{ transactions : "has"
    
    users {
        string user_id PK "来自官网的用户ID"
        string nickname "用户昵称"
        string avatar_url "头像URL"
        float balance "账户余额（元）"
        float free_quota "剩余免费额度（元）"
        datetime created_at "创建时间"
        datetime updated_at "更新时间"
    }
    
    usage_records {
        int id PK "自增主键"
        string user_id FK "用户ID"
        string request_id UK "请求唯一ID"
        string operation "操作类型"
        string model "使用的模型"
        int prompt_tokens "输入Token数"
        int completion_tokens "输出Token数"
        float cost "花费（元）"
        datetime created_at "使用时间"
    }
    
    transactions {
        int id PK "自增主键"
        string user_id FK "用户ID"
        string type "类型"
        float amount "金额"
        float balance_after "交易后余额"
        string reference_id "关联ID"
        string remark "备注"
        datetime created_at "交易时间"
    }
```

---

## 表结构详解

### `users` - 用户表

存储用户基本信息和账户余额。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `user_id` | VARCHAR(64) | PK | 来自官网的用户唯一标识 |
| `nickname` | VARCHAR(100) | | 用户昵称 |
| `avatar_url` | TEXT | | 头像 URL |
| `balance` | FLOAT | NOT NULL, DEFAULT 0 | 账户余额（元） |
| `free_quota` | FLOAT | NOT NULL, DEFAULT 0 | 剩余免费额度（元） |
| `created_at` | DATETIME | | 创建时间 |
| `updated_at` | DATETIME | | 更新时间 |

**索引：**
- `user_id`（主键索引）

**业务逻辑：**
- 新用户自动获得免费额度（默认 ¥1.0）
- `total_available = balance + free_quota`

---

### `usage_records` - 使用记录表

记录每次 API 调用的 Token 消耗和费用。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | INTEGER | PK, AUTO | 自增主键 |
| `user_id` | VARCHAR(64) | FK, NOT NULL | 用户 ID |
| `request_id` | VARCHAR(64) | UNIQUE, NOT NULL | 请求唯一 ID（幂等） |
| `operation` | VARCHAR(20) | NOT NULL | 操作类型：`ocr` / `analysis` |
| `model` | VARCHAR(50) | NOT NULL | 模型名称 |
| `prompt_tokens` | INTEGER | DEFAULT 0 | 输入 Token 数 |
| `completion_tokens` | INTEGER | DEFAULT 0 | 输出 Token 数 |
| `cost` | FLOAT | NOT NULL | 本次花费（元） |
| `created_at` | DATETIME | | 使用时间 |

**索引：**
- `request_id`（唯一索引，用于幂等）
- `user_id`（外键索引）
- `(user_id, created_at)`（复合索引，用于用户历史查询）

**操作类型枚举：**
| 值 | 说明 |
|------|------|
| `ocr` | PDF/图片 OCR 识别 |
| `analysis` | JD-简历匹配分析 |

---

### `transactions` - 交易流水表

记录所有余额变动，包括充值、扣费、退款等。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | INTEGER | PK, AUTO | 自增主键 |
| `user_id` | VARCHAR(64) | FK, NOT NULL | 用户 ID |
| `type` | VARCHAR(20) | NOT NULL | 交易类型 |
| `amount` | FLOAT | NOT NULL | 金额（正=入账，负=出账） |
| `balance_after` | FLOAT | NOT NULL | 交易后余额 |
| `reference_id` | VARCHAR(64) | | 关联 ID |
| `remark` | TEXT | | 备注信息 |
| `created_at` | DATETIME | | 交易时间 |

**索引：**
- `user_id`（外键索引）
- `(user_id, created_at)`（复合索引）

**交易类型枚举：**
| 值 | 说明 | amount |
|------|------|--------|
| `recharge` | 充值 | 正数 |
| `deduct` | 扣费 | 负数 |
| `refund` | 退款 | 正数 |
| `free_grant` | 免费额度发放 | 正数 |

---

## 扣费逻辑

```mermaid
flowchart TD
    A[用户发起请求] --> B{检查余额}
    B -->|不足| C[拒绝请求]
    B -->|充足| D[执行 API 调用]
    D --> E[计算实际费用]
    E --> F{免费额度足够?}
    F -->|是| G[从免费额度扣除]
    F -->|否| H{部分足够?}
    H -->|是| I[先扣免费额度<br>再扣余额]
    H -->|否| J[全部从余额扣除]
    G --> K[记录使用量]
    I --> K
    J --> K
    K --> L[记录交易流水]
    L --> M[返回结果]
```

**优先级规则：**
1. 优先使用免费额度
2. 免费额度不足时，不足部分从余额扣除
3. 余额不足时拒绝请求

---

## 数据库迁移

### SQLite → PostgreSQL

1. **导出数据**
   ```bash
   sqlite3 data/hirestream.db .dump > backup.sql
   ```

2. **修改配置**
   ```bash
   # .env
   DATABASE_URL=postgresql://user:pass@host:5432/hirestream
   ```

3. **初始化新库**
   ```python
   from database import init_db
   init_db()
   ```

4. **导入数据**
   - 使用 `pgloader` 或手动迁移

---

## 相关文件

- [`models.py`](../../models.py) - SQLAlchemy 模型定义
- [`database.py`](../../database.py) - 数据库连接和初始化
- [`user_service.py`](../../user_service.py) - 用户服务层
