"""测试最佳实践资源."""

from skill_creator_mcp.resources.best_practices import (
    get_best_practices,
    get_best_practices_summary,
)


def test_get_best_practices_returns_markdown():
    """测试返回 Markdown 格式."""
    content = get_best_practices()

    assert content.startswith("#")
    assert "##" in content
    assert len(content) > 1000


def test_get_best_practices_contains_key_sections():
    """测试包含关键章节."""
    content = get_best_practices()

    assert "# Agent-Skills 开发最佳实践" in content
    assert "## 1. 技能设计原则" in content
    assert "## 2. SKILL.md 结构规范" in content
    assert "## 3. 目录结构规范" in content
    assert "## 4. MCP 工具使用规范" in content
    assert "## 5. 命名规范" in content
    assert "## 6. 文档编写规范" in content
    assert "## 7. 测试规范" in content
    assert "## 8. 质量检查清单" in content
    assert "## 9. 常见反模式" in content


def test_get_best_practices_summary():
    """测试获取最佳实践摘要."""
    summary = get_best_practices_summary()

    assert "design_principles" in summary
    assert "structure_rules" in summary
    assert "naming_conventions" in summary
    assert "quality_checks" in summary


def test_best_practices_design_principles():
    """测试设计原则."""
    summary = get_best_practices_summary()

    principles = summary["design_principles"]
    assert "单一职责" in principles
    assert "渐进式披露" in principles
    assert "上下文感知" in principles


def test_best_practices_structure_rules():
    """测试结构规则."""
    summary = get_best_practices_summary()

    rules = summary["structure_rules"]
    # structure_rules 是字符串列表
    assert any("SKILL.md" in rule for rule in rules)
    assert any("150" in rule for rule in rules)


def test_best_practices_naming_conventions():
    """测试命名规范."""
    summary = get_best_practices_summary()

    naming = summary["naming_conventions"]
    assert "skill_name" in naming
    assert "python_modules" in naming
    assert "markdown_files" in naming


def test_best_practices_quality_checks():
    """测试质量检查."""
    summary = get_best_practices_summary()

    checks = summary["quality_checks"]
    assert len(checks) > 0
