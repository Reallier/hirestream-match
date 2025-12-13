# HireStream-Match 与 TalentAI 融合说明

## 融合概述

本次融合将两个招聘相关的项目整合为一个统一的业务体系：

| 功能 | 定位 | 技术实现 |
|------|------|----------|
| **即时匹配** | 上传简历+JD，立即获取匹配分析（不入库） | 共享 OCR + LLM 模块 |
| **人才库管理** | 简历入库、去重、索引管理 | TalentAI PostgreSQL + pgvector |
| **JD 匹配搜索** | 从人才库中匹配候选人 | TalentAI RAG 双路召回 |

## 项目结构

```
app01-hirestream-match/
├── shared/                      # [NEW] 共享模块
│   ├── __init__.py             # 模块导出
│   ├── qwen_pdf_ocr.py         # PDF/图片 OCR
│   ├── token_calculator.py     # Token 费用计算
│   ├── pricing_config.py       # 模型定价配置
│   ├── llm_client.py           # 统一 LLM 调用客户端
│   └── log.py                  # 共享日志模块
│
├── app.py                      # HireStream Streamlit 应用
├── match_engine.py             # HireStream 匹配引擎
├── ...                         # 其他 HireStream 文件
│
└── TalentAI/                   # TalentAI 人才库系统
    ├── frontend/
    │   ├── index.html          # [UPDATED] 新增"即时匹配"标签页
    │   └── app.js              # [UPDATED] 新增即时匹配 JS 功能
    ├── backend/
    │   ├── main.py             # [UPDATED] 新增 /api/instant-match 端点
    │   ├── requirements.txt    # [UPDATED] 新增共享模块依赖
    │   └── services/           # 业务服务
    └── ...
```

## 新增功能

### 即时匹配 API

**端点**: `POST /api/instant-match`

**功能**: 上传简历文件和职位描述，AI 立即分析匹配度并返回结果。此功能不会将简历入库到人才库。

**请求格式** (multipart/form-data):
- `resume`: 简历文件 (PDF/JPG/PNG/GIF/WEBP)
- `jd`: 职位描述文本

**响应示例**:
```json
{
  "match_score": 75,
  "advantages": [
    "具备3年Python后端开发经验",
    "熟悉FastAPI和PostgreSQL",
    "有微服务架构经验"
  ],
  "risks": [
    "缺乏容器化部署经验",
    "大数据处理经验较少"
  ],
  "advice": "建议候选人补充Docker和Kubernetes相关技能",
  "token_usage": {
    "total_tokens": 3500,
    "cost": 0.0125
  }
}
```

## 启动说明

### 本地开发

1. **启动 TalentAI**:
   ```bash
   cd TalentAI
   docker-compose up -d
   ```

2. **访问前端**: http://localhost:3000
3. **API 文档**: http://localhost:8000/docs

### 生产环境

- **前端**: https://talentai.reallier.top:5443
- **API**: https://api.talentai.reallier.top:5443

## 环境变量

确保在 `TalentAI/backend/.env` 中配置：

```bash
# DashScope API (必需)
DASHSCOPE_API_KEY=sk-your-api-key

# 可选：匹配分析系统提示词
SYSTEM_PROMPT="你是一位资深的HR招聘专家..."
```

## 共享模块说明

共享模块位于 `shared/` 目录，可被两个系统复用：

| 模块 | 功能 |
|------|------|
| `qwen_pdf_ocr.py` | PDF/图片 OCR 识别 (Qwen-VL-OCR) |
| `llm_client.py` | 统一 LLM 调用 (支持 JSON 解析) |
| `token_calculator.py` | Token 费用计算 |
| `pricing_config.py` | 模型定价配置 |

## 后续优化建议

1. **用户系统迁移**: 将 HireStream 的用户认证/计费迁移到 TalentAI
2. **数据库统一**: 考虑将 SQLite 用户数据迁移到 PostgreSQL
3. **入库按钮**: 在即时匹配结果页添加"加入人才库"功能
4. **批量匹配**: 支持批量上传多份简历同时匹配
