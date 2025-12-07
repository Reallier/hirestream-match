# 版本更新记录

本文档记录 HireStream Match 的版本历史和重要变更。

---

## [0.2.0] - 2024-12-07

### ✨ 新增功能

- **用户模块**
  - 用户认证：支持 JWT Token 和 Mock 模式
  - 账户管理：余额查询、免费额度
  - 使用统计：调用次数、Token 消耗、费用统计
  - 预付费扣款：优先使用免费额度

- **数据库支持**
  - SQLite 存储（开发环境）
  - SQLAlchemy ORM 抽象
  - 三表结构：users, usage_records, transactions

- **UI 增强**
  - 侧边栏用户信息显示
  - 实时余额和统计展示
  - 余额不足提示

### 📁 新增文件

- `database.py` - 数据库连接和初始化
- `models.py` - SQLAlchemy 模型定义
- `auth.py` - JWT 认证模块
- `user_service.py` - 用户业务逻辑
- `docs/` - 项目文档目录

### ⚙️ 配置变更

新增环境变量：
```bash
JWT_SECRET=...           # JWT 签名密钥
JWT_ALGORITHM=HS256      # 签名算法
USER_AUTH_MODE=mock      # 认证模式
DEFAULT_FREE_QUOTA=1.0   # 新用户免费额度
DATABASE_URL=sqlite:///./data/hirestream.db
```

---

## [0.1.0] - 2024-12-06

### ✨ 新增功能

- **Token 计费系统**
  - 多模型定价配置
  - 阶梯计费支持（Qwen3-Max）
  - 固定计费支持（Qwen-VL-OCR）
  - 费用明细 UI 展示

### 📁 新增文件

- `pricing_config.py` - 模型定价配置
- `token_calculator.py` - Token 费用计算器

---

## [0.0.1] - 初始版本

### ✨ 核心功能

- **智能匹配**：基于 Qwen-3 Max 的 JD-简历匹配分析
- **OCR 识别**：支持 PDF 和图片格式简历
- **自动触发**：输入变化自动分析，无需手动点击
- **可视化报告**：匹配度评分 + 优势/风险分析

### 📁 核心文件

- `app.py` - Streamlit 主应用
- `match_engine.py` - 匹配引擎
- `qwen_pdf_ocr.py` - OCR 处理模块
- `utils.py` - 工具函数
- `log.py` - 日志配置

---

## 版本规范

版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)：

```
MAJOR.MINOR.PATCH

MAJOR: 不兼容的 API 变更
MINOR: 向下兼容的功能新增
PATCH: 向下兼容的问题修复
```
