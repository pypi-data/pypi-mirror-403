"""日志配置模块.

为 skill-creator-mcp 提供统一的日志配置。
支持通过环境变量自定义日志行为。
"""

import logging
import sys
from pathlib import Path
from typing import Literal

# 日志级别字面量
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

# 默认日志格式
DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# 简洁日志格式（用于生产环境）
SIMPLE_FORMAT = "%(levelname)s - %(message)s"

# 详细日志格式（用于开发环境）
DETAILED_FORMAT = (
    "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s"
)


def setup_logging(
    level: LogLevel = "INFO",
    log_file: str | None = None,
    format_type: Literal["default", "simple", "detailed"] = "default",
) -> None:
    """配置日志系统.

    Args:
        level: 日志级别 (DEBUG/INFO/WARNING/ERROR/CRITICAL)
        log_file: 日志文件路径（可选，默认输出到控制台）
        format_type: 日志格式类型
    """
    # 选择格式
    if format_type == "simple":
        log_format = SIMPLE_FORMAT
    elif format_type == "detailed":
        log_format = DETAILED_FORMAT
    else:
        log_format = DEFAULT_FORMAT

    # 配置 root logger
    logging.basicConfig(
        level=getattr(logging, level),
        format=log_format,
        stream=sys.stderr,
        force=True,
    )

    # 如果指定了日志文件，添加文件处理器
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setLevel(getattr(logging, level))
        file_handler.setFormatter(logging.Formatter(log_format))

        root_logger = logging.getLogger()
        root_logger.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """获取指定名称的 logger.

    Args:
        name: logger 名称，通常使用 __name__

    Returns:
        配置好的 logger 实例

    Example:
        >>> from skill_creator_mcp.logging_config import get_logger
        >>> logger = get_logger(__name__)
        >>> logger.info("Processing skill: %s", skill_path)
    """
    return logging.getLogger(name)


# 创建模块级别的 logger
logger = get_logger(__name__)

__all__ = [
    "setup_logging",
    "get_logger",
    "logger",
    "LogLevel",
]
