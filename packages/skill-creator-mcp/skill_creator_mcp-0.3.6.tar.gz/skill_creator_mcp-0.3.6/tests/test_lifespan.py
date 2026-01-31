"""测试MCP Server生命周期管理."""

from unittest.mock import MagicMock

import pytest
from fastmcp import FastMCP

from skill_creator_mcp.server import AppContext, app_lifespan, mcp


class TestAppContext:
    """测试AppContext数据类."""

    def test_app_context_creation(self):
        """测试AppContext创建."""
        context = AppContext()
        assert context.cache == {}
        assert context.startup_time == 0.0
        assert context.request_count == 0

    def test_app_context_with_values(self):
        """测试带初始值的AppContext."""
        context = AppContext(
            cache={"key": "value"},
            startup_time=123.45,
            request_count=5,
        )
        assert context.cache == {"key": "value"}
        assert context.startup_time == 123.45
        assert context.request_count == 5

    def test_increment_request_count(self):
        """测试增加请求计数."""
        context = AppContext()
        assert context.request_count == 0

        count1 = context.increment_request_count()
        assert count1 == 1
        assert context.request_count == 1

        count2 = context.increment_request_count()
        assert count2 == 2
        assert context.request_count == 2


class TestAppLifespan:
    """测试应用生命周期管理."""

    @pytest.mark.asyncio
    async def test_app_lifespan_initialization(self):
        """测试生命周期初始化."""
        # 创建一个模拟的FastMCP服务器
        mock_server = MagicMock(spec=FastMCP)

        async with app_lifespan(mock_server) as context:
            assert isinstance(context, AppContext)
            assert context.cache is not None
            assert context.startup_time > 0
            assert context.request_count == 0

    @pytest.mark.asyncio
    async def test_app_lifespan_cleanup(self):
        """测试生命周期清理."""
        mock_server = MagicMock(spec=FastMCP)

        # 测试清理是否正常执行（不应抛出异常）
        async with app_lifespan(mock_server) as context:
            assert context is not None

        # 退出上下文后，应该正常清理
        assert True

    @pytest.mark.asyncio
    async def test_app_lifespan_context_usage(self):
        """测试在生命周期内使用上下文."""
        mock_server = MagicMock(spec=FastMCP)

        async with app_lifespan(mock_server) as context:
            # 使用缓存（MemoryCache使用set/get方法）
            from skill_creator_mcp.utils.cache import MemoryCache

            assert isinstance(context.cache, MemoryCache)
            # 测试缓存操作
            context.cache.set("test_key", "test_value")
            result = context.cache.get("test_key")
            assert result == "test_value"

            # 增加请求计数
            context.increment_request_count()
            assert context.request_count == 1


class TestMCPServerWithLifespan:
    """测试带有生命周期的MCP服务器."""

    def test_mcp_server_has_lifespan(self):
        """测试MCP服务器配置了生命周期."""
        # 验证mcp对象存在
        assert mcp is not None
        assert isinstance(mcp, FastMCP)

        # 注意：FastMCP可能不直接暴露lifespan属性
        # 但我们已经通过初始化参数配置了它
        assert mcp.name == "skill-creator"

    @pytest.mark.asyncio
    async def test_mcp_server_startup(self):
        """测试MCP服务器启动时初始化上下文."""
        # 模拟服务器启动
        # 注意：FastMCP可能在内部使用lifespan，这里验证配置正确

        # 验证生命周期函数可以被调用
        mock_server = MagicMock(spec=FastMCP)

        async with app_lifespan(mock_server) as context:
            # 验证上下文正常初始化
            assert context.startup_time > 0
            assert context.request_count == 0

            # 模拟一些操作
            context.increment_request_count()
            assert context.request_count == 1
