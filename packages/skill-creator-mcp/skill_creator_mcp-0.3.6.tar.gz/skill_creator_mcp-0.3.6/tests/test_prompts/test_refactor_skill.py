"""测试 refactor_skill Prompt."""

from skill_creator_mcp.prompts.refactor_skill import get_refactor_skill_prompt


def test_get_refactor_skill_prompt_basic():
    """测试获取基本重构技能 Prompt."""
    prompt = get_refactor_skill_prompt("/path/to/skill")

    assert "你是一个专业的 Agent-Skill 重构专家" in prompt
    assert "/path/to/skill" in prompt


def test_get_refactor_skill_prompt_with_focus():
    """测试带重点关注领域的重构 Prompt."""
    prompt = get_refactor_skill_prompt("/path/to/skill", ["structure", "performance"])

    assert "/path/to/skill" in prompt
    assert "`structure`" in prompt
    assert "`performance`" in prompt


def test_get_refactor_skill_prompt_without_focus():
    """测试不带重点领域的重构 Prompt."""
    prompt = get_refactor_skill_prompt("/path/to/skill")

    # 应该包含基本分析步骤
    assert "### 1. 当前状态分析" in prompt
    assert "### 2. 问题识别" in prompt
    assert "### 3. 重构建议" in prompt


def test_get_refactor_skill_prompt_contains_analysis_steps():
    """测试 Prompt 包含分析步骤."""
    prompt = get_refactor_skill_prompt("/path/to/skill")

    assert "### 1. 当前状态分析" in prompt
    assert "### 2. 问题识别" in prompt
    assert "### 3. 重构建议" in prompt


def test_get_refactor_skill_prompt_contains_refactor_principles():
    """测试 Prompt 包含重构原则."""
    prompt = get_refactor_skill_prompt("/path/to/skill")

    assert "## 重构原则" in prompt
    assert "保持功能不变" in prompt
    assert "渐进式改进" in prompt
    assert "向后兼容" in prompt
    assert "文档同步" in prompt


def test_get_refactor_skill_prompt_contains_output_format():
    """测试 Prompt 包含输出格式说明."""
    prompt = get_refactor_skill_prompt("/path/to/skill")

    assert "## 输出格式" in prompt
    assert "# 重构分析报告" in prompt
    assert "## 当前状态评估" in prompt
    assert "## 发现的问题" in prompt
    assert "## 重构建议" in prompt
    assert "## 实施计划" in prompt
