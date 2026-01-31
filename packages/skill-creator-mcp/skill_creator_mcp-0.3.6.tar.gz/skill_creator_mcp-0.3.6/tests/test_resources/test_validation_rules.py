"""测试验证规则资源."""

from skill_creator_mcp.resources.validation_rules import (
    get_validation_rules,
    get_validation_rules_summary,
)


def test_get_validation_rules_returns_markdown():
    """测试返回 Markdown 格式."""
    content = get_validation_rules()

    assert content.startswith("#")
    assert "##" in content
    assert len(content) > 1000


def test_get_validation_rules_contains_key_sections():
    """测试包含关键章节."""
    content = get_validation_rules()

    assert "# Agent-Skills 验证规则" in content
    assert "## 1. 命名验证规则" in content
    assert "## 2. 结构验证规则" in content
    assert "## 3. 内容验证规则" in content
    assert "## 4. 模板特定验证规则" in content
    assert "## 5. 质量验证规则" in content
    assert "## 6. 验证优先级" in content
    assert "## 7. 验证命令" in content
    assert "## 8. 常见验证错误" in content


def test_get_validation_rules_summary():
    """测试获取验证规则摘要."""
    summary = get_validation_rules_summary()

    assert "naming" in summary
    assert "required_files" in summary
    assert "required_directories" in summary
    assert "required_fields" in summary
    assert "template_requirements" in summary


def test_validation_rules_naming_pattern():
    """测试命名规则模式."""
    summary = get_validation_rules_summary()

    naming = summary["naming"]
    assert "pattern" in naming
    assert "min_length" in naming
    assert "max_length" in naming
    assert "allowed_chars" in naming


def test_validation_rules_required_files():
    """测试必需文件列表."""
    summary = get_validation_rules_summary()

    files = summary["required_files"]
    assert "SKILL.md" in files


def test_validation_rules_required_directories():
    """测试必需目录列表."""
    summary = get_validation_rules_summary()

    dirs = summary["required_directories"]
    assert "references" in dirs
    assert "examples" in dirs
    assert "scripts" in dirs
    assert ".claude" in dirs


def test_validation_rules_required_fields():
    """测试必需字段列表."""
    summary = get_validation_rules_summary()

    fields = summary["required_fields"]
    assert "name" in fields
    assert "description" in fields
    assert "allowed-tools" in fields


def test_validation_rules_template_requirements():
    """测试模板特定要求."""
    summary = get_validation_rules_summary()

    template_reqs = summary["template_requirements"]
    assert "minimal" in template_reqs
    assert "tool-based" in template_reqs
    assert "workflow-based" in template_reqs
    assert "analyzer-based" in template_reqs


def test_validation_rules_template_requirements_minimal():
    """测试 minimal 模板无额外要求."""
    summary = get_validation_rules_summary()

    assert summary["template_requirements"]["minimal"] == []


def test_validation_rules_template_requirements_tool_based():
    """测试 tool-based 模板要求."""
    summary = get_validation_rules_summary()

    reqs = summary["template_requirements"]["tool-based"]
    assert "tool-integration.md" in reqs
    assert "usage-examples.md" in reqs


def test_validation_rules_naming_pattern_valid():
    """测试命名模式正则表达式."""
    import re

    summary = get_validation_rules_summary()
    pattern = summary["naming"]["pattern"]

    # 有效名称
    assert re.match(pattern, "valid-name")
    assert re.match(pattern, "my-skill")
    assert re.match(pattern, "code-helper-v2")

    # 无效名称
    assert not re.match(pattern, "Invalid_Name")
    assert not re.match(pattern, "-prefix")
    assert not re.match(pattern, "suffix-")
