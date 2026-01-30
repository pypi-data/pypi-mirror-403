"""测试配置模块."""

import os
from pathlib import Path

import pytest

from skill_creator_mcp.config import Config, LogFormat, LogLevel, get_config, reload_config


@pytest.fixture(autouse=True)
def clear_env() -> None:
    """每个测试前清除环境变量."""
    # 保存原始环境变量
    original_env = os.environ.copy()
    # 清除相关环境变量
    for key in list(os.environ.keys()):
        if key.startswith("SKILL_CREATOR_"):
            del os.environ[key]

    yield

    # 恢复原始环境变量
    os.environ.clear()
    os.environ.update(original_env)

    # 重新加载配置
    reload_config()


# ==================== Config 基础测试 ====================


def test_config_default_values():
    """测试配置的默认值."""
    config = Config()

    assert config.log_level == "INFO"
    assert config.log_format == "default"
    assert config.log_file is None
    assert config.output_dir == Path(".")
    assert config.max_retries == 3
    assert config.timeout_seconds == 30


def test_config_from_env():
    """测试从环境变量读取配置."""
    os.environ["SKILL_CREATOR_LOG_LEVEL"] = "DEBUG"
    os.environ["SKILL_CREATOR_LOG_FORMAT"] = "simple"
    os.environ["SKILL_CREATOR_LOG_FILE"] = "/tmp/test.log"
    os.environ["SKILL_CREATOR_OUTPUT_DIR"] = "/tmp/output"
    os.environ["SKILL_CREATOR_MAX_RETRIES"] = "5"
    os.environ["SKILL_CREATOR_TIMEOUT_SECONDS"] = "60"

    config = Config()

    assert config.log_level == "DEBUG"
    assert config.log_format == "simple"
    assert config.log_file == "/tmp/test.log"
    assert config.output_dir == Path("/tmp/output")
    assert config.max_retries == 5
    assert config.timeout_seconds == 60


def test_config_invalid_log_level():
    """测试无效的日志级别."""
    os.environ["SKILL_CREATOR_LOG_LEVEL"] = "INVALID"

    config = Config()
    errors = config.validate()

    assert len(errors) > 0
    assert any("无效的 SKILL_CREATOR_LOG_LEVEL" in e for e in errors)


def test_config_invalid_log_format():
    """测试无效的日志格式."""
    os.environ["SKILL_CREATOR_LOG_FORMAT"] = "json"

    config = Config()
    errors = config.validate()

    assert len(errors) > 0
    assert any("无效的 SKILL_CREATOR_LOG_FORMAT" in e for e in errors)


def test_config_invalid_max_retries():
    """测试无效的最大重试次数."""
    os.environ["SKILL_CREATOR_MAX_RETRIES"] = "-1"

    config = Config()
    errors = config.validate()

    assert len(errors) > 0
    assert any("MAX_RETRIES 必须大于等于 0" in e for e in errors)


def test_config_invalid_timeout():
    """测试无效的超时时间."""
    os.environ["SKILL_CREATOR_TIMEOUT_SECONDS"] = "0"

    config = Config()
    errors = config.validate()

    assert len(errors) > 0
    assert any("TIMEOUT_SECONDS 必须大于 0" in e for e in errors)


def test_config_invalid_output_dir():
    """测试无效的输出目录（指向文件而非目录）."""
    import tempfile

    with tempfile.NamedTemporaryFile(delete=False) as f:
        os.environ["SKILL_CREATOR_OUTPUT_DIR"] = f.name

    config = Config()
    errors = config.validate()

    assert len(errors) > 0
    assert any("不是目录" in e for e in errors)

    # 清理
    os.unlink(f.name)


def test_config_valid_output_dir_exists():
    """测试已存在的输出目录."""
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ["SKILL_CREATOR_OUTPUT_DIR"] = tmpdir

        config = Config()
        errors = config.validate()

        # 应该没有错误
        assert len(errors) == 0


def test_config_output_dir_not_exists():
    """测试不存在的输出目录（不应该报错，因为可以创建）."""
    os.environ["SKILL_CREATOR_OUTPUT_DIR"] = "/tmp/skill_creator_test_xyz"

    config = Config()
    errors = config.validate()

    # 不存在的目录不应该报错
    assert len(errors) == 0


# ==================== get_config 单例测试 ====================


def test_get_config_singleton():
    """测试 get_config 返回单例."""
    config1 = get_config()
    config2 = get_config()

    assert config1 is config2


def test_get_config_with_env():
    """测试 get_config 读取环境变量."""
    # 重新加载配置以清除单例缓存
    reload_config()

    os.environ["SKILL_CREATOR_LOG_LEVEL"] = "ERROR"

    # 重新加载以获取新配置
    config = reload_config()

    assert config.log_level == "ERROR"


def test_reload_config():
    """测试重新加载配置."""
    # 第一次加载
    config1 = get_config()
    assert config1.log_level == "INFO"  # 默认值

    # 修改环境变量
    os.environ["SKILL_CREATOR_LOG_LEVEL"] = "WARNING"

    # 重新加载
    config2 = reload_config()

    assert config2.log_level == "WARNING"
    assert config1 is not config2  # 新的实例


# ==================== 类型注解测试 ====================


def test_log_level_type():
    """测试 LogLevel 类型注解."""
    level: LogLevel = "DEBUG"
    assert level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


def test_log_format_type():
    """测试 LogFormat 类型注解."""
    format_type: LogFormat = "detailed"
    assert format_type in ["default", "simple", "detailed"]
