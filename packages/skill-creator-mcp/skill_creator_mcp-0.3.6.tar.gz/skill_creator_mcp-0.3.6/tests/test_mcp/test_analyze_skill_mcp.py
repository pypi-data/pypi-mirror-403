"""测试 FastMCP 包装的 analyze_skill 工具."""

from unittest.mock import MagicMock, patch

import pytest

from skill_creator_mcp.server import mcp


@pytest.mark.asyncio
async def test_analyze_skill_mcp_basic(temp_dir):
    """测试通过 MCP Server 分析基本技能."""
    # 获取 analyze_skill 工具
    analyze_skill_tool = None
    tools = await mcp.list_tools()
    for tool in tools:
        if hasattr(tool, "name") and tool.name == "analyze_skill_tool":
            analyze_skill_tool = tool
            break

    assert analyze_skill_tool is not None, "analyze_skill tool not found in MCP server"

    # 创建技能目录
    skill_dir = temp_dir / "test-analyze-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("""---
name: test-analyze-skill
description: |
  A skill for testing analysis
allowed-tools: Read, Write
---
# Test Analyze Skill

## 描述
This is a test skill.

## 示例

```python
example code here
```
""")
    # 创建目录结构
    for dir_name in ["references", "examples", "scripts", ".claude"]:
        (skill_dir / dir_name).mkdir()
    (skill_dir / "references" / "guide.md").write_text("# Guide\n\nContent here")
    (skill_dir / "pyproject.toml").write_text("[project]\nname = 'test-analyze-skill'")

    # 创建模拟的 MCP Context
    ctx = MagicMock()
    ctx.log = MagicMock()

    # 调用工具
    if hasattr(analyze_skill_tool, "fn"):
        result = await analyze_skill_tool.fn(
            ctx,
            skill_path=str(skill_dir),
            analyze_structure=True,
            analyze_complexity=True,
            analyze_quality=True,
        )

        assert result["success"] is True
        assert result["skill_name"] == "test-analyze-skill"
        assert "structure" in result
        assert "complexity" in result
        assert "quality" in result
        assert "summary" in result


@pytest.mark.asyncio
async def test_analyze_skill_mcp_analyze_structure_false(temp_dir):
    """测试通过 MCP Server 分析技能（不分析结构）."""
    # 获取 analyze_skill 工具
    analyze_skill_tool = None
    tools = await mcp.list_tools()
    for tool in tools:
        if hasattr(tool, "name") and tool.name == "analyze_skill_tool":
            analyze_skill_tool = tool
            break

    assert analyze_skill_tool is not None

    # 创建技能目录
    skill_dir = temp_dir / "test-no-structure"
    skill_dir.mkdir()

    # 创建模拟的 MCP Context
    ctx = MagicMock()
    ctx.log = MagicMock()

    # 调用工具（不分析结构）
    if hasattr(analyze_skill_tool, "fn"):
        result = await analyze_skill_tool.fn(
            ctx,
            skill_path=str(skill_dir),
            analyze_structure=False,
            analyze_complexity=True,
            analyze_quality=True,
        )

        assert result["success"] is True
        # 不分析结构时，返回空对象而不是 None
        assert result["structure"]["total_files"] == 0
        assert result["structure"]["total_lines"] == 0
        assert result["structure"]["file_breakdown"] == {}


@pytest.mark.asyncio
async def test_analyze_skill_mcp_analyze_complexity_false(temp_dir):
    """测试通过 MCP Server 分析技能（不分析复杂度）."""
    # 获取 analyze_skill 工具
    analyze_skill_tool = None
    tools = await mcp.list_tools()
    for tool in tools:
        if hasattr(tool, "name") and tool.name == "analyze_skill_tool":
            analyze_skill_tool = tool
            break

    assert analyze_skill_tool is not None

    # 创建技能目录
    skill_dir = temp_dir / "test-no-complexity"
    skill_dir.mkdir()

    # 创建模拟的 MCP Context
    ctx = MagicMock()
    ctx.log = MagicMock()

    # 调用工具（不分析复杂度）
    if hasattr(analyze_skill_tool, "fn"):
        result = await analyze_skill_tool.fn(
            ctx,
            skill_path=str(skill_dir),
            analyze_structure=True,
            analyze_complexity=False,
            analyze_quality=True,
        )

        assert result["success"] is True
        # 不分析复杂度时，返回空对象而不是 None
        assert result["complexity"]["cyclomatic_complexity"] is None
        assert result["complexity"]["maintainability_index"] is None
        assert result["complexity"]["code_duplication"] is None


@pytest.mark.asyncio
async def test_analyze_skill_mcp_analyze_quality_false(temp_dir):
    """测试通过 MCP Server 分析技能（不分析质量）."""
    # 获取 analyze_skill 工具
    analyze_skill_tool = None
    tools = await mcp.list_tools()
    for tool in tools:
        if hasattr(tool, "name") and tool.name == "analyze_skill_tool":
            analyze_skill_tool = tool
            break

    assert analyze_skill_tool is not None

    # 创建技能目录
    skill_dir = temp_dir / "test-no-quality"
    skill_dir.mkdir()

    # 创建模拟的 MCP Context
    ctx = MagicMock()
    ctx.log = MagicMock()

    # 调用工具（不分析质量）
    if hasattr(analyze_skill_tool, "fn"):
        result = await analyze_skill_tool.fn(
            ctx,
            skill_path=str(skill_dir),
            analyze_structure=True,
            analyze_complexity=True,
            analyze_quality=False,
        )

        assert result["success"] is True
        # 不分析质量时，返回 0 分而不是 None
        assert result["quality"]["overall_score"] == 0.0
        assert result["quality"]["structure_score"] == 0.0
        assert result["quality"]["documentation_score"] == 0.0
        assert result["quality"]["test_coverage_score"] == 0.0


@pytest.mark.asyncio
async def test_analyze_skill_mcp_all_false(temp_dir):
    """测试通过 MCP Server 分析技能（所有分析选项都关闭）."""
    # 获取 analyze_skill 工具
    analyze_skill_tool = None
    tools = await mcp.list_tools()
    for tool in tools:
        if hasattr(tool, "name") and tool.name == "analyze_skill_tool":
            analyze_skill_tool = tool
            break

    assert analyze_skill_tool is not None

    # 创建技能目录
    skill_dir = temp_dir / "test-no-analysis"
    skill_dir.mkdir()

    # 创建模拟的 MCP Context
    ctx = MagicMock()
    ctx.log = MagicMock()

    # 调用工具（所有分析都关闭）
    if hasattr(analyze_skill_tool, "fn"):
        result = await analyze_skill_tool.fn(
            ctx,
            skill_path=str(skill_dir),
            analyze_structure=False,
            analyze_complexity=False,
            analyze_quality=False,
        )

        assert result["success"] is True
        # 所有分析都关闭时，返回空对象而不是 None
        assert result["structure"]["total_files"] == 0
        assert result["structure"]["total_lines"] == 0
        assert result["complexity"]["cyclomatic_complexity"] is None
        assert result["quality"]["overall_score"] == 0.0


@pytest.mark.asyncio
async def test_analyze_skill_mcp_directory_not_exists(temp_dir):
    """测试通过 MCP Server 分析不存在的目录."""
    # 获取 analyze_skill 工具
    analyze_skill_tool = None
    tools = await mcp.list_tools()
    for tool in tools:
        if hasattr(tool, "name") and tool.name == "analyze_skill_tool":
            analyze_skill_tool = tool
            break

    assert analyze_skill_tool is not None

    # 创建模拟的 MCP Context
    ctx = MagicMock()
    ctx.log = MagicMock()

    # 调用工具（目录不存在）
    if hasattr(analyze_skill_tool, "fn"):
        result = await analyze_skill_tool.fn(
            ctx,
            skill_path=str(temp_dir / "non-existent-skill"),
        )

        assert result["success"] is False
        assert "目录不存在" in result["error"]


@pytest.mark.asyncio
async def test_analyze_skill_mcp_internal_error(temp_dir):
    """测试通过 MCP Server 分析技能时的内部错误."""
    # 获取 analyze_skill 工具
    analyze_skill_tool = None
    tools = await mcp.list_tools()
    for tool in tools:
        if hasattr(tool, "name") and tool.name == "analyze_skill_tool":
            analyze_skill_tool = tool
            break

    assert analyze_skill_tool is not None

    # 创建模拟的 MCP Context
    ctx = MagicMock()
    ctx.log = MagicMock()

    # 模拟 Path 构造函数抛出异常
    with patch("skill_creator_mcp.tools.skill_tools.Path", side_effect=RuntimeError("Simulated error")):
        result = await analyze_skill_tool.fn(
            ctx,
            skill_path="/some/path",
        )

        assert result["success"] is False
        assert result["error_type"] == "internal_error"


@pytest.mark.asyncio
async def test_analyze_skill_mcp_with_python_files(temp_dir):
    """测试通过 MCP Server 分析包含 Python 文件的技能."""
    # 获取 analyze_skill 工具
    analyze_skill_tool = None
    tools = await mcp.list_tools()
    for tool in tools:
        if hasattr(tool, "name") and tool.name == "analyze_skill_tool":
            analyze_skill_tool = tool
            break

    assert analyze_skill_tool is not None

    # 创建技能目录（包含 Python 文件）
    skill_dir = temp_dir / "test-with-code"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("---\nname: test-with-code\n---")

    # 创建包含代码的目录
    src_dir = skill_dir / "src" / "test_with_code"
    src_dir.mkdir(parents=True)
    (src_dir / "__init__.py").write_text("")
    (src_dir / "server.py").write_text("""
def hello():
    if True:
        return "world"
    return "done"
""")

    tests_dir = skill_dir / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_main.py").write_text("def test(): pass")

    # 创建模拟的 MCP Context
    ctx = MagicMock()
    ctx.log = MagicMock()

    # 调用工具
    if hasattr(analyze_skill_tool, "fn"):
        result = await analyze_skill_tool.fn(
            ctx,
            skill_path=str(skill_dir),
        )

        assert result["success"] is True
        # 结构分析应该统计到文件
        assert result["structure"]["total_files"] > 0
        # 复杂度分析应该有结果
        assert result["complexity"]["cyclomatic_complexity"] is not None


@pytest.mark.asyncio
async def test_analyze_skill_mcp_empty_directory(temp_dir):
    """测试通过 MCP Server 分析空目录."""
    # 获取 analyze_skill 工具
    analyze_skill_tool = None
    tools = await mcp.list_tools()
    for tool in tools:
        if hasattr(tool, "name") and tool.name == "analyze_skill_tool":
            analyze_skill_tool = tool
            break

    assert analyze_skill_tool is not None

    # 创建空的技能目录
    skill_dir = temp_dir / "test-empty"
    skill_dir.mkdir()

    # 创建模拟的 MCP Context
    ctx = MagicMock()
    ctx.log = MagicMock()

    # 调用工具
    if hasattr(analyze_skill_tool, "fn"):
        result = await analyze_skill_tool.fn(
            ctx,
            skill_path=str(skill_dir),
        )

        assert result["success"] is True
        # 空目录应该有 0 个文件
        assert result["structure"]["total_files"] == 0
        # 复杂度应该为 None（没有文件）
        assert result["complexity"]["cyclomatic_complexity"] is None
