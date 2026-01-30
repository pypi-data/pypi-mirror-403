"""测试 validate_skill 验证函数."""

from pathlib import Path

from skill_creator_mcp.utils.validators import (
    _validate_naming,
    _validate_skill_md,
    _validate_structure,
    _validate_template_requirements,
)

# ==================== _validate_structure 测试 ====================


def test_validate_structure_complete(temp_dir: Path):
    """测试完整目录结构."""
    skill_dir = temp_dir / "test-skill"
    skill_dir.mkdir()

    # 创建所有必需目录
    (skill_dir / "SKILL.md").write_text("# Test")
    for dir_name in ["references", "examples", "scripts", ".claude"]:
        (skill_dir / dir_name).mkdir()

    errors = _validate_structure(skill_dir)
    assert errors == []


def test_validate_structure_missing_skill_md(temp_dir: Path):
    """测试缺少 SKILL.md."""
    skill_dir = temp_dir / "test-skill"
    skill_dir.mkdir()
    (skill_dir / "references").mkdir()
    (skill_dir / "examples").mkdir()
    (skill_dir / "scripts").mkdir()
    (skill_dir / ".claude").mkdir()

    errors = _validate_structure(skill_dir)
    assert "缺少必需文件: SKILL.md" in errors


def test_validate_structure_missing_directories(temp_dir: Path):
    """测试缺少必需目录."""
    skill_dir = temp_dir / "test-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("# Test")

    errors = _validate_structure(skill_dir)
    assert "缺少必需目录: references" in errors
    assert "缺少必需目录: examples" in errors
    assert "缺少必需目录: scripts" in errors
    assert "缺少必需目录: .claude" in errors


def test_validate_structure_partial_missing(temp_dir: Path):
    """测试部分缺失."""
    skill_dir = temp_dir / "test-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("# Test")
    (skill_dir / "references").mkdir()

    errors = _validate_structure(skill_dir)
    assert "缺少必需目录: examples" in errors
    assert "缺少必需目录: scripts" in errors
    assert "缺少必需目录: .claude" in errors
    assert "缺少必需文件: SKILL.md" not in errors


# ==================== _validate_naming 测试 ====================


def test_validate_naming_valid(temp_dir: Path):
    """测试有效命名."""
    skill_dir = temp_dir / "test-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("name: test-skill")

    errors = _validate_naming(skill_dir)
    assert errors == []


def test_validate_naming_invalid_directory_name(temp_dir: Path):
    """测试无效目录名."""
    skill_dir = temp_dir / "Test_Skill"
    skill_dir.mkdir()

    errors = _validate_naming(skill_dir)
    assert len(errors) > 0
    assert any("不符合规范" in e for e in errors)


def test_validate_naming_name_mismatch(temp_dir: Path):
    """测试 SKILL.md 中 name 字段与目录名不一致."""
    skill_dir = temp_dir / "test-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("name: different-skill")

    errors = _validate_naming(skill_dir)
    assert any("不一致" in e for e in errors)


def test_validate_naming_no_skill_md(temp_dir: Path):
    """测试没有 SKILL.md 的情况."""
    skill_dir = temp_dir / "test-skill"
    skill_dir.mkdir()

    errors = _validate_naming(skill_dir)
    # 只有目录名验证，没有 name 不一致错误
    assert errors == []


# ==================== _validate_skill_md 测试 ====================


def test_validate_skill_md_valid(temp_dir: Path):
    """测试有效的 SKILL.md."""
    skill_dir = temp_dir / "test-skill"
    skill_dir.mkdir()
    content = """---
name: test-skill
description: |
  Test skill description
allowed-tools: Read, Write, Edit
---
# Test Skill
"""
    (skill_dir / "SKILL.md").write_text(content)

    errors, warnings, template_type = _validate_skill_md(skill_dir)
    assert errors == []
    assert warnings == []
    assert template_type is None


def test_validate_skill_md_missing_file(temp_dir: Path):
    """测试缺少 SKILL.md."""
    skill_dir = temp_dir / "test-skill"
    skill_dir.mkdir()

    errors, warnings, template_type = _validate_skill_md(skill_dir)
    assert "SKILL.md 文件不存在" in errors


def test_validate_skill_md_no_frontmatter(temp_dir: Path):
    """测试缺少 YAML frontmatter."""
    skill_dir = temp_dir / "test-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("# Test Skill")

    errors, warnings, template_type = _validate_skill_md(skill_dir)
    assert any("缺少 YAML frontmatter" in e for e in errors)


def test_validate_skill_md_missing_fields(temp_dir: Path):
    """测试缺少必需字段."""
    skill_dir = temp_dir / "test-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("---\nname: test-skill\n---")

    errors, warnings, template_type = _validate_skill_md(skill_dir)
    assert any("缺少必需字段: description" in e for e in errors)
    assert any("缺少必需字段: allowed-tools" in e for e in errors)


def test_validate_skill_md_with_template(temp_dir: Path):
    """测试带模板类型的 SKILL.md."""
    skill_dir = temp_dir / "test-skill"
    skill_dir.mkdir()
    content = """---
name: test-skill
template: tool-based
description: |
  Test skill
allowed-tools: Read, Write
---
"""
    (skill_dir / "SKILL.md").write_text(content)

    errors, warnings, template_type = _validate_skill_md(skill_dir)
    assert template_type == "tool-based"


def test_validate_skill_md_invalid_tools(temp_dir: Path):
    """测试包含无效工具."""
    skill_dir = temp_dir / "test-skill"
    skill_dir.mkdir()
    content = """---
name: test-skill
description: |
  Test skill
allowed-tools: [Read, InvalidTool, Write]
---
"""
    (skill_dir / "SKILL.md").write_text(content)

    errors, warnings, template_type = _validate_skill_md(skill_dir)
    assert len(warnings) > 0
    assert any("InvalidTool" in w for w in warnings)


# ==================== _validate_template_requirements 测试 ====================


def test_validate_template_requirements_minimal(temp_dir: Path):
    """测试 minimal 模板（无额外要求）."""
    skill_dir = temp_dir / "test-skill"
    skill_dir.mkdir()
    (skill_dir / "references").mkdir()

    errors = _validate_template_requirements(skill_dir, "minimal")
    assert errors == []


def test_validate_template_requirements_tool_based_complete(temp_dir: Path):
    """测试 tool-based 模板完整."""
    skill_dir = temp_dir / "test-skill"
    skill_dir.mkdir()
    refs_dir = skill_dir / "references"
    refs_dir.mkdir()
    (refs_dir / "tool-integration.md").write_text("# Tools")
    (refs_dir / "usage-examples.md").write_text("# Examples")

    errors = _validate_template_requirements(skill_dir, "tool-based")
    assert errors == []


def test_validate_template_requirements_tool_based_missing(temp_dir: Path):
    """测试 tool-based 模板缺少文件."""
    skill_dir = temp_dir / "test-skill"
    skill_dir.mkdir()
    (skill_dir / "references").mkdir()

    errors = _validate_template_requirements(skill_dir, "tool-based")
    assert any("references/tool-integration.md" in e for e in errors)
    assert any("references/usage-examples.md" in e for e in errors)


def test_validate_template_requirements_workflow_based(temp_dir: Path):
    """测试 workflow-based 模板."""
    skill_dir = temp_dir / "test-skill"
    skill_dir.mkdir()
    (skill_dir / "references").mkdir()

    errors = _validate_template_requirements(skill_dir, "workflow-based")
    assert any("references/workflow-steps.md" in e for e in errors)
    assert any("references/decision-points.md" in e for e in errors)


def test_validate_template_requirements_analyzer_based(temp_dir: Path):
    """测试 analyzer-based 模板."""
    skill_dir = temp_dir / "test-skill"
    skill_dir.mkdir()
    (skill_dir / "references").mkdir()

    errors = _validate_template_requirements(skill_dir, "analyzer-based")
    assert any("references/analysis-methods.md" in e for e in errors)
    assert any("references/metrics.md" in e for e in errors)


def test_validate_template_requirements_none_template(temp_dir: Path):
    """测试模板类型为 None."""
    skill_dir = temp_dir / "test-skill"
    skill_dir.mkdir()

    errors = _validate_template_requirements(skill_dir, None)
    assert errors == []


def test_validate_template_requirements_invalid_template(temp_dir: Path):
    """测试无效模板类型."""
    skill_dir = temp_dir / "test-skill"
    skill_dir.mkdir()

    errors = _validate_template_requirements(skill_dir, "invalid-type")
    assert errors == []
