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

**一页式 · 零学习成本 · 清晰匹配报告 · 隐私安全**

[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/streamlit-1.51-red.svg)](https://streamlit.io)
[![Qwen](https://img.shields.io/badge/powered%20by-Qwen--3%20Max-orange.svg)](https://www.alibabacloud.com/help/zh/model-studio)

</div>

## 📋 项目简介

HireStream Match 是一款基于大语言模型的智能简历匹配工具，专为招聘场景设计。通过先进的 AI 技术，自动分析候选人简历与职位描述的匹配度，并提供详细的评估报告。

**核心特性：**
- 🎯 **精准匹配**：基于 Qwen-3 Max 模型的深度语义理解
- ⚡ **即时分析**：自动触发，无需手动点击，秒级响应
- 📄 **智能OCR**：支持PDF简历的精准文字识别
- 🔒 **隐私保护**：全程内存处理，不落盘，不持久化
- 📊 **可视化报告**：匹配度评分 + 优势/风险分析 + 改进建议
- 🚀 **开箱即用**：极简配置，一键启动


## 🚀 快速开始

### 前置要求

- Python 3.13+
- DashScope API Key（通义千问）

### 方式一：使用 UV（推荐）

```bash
# 1. 克隆项目
git clone <your-repo-url>
cd hirestream-match

# 2. 安装 uv（如未安装）
pip install uv

# 3. 同步依赖
uv sync

# 4. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入你的 DASHSCOPE_API_KEY

# 5. 运行应用
uv run streamlit run app.py
```

### 方式二：传统 pip 安装

```bash
# 1. 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
export DASHSCOPE_API_KEY="你的API密钥"  # Windows: set DASHSCOPE_API_KEY=你的密钥

# 4. 运行应用
streamlit run app.py
```

### 方式三：Docker 部署

```bash
# 1. 构建镜像
docker build -t hirestream-match .

# 2. 运行容器
docker run -p 8501:8501 \
  -e DASHSCOPE_API_KEY="你的API密钥" \
  hirestream-match
```

### 🎮 使用方法

1. **输入职位描述**：在第一个文本框粘贴完整的 JD 内容
2. **上传简历**：选择候选人的 PDF 简历（≤2MB）
3. **查看结果**：系统自动分析并展示匹配报告
   - 匹配度评分（0-100%）
   - 候选人优势列表
   - 潜在风险提示
   - 综合建议

> 💡 **特别提示**：无需点击任何按钮，系统会在 JD 和简历都准备就绪后自动触发分析！

---

## 📁 项目结构

```
hirestream-match/
├── app.py                 # Streamlit 主应用
├── match_engine.py        # 核心匹配引擎（LLM 调用 + 文件解析）
├── qwen_pdf_ocr.py       # PDF OCR 处理模块
├── utils.py              # 工具函数（哈希、报告渲染）
├── log.py                # 日志配置
├── .env                  # 环境配置文件
├── pyproject.toml        # 项目依赖（UV 管理）
├── Dockerfile            # Docker 部署配置
└── logs/                 # 运行日志目录
```

---

## ⚙️ 技术栈

| 模块 | 技术 | 说明 |
|------|------|------|
| **前端框架** | Streamlit 1.51 | 低代码 Web 应用 |
| **LLM 模型** | Qwen-3 Max | 阿里云通义千问 |
| **PDF 处理** | PyMuPDF + OCR | 高精度文字提取 |
| **API 调用** | DashScope SDK | 官方推荐接口 |
| **日志系统** | Loguru | 结构化日志 |
| **依赖管理** | UV | 快速依赖解析 |

---

## 🔧 配置说明

### 环境变量详解

在 [`.env`](.env) 文件中配置以下参数：

```bash
# ===== API 密钥 =====
DASHSCOPE_API_KEY=your-api-key-here

# ===== 模型配置 =====
QWEN_MODEL=qwen3-max             # 可选: qwen-max, qwen2.5-72b-instruct

# ===== 系统提示词 =====
SYSTEM_PROMPT="你是一位资深猎头与人才评估专家..."

# ===== 用户模板 =====
USER_TEMPLATE=【职位描述】{job_description}【候选人简历】{resume_content}
```

### 核心参数调优

| 参数 | 位置 | 默认值 | 说明 |
|------|------|--------|------|
| `timeout` | [`match_engine.py:85`](match_engine.py:85) | 10秒 | API 调用超时时间 |
| `retries` | [`match_engine.py:59`](match_engine.py:59) | 1次 | 失败重试次数 |
| `temperature` | [`match_engine.py:48`](match_engine.py:48) | 0.2 | 模型创造性（0-1） |
| `max_tokens` | [`match_engine.py:49`](match_engine.py:49) | 800 | 最大输出长度 |
| `dpi` | [`qwen_pdf_ocr.py:27`](qwen_pdf_ocr.py:27) | 400 | PDF 渲染精度 |

---

## 🎯 核心功能设计

### 1. 智能防抖机制

使用 SHA256 哈希计算输入变化，避免重复调用：

```python
# utils.py
def hash_inputs(jd_text: str, resume_text: str) -> str:
    """计算输入哈希，用于缓存判断"""
```

### 2. 严谨的评分算法

基于 `.env` 中的 [`SYSTEM_PROMPT`](.env:5-58)，模型遵循以下规则：

- **淘汰机制**：任一必需项不满足 → 评分 ≤25%
- **封顶限制**：证据不足或仅相当 → 评分 ≤65%
- **溢价加分**：显著超配 → +0~10分（总分≤95）

### 3. 隐私保护设计

- ✅ 所有文件纯内存处理，不写入磁盘
- ✅ 不记录用户上传内容
- ✅ Session 结束后数据自动清除
- ✅ 日志中敏感信息自动脱敏

### 4. 自动重试与容错

```python
# match_engine.py
for attempt in range(retries + 1):
    try:
        content = _call_dashscope_via_openai(messages, model, timeout)
        # 鲁棒的 JSON 提取与数据规范化
        result = _normalize_result(json.loads(_extract_json(content)))
        return result
    except Exception as e:
        if attempt < retries:
            time.sleep(0.8)
            continue
```

---

## 📊 输出格式

系统返回标准化的 JSON 结构：

```json
{
  "match_score": 75,
  "advantages": [
    "5年云原生架构经验，深度熟悉 K8s 与微服务",
    "曾主导千万级用户平台的性能优化"
  ],
  "risks": [
    "缺少 JD 要求的金融行业经验",
    "未明确提及 DevOps 工具链（Jenkins/GitLab CI）"
  ],
  "advice": "技术能力匹配度高，但需补充行业经验，建议面试深入考察业务理解能力。"
}
```

---

## 🔍 高级用法

### 自定义评估维度

修改 [`.env`](.env) 中的 `SYSTEM_PROMPT`，添加行业特定的评估标准：

```bash
SYSTEM_PROMPT="...
额外维度：
- 金融合规：是否有 SOC2/PCI-DSS 认证经验
- 出海能力：是否有海外产品运营经验
..."
```

### 批量处理（开发中）

```python
# 伪代码示例
for resume_file in resume_list:
    result = match_engine.analyze(jd_text, resume_file)
    results.append(result)
export_to_excel(results)
```

---

## 📈 性能基准

在典型硬件配置下（8核 CPU，16GB RAM）：

| 指标 | 数值 |
|------|------|
| PDF 解析速度 | ~2秒/页 |
| LLM 分析耗时 | 3-8秒 |
| 内存占用 | <500MB |
| 并发支持 | 单进程 |

---

## 🛠️ 开发指南

### 运行测试

```bash
# 单元测试（待实现）
pytest tests/

# 日志查看
tail -f logs/app.log
```

### 代码规范

- 遵循 PEP 8 风格指南
- 使用 Type Hints 标注类型
- 核心函数添加详细 Docstring

---

## 🚧 Roadmap

### v1.1（计划中）
- [ ] 内置岗位模板（技术/销售/设计）
- [ ] 支持 DOCX 和 TXT 简历格式
- [ ] 添加历史记录功能

### v1.2（规划中）
- [ ] 雷达图可视化
- [ ] PDF 报告导出
- [ ] 对比模式（多候选人横向对比）

### v2.0（蓝图）
- [ ] 批量上传与异步处理
- [ ] 数据导出（CSV/Excel）
- [ ] API 接口封装

### v3.0（愿景）
- [ ] 多租户 SaaS 版本
- [ ] 用户认证与权限管理
- [ ] 审计日志与合规增强

---

## ❓ 常见问题

<details>
<summary><b>Q: 支持哪些简历格式？</b></summary>

目前仅支持 PDF 格式，大小限制 2MB。后续版本将支持 DOCX 和 TXT。
</details>

<details>
<summary><b>Q: 为什么匹配度低于预期？</b></summary>

系统采用严格的评分标准，必需项不满足会大幅降分。请检查简历是否明确体现了 JD 中的硬性要求。
</details>

<details>
<summary><b>Q: 如何获取 DashScope API Key？</b></summary>

访问 [阿里云 Model Studio](https://www.alibabacloud.com/help/zh/model-studio) 注册并创建应用。
</details>

<details>
<summary><b>Q: 可以本地部署吗？</b></summary>

完全可以！使用 Docker 或直接运行均支持内网部署，无需外部连接（需有 API 访问权限）。
</details>

---

## 📄 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

---

## ⚠️ 免责声明

1. **仅供参考**：本工具使用生成式 AI 技术，结果存在不确定性，应作为辅助工具而非唯一决策依据。
2. **隐私合规**：实际生产环境部署需遵循当地数据保护法规（如 GDPR、PIPL）。
3. **商业使用**：如需商业使用，请确保符合 DashScope 服务条款。

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

### 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## 📞 联系方式

- 项目维护者：HireStream Team
- 问题反馈：[GitHub Issues](https://github.com/your-repo/issues)

---

<div align="center">

**🌟 如果这个项目对你有帮助，请给个 Star！🌟**

Made with ❤️ by HireStream Team | Powered by Qwen-3 Max

</div>
