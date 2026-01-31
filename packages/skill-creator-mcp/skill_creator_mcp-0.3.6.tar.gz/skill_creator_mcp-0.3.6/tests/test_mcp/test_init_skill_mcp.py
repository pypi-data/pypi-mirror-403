"""测试 FastMCP 包装的 init_skill 工具."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from skill_creator_mcp.server import mcp


@pytest.mark.asyncio
async def test_init_skill_mcp_tool_minimal(temp_dir):
    """测试通过 MCP Server 调用 init_skill."""
    # 获取 init_skill 工具
    init_skill_tool = None
    tools = await mcp.list_tools()
    for tool in tools:
        if hasattr(tool, "name") and tool.name == "init_skill_tool":
            init_skill_tool = tool
            break

    assert init_skill_tool is not None, "init_skill tool not found in MCP server"

    # 创建模拟的 MCP Context
    ctx = MagicMock()
    ctx.log = MagicMock()

    # 调用工具的内部函数（FastMCP 包装后，原始函数在 fn 属性）
    if hasattr(init_skill_tool, "fn"):
        # 直接调用原始函数
        result = await init_skill_tool.fn(
            ctx,
            name="test-mcp-minimal",
            template="minimal",
            output_dir=str(temp_dir),
            with_scripts=False,
            with_examples=False,
        )

        assert result["success"] is True
        assert result["skill_name"] == "test-mcp-minimal"

        skill_dir = Path(result["skill_path"])
        assert skill_dir.exists()
        assert (skill_dir / "SKILL.md").exists()


@pytest.mark.asyncio
async def test_init_skill_mcp_tool_invalid_name(temp_dir):
    """测试通过 MCP Server 调用 init_skill（无效名称）."""
    # 获取 init_skill 工具
    init_skill_tool = None
    tools = await mcp.list_tools()
    for tool in tools:
        if hasattr(tool, "name") and tool.name == "init_skill_tool":
            init_skill_tool = tool
            break

    assert init_skill_tool is not None

    # 创建模拟的 MCP Context
    ctx = MagicMock()
    ctx.log = MagicMock()

    # 调用工具的内部函数
    if hasattr(init_skill_tool, "fn"):
        result = await init_skill_tool.fn(
            ctx,
            name="Invalid_Name",
            template="minimal",
            output_dir=str(temp_dir),
        )

        assert result["success"] is False
        assert result["error_type"] == "validation_error"


@pytest.mark.asyncio
async def test_init_skill_mcp_tool_invalid_template(temp_dir):
    """测试通过 MCP Server 调用 init_skill（无效模板）."""
    # 获取 init_skill 工具
    init_skill_tool = None
    tools = await mcp.list_tools()
    for tool in tools:
        if hasattr(tool, "name") and tool.name == "init_skill_tool":
            init_skill_tool = tool
            break

    assert init_skill_tool is not None

    # 创建模拟的 MCP Context
    ctx = MagicMock()
    ctx.log = MagicMock()

    # 调用工具的内部函数
    if hasattr(init_skill_tool, "fn"):
        result = await init_skill_tool.fn(
            ctx,
            name="test-skill",
            template="invalid-template",
            output_dir=str(temp_dir),
        )

        assert result["success"] is False
        assert result["error_type"] == "validation_error"


@pytest.mark.asyncio
async def test_init_skill_mcp_tool_with_all_options(temp_dir):
    """测试通过 MCP Server 调用 init_skill（所有选项）."""
    # 获取 init_skill 工具
    init_skill_tool = None
    tools = await mcp.list_tools()
    for tool in tools:
        if hasattr(tool, "name") and tool.name == "init_skill_tool":
            init_skill_tool = tool
            break

    assert init_skill_tool is not None

    # 创建模拟的 MCP Context
    ctx = MagicMock()
    ctx.log = MagicMock()

    # 调用工具的内部函数
    if hasattr(init_skill_tool, "fn"):
        result = await init_skill_tool.fn(
            ctx,
            name="test-mcp-full",
            template="tool-based",
            output_dir=str(temp_dir),
            with_scripts=True,
            with_examples=True,
        )

        assert result["success"] is True

        skill_dir = Path(result["skill_path"])
        # 验证所有文件都创建了
        assert (skill_dir / "SKILL.md").exists()
        assert (skill_dir / "scripts" / "helper.py").exists()
        assert (skill_dir / "examples" / "basic-usage.md").exists()
        assert (skill_dir / "references" / "tool-integration.md").exists()


@pytest.mark.asyncio
async def test_init_skill_mcp_tool_internal_error(temp_dir):
    """测试通过 MCP Server 调用 init_skill（内部错误）."""
    # 获取 init_skill 工具
    init_skill_tool = None
    tools = await mcp.list_tools()
    for tool in tools:
        if hasattr(tool, "name") and tool.name == "init_skill_tool":
            init_skill_tool = tool
            break

    assert init_skill_tool is not None

    # 创建模拟的 MCP Context
    ctx = MagicMock()
    ctx.log = MagicMock()

    # 模拟 write_file_async 抛出异常
    with patch(
        "skill_creator_mcp.tools.skill_tools.write_file_async", side_effect=RuntimeError("Simulated error")
    ):
        result = await init_skill_tool.fn(
            ctx,
            name="test-error",
            template="minimal",
            output_dir=str(temp_dir),
        )

        assert result["success"] is False
        assert result["error_type"] == "internal_error"
        assert "Simulated error" in result["error"]
