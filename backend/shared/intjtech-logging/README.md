# INTJTech Unified Logging Library

统一日志库，为所有 INTJTech 服务提供结构化日志支持。

## 安装

```bash
# 从本地安装
pip install -e shared/intjtech-logging

# 带 FastAPI 中间件支持
pip install -e "shared/intjtech-logging[fastapi]"

# 带 Loki 直推支持
pip install -e "shared/intjtech-logging[loki]"
```

## 快速开始

### 1. 初始化日志

```python
from intjtech_logging import setup_logging, get_logger

# 在 main.py 中初始化（只需一次）
setup_logging(
    service_name="app01-hirestream",
    log_level="INFO",
    enable_json=True,  # 生产环境使用 JSON 格式
)

# 获取 logger
logger = get_logger(__name__)
logger.info("Service started")
```

### 2. 使用上下文

```python
from intjtech_logging import LogContext, get_logger

logger = get_logger(__name__)

# 在上下文内的日志自动包含 trace_id 和 user_id
with LogContext(trace_id="abc123", user_id="user_001"):
    logger.info("Processing request")
    # 输出: {"timestamp": "...", "level": "INFO", "trace_id": "abc123", "user_id": "user_001", ...}
```

### 3. FastAPI 中间件

```python
from fastapi import FastAPI
from intjtech_logging import setup_logging
from intjtech_logging.middleware import LoggingMiddleware

app = FastAPI()

# 初始化日志
setup_logging(service_name="my-service")

# 添加中间件
app.add_middleware(LoggingMiddleware)
```

中间件自动：
- 生成/传递 `X-Trace-ID` header
- 记录请求开始/结束
- 计算请求耗时
- 从 JWT 提取 user_id

## 日志格式

JSON 格式输出示例：

```json
{
  "timestamp": "2025-12-25T16:00:00.123",
  "level": "INFO",
  "service": "app01-hirestream",
  "logger": "app.api.routes",
  "trace_id": "abc123def456",
  "user_id": "user_001",
  "message": "Request completed",
  "method": "POST",
  "path": "/api/match",
  "status_code": 200,
  "duration_ms": 234.5
}
```

## 与 Loki 集成

```python
setup_logging(
    service_name="my-service",
    loki_url="http://43.136.53.213:3100",  # 监控服务器地址
)
```
