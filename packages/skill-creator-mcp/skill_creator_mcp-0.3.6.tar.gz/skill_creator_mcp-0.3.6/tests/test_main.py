"""测试入口点模块.

测试 __main__.py (STDIO) 和 http.py (HTTP/SSE) 入口点.
"""

from unittest.mock import MagicMock, patch

from skill_creator_mcp.__main__ import main as stdio_main
from skill_creator_mcp.http import main as http_main


class TestStdioMain:
    """测试 STDIO 入口点."""

    @patch("skill_creator_mcp.__main__.mcp")
    @patch("skill_creator_mcp.__main__.setup_logging")
    @patch("skill_creator_mcp.__main__.get_config")
    def test_main_success(self, mock_config, mock_setup, mock_mcp):
        """测试正常启动."""
        mock_config.return_value = MagicMock(
            log_level="INFO",
            log_file=None,
            log_format="default",
        )
        mock_mcp.run.return_value = None

        result = stdio_main()

        assert result == 0
        mock_setup.assert_called_once()
        mock_mcp.run.assert_called_once()

    @patch("skill_creator_mcp.__main__.mcp")
    @patch("skill_creator_mcp.__main__.setup_logging")
    @patch("skill_creator_mcp.__main__.get_config")
    def test_main_keyboard_interrupt(self, mock_config, mock_setup, mock_mcp):
        """测试键盘中断."""
        mock_config.return_value = MagicMock(
            log_level="INFO",
            log_file=None,
            log_format="default",
        )
        mock_mcp.run.side_effect = KeyboardInterrupt()

        result = stdio_main()

        assert result == 130

    @patch("skill_creator_mcp.__main__.mcp")
    @patch("skill_creator_mcp.__main__.setup_logging")
    @patch("skill_creator_mcp.__main__.get_config")
    def test_main_exception(self, mock_config, mock_setup, mock_mcp):
        """测试异常处理."""
        mock_config.return_value = MagicMock(
            log_level="INFO",
            log_file=None,
            log_format="default",
        )
        mock_mcp.run.side_effect = RuntimeError("Test error")

        result = stdio_main()

        assert result == 1


class TestHttpMain:
    """测试 HTTP/SSE 入口点."""

    @patch("skill_creator_mcp.http.mcp")
    def test_main_success(self, mock_mcp):
        """测试正常启动."""
        mock_mcp.run.return_value = None

        result = http_main()

        assert result == 0
        mock_mcp.run.assert_called_once_with(transport="sse")

    @patch("skill_creator_mcp.http.mcp")
    def test_main_keyboard_interrupt(self, mock_mcp):
        """测试键盘中断."""
        mock_mcp.run.side_effect = KeyboardInterrupt()

        result = http_main()

        assert result == 130

    @patch("skill_creator_mcp.http.mcp")
    def test_main_exception(self, mock_mcp):
        """测试异常处理."""
        mock_mcp.run.side_effect = RuntimeError("Test error")

        result = http_main()

        assert result == 1
