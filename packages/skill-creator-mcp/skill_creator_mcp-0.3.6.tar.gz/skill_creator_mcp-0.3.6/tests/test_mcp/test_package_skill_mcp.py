"""测试 FastMCP 包装的 package_skill 工具."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from skill_creator_mcp.server import mcp


@pytest.mark.asyncio
async def test_package_skill_mcp_basic_zip(temp_dir):
    """测试通过 MCP Server 打包技能为 ZIP 格式."""
    # 获取 package_skill 工具
    package_skill_tool = None
    tools = await mcp.list_tools()
    for tool in tools:
        if hasattr(tool, "name") and tool.name == "package_skill":
            package_skill_tool = tool
            break

    assert package_skill_tool is not None, "package_skill not found in MCP server"

    # 创建技能目录
    skill_dir = temp_dir / "test-package-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        "---\nname: test-package-skill\ndescription: Test\nallowed-tools: Read\n---\n# Test"
    )
    for dir_name in ["references", "examples", "scripts", ".claude"]:
        (skill_dir / dir_name).mkdir()

    output_dir = temp_dir / "output"
    output_dir.mkdir()

    # 创建模拟的 MCP Context
    ctx = MagicMock()
    ctx.log = MagicMock()

    # 调用工具（默认 strict=False）
    if hasattr(package_skill_tool, "fn"):
        result = await package_skill_tool.fn(
            ctx,
            skill_path=str(skill_dir),
            output_dir=str(output_dir),
            format="zip",
            include_tests=False,
            strict=False,
            validate_before_package=False,
        )

        assert result["success"] is True
        assert result["format"] == "zip"
        assert result["files_included"] > 0
        assert result["package_path"] is not None
        assert Path(result["package_path"]).exists()


@pytest.mark.asyncio
async def test_package_skill_mcp_strict_mode_with_version(temp_dir):
    """测试 strict 模式需要 version 参数."""
    package_skill_tool = None
    tools = await mcp.list_tools()
    for tool in tools:
        if hasattr(tool, "name") and tool.name == "package_skill":
            package_skill_tool = tool
            break

    assert package_skill_tool is not None

    # 创建技能目录
    skill_dir = temp_dir / "test-strict-mode"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        "---\nname: test-strict\ndescription: Test\nallowed-tools: Read\n---\n# Test"
    )
    for dir_name in ["references", "examples", "scripts", ".claude"]:
        (skill_dir / dir_name).mkdir()

    output_dir = temp_dir / "output"
    output_dir.mkdir()

    # 创建模拟的 MCP Context
    ctx = MagicMock()
    ctx.log = MagicMock()

    # 测试 strict=True 但没有 version 参数
    if hasattr(package_skill_tool, "fn"):
        result = await package_skill_tool.fn(
            ctx,
            skill_path=str(skill_dir),
            output_dir=str(output_dir),
            format="zip",
            include_tests=False,
            strict=True,
            validate_before_package=False,
        )

        assert result["success"] is False
        assert "strict模式需要version参数" in result["error"]
        assert result["error_type"] == "validation_error"


@pytest.mark.asyncio
async def test_package_skill_mcp_strict_mode_with_version_provided(temp_dir):
    """测试 strict 模式带 version 参数."""
    package_skill_tool = None
    tools = await mcp.list_tools()
    for tool in tools:
        if hasattr(tool, "name") and tool.name == "package_skill":
            package_skill_tool = tool
            break

    assert package_skill_tool is not None

    # 创建技能目录
    skill_dir = temp_dir / "test-strict-version"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        "---\nname: test-strict-version\ndescription: Test\nallowed-tools: Read\n---\n# Test"
    )
    for dir_name in ["references", "examples", "scripts", ".claude"]:
        (skill_dir / dir_name).mkdir()

    output_dir = temp_dir / "output"
    output_dir.mkdir()

    # 创建模拟的 MCP Context
    ctx = MagicMock()
    ctx.log = MagicMock()

    # 测试 strict=True 带正确的 version 参数
    if hasattr(package_skill_tool, "fn"):
        result = await package_skill_tool.fn(
            ctx,
            skill_path=str(skill_dir),
            output_dir=str(output_dir),
            version="0.3.1",
            format="zip",
            include_tests=False,
            strict=True,
            validate_before_package=False,
        )

        assert result["success"] is True
        assert result["format"] == "zip"
        # 验证包名包含版本号
        assert "0.3.1" in result["package_path"]


@pytest.mark.asyncio
async def test_package_skill_mcp_with_validation(temp_dir):
    """测试通过 MCP Server 打包技能（带验证）."""
    package_skill_tool = None
    tools = await mcp.list_tools()
    for tool in tools:
        if hasattr(tool, "name") and tool.name == "package_skill":
            package_skill_tool = tool
            break

    assert package_skill_tool is not None

    # 创建有效的技能目录
    skill_dir = temp_dir / "test-package-valid"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        "---\n"
        "name: test-package-valid\n"
        "description: A valid skill\n"
        "allowed-tools: [Read, Write]\n"
        "---\n"
        "# Test Skill\n"
    )
    for dir_name in ["references", "examples", "scripts", ".claude"]:
        (skill_dir / dir_name).mkdir()

    output_dir = temp_dir / "output"
    output_dir.mkdir()

    # 创建模拟的 MCP Context
    ctx = MagicMock()
    ctx.log = MagicMock()

    # 调用工具（带验证）
    if hasattr(package_skill_tool, "fn"):
        result = await package_skill_tool.fn(
            ctx,
            skill_path=str(skill_dir),
            output_dir=str(output_dir),
            format="zip",
            include_tests=False,
            strict=False,
            validate_before_package=True,
        )

        assert result["success"] is True
        assert result["validation_passed"] is True


@pytest.mark.asyncio
async def test_package_skill_mcp_validation_fails(temp_dir):
    """测试通过 MCP Server 打包技能（验证失败）."""
    package_skill_tool = None
    tools = await mcp.list_tools()
    for tool in tools:
        if hasattr(tool, "name") and tool.name == "package_skill":
            package_skill_tool = tool
            break

    assert package_skill_tool is not None

    # 创建无效的技能目录（缺少必需目录）
    skill_dir = temp_dir / "test-package-invalid"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("# Invalid")

    output_dir = temp_dir / "output"
    output_dir.mkdir()

    # 创建模拟的 MCP Context
    ctx = MagicMock()
    ctx.log = MagicMock()

    # 调用工具（带验证，应该失败）
    if hasattr(package_skill_tool, "fn"):
        result = await package_skill_tool.fn(
            ctx,
            skill_path=str(skill_dir),
            output_dir=str(output_dir),
            format="zip",
            strict=False,
            validate_before_package=True,
        )

        assert result["success"] is False
        assert result["validation_passed"] is False
        assert len(result["validation_errors"]) > 0


@pytest.mark.asyncio
async def test_package_skill_mcp_tar_gz(temp_dir):
    """测试通过 MCP Server 打包技能为 tar.gz 格式."""
    package_skill_tool = None
    tools = await mcp.list_tools()
    for tool in tools:
        if hasattr(tool, "name") and tool.name == "package_skill":
            package_skill_tool = tool
            break

    assert package_skill_tool is not None

    # 创建技能目录
    skill_dir = temp_dir / "test-package-tar"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("---\nname: test\ndescription: Test\n---\n# Test")
    for dir_name in ["references", "examples", "scripts", ".claude"]:
        (skill_dir / dir_name).mkdir()

    output_dir = temp_dir / "output"
    output_dir.mkdir()

    # 创建模拟的 MCP Context
    ctx = MagicMock()
    ctx.log = MagicMock()

    # 调用工具（tar.gz 格式）
    if hasattr(package_skill_tool, "fn"):
        result = await package_skill_tool.fn(
            ctx,
            skill_path=str(skill_dir),
            output_dir=str(output_dir),
            format="tar.gz",
            include_tests=False,
            strict=False,
            validate_before_package=False,
        )

        assert result["success"] is True
        assert result["format"] == "tar.gz"
        assert result["package_path"] is not None
        assert Path(result["package_path"]).exists()


@pytest.mark.asyncio
async def test_package_skill_mcp_exclude_tests(temp_dir):
    """测试通过 MCP Server 打包技能（排除测试文件）."""
    package_skill_tool = None
    tools = await mcp.list_tools()
    for tool in tools:
        if hasattr(tool, "name") and tool.name == "package_skill":
            package_skill_tool = tool
            break

    assert package_skill_tool is not None

    # 创建技能目录
    skill_dir = temp_dir / "test-package-no-tests"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("---\nname: test\ndescription: Test\n---\n# Test")
    for dir_name in ["references", "examples", "scripts", ".claude"]:
        (skill_dir / dir_name).mkdir()

    # 创建测试文件
    tests_dir = skill_dir / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_example.py").write_text("def test(): pass")

    output_dir = temp_dir / "output"
    output_dir.mkdir()

    # 创建模拟的 MCP Context
    ctx = MagicMock()
    ctx.log = MagicMock()

    # 调用工具（排除测试）
    if hasattr(package_skill_tool, "fn"):
        result = await package_skill_tool.fn(
            ctx,
            skill_path=str(skill_dir),
            output_dir=str(output_dir),
            format="zip",
            include_tests=False,
            strict=False,
            validate_before_package=False,
        )

        assert result["success"] is True
        # 测试文件应该被排除
        assert result["files_included"] == 1  # 只有 SKILL.md


@pytest.mark.asyncio
async def test_package_skill_mcp_nonexistent_directory(temp_dir):
    """测试通过 MCP Server 打包不存在的目录."""
    package_skill_tool = None
    tools = await mcp.list_tools()
    for tool in tools:
        if hasattr(tool, "name") and tool.name == "package_skill":
            package_skill_tool = tool
            break

    assert package_skill_tool is not None

    output_dir = temp_dir / "output"
    output_dir.mkdir()

    # 创建模拟的 MCP Context
    ctx = MagicMock()
    ctx.log = MagicMock()

    # 调用工具（目录不存在）
    if hasattr(package_skill_tool, "fn"):
        result = await package_skill_tool.fn(
            ctx,
            skill_path=str(temp_dir / "nonexistent-skill"),
            output_dir=str(output_dir),
            format="zip",
            strict=False,
            validate_before_package=False,
        )

        assert result["success"] is False
        assert "目录不存在" in result["error"]


@pytest.mark.asyncio
async def test_package_skill_mcp_invalid_format(temp_dir):
    """测试通过 MCP Server 打包技能（无效格式）."""
    package_skill_tool = None
    tools = await mcp.list_tools()
    for tool in tools:
        if hasattr(tool, "name") and tool.name == "package_skill":
            package_skill_tool = tool
            break

    assert package_skill_tool is not None

    # 创建技能目录
    skill_dir = temp_dir / "test-package-invalid-format"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("# Test")

    output_dir = temp_dir / "output"
    output_dir.mkdir()

    # 创建模拟的 MCP Context
    ctx = MagicMock()
    ctx.log = MagicMock()

    # 调用工具（无效格式）
    if hasattr(package_skill_tool, "fn"):
        result = await package_skill_tool.fn(
            ctx,
            skill_path=str(skill_dir),
            output_dir=str(output_dir),
            format="invalid-format",
            strict=False,
            validate_before_package=False,
        )

        assert result["success"] is False
        assert result["error_type"] == "format_error"


@pytest.mark.asyncio
async def test_package_skill_mcp_with_size_info(temp_dir):
    """测试通过 MCP Server 打包技能（包大小信息）."""
    package_skill_tool = None
    tools = await mcp.list_tools()
    for tool in tools:
        if hasattr(tool, "name") and tool.name == "package_skill":
            package_skill_tool = tool
            break

    assert package_skill_tool is not None

    # 创建技能目录
    skill_dir = temp_dir / "test-package-size"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("---\nname: test\ndescription: Test\n---\n# Test")
    for dir_name in ["references", "examples", "scripts", ".claude"]:
        (skill_dir / dir_name).mkdir()

    output_dir = temp_dir / "output"
    output_dir.mkdir()

    # 创建模拟的 MCP Context
    ctx = MagicMock()
    ctx.log = MagicMock()

    # 调用工具
    if hasattr(package_skill_tool, "fn"):
        result = await package_skill_tool.fn(
            ctx,
            skill_path=str(skill_dir),
            output_dir=str(output_dir),
            format="zip",
            include_tests=False,
            strict=False,
            validate_before_package=False,
        )

        assert result["success"] is True
        # 检查包大小信息
        assert result["package_size"] is not None
        assert result["package_size"] > 0
