"""测试模板资源."""

from skill_creator_mcp.resources.templates import (
    TEMPLATE_DESCRIPTIONS,
    TEMPLATE_REFERENCES,
    TEMPLATE_TOOLS,
    get_template_content,
    get_template_info,
    get_template_references,
    list_templates,
)


def test_list_templates():
    """测试列出所有模板."""
    templates = list_templates()

    assert len(templates) == 4
    template_types = [t["type"] for t in templates]
    assert "minimal" in template_types
    assert "tool-based" in template_types
    assert "workflow-based" in template_types
    assert "analyzer-based" in template_types


def test_list_templates_has_descriptions():
    """测试模板包含描述."""
    templates = list_templates()

    for t in templates:
        assert "description" in t
        assert len(t["description"]) > 0


def test_get_template_content_minimal():
    """测试获取 minimal 模板内容."""
    content = get_template_content("minimal")

    assert "---" in content
    assert "name:" in content
    assert "description:" in content
    assert "allowed-tools:" in content
    assert "Read, Write, Edit, Bash" in content


def test_get_template_content_tool_based():
    """测试获取 tool-based 模板内容."""
    content = get_template_content("tool-based")

    assert "---" in content
    assert "Read, Write, Edit, Bash" in content


def test_get_template_content_workflow_based():
    """测试获取 workflow-based 模板内容."""
    content = get_template_content("workflow-based")

    assert "---" in content
    assert "Glob, Grep" in content


def test_get_template_content_analyzer_based():
    """测试获取 analyzer-based 模板内容."""
    content = get_template_content("analyzer-based")

    assert "---" in content
    assert "Glob, Grep, Bash" in content


def test_get_template_references_minimal():
    """测试 minimal 模板无必需引用文件."""
    refs = get_template_references("minimal")

    assert refs == []


def test_get_template_references_tool_based():
    """测试 tool-based 模板引用文件."""
    refs = get_template_references("tool-based")

    assert len(refs) == 2
    filenames = [f[0] for f in refs]
    assert "tool-integration.md" in filenames
    assert "usage-examples.md" in filenames


def test_get_template_references_workflow_based():
    """测试 workflow-based 模板引用文件."""
    refs = get_template_references("workflow-based")

    assert len(refs) == 2
    filenames = [f[0] for f in refs]
    assert "workflow-steps.md" in filenames
    assert "decision-points.md" in filenames


def test_get_template_references_analyzer_based():
    """测试 analyzer-based 模板引用文件."""
    refs = get_template_references("analyzer-based")

    assert len(refs) == 2
    filenames = [f[0] for f in refs]
    assert "analysis-methods.md" in filenames
    assert "metrics.md" in filenames


def test_get_template_info():
    """测试获取模板信息."""
    info = get_template_info("tool-based")

    assert info["type"] == "tool-based"
    assert info["description"] == TEMPLATE_DESCRIPTIONS["tool-based"]
    assert info["allowed_tools"] == TEMPLATE_TOOLS["tool-based"]
    assert info["required_references"] == TEMPLATE_REFERENCES["tool-based"]


def test_template_references_has_content():
    """测试引用文件有内容."""
    refs = get_template_references("tool-based")

    for filename, content in refs:
        assert len(content) > 0
        assert "#" in content  # Markdown 标题
