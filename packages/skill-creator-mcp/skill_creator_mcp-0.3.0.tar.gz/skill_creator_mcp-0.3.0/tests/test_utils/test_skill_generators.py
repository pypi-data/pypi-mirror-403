"""skill_generators.py 单元测试.

直接测试 skill_generators 模块中的所有函数：
- _generate_skill_md_content
- _create_reference_files
- _create_example_scripts
- _create_example_examples
"""

from pathlib import Path

import pytest

# ============================================================================
# _generate_skill_md_content 测试
# ============================================================================


def test_generate_skill_md_content_minimal_template():
    """测试 minimal 模板的 SKILL.md 内容生成."""
    from skill_creator_mcp.utils.skill_generators import _generate_skill_md_content

    result = _generate_skill_md_content("test-skill", "minimal")

    assert "name: test-skill" in result
    assert "description:" in result
    assert "allowed-tools: Read, Write, Edit, Bash" in result
    assert "# Test Skill" in result


def test_generate_skill_md_content_tool_based_template():
    """测试 tool-based 模板的 SKILL.md 内容生成."""
    from skill_creator_mcp.utils.skill_generators import _generate_skill_md_content

    result = _generate_skill_md_content("api-tool", "tool-based")

    assert "name: api-tool" in result
    assert "allowed-tools: Read, Write, Edit, Bash" in result
    assert "基于工具的技能模板" in result  # description is Chinese


def test_generate_skill_md_content_workflow_based_template():
    """测试 workflow-based 模板的 SKILL.md 内容生成."""
    from skill_creator_mcp.utils.skill_generators import _generate_skill_md_content

    result = _generate_skill_md_content("workflow-automation", "workflow-based")

    assert "name: workflow-automation" in result
    assert "allowed-tools: Read, Write, Edit, Bash, Glob, Grep" in result


def test_generate_skill_md_content_analyzer_based_template():
    """测试 analyzer-based 模板的 SKILL.md 内容生成."""
    from skill_creator_mcp.utils.skill_generators import _generate_skill_md_content

    result = _generate_skill_md_content("code-analyzer", "analyzer-based")

    assert "name: code-analyzer" in result
    assert "allowed-tools: Read, Glob, Grep, Bash" in result


def test_generate_skill_md_content_custom_name():
    """测试自定义技能名称的标题生成."""
    from skill_creator_mcp.utils.skill_generators import _generate_skill_md_content

    result = _generate_skill_md_content("my-custom-skill", "minimal")

    assert "# My Custom Skill" in result
    assert "name: my-custom-skill" in result


def test_generate_skill_md_content_underscore_to_space():
    """测试下划线转换为空格."""
    from skill_creator_mcp.utils.skill_generators import _generate_skill_md_content

    result = _generate_skill_md_content("my_test_skill", "minimal")

    assert "# My Test Skill" in result


def test_generate_skill_md_content_description_content():
    """测试不同模板的描述内容."""
    from skill_creator_mcp.utils.skill_generators import _generate_skill_md_content

    minimal_result = _generate_skill_md_content("test", "minimal")
    assert "最小化技能模板" in minimal_result

    tool_result = _generate_skill_md_content("test", "tool-based")
    assert "基于工具的技能模板" in tool_result


# ============================================================================
# _create_reference_files 测试
# ============================================================================


@pytest.mark.asyncio
async def test_create_reference_files_tool_based():
    """测试创建 tool-based 模板的引用文件."""
    from skill_creator_mcp.utils.skill_generators import _create_reference_files

    # Mock write_file_async
    written_files = {}
    async def mock_write(file_path, content):
        written_files[file_path.name] = content

    # 使用 monkey patch 或者直接替换模块中的函数
    import skill_creator_mcp.utils.skill_generators as sg_module
    original_write = sg_module.write_file_async
    sg_module.write_file_async = mock_write

    try:
        temp_dir = Path("/tmp/test_skill")
        await _create_reference_files(temp_dir, "tool-based")
    finally:
        sg_module.write_file_async = original_write

    # 验证文件被创建
    assert "tool-integration.md" in written_files
    assert "usage-examples.md" in written_files
    assert "# 工具集成" in written_files["tool-integration.md"]
    assert "# 使用示例" in written_files["usage-examples.md"]


@pytest.mark.asyncio
async def test_create_reference_files_workflow_based():
    """测试创建 workflow-based 模板的引用文件."""
    import skill_creator_mcp.utils.skill_generators as sg_module
    from skill_creator_mcp.utils.skill_generators import _create_reference_files

    written_files = {}
    async def mock_write(file_path, content):
        written_files[file_path.name] = content

    original_write = sg_module.write_file_async
    sg_module.write_file_async = mock_write

    try:
        temp_dir = Path("/tmp/test_skill")
        await _create_reference_files(temp_dir, "workflow-based")
    finally:
        sg_module.write_file_async = original_write

    assert "workflow-steps.md" in written_files
    assert "decision-points.md" in written_files


@pytest.mark.asyncio
async def test_create_reference_files_analyzer_based():
    """测试创建 analyzer-based 模板的引用文件."""
    import skill_creator_mcp.utils.skill_generators as sg_module
    from skill_creator_mcp.utils.skill_generators import _create_reference_files

    written_files = {}
    async def mock_write(file_path, content):
        written_files[file_path.name] = content

    original_write = sg_module.write_file_async
    sg_module.write_file_async = mock_write

    try:
        temp_dir = Path("/tmp/test_skill")
        await _create_reference_files(temp_dir, "analyzer-based")
    finally:
        sg_module.write_file_async = original_write

    assert "analysis-methods.md" in written_files
    assert "metrics.md" in written_files


@pytest.mark.asyncio
async def test_create_reference_files_minimal_no_files():
    """测试 minimal 模式不创建引用文件."""
    import skill_creator_mcp.utils.skill_generators as sg_module
    from skill_creator_mcp.utils.skill_generators import _create_reference_files

    written_files = {}
    async def mock_write(file_path, content):
        written_files[file_path.name] = content

    original_write = sg_module.write_file_async
    sg_module.write_file_async = mock_write

    try:
        temp_dir = Path("/tmp/test_skill")
        await _create_reference_files(temp_dir, "minimal")
    finally:
        sg_module.write_file_async = original_write

    # minimal 模式不应该创建任何引用文件
    assert len(written_files) == 0


# ============================================================================
# _create_example_scripts 测试
# ============================================================================


@pytest.mark.asyncio
async def test_create_example_scripts():
    """测试创建示例脚本."""
    import skill_creator_mcp.utils.skill_generators as sg_module
    from skill_creator_mcp.utils.skill_generators import _create_example_scripts

    written_files = {}
    async def mock_write(file_path, content):
        written_files[file_path.name] = content

    original_write = sg_module.write_file_async
    sg_module.write_file_async = mock_write

    try:
        temp_dir = Path("/tmp/test_skill/scripts")
        await _create_example_scripts(temp_dir)
    finally:
        sg_module.write_file_async = original_write

    assert "helper.py" in written_files
    assert "validate.py" in written_files
    assert "#!/usr/bin/env python3" in written_files["helper.py"]
    assert "示例辅助脚本" in written_files["helper.py"]
    assert "技能验证脚本" in written_files["validate.py"]


def test_create_example_scripts_content_helper():
    """验证 helper.py 内容结构."""

    content = """#!/usr/bin/env python3
\"\"\"示例辅助脚本\"\"\"

import argparse


def main():
    parser = argparse.ArgumentParser(description="示例辅助脚本")
    parser.add_argument("--option", help="选项说明")
    args = parser.parse_args()

    print(f"执行示例脚本，选项: {args.option}")


if __name__ == "__main__":
    main()
"""
    assert "argparse" in content
    assert "description=" in content
    assert "--option" in content


def test_create_example_scripts_content_validate():
    """验证 validate.py 内容结构."""

    content = """#!/usr/bin/env python3
\"\"\"技能验证脚本\"\"\"

import sys
from pathlib import Path


def validate_skill():
    \"\"\"验证技能结构\"\"\"
    skill_dir = Path(__file__).parent.parent

    required_files = ["SKILL.md"]
    missing_files = []

    for file in required_files:
        if not (skill_dir / file).exists():
            missing_files.append(file)

    if missing_files:
        print(f"缺少必需文件: {', '.join(missing_files)}")
        return False

    print("技能结构验证通过")
    return True


if __name__ == "__main__":
    sys.exit(0 if validate_skill() else 1)
"""
    assert "SKILL.md" in content
    assert "validate_skill" in content
    assert "Path" in content


# ============================================================================
# _create_example_examples 测试
# ============================================================================


@pytest.mark.asyncio
async def test_create_example_examples():
    """测试创建使用示例."""
    import skill_creator_mcp.utils.skill_generators as sg_module
    from skill_creator_mcp.utils.skill_generators import _create_example_examples

    written_files = {}
    async def mock_write(file_path, content):
        written_files[file_path.name] = content

    original_write = sg_module.write_file_async
    sg_module.write_file_async = mock_write

    try:
        temp_dir = Path("/tmp/test_skill/examples")
        await _create_example_examples(temp_dir, "test-skill")
    finally:
        sg_module.write_file_async = original_write

    assert "basic-usage.md" in written_files


def test_create_example_examples_content():
    """验证使用示例内容结构."""

    result = """# Test Skill 使用示例

## 示例 1：基本用法

描述基本使用方法和预期结果。

## 示例 2：高级用法

描述高级使用方法和预期结果。

## 示例 3：错误处理

描述错误情况的处理方式。
"""
    assert "# Test Skill 使用示例" in result
    assert "基本用法" in result
    assert "高级用法" in result
    assert "错误处理" in result


def test_create_example_examples_title_formatting():
    """测试技能名称转换为标题格式."""

    # 测试连字符转换为空格
    result1 = """# My Test Skill 使用示例"""
    result2 = """# My Other Skill 使用示例"""

    # 验证标题格式
    assert "My Test Skill" in result1
    assert "My Other Skill" in result2


# ============================================================================
# 边界条件和错误处理测试
# ============================================================================


def test_generate_skill_md_content_unknown_template():
    """测试未知模板类型时的默认行为."""
    from skill_creator_mcp.utils.skill_generators import _generate_skill_md_content

    result = _generate_skill_md_content("test", "unknown-template")

    # 应该回退到 minimal 模板
    assert "name: test" in result
    assert "最小化技能模板" in result


def test_generate_skill_md_content_empty_name():
    """测试空名称的处理."""
    from skill_creator_mcp.utils.skill_generators import _generate_skill_md_content

    result = _generate_skill_md_content("", "minimal")

    # 应该生成空标题
    assert "#" in result
    assert "name: " in result


def test_generate_skill_md_content_special_chars():
    """测试特殊字符在名称中的处理."""
    from skill_creator_mcp.utils.skill_generators import _generate_skill_md_content

    result = _generate_skill_md_content("test_skill_with_123_numbers", "minimal")

    assert "name: test_skill_with_123_numbers" in result
    assert "Test Skill With 123 Numbers" in result  # 标题会移除数字


# ============================================================================
# 集成测试
# ============================================================================


@pytest.mark.asyncio
async def test_full_skill_generation_workflow():
    """测试完整的技能生成工作流."""
    import skill_creator_mcp.utils.skill_generators as sg_module
    from skill_creator_mcp.utils.skill_generators import (
        _create_example_examples,
        _create_example_scripts,
        _create_reference_files,
        _generate_skill_md_content,
    )

    written_files = {}
    async def mock_write(file_path, content):
        written_files[str(file_path)] = content

    original_write = sg_module.write_file_async
    sg_module.write_file_async = mock_write

    try:
        temp_dir = Path("/tmp/test_full_skill")
        scripts_dir = temp_dir / "scripts"
        examples_dir = temp_dir / "examples"
        refs_dir = temp_dir / "references"

        # 模拟目录创建
        scripts_dir.mkdir(parents=True, exist_ok=True)
        examples_dir.mkdir(parents=True, exist_ok=True)
        refs_dir.mkdir(parents=True, exist_ok=True)

        # 1. 生成 SKILL.md
        skill_md = _generate_skill_md_content("full-test", "workflow-based")
        written_files["SKILL.md"] = skill_md

        # 2. 创建引用文件
        await _create_reference_files(temp_dir, "workflow-based")

        # 3. 创建示例脚本
        await _create_example_scripts(temp_dir / "scripts")

        # 4. 创建使用示例
        await _create_example_examples(temp_dir / "examples", "full-test")

    finally:
        sg_module.write_file_async = original_write

    # 验证所有文件都被创建
    assert "SKILL.md" in written_files
    assert any("workflow-steps.md" in key for key in written_files) or any("decision-points.md" in key for key in written_files)
    assert any("helper.py" in key for key in written_files)
    assert any("basic-usage.md" in key for key in written_files)
    assert "# Full Test" in written_files["SKILL.md"]
