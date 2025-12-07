# 整体架构

HireStream Match 是一个基于 LLM 的智能简历匹配系统。

## 系统架构图

```mermaid
graph TB
    subgraph Frontend["前端层"]
        UI[Streamlit Web UI]
    end
    
    subgraph Backend["业务层"]
        APP[app.py<br>主应用]
        AUTH[auth.py<br>认证模块]
        USER[user_service.py<br>用户服务]
        MATCH[match_engine.py<br>匹配引擎]
        OCR[qwen_pdf_ocr.py<br>OCR模块]
        PRICE[pricing_config.py<br>定价配置]
        CALC[token_calculator.py<br>费用计算]
    end
    
    subgraph Data["数据层"]
        DB[(SQLite/PostgreSQL)]
    end
    
    subgraph External["外部服务"]
        QWEN[阿里云<br>Qwen-3 Max]
        VL[阿里云<br>Qwen-VL-OCR]
    end
    
    UI --> APP
    APP --> AUTH
    APP --> USER
    APP --> MATCH
    APP --> OCR
    
    USER --> DB
    
    MATCH --> QWEN
    MATCH --> PRICE
    MATCH --> CALC
    
    OCR --> VL
    OCR --> PRICE
    OCR --> CALC
```

---

## 技术栈

| 层级 | 技术 | 版本 | 说明 |
|------|------|------|------|
| **前端** | Streamlit | 1.51 | 低代码 Web 应用框架 |
| **后端** | Python | 3.13 | 主语言 |
| **ORM** | SQLAlchemy | 2.0 | 数据库抽象层 |
| **数据库** | SQLite / PostgreSQL | - | 开发用 SQLite，生产用 PostgreSQL |
| **认证** | PyJWT | 2.x | JWT Token 处理 |
| **LLM** | Qwen-3 Max | - | JD-简历匹配分析 |
| **OCR** | Qwen-VL-OCR | - | PDF/图片文字识别 |
| **PDF** | PyMuPDF | - | PDF 渲染和处理 |
| **日志** | Loguru | - | 结构化日志 |
| **包管理** | UV | - | 快速依赖管理 |

---

## 模块依赖关系

```mermaid
graph LR
    subgraph Core["核心模块"]
        APP[app.py]
        MATCH[match_engine.py]
        OCR[qwen_pdf_ocr.py]
    end
    
    subgraph User["用户模块"]
        AUTH[auth.py]
        USER[user_service.py]
        MODELS[models.py]
        DB[database.py]
    end
    
    subgraph Pricing["计费模块"]
        PRICE[pricing_config.py]
        CALC[token_calculator.py]
    end
    
    subgraph Utils["工具模块"]
        UTILS[utils.py]
        LOG[log.py]
    end
    
    APP --> MATCH
    APP --> AUTH
    APP --> USER
    APP --> CALC
    
    MATCH --> OCR
    MATCH --> CALC
    
    OCR --> CALC
    
    USER --> MODELS
    USER --> DB
    USER --> AUTH
    
    CALC --> PRICE
    
    MATCH --> LOG
    OCR --> LOG
    USER --> LOG
```

---

## 核心流程

### 完整请求处理流程

```mermaid
sequenceDiagram
    participant U as 用户
    participant App as app.py
    participant Auth as auth.py
    participant User as user_service
    participant Match as match_engine
    participant OCR as qwen_pdf_ocr
    participant LLM as 阿里云 API
    participant DB as 数据库

    U->>App: 访问页面 (?mock_user=xxx)
    App->>Auth: authenticate_user()
    Auth-->>App: UserInfo
    App->>User: get_or_create_user()
    User->>DB: 查询/创建用户
    DB-->>User: User
    User-->>App: user_summary
    
    Note over App: 显示侧边栏（余额、统计）
    
    U->>App: 上传简历 + 粘贴 JD
    App->>User: check_balance()
    User->>DB: 查询余额
    
    alt 余额不足
        User-->>App: insufficient
        App-->>U: 提示充值
    else 余额充足
        App->>OCR: extract_text_from_upload()
        OCR->>LLM: 调用 Qwen-VL-OCR
        LLM-->>OCR: OCR 结果 + Token
        OCR-->>App: 简历文本 + 用量
        
        App->>Match: call_qwen_json()
        Match->>LLM: 调用 Qwen-3 Max
        LLM-->>Match: 分析结果 + Token
        Match-->>App: 匹配报告 + 用量
        
        App->>User: record_usage() × 2
        App->>User: deduct_balance()
        User->>DB: 更新余额 + 记录流水
        
        App-->>U: 显示匹配结果 + 费用
    end
```

---

## 目录结构

```
hirestream-match/
├── app.py                 # Streamlit 主应用入口
├── match_engine.py        # 核心匹配引擎
├── qwen_pdf_ocr.py       # PDF/图片 OCR 处理
├── utils.py              # 工具函数
├── log.py                # 日志配置
│
├── auth.py               # JWT 认证模块
├── user_service.py       # 用户服务层
├── models.py             # SQLAlchemy 模型
├── database.py           # 数据库连接
│
├── pricing_config.py     # 模型定价配置
├── token_calculator.py   # Token 费用计算
│
├── .env                  # 环境配置
├── pyproject.toml        # 项目依赖
├── Dockerfile            # Docker 配置
│
├── data/                 # 数据目录
│   └── hirestream.db    # SQLite 数据库
│
├── docs/                 # 项目文档
│   ├── architecture/    # 架构文档
│   ├── modules/         # 模块文档
│   ├── deployment/      # 部署文档
│   └── roadmap/         # 路线规划
│
└── logs/                 # 运行日志
```

---

## 相关文档

- [数据库设计](database.md)
- [认证流程](auth-flow.md)
- [用户模块](../modules/user.md)
- [计费定价](../modules/pricing.md)
