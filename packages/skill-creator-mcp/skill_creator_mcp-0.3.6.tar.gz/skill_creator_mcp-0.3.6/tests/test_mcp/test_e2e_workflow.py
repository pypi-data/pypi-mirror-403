"""MCP Tools 端到端集成测试.

测试完整的技能开发工作流程：
创建 → 分析 → 重构 → 打包
"""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from skill_creator_mcp.server import mcp


@pytest.mark.asyncio
async def test_e2e_complete_workflow(temp_dir):
    """测试完整的技能开发工作流程."""
    # 获取所有 MCP 工具
    init_skill_tool = None
    analyze_skill_tool = None
    refactor_skill_tool = None
    package_skill_tool = None

    tools = await mcp.list_tools()
    for tool in tools:
        if hasattr(tool, "name"):
            if tool.name == "init_skill_tool":
                init_skill_tool = tool
            elif tool.name == "analyze_skill_tool":
                analyze_skill_tool = tool
            elif tool.name == "refactor_skill_tool":
                refactor_skill_tool = tool
            elif tool.name == "package_skill":
                package_skill_tool = tool

    assert init_skill_tool is not None, "init_skill tool not found"
    assert analyze_skill_tool is not None, "analyze_skill tool not found"
    assert refactor_skill_tool is not None, "refactor_skill tool not found"
    assert package_skill_tool is not None, "package_skill_tool not found"

    ctx = MagicMock()
    ctx.log = MagicMock()

    skill_name = "test-e2e-skill"
    skill_dir = temp_dir / skill_name
    output_dir = temp_dir / "packages"
    output_dir.mkdir()

    # 步骤 1: 创建技能
    if hasattr(init_skill_tool, "fn"):
        init_result = await init_skill_tool.fn(
            ctx,
            name=skill_name,
            template="minimal",
            output_dir=str(temp_dir),
        )
        assert init_result["success"] is True
        assert skill_name in init_result["skill_path"]
        assert (skill_dir / "SKILL.md").exists()

    # 步骤 2: 分析技能
    if hasattr(analyze_skill_tool, "fn"):
        analyze_result = await analyze_skill_tool.fn(
            ctx,
            skill_path=str(skill_dir),
            analyze_structure=True,
            analyze_complexity=True,
            analyze_quality=True,
        )
        assert analyze_result["success"] is True
        assert "structure" in analyze_result
        assert "quality" in analyze_result
        assert analyze_result["quality"]["overall_score"] >= 0

    # 步骤 3: 重构技能（分析建议）
    if hasattr(refactor_skill_tool, "fn"):
        refactor_result = await refactor_skill_tool.fn(
            ctx,
            skill_path=str(skill_dir),
            analyze_structure=True,
            analyze_complexity=True,
            analyze_quality=True,
        )
        assert refactor_result["success"] is True
        assert "suggestions" in refactor_result
        assert "report" in refactor_result
        assert refactor_result["skill_name"] == skill_name

    # 步骤 4: 打包技能
    if hasattr(package_skill_tool, "fn"):
        package_result = await package_skill_tool.fn(
            ctx,
            skill_path=str(skill_dir),
            output_dir=str(output_dir),
            format="zip",
            include_tests=False,
            validate_before_package=False,
        )
        assert package_result["success"] is True
        assert package_result["format"] == "zip"
        assert Path(package_result["package_path"]).exists()


@pytest.mark.asyncio
async def test_e2e_workflow_with_validation(temp_dir):
    """测试带验证的完整工作流程."""
    init_skill_tool = None
    analyze_skill_tool = None
    package_skill_tool = None

    tools = await mcp.list_tools()
    for tool in tools:
        if hasattr(tool, "name"):
            if tool.name == "init_skill_tool":
                init_skill_tool = tool
            elif tool.name == "analyze_skill_tool":
                analyze_skill_tool = tool
            elif tool.name == "package_skill":
                package_skill_tool = tool

    ctx = MagicMock()
    ctx.log = MagicMock()

    skill_name = "test-e2e-valid"
    skill_dir = temp_dir / skill_name
    output_dir = temp_dir / "packages"
    output_dir.mkdir()

    # 创建完整模板的技能
    if hasattr(init_skill_tool, "fn"):
        init_result = await init_skill_tool.fn(
            ctx,
            name=skill_name,
            template="tool-based",
            output_dir=str(temp_dir),
        )
        assert init_result["success"] is True

    # 分析验证
    if hasattr(analyze_skill_tool, "fn"):
        analyze_result = await analyze_skill_tool.fn(
            ctx,
            skill_path=str(skill_dir),
        )
        assert analyze_result["success"] is True

    # 打包时验证
    if hasattr(package_skill_tool, "fn"):
        package_result = await package_skill_tool.fn(
            ctx,
            skill_path=str(skill_dir),
            output_dir=str(output_dir),
            format="zip",
            validate_before_package=True,
        )
        assert package_result["success"] is True
        assert package_result["validation_passed"] is True


@pytest.mark.asyncio
async def test_e2e_error_recovery(temp_dir):
    """测试工作流程中的错误恢复."""
    init_skill_tool = None
    analyze_skill_tool = None

    tools = await mcp.list_tools()
    for tool in tools:
        if hasattr(tool, "name"):
            if tool.name == "init_skill_tool":
                init_skill_tool = tool
            elif tool.name == "analyze_skill_tool":
                analyze_skill_tool = tool

    ctx = MagicMock()
    ctx.log = MagicMock()

    skill_dir = temp_dir / "test-error-skill"
    output_dir = temp_dir / "packages"
    output_dir.mkdir()

    # 尝试分析不存在的技能
    if hasattr(analyze_skill_tool, "fn"):
        analyze_result = await analyze_skill_tool.fn(
            ctx,
            skill_path=str(skill_dir),
        )
        assert analyze_result["success"] is False
        assert "error" in analyze_result

    # 创建技能
    if hasattr(init_skill_tool, "fn"):
        init_result = await init_skill_tool.fn(
            ctx,
            name="test-error-skill",
            template="minimal",
            output_dir=str(temp_dir),
        )
        assert init_result["success"] is True

    # 现在分析应该成功
    if hasattr(analyze_skill_tool, "fn"):
        analyze_result = await analyze_skill_tool.fn(
            ctx,
            skill_path=str(skill_dir),
        )
        assert analyze_result["success"] is True


@pytest.mark.asyncio
async def test_e2e_iterative_refinement(temp_dir):
    """测试迭代改进的工作流程."""
    init_skill_tool = None
    refactor_skill_tool = None
    analyze_skill_tool = None

    tools = await mcp.list_tools()
    for tool in tools:
        if hasattr(tool, "name"):
            if tool.name == "init_skill_tool":
                init_skill_tool = tool
            elif tool.name == "refactor_skill_tool":
                refactor_skill_tool = tool
            elif tool.name == "analyze_skill_tool":
                analyze_skill_tool = tool

    ctx = MagicMock()
    ctx.log = MagicMock()

    skill_name = "test-iterative"
    skill_dir = temp_dir / skill_name

    # 创建基础技能
    if hasattr(init_skill_tool, "fn"):
        init_result = await init_skill_tool.fn(
            ctx,
            name=skill_name,
            template="minimal",
            output_dir=str(temp_dir),
        )
        assert init_result["success"] is True

    # 第一次分析
    if hasattr(analyze_skill_tool, "fn"):
        first_analysis = await analyze_skill_tool.fn(
            ctx,
            skill_path=str(skill_dir),
        )
        assert first_analysis["success"] is True
        _first_score = first_analysis["quality"]["overall_score"]

    # 获取重构建议
    if hasattr(refactor_skill_tool, "fn"):
        refactor_result = await refactor_skill_tool.fn(
            ctx,
            skill_path=str(skill_dir),
        )
        assert refactor_result["success"] is True
        _suggestions = refactor_result["suggestions"]

        # 根据建议改进技能（模拟）
        # 在真实场景中，这里会应用建议的修改

    # 第二次分析（验证改进）
    if hasattr(analyze_skill_tool, "fn"):
        second_analysis = await analyze_skill_tool.fn(
            ctx,
            skill_path=str(skill_dir),
        )
        assert second_analysis["success"] is True
        second_score = second_analysis["quality"]["overall_score"]

        # 验证分析可以被重复执行
        assert second_score >= 0


@pytest.mark.asyncio
async def test_e2e_multiple_skills(temp_dir):
    """测试管理多个技能的工作流程."""
    init_skill_tool = None
    analyze_skill_tool = None

    tools = await mcp.list_tools()
    for tool in tools:
        if hasattr(tool, "name"):
            if tool.name == "init_skill_tool":
                init_skill_tool = tool
            elif tool.name == "analyze_skill_tool":
                analyze_skill_tool = tool

    ctx = MagicMock()
    ctx.log = MagicMock()

    # 创建多个技能
    skill_names = ["skill-a", "skill-b", "skill-c"]
    skill_dirs = []

    for name in skill_names:
        if hasattr(init_skill_tool, "fn"):
            result = await init_skill_tool.fn(
                ctx,
                name=name,
                template="minimal",
                output_dir=str(temp_dir),
            )
            assert result["success"] is True
            skill_dirs.append(result["skill_path"])

    # 分析所有技能
    analysis_results = []
    for skill_path in skill_dirs:
        if hasattr(analyze_skill_tool, "fn"):
            result = await analyze_skill_tool.fn(
                ctx,
                skill_path=skill_path,
            )
            assert result["success"] is True
            analysis_results.append(result)

    # 验证每个技能都有独立的分析结果
    assert len(analysis_results) == 3
    for i, result in enumerate(analysis_results):
        assert result["success"] is True
        assert skill_names[i] in result["skill_path"]


@pytest.mark.asyncio
async def test_e2e_package_formats(temp_dir):
    """测试不同打包格式的端到端工作流程."""
    init_skill_tool = None
    package_skill_tool = None

    tools = await mcp.list_tools()
    for tool in tools:
        if hasattr(tool, "name"):
            if tool.name == "init_skill_tool":
                init_skill_tool = tool
            elif tool.name == "package_skill":
                package_skill_tool = tool

    ctx = MagicMock()
    ctx.log = MagicMock()

    skill_name = "test-formats"
    skill_dir = temp_dir / skill_name
    output_dir = temp_dir / "packages"
    output_dir.mkdir()

    # 创建技能
    if hasattr(init_skill_tool, "fn"):
        init_result = await init_skill_tool.fn(
            ctx,
            name=skill_name,
            template="minimal",
            output_dir=str(temp_dir),
        )
        assert init_result["success"] is True

    # 测试不同打包格式
    formats = ["zip", "tar.gz", "tar.bz2"]
    package_paths = []

    for fmt in formats:
        if hasattr(package_skill_tool, "fn"):
            result = await package_skill_tool.fn(
                ctx,
                skill_path=str(skill_dir),
                output_dir=str(output_dir),
                format=fmt,
                validate_before_package=False,
            )
            assert result["success"] is True
            assert result["format"] == fmt
            assert Path(result["package_path"]).exists()
            package_paths.append(result["package_path"])

    # 验证所有包都创建成功
    assert len(package_paths) == 3
    for path in package_paths:
        assert Path(path).exists()
