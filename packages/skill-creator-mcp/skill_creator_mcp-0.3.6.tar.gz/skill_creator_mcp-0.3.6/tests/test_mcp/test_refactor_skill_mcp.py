"""测试 FastMCP 包装的 refactor_skill 工具."""

from unittest.mock import MagicMock

import pytest

from skill_creator_mcp.server import mcp


@pytest.mark.asyncio
async def test_refactor_skill_mcp_basic(temp_dir):
    """测试通过 MCP Server 重构基本技能."""
    # 获取 refactor_skill 工具
    refactor_skill_tool = None
    tools = await mcp.list_tools()
    for tool in tools:
        if hasattr(tool, "name") and tool.name == "refactor_skill_tool":
            refactor_skill_tool = tool
            break

    assert refactor_skill_tool is not None, "refactor_skill tool not found in MCP server"

    # 创建技能目录
    skill_dir = temp_dir / "test-refactor-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("""---
name: test-refactor-skill
description: |
  A skill for testing refactoring
allowed-tools: Read, Write
---
# Test Refactor Skill

## 描述
This is a test skill.
""")
    # 创建目录结构
    for dir_name in ["references", "examples", "scripts", ".claude"]:
        (skill_dir / dir_name).mkdir()

    # 创建模拟的 MCP Context
    ctx = MagicMock()
    ctx.log = MagicMock()

    # 调用工具
    if hasattr(refactor_skill_tool, "fn"):
        result = await refactor_skill_tool.fn(
            ctx,
            skill_path=str(skill_dir),
            focus=None,
            analyze_structure=True,
            analyze_complexity=True,
            analyze_quality=True,
        )

        assert result["success"] is True
        assert result["skill_name"] == "test-refactor-skill"
        assert "structure" in result
        assert "complexity" in result
        assert "quality" in result
        assert "suggestions" in result
        assert "report" in result
        assert "effort_estimate" in result


@pytest.mark.asyncio
async def test_refactor_skill_mcp_with_focus(temp_dir):
    """测试通过 MCP Server 重构技能（关注领域过滤）."""
    refactor_skill_tool = None
    tools = await mcp.list_tools()
    for tool in tools:
        if hasattr(tool, "name") and tool.name == "refactor_skill_tool":
            refactor_skill_tool = tool
            break

    assert refactor_skill_tool is not None

    # 创建技能目录
    skill_dir = temp_dir / "test-refactor-focus"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("# " + "\n".join(["Content"] * 200))
    (skill_dir / "references").mkdir()

    # 创建模拟的 MCP Context
    ctx = MagicMock()
    ctx.log = MagicMock()

    # 调用工具（关注文档）
    if hasattr(refactor_skill_tool, "fn"):
        result = await refactor_skill_tool.fn(
            ctx,
            skill_path=str(skill_dir),
            focus=["documentation"],
            analyze_structure=True,
            analyze_complexity=True,
            analyze_quality=True,
        )

        assert result["success"] is True
        # 检查建议只包含文档相关的
        for suggestion in result["suggestions"]:
            assert "documentation" in suggestion["category"] or "token" in suggestion["category"]


@pytest.mark.asyncio
async def test_refactor_skill_mcp_no_analysis(temp_dir):
    """测试通过 MCP Server 重构技能（关闭所有分析）."""
    refactor_skill_tool = None
    tools = await mcp.list_tools()
    for tool in tools:
        if hasattr(tool, "name") and tool.name == "refactor_skill_tool":
            refactor_skill_tool = tool
            break

    assert refactor_skill_tool is not None

    # 创建技能目录
    skill_dir = temp_dir / "test-refactor-no-analysis"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("---\nname: test\n---\n# Test")

    # 创建模拟的 MCP Context
    ctx = MagicMock()
    ctx.log = MagicMock()

    # 调用工具（所有分析都关闭）
    if hasattr(refactor_skill_tool, "fn"):
        result = await refactor_skill_tool.fn(
            ctx,
            skill_path=str(skill_dir),
            focus=None,
            analyze_structure=False,
            analyze_complexity=False,
            analyze_quality=False,
        )

        assert result["success"] is True
        # 检查返回空结果
        assert result["structure"]["total_files"] == 0
        assert result["structure"]["total_lines"] == 0
        assert result["complexity"]["cyclomatic_complexity"] is None
        assert result["quality"]["overall_score"] == 0.0


@pytest.mark.asyncio
async def test_refactor_skill_mcp_directory_not_exists(temp_dir):
    """测试通过 MCP Server 重构不存在的目录."""
    refactor_skill_tool = None
    tools = await mcp.list_tools()
    for tool in tools:
        if hasattr(tool, "name") and tool.name == "refactor_skill_tool":
            refactor_skill_tool = tool
            break

    assert refactor_skill_tool is not None

    # 创建模拟的 MCP Context
    ctx = MagicMock()
    ctx.log = MagicMock()

    # 调用工具（目录不存在）
    if hasattr(refactor_skill_tool, "fn"):
        result = await refactor_skill_tool.fn(
            ctx,
            skill_path=str(temp_dir / "non-existent-skill"),
        )

        assert result["success"] is False
        assert "目录不存在" in result["error"]


@pytest.mark.asyncio
async def test_refactor_skill_mcp_path_not_directory(temp_dir):
    """测试通过 MCP Server 重构非目录路径."""
    refactor_skill_tool = None
    tools = await mcp.list_tools()
    for tool in tools:
        if hasattr(tool, "name") and tool.name == "refactor_skill_tool":
            refactor_skill_tool = tool
            break

    assert refactor_skill_tool is not None

    # 创建文件而不是目录
    file_path = temp_dir / "not-a-directory"
    file_path.write_text("content")

    # 创建模拟的 MCP Context
    ctx = MagicMock()
    ctx.log = MagicMock()

    # 调用工具（路径不是目录）
    if hasattr(refactor_skill_tool, "fn"):
        result = await refactor_skill_tool.fn(
            ctx,
            skill_path=str(file_path),
        )

        assert result["success"] is False
        assert "路径不是目录" in result["error"]


@pytest.mark.asyncio
async def test_refactor_skill_mcp_internal_error(temp_dir):
    """测试通过 MCP Server 重构技能时的内部错误."""
    refactor_skill_tool = None
    tools = await mcp.list_tools()
    for tool in tools:
        if hasattr(tool, "name") and tool.name == "refactor_skill_tool":
            refactor_skill_tool = tool
            break

    assert refactor_skill_tool is not None

    # 创建模拟的 MCP Context
    ctx = MagicMock()
    ctx.log = MagicMock()

    # 模拟 Path 构造函数抛出异常
    from unittest.mock import patch

    with patch("skill_creator_mcp.tools.skill_tools.Path", side_effect=RuntimeError("Simulated error")):
        result = await refactor_skill_tool.fn(
            ctx,
            skill_path="/some/path",
        )

        assert result["success"] is False
        assert result["error_type"] == "internal_error"


@pytest.mark.asyncio
async def test_refactor_skill_mcp_with_complex_skill(temp_dir):
    """测试通过 MCP Server 重构复杂技能."""
    refactor_skill_tool = None
    tools = await mcp.list_tools()
    for tool in tools:
        if hasattr(tool, "name") and tool.name == "refactor_skill_tool":
            refactor_skill_tool = tool
            break

    assert refactor_skill_tool is not None

    # 创建复杂技能目录
    skill_dir = temp_dir / "complex-skill"
    skill_dir.mkdir()

    # 创建 SKILL.md（过长）
    (skill_dir / "SKILL.md").write_text("# " + "\n".join(["Long content"] * 500))

    # 创建过多文件
    for i in range(25):
        (skill_dir / f"file_{i}.py").write_text("# File " + str(i))

    # 创建目录结构
    (skill_dir / "references").mkdir()

    # 创建模拟的 MCP Context
    ctx = MagicMock()
    ctx.log = MagicMock()

    # 调用工具
    if hasattr(refactor_skill_tool, "fn"):
        result = await refactor_skill_tool.fn(
            ctx,
            skill_path=str(skill_dir),
        )

        assert result["success"] is True
        # 应该生成多个建议
        assert len(result["suggestions"]) > 0

        # 检查有 token 效率建议（因为 SKILL.md 过长）
        token_suggestions = [
            s for s in result["suggestions"] if s["category"] == "token-efficiency"
        ]
        assert len(token_suggestions) > 0

        # 检查有模块化建议（因为文件过多）
        modularity_suggestions = [s for s in result["suggestions"] if s["category"] == "modularity"]
        assert len(modularity_suggestions) > 0


@pytest.mark.asyncio
async def test_refactor_skill_mcp_generates_report(temp_dir):
    """测试通过 MCP Server 重构技能生成完整报告."""
    refactor_skill_tool = None
    tools = await mcp.list_tools()
    for tool in tools:
        if hasattr(tool, "name") and tool.name == "refactor_skill_tool":
            refactor_skill_tool = tool
            break

    assert refactor_skill_tool is not None

    # 创建技能目录
    skill_dir = temp_dir / "test-refactor-report"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("---\nname: test\n---\n# Test")

    # 创建模拟的 MCP Context
    ctx = MagicMock()
    ctx.log = MagicMock()

    # 调用工具
    if hasattr(refactor_skill_tool, "fn"):
        result = await refactor_skill_tool.fn(
            ctx,
            skill_path=str(skill_dir),
        )

        assert result["success"] is True
        # 检查报告内容
        report = result["report"]
        assert "# 重构分析报告" in report
        assert "## 当前状态评估" in report
        assert "## 发现的问题" in report
        assert "## 实施计划" in report


@pytest.mark.asyncio
async def test_refactor_skill_mcp_effort_estimate(temp_dir):
    """测试通过 MCP Server 重构技能时的工作量估算."""
    refactor_skill_tool = None
    tools = await mcp.list_tools()
    for tool in tools:
        if hasattr(tool, "name") and tool.name == "refactor_skill_tool":
            refactor_skill_tool = tool
            break

    assert refactor_skill_tool is not None

    # 创建技能目录（有多个问题）
    skill_dir = temp_dir / "test-effort"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("# " + "\n".join(["Long"] * 300))

    for i in range(25):
        (skill_dir / f"file_{i}.py").write_text("#")

    # 创建模拟的 MCP Context
    ctx = MagicMock()
    ctx.log = MagicMock()

    # 调用工具
    if hasattr(refactor_skill_tool, "fn"):
        result = await refactor_skill_tool.fn(
            ctx,
            skill_path=str(skill_dir),
        )

        assert result["success"] is True
        # 检查工作量估算
        effort = result["effort_estimate"]
        assert "p0_hours" in effort
        assert "p1_hours" in effort
        assert "p2_hours" in effort
        assert "total_hours" in effort
        # 应该有工作量（因为有问题）
        assert effort["total_hours"] > 0
