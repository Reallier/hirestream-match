# HireStream Match — 简历与 JD 智能匹配助手

> 一页式 · 零学习成本 · 清晰匹配报告

本仓库实现了你的PRD（v1.0）：单页三模块（JD输入、简历上传、结果输出），自动触发分析，无需点击按钮。

## 快速开始

1. **准备环境**
   ```bash
   python -m venv .venv && source .venv/bin/activate  # Windows 用 .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **配置API Key**
   - 推荐使用 DashScope（通义千问）密钥：
     ```bash
     export DASHSCOPE_API_KEY="你的key"  # Windows: set DASHSCOPE_API_KEY=你的key
     ```
   - 可选：使用 OpenAI 兼容模式调用 DashScope（国际或北京区域）
     ```bash
     export OPENAI_API_KEY="$DASHSCOPE_API_KEY"
     # 新加坡/国际：
     export OPENAI_BASE_URL="https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
     # 中国（北京）：
     # export OPENAI_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"
     # 可选指定模型（默认 qwen-max 或 qwen3-max）
     export OPENAI_MODEL="qwen3-max"
     ```

3. **运行**
   ```bash
   streamlit run app.py
   ```

4. **使用**
   - 粘贴JD → 上传简历（PDF/DOCX/TXT，≤2MB）→ 自动生成报告。
   - 无需点击，结果区自动出现 Markdown 报告（包含匹配度、优势、风险、建议）。

## 设计要点对齐 PRD

- **极简三区块**：JD输入 / 简历上传 / 结果展示。
- **自动触发**：两端就绪即发起请求；使用输入内容哈希去抖，避免频繁调用。
- **文件解析在内存**：PDF（pdfplumber）、DOCX（python-docx）、TXT（多编码尝试）。
- **隐私**：不落盘，不做持久化；仅驻留内存。
- **失败重试**：模型调用失败自动重试一次（默认1次）。
- **性能**：默认超时10秒（可在 `call_qwen_json(... timeout=10)` 修改）。
- **展示**：Markdown 报告 + 进度条式评分可视化；底部 “Powered by Qwen-3 Max”。

## 可配置项

- 环境变量
  - `DASHSCOPE_API_KEY`：DashScope密钥（推荐）。
  - `OPENAI_BASE_URL`：DashScope的OpenAI兼容端点（见官方文档）。
  - `OPENAI_API_KEY`：若使用OpenAI兼容SDK调用。
  - `QWEN_MODEL` / `OPENAI_MODEL`：例如 `qwen3-max`、`qwen-max`、`qwen2.5-72b-instruct` 等。

## 模型与API说明（官方参考）

- DashScope / Qwen 支持 OpenAI 兼容模式与原生 SDK：参见阿里云 Model Studio 文档。
- 若在国内环境，建议使用北京区域兼容端点；国际环境使用新加坡区域端点。

## 后续版本建议（根据PRD）

- v1.1：内置“岗位模板”下拉（技术/销售/设计），在 `USER_TEMPLATE` 中添加针对性评价维度。
- v1.2：将JSON结果渲染为更丰富的可视化（雷达图/命中缺口表），支持导出PDF。
- v2.0：批量上传与导出（CSV/Excel），需新增后端任务队列与持久化方案。
- v3.0：企业版SaaS，接入登录权限与审计日志；强化隐私合规。

## 许可与声明

- 本项目仅作为演示与加速开发用途，实际部署需遵循当地与公司合规规范。
- 生成式AI存在不确定性，请将结果作为辅助参考，而非唯一决策依据。
