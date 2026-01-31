"""测试会话状态管理模块.

测试 session_manager.py 的功能：
- load_session_state - 加载会话状态
- save_session_state - 保存会话状态
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from skill_creator_mcp.models.skill_config import SessionState

# ============================================================================
# load_session_state 测试
# ============================================================================


@pytest.mark.asyncio
async def test_load_session_state_success():
    """测试成功加载会话状态."""
    from skill_creator_mcp.utils.requirement_collection.session_manager import (
        load_session_state,
    )

    mock_ctx = MagicMock()
    mock_ctx.get_state = AsyncMock(
        return_value={
            "mode": "basic",
            "current_step_index": 0,
            "total_steps": 5,
            "answers": {},
            "started_at": "2024-01-01T00:00:00Z",
        }
    )

    result = await load_session_state(mock_ctx, "test-session")

    assert isinstance(result, SessionState)
    assert result.mode == "basic"
    assert result.current_step_index == 0
    assert result.total_steps == 5
    mock_ctx.get_state.assert_called_once_with("requirement_test-session")


@pytest.mark.asyncio
async def test_load_session_state_not_found():
    """测试加载不存在的会话状态."""
    from skill_creator_mcp.utils.requirement_collection.session_manager import (
        load_session_state,
    )

    mock_ctx = MagicMock()
    mock_ctx.get_state = AsyncMock(return_value=None)

    result = await load_session_state(mock_ctx, "non-existent")

    assert result is None
    mock_ctx.get_state.assert_called_once_with("requirement_non-existent")


@pytest.mark.asyncio
async def test_load_session_state_with_answers():
    """测试加载包含答案的会话状态."""
    from skill_creator_mcp.utils.requirement_collection.session_manager import (
        load_session_state,
    )

    mock_ctx = MagicMock()
    mock_ctx.get_state = AsyncMock(
        return_value={
            "mode": "complete",
            "current_step_index": 2,
            "total_steps": 10,
            "answers": {
                "skill_name": "test-skill",
                "skill_function": "do something",
            },
            "started_at": "2024-01-01T00:00:00Z",
        }
    )

    result = await load_session_state(mock_ctx, "test-session")

    assert isinstance(result, SessionState)
    assert result.mode == "complete"
    assert result.current_step_index == 2
    assert result.answers["skill_name"] == "test-skill"
    assert result.answers["skill_function"] == "do something"


# ============================================================================
# save_session_state 测试
# ============================================================================


@pytest.mark.asyncio
async def test_save_session_state_basic():
    """测试保存基本会话状态."""
    from skill_creator_mcp.utils.requirement_collection.session_manager import (
        save_session_state,
    )

    mock_ctx = MagicMock()
    mock_ctx.set_state = AsyncMock()

    state = SessionState(
        mode="basic",
        current_step_index=0,
        total_steps=5,
        answers={},
    )

    await save_session_state(mock_ctx, "test-session", state)

    mock_ctx.set_state.assert_called_once()
    call_args = mock_ctx.set_state.call_args
    assert call_args[0][0] == "requirement_test-session"
    assert call_args[0][1]["mode"] == "basic"
    assert call_args[0][1]["current_step_index"] == 0


@pytest.mark.asyncio
async def test_save_session_state_with_answers():
    """测试保存包含答案的会话状态."""
    from skill_creator_mcp.utils.requirement_collection.session_manager import (
        save_session_state,
    )

    mock_ctx = MagicMock()
    mock_ctx.set_state = AsyncMock()

    state = SessionState(
        mode="complete",
        current_step_index=3,
        total_steps=10,
        answers={
            "skill_name": "my-skill",
            "skill_function": "perform tasks",
            "use_cases": "case1, case2",
        },
    )

    await save_session_state(mock_ctx, "test-session", state)

    mock_ctx.set_state.assert_called_once()
    call_args = mock_ctx.set_state.call_args
    assert call_args[0][1]["answers"]["skill_name"] == "my-skill"
    assert call_args[0][1]["answers"]["skill_function"] == "perform tasks"
    assert "case1" in call_args[0][1]["answers"]["use_cases"]


@pytest.mark.asyncio
async def test_save_session_state_increment_step():
    """测试保存步数递增的会话状态."""
    from skill_creator_mcp.utils.requirement_collection.session_manager import (
        save_session_state,
    )

    mock_ctx = MagicMock()
    mock_ctx.set_state = AsyncMock()

    state = SessionState(
        mode="basic",
        current_step_index=5,
        total_steps=10,
        answers={},
    )

    await save_session_state(mock_ctx, "test-session", state)

    mock_ctx.set_state.assert_called_once()
    call_args = mock_ctx.set_state.call_args
    assert call_args[0][1]["current_step_index"] == 5


@pytest.mark.asyncio
async def test_save_and_load_session_state_roundtrip():
    """测试保存后加载会话状态的往返."""
    from skill_creator_mcp.utils.requirement_collection.session_manager import (
        load_session_state,
        save_session_state,
    )

    mock_ctx = MagicMock()
    mock_ctx.get_state = AsyncMock()
    mock_ctx.set_state = AsyncMock()

    # 保存状态
    original_state = SessionState(
        mode="complete",
        current_step_index=2,
        total_steps=8,
        answers={"skill_name": "roundtrip-skill"},
    )

    await save_session_state(mock_ctx, "test-session", original_state)

    # 模拟加载时返回保存的数据
    saved_data = original_state.model_dump()
    mock_ctx.get_state = AsyncMock(return_value=saved_data)

    # 加载状态
    loaded_state = await load_session_state(mock_ctx, "test-session")

    assert loaded_state.mode == original_state.mode
    assert loaded_state.current_step_index == original_state.current_step_index
    assert loaded_state.answers == original_state.answers


# ============================================================================
# 边界条件测试
# ============================================================================


@pytest.mark.asyncio
async def test_load_session_state_empty_data():
    """测试加载空数据."""
    from skill_creator_mcp.utils.requirement_collection.session_manager import (
        load_session_state,
    )

    mock_ctx = MagicMock()
    mock_ctx.get_state = AsyncMock(return_value=None)

    result = await load_session_state(mock_ctx, "empty-session")

    # None 应该返回 None
    assert result is None


@pytest.mark.asyncio
async def test_save_session_state_with_all_fields():
    """测试保存包含所有字段的会话状态."""
    from skill_creator_mcp.utils.requirement_collection.session_manager import (
        save_session_state,
    )

    mock_ctx = MagicMock()
    mock_ctx.set_state = AsyncMock()

    state = SessionState(
        mode="complete",
        current_step_index=1,
        total_steps=8,
        answers={
            "skill_name": "complex-skill",
            "skill_function": "complex function",
            "use_cases": "case1, case2, case3",
        },
        conversation_history=[
            {"role": "user", "content": "question 1"},
            {"role": "assistant", "content": "answer 1"},
        ],
        started_at="2024-01-01T00:00:00Z",
        completed=False,
    )

    await save_session_state(mock_ctx, "test-session", state)

    mock_ctx.set_state.assert_called_once()
    call_args = mock_ctx.set_state.call_args
    assert "case1" in call_args[0][1]["answers"]["use_cases"]
    assert len(call_args[0][1]["conversation_history"]) == 2
