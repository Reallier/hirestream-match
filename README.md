---
title: HireStream Match — 简历与 JD 智能匹配助手
emoji: 🧠
colorFrom: blue
colorTo: indigo
sdk: streamlit
app_file: app.py
python_version: "3.13"
pinned: false
---

# HireStream Match — 简历与 JD 智能匹配助手

<div align="center">

**一页式 · 零学习成本 · 清晰匹配报告 · 预付费计费**

[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/streamlit-1.51-red.svg)](https://streamlit.io)
[![Qwen](https://img.shields.io/badge/powered%20by-Qwen--3%20Max-orange.svg)](https://www.alibabacloud.com/help/zh/model-studio)

</div>

## 📋 简介

HireStream Match 是一款基于大语言模型的智能简历匹配工具，专为招聘场景设计。通过先进的 AI 技术，自动分析候选人简历与职位描述的匹配度，并提供详细的评估报告。

**核心特性：**
- 🎯 **精准匹配** — 基于 Qwen-3 Max 模型的深度语义理解
- ⚡ **即时分析** — 自动触发，秒级响应
- 📄 **智能OCR** — 支持 PDF 和图片格式简历
- 💰 **用量计费** — Token 级别的精确计费
- 👤 **用户系统** — 账户余额、免费额度、使用统计

---

## 🚀 快速开始

### 前置要求

- Python 3.13+
- DashScope API Key（通义千问）

### 安装与运行

```bash
# 1. 克隆项目
git clone <your-repo-url>
cd hirestream-match

# 2. 安装依赖（推荐使用 UV）
pip install uv
uv sync

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env，填入 DASHSCOPE_API_KEY

# 4. 运行应用
uv run streamlit run app.py
```

### 访问应用

开发模式（Mock 用户）：
```
http://localhost:8501?mock_user=test_user_001
```

---

## 🎮 使用方法

1. **输入职位描述** — 粘贴完整的 JD 内容
2. **上传简历** — PDF 或图片格式（≤2MB）
3. **查看结果** — 自动分析并展示匹配报告

> 💡 无需点击任何按钮，系统会自动触发分析！

---

## 📁 项目结构

```
hirestream-match/
├── app.py                 # Streamlit 主应用
├── match_engine.py        # 核心匹配引擎
├── qwen_pdf_ocr.py       # PDF/图片 OCR 模块
│
├── auth.py               # 用户认证
├── user_service.py       # 用户服务层
├── models.py             # 数据库模型
├── database.py           # 数据库连接
│
├── pricing_config.py     # 模型定价配置
├── token_calculator.py   # Token 费用计算
│
├── docs/                 # 📚 详细文档
│   ├── architecture/    # 架构设计
│   ├── modules/         # 模块文档
│   └── roadmap/         # 路线规划
│
├── TalentAI/             # 🧑‍💼 人才库子系统（共享 PostgreSQL）
│
└── .env.example          # 环境变量配置示例
```

---

## 📚 详细文档

更多信息请查看 [docs/](docs/) 目录：

| 文档 | 说明 |
|------|------|
| [文档索引](docs/README.md) | 文档导航 |
| [整体架构](docs/architecture/overview.md) | 系统架构图、技术栈 |
| [数据库设计](docs/architecture/database.md) | 表结构、ER 图 |
| [用户模块](docs/modules/user.md) | 认证、计费、统计 |
| [计费定价](docs/modules/pricing.md) | Token 定价策略 |
| [更新记录](docs/roadmap/changelog.md) | 版本历史 |
| [未来规划](docs/roadmap/future.md) | 路线图 |

---

## ⚙️ 配置说明

关键环境变量（`.env`）：

```bash
# API 密钥
DASHSCOPE_API_KEY=your-api-key

# 模型配置
QWEN_MODEL=qwen-max-2025-01-25
OCR_MODEL=qwen-vl-ocr-2025-11-20

# 用户模块
USER_AUTH_MODE=mock              # mock / jwt
DEFAULT_FREE_QUOTA=1.0           # 新用户免费额度（元）

# 数据库（与 TalentAI 共享 PostgreSQL）
# 本地开发: postgresql://talentai:talentai123@localhost:5432/talentai
# Docker:   postgresql://talentai:talentai123@talentai-db:5432/talentai
DATABASE_URL=postgresql://talentai:talentai123@talentai-db:5432/talentai

# JWT（必须与官网 INTJTech_04 保持一致）
JWT_SECRET=your-jwt-secret
JWT_ALGORITHM=HS256
```

> ⚠️ **重要**: 计费数据现在存储在 PostgreSQL 中，与 TalentAI 人才库共享同一数据库实例。
> 表名使用 `hm_` 前缀：`hm_users`, `hm_usage_records`, `hm_transactions`

---

## 📄 许可证

本项目采用 MIT 许可证。

---

<div align="center">

**🌟 如果这个项目对你有帮助，请给个 Star！🌟**

Made with ❤️ by HireStream Team | Powered by Qwen-3 Max

</div>
