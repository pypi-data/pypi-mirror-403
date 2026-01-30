"""测试 validate_skill Prompt."""

from skill_creator_mcp.prompts.validate_skill import get_validate_skill_prompt


def test_get_validate_skill_prompt_basic():
    """测试获取基本验证技能 Prompt."""
    prompt = get_validate_skill_prompt("/path/to/skill")

    assert "你是一个专业的 Agent-Skill 质量审核专家" in prompt
    assert "/path/to/skill" in prompt


def test_get_validate_skill_prompt_with_template():
    """测试带模板类型的验证 Prompt."""
    prompt = get_validate_skill_prompt("/path/to/skill", "tool-based")

    assert "/path/to/skill" in prompt
    assert "tool-based" in prompt
    assert "tool-integration.md" in prompt


def test_get_validate_skill_prompt_without_template():
    """测试不带模板类型的验证 Prompt."""
    prompt = get_validate_skill_prompt("/path/to/skill")

    # 不应该包含特定模板的要求
    assert "/path/to/skill" in prompt
    # 应该包含基本验证清单
    assert "1. 命名验证" in prompt or "命名验证" in prompt
    assert "2. 结构验证" in prompt or "结构验证" in prompt


def test_get_validate_skill_prompt_contains_checklist():
    """测试 Prompt 包含验证清单."""
    prompt = get_validate_skill_prompt("/path/to/skill")

    # 检查包含验证清单相关内容
    assert "## 验证清单" in prompt
    assert "1. 命名验证" in prompt or "命名验证" in prompt
    assert "2. 结构验证" in prompt or "结构验证" in prompt


def test_get_validate_skill_prompt_contains_output_format():
    """测试 Prompt 包含输出格式说明."""
    prompt = get_validate_skill_prompt("/path/to/skill")

    assert "## 输出格式" in prompt
    assert "# 验证结果" in prompt
    assert "## 总体评估" in prompt
    assert "## 发现的问题" in prompt
