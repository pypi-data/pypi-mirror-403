"""测试问题模块.

测试 questions.py 的功能：
- get_static_questions - 获取静态问题列表
- get_next_static_question - 获取下一个静态问题
"""

from unittest.mock import MagicMock

import pytest

# ============================================================================
# get_static_questions 测试
# ============================================================================


def test_get_static_questions_basic_mode():
    """测试获取 basic 模式的静态问题."""
    from skill_creator_mcp.utils.requirement_collection.questions import (
        get_static_questions,
    )

    result = get_static_questions("basic")

    assert isinstance(result, list)
    assert len(result) > 0
    # basic 模式应该有基本的步骤
    assert all("key" in step for step in result)
    assert all("prompt" in step for step in result)
    assert all("validation" in step for step in result)


def test_get_static_questions_complete_mode():
    """测试获取 complete 模式的静态问题."""
    from skill_creator_mcp.utils.requirement_collection.questions import (
        get_static_questions,
    )

    basic_result = get_static_questions("basic")
    complete_result = get_static_questions("complete")

    assert isinstance(complete_result, list)
    assert len(complete_result) > len(basic_result)
    # complete 模式应该包含 basic 模式的所有步骤
    assert len(complete_result) > 0


def test_get_static_questions_brainstorm_mode():
    """测试获取 brainstorm 模式的静态问题."""
    from skill_creator_mcp.utils.requirement_collection.questions import (
        get_static_questions,
    )

    result = get_static_questions("brainstorm")

    assert isinstance(result, list)
    assert len(result) == 0  # 动态模式返回空列表


def test_get_static_questions_progressive_mode():
    """测试获取 progressive 模式的静态问题."""
    from skill_creator_mcp.utils.requirement_collection.questions import (
        get_static_questions,
    )

    result = get_static_questions("progressive")

    assert isinstance(result, list)
    assert len(result) == 0  # 动态模式返回空列表


def test_get_static_questions_invalid_mode():
    """测试获取无效模式的静态问题."""
    from skill_creator_mcp.utils.requirement_collection.questions import (
        get_static_questions,
    )

    result = get_static_questions("invalid")

    # 无效模式应该返回空列表或 basic 模式的问题
    assert isinstance(result, list)


# ============================================================================
# get_next_static_question 测试
# ============================================================================


@pytest.mark.asyncio
async def test_get_next_static_question_basic_first_step():
    """测试获取 basic 模式的第一个问题."""
    from skill_creator_mcp.utils.requirement_collection.questions import (
        get_next_static_question,
    )

    mock_ctx = MagicMock()

    result = await get_next_static_question(mock_ctx, "basic", 0)

    assert result["success"] is True
    assert result["completed"] is False
    assert "question_key" in result
    assert "question_text" in result
    assert "validation" in result
    assert result["step_index"] == 0


@pytest.mark.asyncio
async def test_get_next_static_question_basic_middle_step():
    """测试获取 basic 模式的中间步骤问题."""
    from skill_creator_mcp.utils.requirement_collection.questions import (
        get_next_static_question,
    )

    mock_ctx = MagicMock()

    result = await get_next_static_question(mock_ctx, "basic", 1)

    assert result["success"] is True
    assert result["completed"] is False
    assert result["step_index"] == 1


@pytest.mark.asyncio
async def test_get_next_static_question_complete_mode():
    """测试获取 complete 模式的问题."""
    from skill_creator_mcp.utils.requirement_collection.questions import (
        get_next_static_question,
    )

    mock_ctx = MagicMock()

    result = await get_next_static_question(mock_ctx, "complete", 0)

    assert result["success"] is True
    assert result["completed"] is False
    assert "question_key" in result


@pytest.mark.asyncio
async def test_get_next_static_question_out_of_bounds():
    """测试获取超出范围的问题索引."""
    from skill_creator_mcp.utils.requirement_collection.questions import (
        get_next_static_question,
    )

    mock_ctx = MagicMock()

    # 使用一个很大的索引值
    result = await get_next_static_question(mock_ctx, "basic", 999)

    assert result["success"] is True
    assert result["completed"] is True
    assert result["message"] == "所有步骤已完成"


@pytest.mark.asyncio
async def test_get_next_static_question_exactly_last_step():
    """测试获取最后一个问题."""
    from skill_creator_mcp.utils.requirement_collection.questions import (
        get_next_static_question,
    )

    mock_ctx = MagicMock()

    # 首先获取问题列表以确定最后一个索引
    from skill_creator_mcp.utils.requirement_collection.questions import (
        get_static_questions,
    )

    questions = get_static_questions("basic")
    last_index = len(questions) - 1

    result = await get_next_static_question(mock_ctx, "basic", last_index)

    assert result["success"] is True
    assert result["completed"] is False
    assert result["step_index"] == last_index

    # 下一步应该完成
    next_result = await get_next_static_question(mock_ctx, "basic", last_index + 1)
    assert next_result["completed"] is True


@pytest.mark.asyncio
async def test_get_next_static_question_brainstorm_mode():
    """测试获取 brainstorm 模式的问题（动态模式）."""
    from skill_creator_mcp.utils.requirement_collection.questions import (
        get_next_static_question,
    )

    mock_ctx = MagicMock()

    result = await get_next_static_question(mock_ctx, "brainstorm", 0)

    # brainstorm 模式没有静态问题，应该立即完成
    assert result["success"] is True
    assert result["completed"] is True


@pytest.mark.asyncio
async def test_get_next_static_question_progressive_mode():
    """测试获取 progressive 模式的问题（动态模式）."""
    from skill_creator_mcp.utils.requirement_collection.questions import (
        get_next_static_question,
    )

    mock_ctx = MagicMock()

    result = await get_next_static_question(mock_ctx, "progressive", 0)

    # progressive 模式没有静态问题，应该立即完成
    assert result["success"] is True
    assert result["completed"] is True


@pytest.mark.asyncio
async def test_get_next_static_question_returns_all_fields():
    """测试返回的问题包含所有必需字段."""
    from skill_creator_mcp.utils.requirement_collection.questions import (
        get_next_static_question,
    )

    mock_ctx = MagicMock()

    result = await get_next_static_question(mock_ctx, "basic", 0)

    # 验证所有必需字段存在
    assert "success" in result
    assert "question_key" in result
    assert "question_text" in result
    assert "validation" in result
    assert "title" in result
    assert "step_index" in result
    assert "completed" in result


@pytest.mark.asyncio
async def test_get_next_static_question_question_structure():
    """测试返回的问题数据结构."""
    from skill_creator_mcp.utils.requirement_collection.questions import (
        get_next_static_question,
    )

    mock_ctx = MagicMock()

    result = await get_next_static_question(mock_ctx, "basic", 0)

    # 验证数据类型
    assert isinstance(result["success"], bool)
    assert isinstance(result["question_key"], str)
    assert isinstance(result["question_text"], str)
    assert isinstance(result["validation"], dict)
    assert isinstance(result["step_index"], int)
    assert isinstance(result["completed"], bool)

    # 验证 validation 结构
    validation = result["validation"]
    assert "required" in validation
    assert "field" in validation
