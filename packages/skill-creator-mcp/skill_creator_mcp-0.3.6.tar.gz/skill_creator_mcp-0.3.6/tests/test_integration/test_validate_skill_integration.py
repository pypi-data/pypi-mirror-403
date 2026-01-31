"""validate_skill 工具集成测试.

测试 validate_skill 的完整流程，包括所有验证函数。
"""

from pathlib import Path

import pytest

from skill_creator_mcp.utils.validators import (
    _validate_naming,
    _validate_skill_md,
    _validate_structure,
    _validate_template_requirements,
)


@pytest.mark.asyncio
async def test_full_validate_skill_flow_valid_minimal(temp_dir: Path):
    """测试验证完整的 minimal 技能."""
    skill_dir = temp_dir / "test-minimal"
    skill_dir.mkdir()

    # 创建完整目录结构
    for dir_name in ["references", "examples", "scripts", ".claude"]:
        (skill_dir / dir_name).mkdir()

    # 创建 SKILL.md
    (skill_dir / "SKILL.md").write_text("""---
name: test-minimal
description: |
  最小化技能模板
allowed-tools: Read, Write, Edit
---
# Test Minimal
""")

    # 执行所有验证
    structure_errors = _validate_structure(skill_dir)
    naming_errors = _validate_naming(skill_dir)
    content_errors, content_warnings, template_type = _validate_skill_md(skill_dir)
    template_errors = _validate_template_requirements(skill_dir, template_type)

    # 验证结果
    assert len(structure_errors) == 0
    assert len(naming_errors) == 0
    assert len(content_errors) == 0
    assert len(template_errors) == 0


@pytest.mark.asyncio
async def test_full_validate_skill_flow_tool_based_complete(temp_dir: Path):
    """测试验证完整的 tool-based 技能."""
    skill_dir = temp_dir / "test-tool"
    skill_dir.mkdir()

    # 创建目录结构
    for dir_name in ["references", "examples", "scripts", ".claude"]:
        (skill_dir / dir_name).mkdir()

    # 创建 SKILL.md
    (skill_dir / "SKILL.md").write_text("""---
name: test-tool
template: tool-based
description: |
  基于工具的技能模板
allowed-tools: Read, Write, Edit
---
# Test Tool
""")

    # 创建必需引用文件
    (skill_dir / "references" / "tool-integration.md").write_text("# Tools")
    (skill_dir / "references" / "usage-examples.md").write_text("# Examples")

    # 执行验证
    structure_errors = _validate_structure(skill_dir)
    naming_errors = _validate_naming(skill_dir)
    content_errors, content_warnings, template_type = _validate_skill_md(skill_dir)
    template_errors = _validate_template_requirements(skill_dir, template_type)

    # 验证结果
    assert len(structure_errors) == 0
    assert len(naming_errors) == 0
    assert len(content_errors) == 0
    assert template_type == "tool-based"
    assert len(template_errors) == 0


@pytest.mark.asyncio
async def test_full_validate_skill_flow_workflow_based_complete(temp_dir: Path):
    """测试验证完整的 workflow-based 技能."""
    skill_dir = temp_dir / "test-workflow"
    skill_dir.mkdir()

    # 创建目录结构
    for dir_name in ["references", "examples", "scripts", ".claude"]:
        (skill_dir / dir_name).mkdir()

    # 创建 SKILL.md
    (skill_dir / "SKILL.md").write_text("""---
name: test-workflow
template: workflow-based
description: |
  基于工作流的技能模板
allowed-tools: Read, Write, Glob, Grep
---
# Test Workflow
""")

    # 创建必需引用文件
    (skill_dir / "references" / "workflow-steps.md").write_text("# Steps")
    (skill_dir / "references" / "decision-points.md").write_text("# Decisions")

    # 执行验证
    structure_errors = _validate_structure(skill_dir)
    naming_errors = _validate_naming(skill_dir)
    content_errors, content_warnings, template_type = _validate_skill_md(skill_dir)
    template_errors = _validate_template_requirements(skill_dir, template_type)

    # 验证结果
    assert len(structure_errors) == 0
    assert len(naming_errors) == 0
    assert len(content_errors) == 0
    assert template_type == "workflow-based"
    assert len(template_errors) == 0


@pytest.mark.asyncio
async def test_full_validate_skill_flow_analyzer_based_complete(temp_dir: Path):
    """测试验证完整的 analyzer-based 技能."""
    skill_dir = temp_dir / "test-analyzer"
    skill_dir.mkdir()

    # 创建目录结构
    for dir_name in ["references", "examples", "scripts", ".claude"]:
        (skill_dir / dir_name).mkdir()

    # 创建 SKILL.md
    (skill_dir / "SKILL.md").write_text("""---
name: test-analyzer
template: analyzer-based
description: |
  基于分析的技能模板
allowed-tools: Read, Glob, Grep
---
# Test Analyzer
""")

    # 创建必需引用文件
    (skill_dir / "references" / "analysis-methods.md").write_text("# Methods")
    (skill_dir / "references" / "metrics.md").write_text("# Metrics")

    # 执行验证
    structure_errors = _validate_structure(skill_dir)
    naming_errors = _validate_naming(skill_dir)
    content_errors, content_warnings, template_type = _validate_skill_md(skill_dir)
    template_errors = _validate_template_requirements(skill_dir, template_type)

    # 验证结果
    assert len(structure_errors) == 0
    assert len(naming_errors) == 0
    assert len(content_errors) == 0
    assert template_type == "analyzer-based"
    assert len(template_errors) == 0


@pytest.mark.asyncio
async def test_full_validate_skill_flow_missing_files(temp_dir: Path):
    """测试验证缺少文件的技能."""
    skill_dir = temp_dir / "incomplete"
    skill_dir.mkdir()

    # 只创建 SKILL.md
    (skill_dir / "SKILL.md").write_text("---\nname: incomplete\n---")

    # 执行验证
    structure_errors = _validate_structure(skill_dir)
    content_errors, content_warnings, template_type = _validate_skill_md(skill_dir)

    # 验证结果 - 应该有错误
    assert len(structure_errors) > 0
    assert any("缺少必需目录" in e for e in structure_errors)
    assert len(content_errors) > 0


@pytest.mark.asyncio
async def test_full_validate_skill_flow_invalid_name(temp_dir: Path):
    """测试验证无效命名的技能."""
    skill_dir = temp_dir / "Invalid_Skill"
    skill_dir.mkdir()

    # 创建 SKILL.md
    (skill_dir / "SKILL.md").write_text("---\nname: Invalid_Skill\n---")

    # 执行验证
    naming_errors = _validate_naming(skill_dir)

    # 验证结果 - 应该有命名错误
    assert len(naming_errors) > 0
    assert any("不符合规范" in e for e in naming_errors)


@pytest.mark.asyncio
async def test_full_validate_skill_flow_name_mismatch(temp_dir: Path):
    """测试 SKILL.md 中 name 字段与目录名不一致."""
    skill_dir = temp_dir / "test-skill"
    skill_dir.mkdir()

    # 创建 SKILL.md，但 name 字段不匹配
    (skill_dir / "SKILL.md").write_text("---\nname: different-skill\n---")

    # 执行验证
    naming_errors = _validate_naming(skill_dir)

    # 验证结果 - 应该有不一致错误
    assert len(naming_errors) > 0
    assert any("不一致" in e for e in naming_errors)


@pytest.mark.asyncio
async def test_full_validate_skill_flow_missing_template_files(temp_dir: Path):
    """测试验证缺少模板特定文件的技能."""
    skill_dir = temp_dir / "tool-skill"
    skill_dir.mkdir()

    # 创建目录结构
    for dir_name in ["references", "examples", "scripts", ".claude"]:
        (skill_dir / dir_name).mkdir()

    # 创建 SKILL.md，声明为 tool-based 但不创建必需文件
    (skill_dir / "SKILL.md").write_text("""---
name: tool-skill
template: tool-based
description: |
  Tool based skill
allowed-tools: Read
---
""")

    # 执行验证
    content_errors, content_warnings, template_type = _validate_skill_md(skill_dir)
    template_errors = _validate_template_requirements(skill_dir, template_type)

    # 验证结果 - 应该有模板要求错误
    assert template_type == "tool-based"
    assert len(template_errors) > 0
    assert any("tool-integration.md" in e for e in template_errors)
