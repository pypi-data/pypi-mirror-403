"""配置管理模块.

通过环境变量提供可配置的设置，支持运行时行为调整。

环境变量：
    SKILL_CREATOR_LOG_LEVEL: 日志级别 (DEBUG/INFO/WARNING/ERROR/CRITICAL)，默认 INFO
    SKILL_CREATOR_LOG_FORMAT: 日志格式 (default/simple/detailed)，默认 default
    SKILL_CREATOR_LOG_FILE: 日志文件路径（可选），默认输出到 stderr
    SKILL_CREATOR_OUTPUT_DIR: 默认输出目录
        - 由 init_skill, package_skill, package_agent_skill 使用
        - 优先级：工具参数 > 环境变量 > 默认值 "."
        - 默认值：当前目录（MCP Server 启动目录）
        - 推荐：设置为绝对路径如 ~/my-skills
    SKILL_CREATOR_MAX_RETRIES: 最大重试次数，默认 3
    SKILL_CREATOR_TIMEOUT_SECONDS: 操作超时时间（秒），默认 30
"""

import os
from pathlib import Path
from typing import Literal

# 类型定义
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
LogFormat = Literal["default", "simple", "detailed"]


class Config:
    """配置类，从环境变量读取设置."""

    def __init__(self) -> None:
        """初始化配置，从环境变量读取所有设置."""
        # 日志配置
        # 默认值已提供，但类型检查器无法推断 Literal 类型
        self._log_level: LogLevel = os.getenv(  # type: ignore[assignment]
            "SKILL_CREATOR_LOG_LEVEL", "INFO"
        )
        self._log_format: LogFormat = os.getenv(  # type: ignore[assignment]
            "SKILL_CREATOR_LOG_FORMAT", "default"
        )
        self._log_file: str | None = os.getenv("SKILL_CREATOR_LOG_FILE")

        # 工作目录配置
        self._output_dir: Path = Path(os.getenv("SKILL_CREATOR_OUTPUT_DIR", "."))

        # 操作配置
        self._max_retries: int = int(os.getenv("SKILL_CREATOR_MAX_RETRIES", "3"))
        self._timeout_seconds: int = int(os.getenv("SKILL_CREATOR_TIMEOUT_SECONDS", "30"))

    @property
    def log_level(self) -> LogLevel:
        """获取日志级别."""
        return self._log_level

    @property
    def log_format(self) -> LogFormat:
        """获取日志格式."""
        return self._log_format

    @property
    def log_file(self) -> str | None:
        """获取日志文件路径."""
        return self._log_file

    @property
    def output_dir(self) -> Path:
        """获取默认输出目录."""
        return self._output_dir

    @property
    def max_retries(self) -> int:
        """获取最大重试次数."""
        return self._max_retries

    @property
    def timeout_seconds(self) -> int:
        """获取操作超时时间（秒）."""
        return self._timeout_seconds

    def validate(self) -> list[str]:
        """验证配置的有效性.

        Returns:
            错误消息列表，如果配置有效则返回空列表
        """
        errors: list[str] = []

        # 验证日志级别
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self._log_level not in valid_levels:
            errors.append(
                f"无效的 SKILL_CREATOR_LOG_LEVEL: {self._log_level}. "
                f"有效值: {', '.join(valid_levels)}"
            )

        # 验证日志格式
        valid_formats = ["default", "simple", "detailed"]
        if self._log_format not in valid_formats:
            errors.append(
                f"无效的 SKILL_CREATOR_LOG_FORMAT: {self._log_format}. "
                f"有效值: {', '.join(valid_formats)}"
            )

        # 验证数值
        if self._max_retries < 0:
            errors.append(f"SKILL_CREATOR_MAX_RETRIES 必须大于等于 0，当前: {self._max_retries}")

        if self._timeout_seconds <= 0:
            errors.append(
                f"SKILL_CREATOR_TIMEOUT_SECONDS 必须大于 0，当前: {self._timeout_seconds}"
            )

        # 验证输出目录
        if self._output_dir.exists() and not self._output_dir.is_dir():
            errors.append(f"SKILL_CREATOR_OUTPUT_DIR 不是目录: {self._output_dir}")

        return errors


# 全局配置单例
_config: Config | None = None


def get_config() -> Config:
    """获取全局配置实例（单例模式）.

    Returns:
        配置实例

    Example:
        >>> from skill_creator_mcp.config import get_config
        >>> config = get_config()
        >>> print(config.log_level)
    """
    global _config
    if _config is None:
        _config = Config()
        # 验证配置
        errors = _config.validate()
        if errors:
            import warnings

            warnings.warn(
                f"配置验证失败: {'; '.join(errors)}",
                stacklevel=2,
            )
    return _config


def reload_config() -> Config:
    """重新加载配置（用于测试或动态更新）.

    Returns:
        新的配置实例
    """
    global _config
    _config = Config()
    return _config


__all__ = [
    "Config",
    "LogLevel",
    "LogFormat",
    "get_config",
    "reload_config",
]
