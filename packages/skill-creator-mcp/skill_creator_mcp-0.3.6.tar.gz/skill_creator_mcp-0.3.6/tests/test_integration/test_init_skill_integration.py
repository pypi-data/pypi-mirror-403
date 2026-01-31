"""init_skill 工具集成测试.

测试 init_skill 的完整流程，包括所有辅助函数。
"""

import pytest

from skill_creator_mcp.tools.skill_tools import (
    _create_example_examples,
    _create_example_scripts,
    _create_reference_files,
    _generate_skill_md_content,
)
from skill_creator_mcp.utils.file_ops import create_directory_structure_async, write_file_async
from skill_creator_mcp.utils.validators import validate_skill_name, validate_template_type


@pytest.mark.asyncio
async def test_full_init_skill_flow_minimal(temp_dir):
    """测试完整的 minimal 模板创建流程."""
    # 1. 验证输入
    validate_skill_name("test-minimal")
    validate_template_type("minimal")

    # 2. 创建目录结构
    skill_dir = await create_directory_structure_async(
        name="test-minimal",
        template_type="minimal",
        output_dir=temp_dir,
    )
    assert skill_dir.exists()

    # 3. 生成并写入 SKILL.md
    skill_md_content = _generate_skill_md_content("test-minimal", "minimal")
    await write_file_async(skill_dir / "SKILL.md", skill_md_content)
    assert (skill_dir / "SKILL.md").exists()

    # 4. 验证内容
    content = (skill_dir / "SKILL.md").read_text()
    assert "name: test-minimal" in content
    assert "最小化技能模板" in content


@pytest.mark.asyncio
async def test_full_init_skill_flow_tool_based(temp_dir):
    """测试完整的 tool-based 模板创建流程."""
    validate_skill_name("test-tool")
    validate_template_type("tool-based")

    skill_dir = await create_directory_structure_async(
        name="test-tool",
        template_type="tool-based",
        output_dir=temp_dir,
    )

    # 生成 SKILL.md
    skill_md_content = _generate_skill_md_content("test-tool", "tool-based")
    await write_file_async(skill_dir / "SKILL.md", skill_md_content)

    # 创建引用文件
    await _create_reference_files(skill_dir, "tool-based")

    # 验证文件
    assert (skill_dir / "references" / "tool-integration.md").exists()
    assert (skill_dir / "references" / "usage-examples.md").exists()

    # 验证 SKILL.md 内容
    content = (skill_dir / "SKILL.md").read_text()
    assert "基于工具的技能模板" in content


@pytest.mark.asyncio
async def test_full_init_skill_flow_workflow_based(temp_dir):
    """测试完整的 workflow-based 模板创建流程."""
    validate_skill_name("test-workflow")
    validate_template_type("workflow-based")

    skill_dir = await create_directory_structure_async(
        name="test-workflow",
        template_type="workflow-based",
        output_dir=temp_dir,
    )

    skill_md_content = _generate_skill_md_content("test-workflow", "workflow-based")
    await write_file_async(skill_dir / "SKILL.md", skill_md_content)

    await _create_reference_files(skill_dir, "workflow-based")

    assert (skill_dir / "references" / "workflow-steps.md").exists()
    assert (skill_dir / "references" / "decision-points.md").exists()


@pytest.mark.asyncio
async def test_full_init_skill_flow_analyzer_based(temp_dir):
    """测试完整的 analyzer-based 模板创建流程."""
    validate_skill_name("test-analyzer")
    validate_template_type("analyzer-based")

    skill_dir = await create_directory_structure_async(
        name="test-analyzer",
        template_type="analyzer-based",
        output_dir=temp_dir,
    )

    skill_md_content = _generate_skill_md_content("test-analyzer", "analyzer-based")
    await write_file_async(skill_dir / "SKILL.md", skill_md_content)

    await _create_reference_files(skill_dir, "analyzer-based")

    assert (skill_dir / "references" / "analysis-methods.md").exists()
    assert (skill_dir / "references" / "metrics.md").exists()


@pytest.mark.asyncio
async def test_full_init_skill_flow_with_scripts(temp_dir):
    """测试完整创建流程（包含脚本）."""
    validate_skill_name("test-with-scripts")
    validate_template_type("minimal")

    skill_dir = await create_directory_structure_async(
        name="test-with-scripts",
        template_type="minimal",
        output_dir=temp_dir,
    )

    skill_md_content = _generate_skill_md_content("test-with-scripts", "minimal")
    await write_file_async(skill_dir / "SKILL.md", skill_md_content)

    # 创建示例脚本
    await _create_example_scripts(skill_dir)

    assert (skill_dir / "scripts" / "helper.py").exists()
    assert (skill_dir / "scripts" / "validate.py").exists()


@pytest.mark.asyncio
async def test_full_init_skill_flow_with_examples(temp_dir):
    """测试完整创建流程（包含示例）."""
    validate_skill_name("test-with-examples")
    validate_template_type("minimal")

    skill_dir = await create_directory_structure_async(
        name="test-with-examples",
        template_type="minimal",
        output_dir=temp_dir,
    )

    skill_md_content = _generate_skill_md_content("test-with-examples", "minimal")
    await write_file_async(skill_dir / "SKILL.md", skill_md_content)

    # 创建使用示例
    await _create_example_examples(skill_dir, "test-with-examples")

    assert (skill_dir / "examples" / "basic-usage.md").exists()


@pytest.mark.asyncio
async def test_full_init_skill_flow_complete(temp_dir):
    """测试完整创建流程（所有选项）."""
    validate_skill_name("test-complete")
    validate_template_type("tool-based")

    skill_dir = await create_directory_structure_async(
        name="test-complete",
        template_type="tool-based",
        output_dir=temp_dir,
    )

    # SKILL.md
    skill_md_content = _generate_skill_md_content("test-complete", "tool-based")
    await write_file_async(skill_dir / "SKILL.md", skill_md_content)

    # 引用文件
    await _create_reference_files(skill_dir, "tool-based")

    # 脚本
    await _create_example_scripts(skill_dir)

    # 示例
    await _create_example_examples(skill_dir, "test-complete")

    # 验证所有文件
    assert (skill_dir / "SKILL.md").exists()
    assert (skill_dir / "references" / "tool-integration.md").exists()
    assert (skill_dir / "references" / "usage-examples.md").exists()
    assert (skill_dir / "scripts" / "helper.py").exists()
    assert (skill_dir / "scripts" / "validate.py").exists()
    assert (skill_dir / "examples" / "basic-usage.md").exists()


# 测试辅助函数


def test_generate_skill_md_content_minimal():
    """测试 minimal 模板 SKILL.md 内容生成."""
    content = _generate_skill_md_content("test-skill", "minimal")

    assert "name: test-skill" in content
    assert "最小化技能模板，适用于简单功能" in content
    assert "allowed-tools: Read, Write, Edit, Bash" in content
    assert "# Test Skill" in content
    assert "## 技能概述" in content
    assert "## 核心能力" in content


def test_generate_skill_md_content_tool_based():
    """测试 tool-based 模板 SKILL.md 内容生成."""
    content = _generate_skill_md_content("my-tool", "tool-based")

    assert "name: my-tool" in content
    assert "基于工具的技能模板，适用于封装特定工具或 API" in content
    assert "allowed-tools: Read, Write, Edit, Bash" in content
    assert "# My Tool" in content


def test_generate_skill_md_content_workflow_based():
    """测试 workflow-based 模板 SKILL.md 内容生成."""
    content = _generate_skill_md_content("workflow-skill", "workflow-based")

    assert "基于工作流的技能模板，适用于多步骤任务" in content
    assert "allowed-tools: Read, Write, Edit, Bash, Glob, Grep" in content


def test_generate_skill_md_content_analyzer_based():
    """测试 analyzer-based 模板 SKILL.md 内容生成."""
    content = _generate_skill_md_content("analyzer", "analyzer-based")

    assert "基于分析的技能模板，适用于数据分析或代码分析" in content
    assert "allowed-tools: Read, Glob, Grep, Bash" in content


def test_generate_skill_md_content_title_formatting():
    """测试标题格式化."""
    assert "# Test Skill" in _generate_skill_md_content("test-skill", "minimal")
    assert "# My Awesome Skill" in _generate_skill_md_content("my-awesome-skill", "minimal")
    assert "# Test" in _generate_skill_md_content("test", "minimal")
    assert "# Skill V2" in _generate_skill_md_content("skill-v2", "minimal")


@pytest.mark.asyncio
async def test_create_reference_files_tool_based(temp_dir):
    """测试 tool-based 引用文件创建."""
    skill_dir = temp_dir / "test-tool"
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "references").mkdir(exist_ok=True)

    await _create_reference_files(skill_dir, "tool-based")

    assert (skill_dir / "references" / "tool-integration.md").exists()
    assert (skill_dir / "references" / "usage-examples.md").exists()

    # 验证内容
    tool_content = (skill_dir / "references" / "tool-integration.md").read_text()
    assert "工具集成" in tool_content


@pytest.mark.asyncio
async def test_create_reference_files_workflow_based(temp_dir):
    """测试 workflow-based 引用文件创建."""
    skill_dir = temp_dir / "test-workflow"
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "references").mkdir(exist_ok=True)

    await _create_reference_files(skill_dir, "workflow-based")

    assert (skill_dir / "references" / "workflow-steps.md").exists()
    assert (skill_dir / "references" / "decision-points.md").exists()


@pytest.mark.asyncio
async def test_create_reference_files_analyzer_based(temp_dir):
    """测试 analyzer-based 引用文件创建."""
    skill_dir = temp_dir / "test-analyzer"
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "references").mkdir(exist_ok=True)

    await _create_reference_files(skill_dir, "analyzer-based")

    assert (skill_dir / "references" / "analysis-methods.md").exists()
    assert (skill_dir / "references" / "metrics.md").exists()


@pytest.mark.asyncio
async def test_create_example_scripts(temp_dir):
    """测试示例脚本创建."""
    skill_dir = temp_dir / "test-scripts"
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "scripts").mkdir(exist_ok=True)

    await _create_example_scripts(skill_dir)

    assert (skill_dir / "scripts" / "helper.py").exists()
    assert (skill_dir / "scripts" / "validate.py").exists()

    # 验证脚本内容
    helper_content = (skill_dir / "scripts" / "helper.py").read_text()
    assert "示例辅助脚本" in helper_content
    assert "argparse" in helper_content


@pytest.mark.asyncio
async def test_create_example_examples(temp_dir):
    """测试使用示例创建."""
    skill_dir = temp_dir / "test-examples"
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "examples").mkdir(exist_ok=True)

    await _create_example_examples(skill_dir, "my-skill")

    assert (skill_dir / "examples" / "basic-usage.md").exists()

    # 验证内容
    content = (skill_dir / "examples" / "basic-usage.md").read_text()
    assert "# My Skill 使用示例" in content
    assert "基本用法" in content
    assert "高级用法" in content
