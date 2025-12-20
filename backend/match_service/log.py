# log.py
from pathlib import Path
from loguru import logger

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

logger.remove()
logger.add(
    LOG_DIR / "app.log",
    rotation="50 MB",
    retention="14 days",
    compression="gz",
    enqueue=True,
    level="INFO",
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
           "<level>{level: <8}</level> | "
           "<cyan>{name}</cyan>:<cyan>{line}</cyan> - "
           "<level>{message}</level>",
)

__all__ = ["logger"]
