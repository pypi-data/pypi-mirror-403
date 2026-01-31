"""测试 server.py 中的中间件和工具函数.

这个测试模块专门测试 server.py 中定义的中间件类，
确保日志记录、错误处理和性能计时功能正常工作。
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from skill_creator_mcp.server import (
    ErrorHandlingMiddleware,
    LoggingMiddleware,
    TimingMiddleware,
)

# ==================== LoggingMiddleware 测试 ====================


@pytest.mark.asyncio
async def test_logging_middleware_logs_tool_call():
    """测试 LoggingMiddleware 记录工具调用."""
    middleware = LoggingMiddleware()
    context = MagicMock()
    context.name = "test_tool"

    call_next = AsyncMock(return_value="result")

    with patch("skill_creator_mcp.logging_config.get_logger") as mock_get_logger:
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        result = await middleware(context, call_next)

        assert result == "result"
        mock_logger.info.assert_any_call("Tool called: test_tool")
        assert mock_logger.info.call_count >= 2  # 至少记录开始和完成


@pytest.mark.asyncio
async def test_logging_middleware_logs_tool_failure():
    """测试 LoggingMiddleware 记录工具失败."""
    middleware = LoggingMiddleware()
    context = MagicMock()
    context.name = "failing_tool"

    call_next = AsyncMock(side_effect=RuntimeError("Tool failed"))

    with patch("skill_creator_mcp.logging_config.get_logger") as mock_get_logger:
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        with pytest.raises(RuntimeError, match="Tool failed"):
            await middleware(context, call_next)

        # 验证记录了错误日志
        mock_logger.error.assert_called()
        error_call_args = str(mock_logger.error.call_args)
        assert "failing_tool" in error_call_args
        assert "failed" in error_call_args


@pytest.mark.asyncio
async def test_logging_middleware_unknown_tool_name():
    """测试 LoggingMiddleware 处理未知工具名."""
    middleware = LoggingMiddleware()
    context = MagicMock()
    # 模拟没有name属性的context
    delattr(context, "name")

    call_next = AsyncMock(return_value="result")

    with patch("skill_creator_mcp.logging_config.get_logger") as mock_get_logger:
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        result = await middleware(context, call_next)

        assert result == "result"
        mock_logger.info.assert_any_call("Tool called: unknown")


# ==================== ErrorHandlingMiddleware 测试 ====================


@pytest.mark.asyncio
async def test_error_handling_middleware_pass_through():
    """测试 ErrorHandlingMiddleware 正常情况透传."""
    middleware = ErrorHandlingMiddleware()
    context = MagicMock()

    call_next = AsyncMock(return_value="result")

    result = await middleware(context, call_next)

    assert result == "result"
    call_next.assert_called_once_with(context)


@pytest.mark.asyncio
async def test_error_handling_middleware_catches_and_rethrows():
    """测试 ErrorHandlingMiddleware 捕获异常并重新抛出."""
    middleware = ErrorHandlingMiddleware()
    context = MagicMock()

    error = ValueError("Test error")
    call_next = AsyncMock(side_effect=error)

    with patch("skill_creator_mcp.logging_config.get_logger") as mock_get_logger:
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        with pytest.raises(ValueError, match="Test error"):
            await middleware(context, call_next)

        # 验证记录了错误日志
        mock_logger.error.assert_called_once()
        error_call_args = str(mock_logger.error.call_args)
        assert "Error in tool execution" in error_call_args
        assert "Test error" in error_call_args


# ==================== TimingMiddleware 测试 ====================


@pytest.mark.asyncio
async def test_timing_middleware_records_timing():
    """测试 TimingMiddleware 记录工具执行时间."""
    middleware = TimingMiddleware()
    context = MagicMock()
    context.name = "timed_tool"

    call_next = AsyncMock(return_value="result")

    result = await middleware(context, call_next)

    assert result == "result"
    assert "timed_tool" in middleware._timings
    assert len(middleware._timings["timed_tool"]) == 1
    assert middleware._timings["timed_tool"][0] > 0


@pytest.mark.asyncio
async def test_timing_middleware_multiple_calls():
    """测试 TimingMiddleware 记录多次调用."""
    middleware = TimingMiddleware()
    context = MagicMock()
    context.name = "multi_call_tool"

    call_next = AsyncMock(return_value="result")

    # 调用3次
    await middleware(context, call_next)
    await middleware(context, call_next)
    await middleware(context, call_next)

    assert len(middleware._timings["multi_call_tool"]) == 3


@pytest.mark.asyncio
async def test_timing_middleware_unknown_tool_name():
    """测试 TimingMiddleware 处理未知工具名."""
    middleware = TimingMiddleware()
    context = MagicMock()
    delattr(context, "name")

    call_next = AsyncMock(return_value="result")

    await middleware(context, call_next)

    assert "unknown" in middleware._timings


@pytest.mark.asyncio
async def test_timing_middleware_get_stats():
    """测试 TimingMiddleware.get_stats 方法."""
    middleware = TimingMiddleware()
    context = MagicMock()
    context.name = "stats_tool"

    call_next = AsyncMock(return_value="result")

    # 执行几次以生成统计数据
    await middleware(context, call_next)
    await middleware(context, call_next)
    await middleware(context, call_next)

    stats = middleware.get_stats()

    assert "stats_tool" in stats
    assert stats["stats_tool"]["count"] == 3
    assert "min" in stats["stats_tool"]
    assert "max" in stats["stats_tool"]
    assert "avg" in stats["stats_tool"]
    assert stats["stats_tool"]["min"] > 0
    assert stats["stats_tool"]["max"] >= stats["stats_tool"]["min"]


@pytest.mark.asyncio
async def test_timing_middleware_get_stats_empty():
    """测试 TimingMiddleware.get_stats 无数据情况."""
    middleware = TimingMiddleware()

    stats = middleware.get_stats()

    assert stats == {}


@pytest.mark.asyncio
async def test_timing_middleware_records_failure_timing():
    """测试 TimingMiddleware 记录失败工具的执行时间."""
    middleware = TimingMiddleware()
    context = MagicMock()
    context.name = "failing_tool"

    call_next = AsyncMock(side_effect=RuntimeError("Failed"))

    with pytest.raises(RuntimeError, match="Failed"):
        await middleware(context, call_next)

    # 即使失败也应该记录时间
    assert "failing_tool" in middleware._timings
    assert len(middleware._timings["failing_tool"]) == 1


@pytest.mark.asyncio
async def test_timing_middleware_multiple_tools():
    """测试 TimingMiddleware 区分不同工具的时间."""
    middleware = TimingMiddleware()

    context1 = MagicMock()
    context1.name = "tool_a"
    call_next1 = AsyncMock(return_value="result_a")

    context2 = MagicMock()
    context2.name = "tool_b"
    call_next2 = AsyncMock(return_value="result_b")

    await middleware(context1, call_next1)
    await middleware(context2, call_next2)
    await middleware(context1, call_next1)

    stats = middleware.get_stats()

    assert "tool_a" in stats
    assert "tool_b" in stats
    assert stats["tool_a"]["count"] == 2
    assert stats["tool_b"]["count"] == 1
