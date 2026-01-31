"""测试 FastMCP 包装的 validate_skill 工具."""

from unittest.mock import MagicMock

import pytest

from skill_creator_mcp.server import mcp


@pytest.mark.asyncio
async def test_validate_skill_mcp_valid_skill(temp_dir):
    """测试通过 MCP Server 验证有效的技能目录."""
    # 获取 validate_skill 工具
    validate_skill_tool = None
    tools = await mcp.list_tools()
    for tool in tools:
        if hasattr(tool, "name") and tool.name == "validate_skill_tool":
            validate_skill_tool = tool
            break

    assert validate_skill_tool is not None, "validate_skill tool not found in MCP server"

    # 创建有效的技能目录
    skill_dir = temp_dir / "test-valid-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("""---
name: test-valid-skill
description: |
  A valid test skill
allowed-tools: Read, Write, Edit
---
# Test Valid Skill
""")
    for dir_name in ["references", "examples", "scripts", ".claude"]:
        (skill_dir / dir_name).mkdir()

    # 创建模拟的 MCP Context
    ctx = MagicMock()
    ctx.log = MagicMock()

    # 调用工具
    if hasattr(validate_skill_tool, "fn"):
        result = await validate_skill_tool.fn(
            ctx,
            skill_path=str(skill_dir),
            check_structure=True,
            check_content=True,
        )

        assert result["success"] is True
        assert result["valid"] is True
        assert result["skill_name"] == "test-valid-skill"
        assert result["errors"] == []
        assert result["checks"]["structure"] is True
        assert result["checks"]["naming"] is True
        assert result["checks"]["content"] is True


@pytest.mark.asyncio
async def test_validate_skill_mcp_directory_not_exists():
    """测试通过 MCP Server 验证不存在的目录."""
    # 获取 validate_skill 工具
    validate_skill_tool = None
    tools = await mcp.list_tools()
    for tool in tools:
        if hasattr(tool, "name") and tool.name == "validate_skill_tool":
            validate_skill_tool = tool
            break

    assert validate_skill_tool is not None

    # 创建模拟的 MCP Context
    ctx = MagicMock()
    ctx.log = MagicMock()

    # 调用工具（目录不存在）
    if hasattr(validate_skill_tool, "fn"):
        result = await validate_skill_tool.fn(
            ctx,
            skill_path="/non-existent-skill",
        )

        assert result["success"] is False
        assert result["valid"] is False
        assert "目录不存在" in result["errors"][0]


@pytest.mark.asyncio
async def test_validate_skill_mcp_path_not_directory(temp_dir):
    """测试通过 MCP Server 验证非目录路径."""
    # 获取 validate_skill 工具
    validate_skill_tool = None
    tools = await mcp.list_tools()
    for tool in tools:
        if hasattr(tool, "name") and tool.name == "validate_skill_tool":
            validate_skill_tool = tool
            break

    assert validate_skill_tool is not None

    # 创建一个文件而不是目录
    file_path = temp_dir / "not-a-directory"
    file_path.write_text("I am a file")

    # 创建模拟的 MCP Context
    ctx = MagicMock()
    ctx.log = MagicMock()

    # 调用工具（路径不是目录）
    if hasattr(validate_skill_tool, "fn"):
        result = await validate_skill_tool.fn(
            ctx,
            skill_path=str(file_path),
        )

        assert result["success"] is False
        assert result["valid"] is False
        assert "路径不是目录" in result["errors"][0]


@pytest.mark.asyncio
async def test_validate_skill_mcp_check_structure_false(temp_dir):
    """测试通过 MCP Server 验证技能（不检查结构）."""
    # 获取 validate_skill 工具
    validate_skill_tool = None
    tools = await mcp.list_tools()
    for tool in tools:
        if hasattr(tool, "name") and tool.name == "validate_skill_tool":
            validate_skill_tool = tool
            break

    assert validate_skill_tool is not None

    # 创建有效的技能目录
    skill_dir = temp_dir / "test-incomplete"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        "---\nname: test-incomplete\ndescription: Test\nallowed-tools: Read\n---"
    )

    # 创建模拟的 MCP Context
    ctx = MagicMock()
    ctx.log = MagicMock()

    # 调用工具（不检查结构）
    if hasattr(validate_skill_tool, "fn"):
        result = await validate_skill_tool.fn(
            ctx,
            skill_path=str(skill_dir),
            check_structure=False,
            check_content=True,
        )

        assert result["success"] is True
        # 结构检查被跳过，所以结构检查结果不在 checks 中
        assert "structure" not in result["checks"]
        # 内容检查应该通过
        assert result["checks"]["content"] is True
        # 命名检查始终执行
        assert "naming" in result["checks"]


@pytest.mark.asyncio
async def test_validate_skill_mcp_check_content_false(temp_dir):
    """测试通过 MCP Server 验证技能（不检查内容）."""
    # 获取 validate_skill 工具
    validate_skill_tool = None
    tools = await mcp.list_tools()
    for tool in tools:
        if hasattr(tool, "name") and tool.name == "validate_skill_tool":
            validate_skill_tool = tool
            break

    assert validate_skill_tool is not None

    # 创建有效的技能目录结构
    skill_dir = temp_dir / "test-structure-only"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("# No frontmatter")
    for dir_name in ["references", "examples", "scripts", ".claude"]:
        (skill_dir / dir_name).mkdir()

    # 创建模拟的 MCP Context
    ctx = MagicMock()
    ctx.log = MagicMock()

    # 调用工具（不检查内容）
    if hasattr(validate_skill_tool, "fn"):
        result = await validate_skill_tool.fn(
            ctx,
            skill_path=str(skill_dir),
            check_structure=True,
            check_content=False,
        )

        assert result["success"] is True
        assert result["checks"]["structure"] is True
        # 内容检查被跳过
        assert "content" not in result["checks"]


@pytest.mark.asyncio
async def test_validate_skill_mcp_with_template_type(temp_dir):
    """测试通过 MCP Server 验证带模板类型的技能."""
    # 获取 validate_skill 工具
    validate_skill_tool = None
    tools = await mcp.list_tools()
    for tool in tools:
        if hasattr(tool, "name") and tool.name == "validate_skill_tool":
            validate_skill_tool = tool
            break

    assert validate_skill_tool is not None

    # 创建 tool-based 模板的技能目录
    skill_dir = temp_dir / "test-tool-based"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("""---
name: test-tool-based
template: tool-based
description: |
  Tool-based skill
allowed-tools: Read, Write, Edit
---
# Tool Based Skill
""")
    refs_dir = skill_dir / "references"
    refs_dir.mkdir()
    (refs_dir / "tool-integration.md").write_text("# Tools")
    (refs_dir / "usage-examples.md").write_text("# Examples")
    for dir_name in ["examples", "scripts", ".claude"]:
        (skill_dir / dir_name).mkdir()

    # 创建模拟的 MCP Context
    ctx = MagicMock()
    ctx.log = MagicMock()

    # 调用工具
    if hasattr(validate_skill_tool, "fn"):
        result = await validate_skill_tool.fn(
            ctx,
            skill_path=str(skill_dir),
        )

        assert result["success"] is True
        assert result["valid"] is True
        assert result["template_type"] == "tool-based"
        assert result["checks"]["template_requirements"] is True


@pytest.mark.asyncio
async def test_validate_skill_mcp_missing_template_files(temp_dir):
    """测试通过 MCP Server 验证缺少模板必需文件的技能."""
    # 获取 validate_skill 工具
    validate_skill_tool = None
    tools = await mcp.list_tools()
    for tool in tools:
        if hasattr(tool, "name") and tool.name == "validate_skill_tool":
            validate_skill_tool = tool
            break

    assert validate_skill_tool is not None

    # 创建 tool-based 模板的技能目录（但缺少必需文件）
    skill_dir = temp_dir / "test-missing-files"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("""---
name: test-missing-files
template: tool-based
description: |
  Missing files skill
allowed-tools: Read, Write
---
# Missing Files
""")
    for dir_name in ["references", "examples", "scripts", ".claude"]:
        (skill_dir / dir_name).mkdir()

    # 创建模拟的 MCP Context
    ctx = MagicMock()
    ctx.log = MagicMock()

    # 调用工具
    if hasattr(validate_skill_tool, "fn"):
        result = await validate_skill_tool.fn(
            ctx,
            skill_path=str(skill_dir),
        )

        assert result["success"] is True
        assert result["valid"] is False
        assert result["template_type"] == "tool-based"
        assert result["checks"]["template_requirements"] is False
        assert any("tool-integration.md" in e for e in result["errors"])


@pytest.mark.asyncio
async def test_validate_skill_mcp_internal_error(temp_dir):
    """测试通过 MCP Server 验证技能时的内部错误."""
    from unittest.mock import patch

    # 获取 validate_skill 工具
    validate_skill_tool = None
    tools = await mcp.list_tools()
    for tool in tools:
        if hasattr(tool, "name") and tool.name == "validate_skill_tool":
            validate_skill_tool = tool
            break

    assert validate_skill_tool is not None

    # 创建模拟的 MCP Context
    ctx = MagicMock()
    ctx.log = MagicMock()

    # 模拟 Path 构造函数抛出异常
    with patch("skill_creator_mcp.tools.skill_tools.Path", side_effect=RuntimeError("Simulated error")):
        result = await validate_skill_tool.fn(
            ctx,
            skill_path="/some/path",
        )

        assert result["success"] is False
        assert result["error_type"] == "internal_error"
        assert "验证过程出错" in result["errors"][0]
