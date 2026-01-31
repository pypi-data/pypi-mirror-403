"""测试日志配置模块."""

import logging
from unittest.mock import patch

from skill_creator_mcp.logging_config import (
    DEFAULT_FORMAT,
    DETAILED_FORMAT,
    SIMPLE_FORMAT,
    get_logger,
    logger,
    setup_logging,
)


class TestSetupLogging:
    """测试 setup_logging 函数."""

    def test_setup_logging_default(self):
        """测试默认日志配置."""
        setup_logging()

        root_logger = logging.getLogger()
        assert root_logger.level == logging.INFO

    def test_setup_logging_debug_level(self):
        """测试 DEBUG 级别."""
        setup_logging(level="DEBUG")

        root_logger = logging.getLogger()
        assert root_logger.level == logging.DEBUG

    def test_setup_logging_error_level(self):
        """测试 ERROR 级别."""
        setup_logging(level="ERROR")

        root_logger = logging.getLogger()
        assert root_logger.level == logging.ERROR

    def test_setup_logging_simple_format(self):
        """测试简洁格式."""
        setup_logging(format_type="simple")

        # 简洁格式不包含asctime
        root_logger = logging.getLogger()
        # 格式检查通过日志记录
        assert root_logger.handlers

    def test_setup_logging_detailed_format(self):
        """测试详细格式."""
        setup_logging(format_type="detailed")

        root_logger = logging.getLogger()
        assert root_logger.handlers

    def test_setup_logging_with_file(self, tmp_path):
        """测试日志文件输出."""
        log_file = tmp_path / "test.log"

        setup_logging(log_file=str(log_file))

        # 检查文件处理器是否添加
        root_logger = logging.getLogger()
        file_handlers = [h for h in root_logger.handlers if isinstance(h, logging.FileHandler)]
        assert len(file_handlers) > 0

    def test_setup_logging_creates_log_directory(self, tmp_path):
        """测试创建日志目录."""
        log_file = tmp_path / "nested" / "dir" / "test.log"

        setup_logging(log_file=str(log_file))

        assert log_file.parent.exists()
        assert log_file.parent.is_dir()

    @patch("skill_creator_mcp.logging_config.logging.basicConfig")
    def test_setup_logging_force_reset(self, mock_basicconfig):
        """测试强制重置日志配置."""
        setup_logging()

        mock_basicconfig.assert_called_once()
        call_kwargs = mock_basicconfig.call_args.kwargs
        assert call_kwargs["force"] is True


class TestGetLogger:
    """测试 get_logger 函数."""

    def test_get_logger(self):
        """测试获取 logger."""
        test_logger = get_logger("test")

        assert isinstance(test_logger, logging.Logger)
        assert test_logger.name == "test"

    def test_get_logger_with_module_name(self):
        """测试使用模块名获取 logger."""
        test_logger = get_logger(__name__)

        assert isinstance(test_logger, logging.Logger)
        assert "test_logging_config" in test_logger.name


class TestModuleLogger:
    """测试模块级别 logger."""

    def test_module_logger_exists(self):
        """测试模块 logger 存在."""
        assert isinstance(logger, logging.Logger)

    def test_module_logger_can_log(self, caplog):
        """测试模块 logger 可以记录日志."""
        with caplog.at_level(logging.INFO):
            logger.info("Test message")

        assert "Test message" in caplog.text


class TestLogFormats:
    """测试日志格式常量."""

    def test_default_format(self):
        """测试默认格式."""
        assert "%(asctime)s" in DEFAULT_FORMAT
        assert "%(levelname)s" in DEFAULT_FORMAT

    def test_simple_format(self):
        """测试简洁格式."""
        assert "%(levelname)s" in SIMPLE_FORMAT
        # 简洁格式不包含时间戳
        assert "%(asctime)s" not in SIMPLE_FORMAT

    def test_detailed_format(self):
        """测试详细格式."""
        assert "%(asctime)s" in DETAILED_FORMAT
        assert "%(funcName)s" in DETAILED_FORMAT
        assert "%(lineno)d" in DETAILED_FORMAT
