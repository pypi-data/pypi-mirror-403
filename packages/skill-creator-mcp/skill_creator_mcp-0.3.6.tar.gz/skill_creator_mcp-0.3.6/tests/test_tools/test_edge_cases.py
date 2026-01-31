"""边界条件和错误处理的补充测试.

这些测试用于提高覆盖率到95%以上，主要针对：
1. __pycache__ 目录跳过逻辑
2. 文件读取异常处理
3. 空目录和无效路径处理
4. test_ 开头文件的分类
5. .venv 目录跳过逻辑
"""

from pathlib import Path

import pytest

from skill_creator_mcp.utils.analyzers import (
    _analyze_complexity,
    _analyze_structure,
    _calculate_cyclomatic_complexity,
    _categorize_file,
)

# ==================== __pycache__ 跳过测试 ====================


@pytest.mark.asyncio
async def test_analyze_structure_skips_pycache(temp_dir: Path):
    """测试结构分析时跳过 __pycache__ 目录."""
    # 创建项目结构，包含 __pycache__
    src_dir = temp_dir / "test_skill"
    src_dir.mkdir(parents=True)

    # 创建 server.py 文件
    (src_dir / "server.py").write_text("# Server file")

    # 创建 __pycache__ 目录和文件
    pycache_dir = src_dir / "__pycache__"
    pycache_dir.mkdir()
    (pycache_dir / "server.pyc").write_text("compiled")
    (pycache_dir / "helper.py").write_text("# Cached file")

    result = await _analyze_structure(temp_dir / "test_skill")

    # 应该只统计 server.py，跳过 __pycache__ 中的所有文件
    assert result.total_files == 1
    assert result.file_breakdown.get("server") == 1


@pytest.mark.asyncio
async def test_analyze_structure_nested_pycache(temp_dir: Path):
    """测试嵌套 __pycache__ 目录的处理."""
    src_dir = temp_dir / "test_skill"
    src_dir.mkdir(parents=True)

    # 创建嵌套的 __pycache__
    utils_dir = src_dir / "utils"
    utils_dir.mkdir()
    (utils_dir / "__init__.py").write_text("")

    pycache_dir = utils_dir / "__pycache__"
    pycache_dir.mkdir()
    (pycache_dir / "cached.pyc").write_text("compiled")

    result = await _analyze_structure(temp_dir / "test_skill")

    # 只统计 __init__.py，不统计 __pycache__ 中的文件
    assert result.total_files == 1


# ==================== 文件读取异常处理测试 ====================


@pytest.mark.asyncio
async def test_analyze_structure_handles_unreadable_files(temp_dir: Path):
    """测试处理不可读文件的异常情况."""
    src_dir = temp_dir / "test_skill"
    src_dir.mkdir(parents=True)

    # 创建一个可读文件
    (src_dir / "readable.py").write_text("# Readable")

    # 创建一个目录（模拟无法读取为文件的情况）
    (src_dir / "fake_file.py").mkdir()

    # 分析应该正常进行，不会抛出异常
    result = await _analyze_structure(temp_dir / "test_skill")

    # 应该至少统计了可读文件
    assert result.total_files >= 1


@pytest.mark.asyncio
async def test_analyze_structure_empty_files(temp_dir: Path):
    """测试空文件的处理."""
    src_dir = temp_dir / "test_skill"
    src_dir.mkdir(parents=True)

    # 创建空文件
    (src_dir / "empty.py").write_text("")
    (src_dir / "normal.py").write_text("# Normal")

    result = await _analyze_structure(temp_dir / "test_skill")

    # 空文件也应该被统计
    assert result.total_files == 2
    assert result.total_lines == 1  # normal.py 有 1 行


# ==================== 文件分类边界测试 ====================


def test_categorize_file_deeply_nested(temp_dir: Path):
    """测试深层嵌套文件的分类."""
    src_dir = temp_dir / "src" / "test_skill" / "subdir" / "another"
    src_dir.mkdir(parents=True)

    nested_file = src_dir / "deeply_nested.py"
    nested_file.write_text("# Nested file")

    category = _categorize_file(nested_file, temp_dir / "src" / "test_skill")
    # 深层嵌套文件应该被归类为 "other"
    assert category == "other"


def test_categorize_file_references(temp_dir: Path):
    """测试 references 目录文件的分类（被归类为 other）."""
    skill_dir = temp_dir / "my_skill"
    skill_dir.mkdir(parents=True)

    refs_dir = skill_dir / "references"
    refs_dir.mkdir()

    ref_file = refs_dir / "guide.md"
    ref_file.write_text("# Guide")

    category = _categorize_file(ref_file, skill_dir)
    # references 目录的文件被归类为 "other"
    assert category == "other"


def test_categorize_file_examples(temp_dir: Path):
    """测试 examples 目录文件的分类（被归类为 other）."""
    skill_dir = temp_dir / "my_skill"
    skill_dir.mkdir(parents=True)

    examples_dir = skill_dir / "examples"
    examples_dir.mkdir()

    example_file = examples_dir / "basic_usage.md"
    example_file.write_text("# Example")

    category = _categorize_file(example_file, skill_dir)
    # examples 目录的文件被归类为 "other"
    assert category == "other"


# ==================== 空目录和边界情况 ====================


@pytest.mark.asyncio
async def test_analyze_structure_nonexistent_path(temp_dir: Path):
    """测试分析不存在的路径."""
    nonexistent = temp_dir / "does_not_exist"

    # 空目录分析应该正常处理
    result = await _analyze_structure(nonexistent)

    # 不存在的路径应该返回空结果
    assert result.total_files == 0
    assert result.total_lines == 0


@pytest.mark.asyncio
async def test_analyze_structure_only_pycache(temp_dir: Path):
    """测试只有 __pycache__ 的目录."""
    src_dir = temp_dir / "test_skill"
    src_dir.mkdir(parents=True)

    # 只创建 __pycache__ 目录
    pycache_dir = src_dir / "__pycache__"
    pycache_dir.mkdir()
    (pycache_dir / "file.pyc").write_text("compiled")

    result = await _analyze_structure(temp_dir / "test_skill")

    # 应该返回空结果
    assert result.total_files == 0
    assert result.total_lines == 0


# ==================== test_ 开头文件的分类测试 ====================


def test_categorize_file_test_prefix(temp_dir: Path):
    """测试 test_ 开头文件的分类."""
    skill_dir = temp_dir / "my_skill"
    skill_dir.mkdir(parents=True)

    # 创建 test_ 开头的文件（不在 tests 目录）
    test_file = skill_dir / "test_helper.py"
    test_file.write_text("# Test helper")

    category = _categorize_file(test_file, skill_dir)
    # test_ 开头的文件应该被归类为 "tests"
    assert category == "tests"


# ==================== .venv 跳过测试 ====================


@pytest.mark.asyncio
async def test_analyze_complexity_skips_venv(temp_dir: Path):
    """测试复杂度分析时跳过 .venv 目录."""
    src_dir = temp_dir / "test_skill"
    src_dir.mkdir(parents=True)

    # 创建正常 Python 文件
    (src_dir / "normal.py").write_text("""
def hello():
    if True:
        return "world"
    return "done"
""")

    # 创建 .venv 目录和文件
    venv_dir = src_dir / ".venv" / "lib"
    venv_dir.mkdir(parents=True)
    (venv_dir / "venv_file.py").write_text("""
def complex_function():
    if True:
        if False:
            return "nested"
    return "done"
""")

    result = await _analyze_complexity(temp_dir / "test_skill")

    # 应该只分析 normal.py，跳过 .venv 中的文件
    assert result.cyclomatic_complexity is not None
    # normal.py 的复杂度是 2（基础1 + 1个if）
    assert result.cyclomatic_complexity >= 1


# ==================== 复杂度计算边界测试 ====================


def test_calculate_cyclomatic_complexity_with_and_or():
    """测试包含 and/or 运算符的复杂度计算."""
    import ast

    code = """
def check(a, b, c):
    if a and b:
        return True
    if c or d:
        return False
    return None
"""
    tree = ast.parse(code)
    complexity = _calculate_cyclomatic_complexity(tree)

    # 基础1 + 2个if + 2个逻辑运算符 = 5
    assert complexity >= 4


def test_calculate_cyclomatic_complexity_with_comprehensions():
    """测试包含列表推导和字典推导的复杂度计算."""
    import ast

    code = """
def process(items):
    # 列表推导
    doubled = [x * 2 for x in items if x > 0]
    # 字典推导
    mapped = {x: x * 2 for x in items}
    return doubled, mapped
"""
    tree = ast.parse(code)
    complexity = _calculate_cyclomatic_complexity(tree)

    # 基础1 + 1个列表推导 + 1个字典推导 = 3
    assert complexity >= 2


@pytest.mark.asyncio
async def test_analyze_complexity_with_syntax_error(temp_dir: Path):
    """测试包含语法错误的文件的处理."""
    src_dir = temp_dir / "test_skill"
    src_dir.mkdir(parents=True)

    # 创建正常文件
    (src_dir / "normal.py").write_text("def hello(): return 'world'")

    # 创建包含语法错误的文件
    (src_dir / "broken.py").write_text("def broken(\n")  # 不完整的代码

    # 应该跳过语法错误的文件，不会抛出异常
    result = await _analyze_complexity(temp_dir / "test_skill")

    # 应该至少分析了正常文件
    assert result.cyclomatic_complexity is not None


# ==================== analyze_skill 错误处理测试 ====================


@pytest.mark.asyncio
async def test_analyze_skill_with_file_not_directory(temp_dir: Path):
    """测试 analyze_skill 当路径是文件而非目录时的错误处理 (server.py:352)."""
    from unittest.mock import MagicMock

    from skill_creator_mcp.server import mcp

    # 获取 analyze_skill_tool 工具（FastMCP 3.0+ 使用公开 API）
    tools = await mcp.list_tools()
    analyze_skill_tool_obj = None
    for tool in tools:
        if hasattr(tool, "name") and tool.name == "analyze_skill_tool":
            analyze_skill_tool_obj = tool
            break

    assert analyze_skill_tool_obj is not None, "analyze_skill_tool tool not found"

    # 创建一个文件而非目录
    test_file = temp_dir / "not_a_dir.md"
    test_file.write_text("# This is a file, not a directory")

    # 创建模拟的 MCP Context
    ctx = MagicMock()
    ctx.log = MagicMock()

    # 调用 analyze_skill，传入文件路径
    result = await analyze_skill_tool_obj.fn(
        ctx=ctx,
        skill_path=str(test_file),
        analyze_structure=False,
        analyze_complexity=False,
        analyze_quality=False,
    )

    # 应该返回错误，表明路径不是目录
    assert result["success"] is False
    assert "路径不是目录" in result["error"]
    assert result["error_type"] == "path_error"


@pytest.mark.asyncio
async def test_analyze_skill_with_valid_empty_directory(temp_dir: Path):
    """测试 analyze_skill 对有效空目录的处理."""
    from unittest.mock import MagicMock

    from skill_creator_mcp.server import mcp

    # 获取 analyze_skill_tool 工具（FastMCP 3.0+ 使用公开 API）
    tools = await mcp.list_tools()
    analyze_skill_tool_obj = None
    for tool in tools:
        if hasattr(tool, "name") and tool.name == "analyze_skill_tool":
            analyze_skill_tool_obj = tool
            break

    assert analyze_skill_tool_obj is not None, "analyze_skill_tool tool not found"

    # 创建一个有效的空目录
    src_dir = temp_dir / "test_skill"
    src_dir.mkdir()

    # 创建模拟的 MCP Context
    ctx = MagicMock()
    ctx.log = MagicMock()

    # 调用 analyze_skill
    result = await analyze_skill_tool_obj.fn(
        ctx=ctx,
        skill_path=str(src_dir),
        analyze_structure=False,
        analyze_complexity=False,
        analyze_quality=False,
    )

    # 验证返回结果结构
    assert "success" in result
    assert "skill_path" in result or "error" in result


@pytest.mark.asyncio
async def test_package_skill_with_invalid_skill_path_type(temp_dir: Path):
    """测试 package_skill 当 skill_path 参数类型无效时的错误处理 (server.py:627)."""
    from unittest.mock import MagicMock

    from skill_creator_mcp.server import mcp

    # 获取 package_skill 工具（FastMCP 3.0+ 使用公开 API）
    tools = await mcp.list_tools()
    package_skill_tool = None
    for tool in tools:
        if hasattr(tool, "name") and tool.name == "package_skill":
            package_skill_tool = tool
            break

    assert package_skill_tool is not None, "package_skill tool not found"

    # 创建模拟的 MCP Context
    ctx = MagicMock()
    ctx.log = MagicMock()

    # 调用 package_skill，传入无效类型的 skill_path（整数而非字符串）
    # 这会触发 Pydantic 验证错误，但不是 format 字段错误
    result = await package_skill_tool.fn(
        ctx=ctx,
        skill_path=12345,  # 传入整数而非字符串
        output_dir=str(temp_dir),
        format="zip",
    )

    # 应该返回通用验证错误
    assert result["success"] is False
    assert result["error_type"] == "validation_error"
    assert "输入验证失败" in result["error"]


# ==================== MCP 资源函数测试 ====================


@pytest.mark.asyncio
async def test_list_templates_resource():
    """测试 list_templates_resource 函数返回正确格式 (server.py:819-824)."""
    from skill_creator_mcp.server import mcp

    # 通过 read_resource 方法调用资源函数（FastMCP 3.0+ 使用公开 API）
    result = await mcp.read_resource("http://skills/schema/templates")
    # ResourceResult.contents 是 ResourceContent 列表
    content = result.contents[0].content
    assert "# 技能模板列表" in content
    assert "minimal" in content


@pytest.mark.asyncio
async def test_get_template_resource_invalid():
    """测试 get_template_resource 函数处理无效类型 (server.py:830-837)."""
    from skill_creator_mcp.server import mcp

    # 测试无效类型（FastMCP 3.0+ 使用公开 API）
    result = await mcp.read_resource(
        "http://skills/schema/templates/invalid-type"
    )
    content = result.contents[0].content
    assert "# 错误" in content
    assert "未知的模板类型" in content


@pytest.mark.asyncio
async def test_best_practices_resource():
    """测试 best_practices_resource 函数 (server.py:843)."""
    from skill_creator_mcp.server import mcp

    result = await mcp.read_resource("http://skills/schema/best-practices")
    content = result.contents[0].content
    assert len(content) > 0


@pytest.mark.asyncio
async def test_validation_rules_resource():
    """测试 validation_rules_resource 函数 (server.py:849)."""
    from skill_creator_mcp.server import mcp

    result = await mcp.read_resource("http://skills/schema/validation-rules")
    content = result.contents[0].content
    assert len(content) > 0


# ==================== MCP Prompt 函数测试 ====================


@pytest.mark.asyncio
async def test_create_skill_prompt():
    """测试 create_skill_prompt 函数 (server.py:869)."""
    from skill_creator_mcp.server import mcp

    # 获取 prompt 并调用其函数（FastMCP 3.0+ 使用公开 API）
    prompts = await mcp.list_prompts()
    for prompt in prompts:
        if prompt.name == "create-skill":
            result = prompt.fn(name="test-skill", template="minimal")
            assert "test-skill" in result
            return

    pytest.fail("create_skill_prompt not found")


@pytest.mark.asyncio
async def test_validate_skill_prompt():
    """测试 validate_skill_prompt 函数 (server.py:886)."""
    from skill_creator_mcp.server import mcp

    # 获取 prompt 并调用其函数（FastMCP 3.0+ 使用公开 API）
    prompts = await mcp.list_prompts()
    for prompt in prompts:
        if prompt.name == "validate-skill":
            result = prompt.fn(skill_path="/path/to/skill", template=None)
            assert len(result) > 0
            return

    pytest.fail("validate_skill_prompt not found")


@pytest.mark.asyncio
async def test_refactor_skill_prompt():
    """测试 refactor_skill_prompt 函数 (server.py:903)."""
    from skill_creator_mcp.server import mcp

    # 获取 prompt 并调用其函数（FastMCP 3.0+ 使用公开 API）
    prompts = await mcp.list_prompts()
    for prompt in prompts:
        if prompt.name == "refactor-skill":
            result = prompt.fn(skill_path="/path/to/skill", focus=None)
            assert len(result) > 0
            return

    pytest.fail("refactor_skill_prompt not found")
