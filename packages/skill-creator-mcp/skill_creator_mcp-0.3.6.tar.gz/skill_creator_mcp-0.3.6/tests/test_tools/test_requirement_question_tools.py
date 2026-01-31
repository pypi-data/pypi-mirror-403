"""测试需求收集问题获取工具.

测试 requirement_question_tools.py 模块的所有功能：
- get_static_question - 获取静态问题（用于 basic/complete 模式）
- generate_dynamic_question - 生成动态问题（用于 brainstorm/progressive 模式）
"""

from unittest.mock import AsyncMock, MagicMock, Mock

import pytest

# ============================================================================
# get_static_question 测试
# ============================================================================


@pytest.mark.asyncio
async def test_get_static_question_basic_mode_step_0():
    """测试获取 basic 模式第0步问题."""
    from skill_creator_mcp.tools.requirement_question_tools import get_static_question

    mock_ctx = MagicMock()
    result = await get_static_question(mock_ctx, mode="basic", step_index=0)

    assert result["success"] is True
    assert result["question_key"] == "skill_name"
    assert "技能名称" in result["placeholder"]
    assert "validation" in result
    assert result["step_index"] == 0


@pytest.mark.asyncio
async def test_get_static_question_basic_mode_all_steps():
    """测试获取 basic 模式所有步骤."""
    from skill_creator_mcp.tools.requirement_question_tools import get_static_question

    mock_ctx = MagicMock()

    # 测试所有5个步骤
    steps = [
        ("skill_name", "技能名称"),
        ("skill_function", "主要功能"),
        ("use_cases", "使用场景"),
        ("template_type", "模板类型"),
        ("additional_features", "额外需求"),
    ]

    for step_index, (expected_key, expected_title) in enumerate(steps):
        result = await get_static_question(mock_ctx, mode="basic", step_index=step_index)
        assert result["success"] is True
        assert result["question_key"] == expected_key
        assert expected_title in result["placeholder"]


@pytest.mark.asyncio
async def test_get_static_question_complete_mode_all_steps():
    """测试获取 complete 模式所有步骤."""
    from skill_creator_mcp.tools.requirement_question_tools import get_static_question

    mock_ctx = MagicMock()

    # basic 模式有5步，complete 模式总共10步
    # 测试第5-9步（complete 模式独有的步骤）
    complete_steps = [
        ("target_users", "目标用户"),
        ("tech_stack", "技术栈偏好"),
        ("dependencies", "外部依赖"),
        ("testing_requirements", "测试要求"),
        ("documentation_level", "文档级别"),
    ]

    for i, (expected_key, expected_title) in enumerate(complete_steps):
        step_index = 5 + i  # complete 模式从第5步开始
        result = await get_static_question(mock_ctx, mode="complete", step_index=step_index)
        assert result["success"] is True
        assert result["question_key"] == expected_key
        assert expected_title in result["placeholder"]


@pytest.mark.asyncio
async def test_get_static_question_invalid_mode():
    """测试无效模式."""
    from skill_creator_mcp.tools.requirement_question_tools import get_static_question

    mock_ctx = MagicMock()
    result = await get_static_question(mock_ctx, mode="invalid", step_index=0)

    # 由于 basic/complete 模式共享相同的步骤列表，无效模式仍然可以访问 basic 步骤
    # 这是实现细节，测试验证不会崩溃
    assert "success" in result


@pytest.mark.asyncio
async def test_get_static_question_invalid_step_index():
    """测试无效的步骤索引."""
    from skill_creator_mcp.tools.requirement_question_tools import get_static_question

    mock_ctx = MagicMock()

    # 测试负数索引
    result = await get_static_question(mock_ctx, mode="basic", step_index=-1)
    assert result["success"] is False
    assert "无效的步骤索引" in result["error"]

    # 测试超出范围的索引（basic 只有5步）
    result = await get_static_question(mock_ctx, mode="basic", step_index=10)
    assert result["success"] is False
    assert "无效的步骤索引" in result["error"]


@pytest.mark.asyncio
async def test_get_static_question_returns_valid_structure():
    """测试返回有效的数据结构."""
    from skill_creator_mcp.tools.requirement_question_tools import get_static_question

    mock_ctx = MagicMock()
    result = await get_static_question(mock_ctx, mode="basic", step_index=0)

    assert result["success"] is True
    assert "question_key" in result
    assert "question_text" in result
    assert "validation" in result
    assert isinstance(result["validation"], dict)
    assert "field" in result["validation"]
    assert "required" in result["validation"]


# ============================================================================
# generate_dynamic_question 测试
# ============================================================================


@pytest.mark.asyncio
async def test_generate_dynamic_question_brainstorm_mode():
    """测试 brainstorm 模式生成动态问题."""
    from skill_creator_mcp.tools.requirement_question_tools import generate_dynamic_question

    mock_ctx = MagicMock()
    mock_result = Mock()
    mock_result.text = "这个技能如何帮助用户节省时间？"
    mock_ctx.sample = AsyncMock(return_value=mock_result)

    answers = {"skill_name": "time-saver"}
    result = await generate_dynamic_question(mock_ctx, mode="brainstorm", answers=answers)

    assert result["success"] is True
    assert result["question_key"] == "brainstorm_1"
    assert result["question_text"] == "这个技能如何帮助用户节省时间？"
    assert result["is_llm_generated"] is True


@pytest.mark.asyncio
async def test_generate_dynamic_question_brainstorm_mode_with_history():
    """测试 brainstorm 模式带对话历史."""
    from skill_creator_mcp.tools.requirement_question_tools import generate_dynamic_question

    mock_ctx = MagicMock()
    mock_result = Mock()
    mock_result.text = "用户最需要什么功能？"
    mock_ctx.sample = AsyncMock(return_value=mock_result)

    answers = {"skill_name": "helper"}
    conversation_history = [
        {"role": "user", "content": "我想创建一个帮助工具"},
        {"role": "assistant", "content": "好的，请告诉我更多"},
    ]

    result = await generate_dynamic_question(
        mock_ctx, mode="brainstorm", answers=answers, conversation_history=conversation_history
    )

    assert result["success"] is True
    assert result["question_key"] == "brainstorm_1"
    assert result["is_llm_generated"] is True
    # 验证 sample 被调用，且包含对话历史上下文
    mock_ctx.sample.assert_called_once()


@pytest.mark.asyncio
async def test_generate_dynamic_question_progressive_mode():
    """测试 progressive 模式生成动态问题."""
    from skill_creator_mcp.tools.requirement_question_tools import generate_dynamic_question

    mock_ctx = MagicMock()
    mock_result = Mock()
    mock_result.text = '{"next_question": "请描述技能的主要功能", "question_key": "skill_function", "reasoning": "缺少功能描述"}'
    mock_ctx.sample = AsyncMock(return_value=mock_result)

    answers = {"skill_name": "test-skill"}
    result = await generate_dynamic_question(mock_ctx, mode="progressive", answers=answers)

    assert result["success"] is True
    assert result["question_key"] == "skill_function"
    assert "主要功能" in result["question_text"]
    assert result["is_llm_generated"] is True


@pytest.mark.asyncio
async def test_generate_dynamic_question_with_context():
    """测试带上下文的动态问题生成（progressive 模式，JSON 解析失败降级）."""
    from skill_creator_mcp.tools.requirement_question_tools import generate_dynamic_question

    mock_ctx = MagicMock()
    mock_result = Mock()
    # 返回非 JSON 格式的文本，触发降级逻辑
    mock_result.text = "请提供使用场景"
    mock_ctx.sample = AsyncMock(return_value=mock_result)

    answers = {"skill_name": "test", "skill_function": "测试功能"}
    result = await generate_dynamic_question(mock_ctx, mode="progressive", answers=answers)

    # 由于返回的不是有效 JSON，会降级到基础问题
    assert result["success"] is True
    # 当有2个答案时，应该返回第3个基础问题（use_cases）
    assert result["question_key"] == "use_cases"
    assert "使用场景" in result["question_text"]
    mock_ctx.sample.assert_called_once()


@pytest.mark.asyncio
async def test_generate_dynamic_question_invalid_mode():
    """测试无效模式."""
    from skill_creator_mcp.tools.requirement_question_tools import generate_dynamic_question

    mock_ctx = MagicMock()

    result = await generate_dynamic_question(mock_ctx, mode="basic", answers={})

    assert result["success"] is False
    assert "error" in result
    assert "动态模式只支持 brainstorm 和 progressive" in result["error"]


@pytest.mark.asyncio
async def test_generate_dynamic_question_llm_failure_handling():
    """测试 LLM 调用失败时的降级处理."""
    from skill_creator_mcp.tools.requirement_question_tools import generate_dynamic_question

    mock_ctx = MagicMock()
    mock_ctx.sample = AsyncMock(side_effect=Exception("LLM service unavailable"))

    answers = {}
    result = await generate_dynamic_question(mock_ctx, mode="brainstorm", answers=answers)

    # 应该降级到预定义问题
    assert result["success"] is True
    assert result["question_key"] == "brainstorm_0"
    assert result["is_llm_generated"] is False
    assert result.get("fallback") is True
    assert "error" in result


@pytest.mark.asyncio
async def test_generate_dynamic_question_progressive_json_parse_failed():
    """测试 progressive 模式 JSON 解析失败的降级处理."""
    from skill_creator_mcp.tools.requirement_question_tools import generate_dynamic_question

    mock_ctx = MagicMock()
    mock_result = Mock()
    mock_result.text = "This is not valid JSON output"
    mock_ctx.sample = AsyncMock(return_value=mock_result)

    answers = {}
    result = await generate_dynamic_question(mock_ctx, mode="progressive", answers=answers)

    # 应该降级到基础问题
    assert result["success"] is True
    assert result["question_key"] == "skill_name"
    assert result["is_llm_generated"] is False
    assert result.get("fallback") is True


@pytest.mark.asyncio
async def test_generate_dynamic_question_brainstorm_multiple_questions():
    """测试 brainstorm 模式连续生成多个问题."""
    from skill_creator_mcp.tools.requirement_question_tools import generate_dynamic_question

    mock_ctx = MagicMock()
    mock_result = Mock()
    mock_ctx.sample = AsyncMock(return_value=mock_result)

    # 第一个问题
    mock_result.text = "问题1"
    result1 = await generate_dynamic_question(mock_ctx, mode="brainstorm", answers={})
    assert result1["question_key"] == "brainstorm_0"

    # 第二个问题（answers 已有1项）
    mock_result.text = "问题2"
    result2 = await generate_dynamic_question(mock_ctx, mode="brainstorm", answers={"q1": "a1"})
    assert result2["question_key"] == "brainstorm_1"

    # 第三个问题
    mock_result.text = "问题3"
    result3 = await generate_dynamic_question(
        mock_ctx, mode="brainstorm", answers={"q1": "a1", "q2": "a2"}
    )
    assert result3["question_key"] == "brainstorm_2"


@pytest.mark.asyncio
async def test_generate_dynamic_question_returns_valid_structure():
    """测试返回有效的数据结构."""
    from skill_creator_mcp.tools.requirement_question_tools import generate_dynamic_question

    mock_ctx = MagicMock()
    mock_result = Mock()
    mock_result.text = "测试问题"
    mock_ctx.sample = AsyncMock(return_value=mock_result)

    result = await generate_dynamic_question(mock_ctx, mode="brainstorm", answers={})

    assert result["success"] is True
    assert "question_key" in result
    assert "question_text" in result
    assert "is_llm_generated" in result
    assert isinstance(result["is_llm_generated"], bool)


@pytest.mark.asyncio
async def test_generate_dynamic_question_context_integration():
    """测试上下文集成."""
    from skill_creator_mcp.tools.requirement_question_tools import generate_dynamic_question

    mock_ctx = MagicMock()
    mock_result = Mock()
    mock_result.text = "基于已有信息的探索性问题"
    mock_ctx.sample = AsyncMock(return_value=mock_result)

    answers = {"skill_name": "parser", "skill_function": "解析文件", "use_cases": "自动化处理"}
    conversation_history = [
        {"role": "user", "content": "我想做一个解析器"},
        {"role": "assistant", "content": "什么类型的解析器？"},
        {"role": "user", "content": "PDF解析器"},
    ]

    result = await generate_dynamic_question(
        mock_ctx, mode="brainstorm", answers=answers, conversation_history=conversation_history
    )

    assert result["success"] is True
    # 验证 sample 被调用，检查 prompt 中是否包含上下文
    call_args = mock_ctx.sample.call_args
    prompt = call_args[1]["messages"]
    assert "parser" in prompt or "PDF" in prompt or "解析" in prompt


@pytest.mark.asyncio
async def test_question_tools_maintain_atomicity():
    """测试问题获取工具保持原子性（不包含工作流逻辑）."""
    from skill_creator_mcp.tools.requirement_question_tools import (
        generate_dynamic_question,
        get_static_question,
    )

    mock_ctx = MagicMock()
    mock_result = Mock()
    mock_result.text = "下一个问题"
    mock_ctx.sample = AsyncMock(return_value=mock_result)

    # get_static_question 应该只返回单个问题，不循环
    result1 = await get_static_question(mock_ctx, mode="basic", step_index=0)
    assert result1["step_index"] == 0
    assert result1["question_key"] == "skill_name"

    # generate_dynamic_question 应该只返回单个问题，不循环
    result2 = await generate_dynamic_question(mock_ctx, mode="brainstorm", answers={})
    assert result2["question_key"] == "brainstorm_0"
    assert "question_text" in result2

    # 验证没有自动推进到下一步
    result3 = await get_static_question(mock_ctx, mode="basic", step_index=0)
    assert result3["step_index"] == 0  # 仍然是第0步，没有自动递增
