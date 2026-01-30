"""测试 create_skill Prompt."""

from skill_creator_mcp.prompts.create_skill import get_create_skill_prompt


def test_get_create_skill_prompt_minimal():
    """测试获取 minimal 模板的创建技能 Prompt."""
    prompt = get_create_skill_prompt("my-skill", "minimal")

    assert "你是一个专业的 Agent-Skill 开发助手" in prompt
    assert "my-skill" in prompt
    assert "minimal" in prompt
    assert "最简单的技能结构" in prompt


def test_get_create_skill_prompt_tool_based():
    """测试获取 tool-based 模板的创建技能 Prompt."""
    prompt = get_create_skill_prompt("api-helper", "tool-based")

    assert "api-helper" in prompt
    assert "tool-based" in prompt
    assert "tool-integration.md" in prompt
    assert "usage-examples.md" in prompt


def test_get_create_skill_prompt_workflow_based():
    """测试获取 workflow-based 模板的创建技能 Prompt."""
    prompt = get_create_skill_prompt("data-pipeline", "workflow-based")

    assert "data-pipeline" in prompt
    assert "workflow-based" in prompt
    assert "workflow-steps.md" in prompt
    assert "decision-points.md" in prompt


def test_get_create_skill_prompt_analyzer_based():
    """测试获取 analyzer-based 模板的创建技能 Prompt."""
    prompt = get_create_skill_prompt("code-metrics", "analyzer-based")

    assert "code-metrics" in prompt
    assert "analyzer-based" in prompt
    assert "analysis-methods.md" in prompt
    assert "metrics.md" in prompt


def test_get_create_skill_prompt_contains_sections():
    """测试 Prompt 包含所有必需章节."""
    prompt = get_create_skill_prompt("test-skill", "minimal")

    assert "## 任务" in prompt
    assert "## 要求" in prompt
    assert "### 1. 技能命名规范" in prompt
    assert "### 2. SKILL.md 结构" in prompt
    assert "### 3. 目录结构" in prompt
    assert "## 输出格式" in prompt
