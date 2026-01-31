"""测试需求收集会话管理工具.

测试 requirement_session_tools.py 模块的所有功能：
- create_requirement_session - 创建需求收集会话
- get_requirement_session - 获取会话状态
- update_requirement_answer - 更新会话答案
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

# ============================================================================
# create_requirement_session 测试
# ============================================================================


@pytest.mark.asyncio
async def test_create_requirement_session_basic_mode():
    """测试创建 basic 模式会话."""
    from skill_creator_mcp.tools.requirement_session_tools import create_requirement_session

    mock_ctx = MagicMock()
    mock_ctx.set_state = AsyncMock()

    result = await create_requirement_session(mock_ctx, mode="basic")

    assert result["success"] is True
    assert result["mode"] == "basic"
    assert result["total_steps"] == 5  # BASIC_REQUIREMENT_STEPS 长度
    assert result["current_step"] == 0
    assert result["completed"] is False
    assert "session_id" in result
    assert "started_at" in result
    assert isinstance(result["answers"], dict)
    mock_ctx.set_state.assert_called_once()


@pytest.mark.asyncio
async def test_create_requirement_session_complete_mode():
    """测试创建 complete 模式会话."""
    from skill_creator_mcp.tools.requirement_session_tools import create_requirement_session

    mock_ctx = MagicMock()
    mock_ctx.set_state = AsyncMock()

    result = await create_requirement_session(mock_ctx, mode="complete")

    assert result["success"] is True
    assert result["mode"] == "complete"
    assert result["total_steps"] == 10  # 5 basic + 5 complete
    assert result["current_step"] == 0
    mock_ctx.set_state.assert_called_once()


@pytest.mark.asyncio
async def test_create_requirement_session_brainstorm_mode():
    """测试创建 brainstorm 模式会话."""
    from skill_creator_mcp.tools.requirement_session_tools import create_requirement_session

    mock_ctx = MagicMock()
    mock_ctx.set_state = AsyncMock()

    result = await create_requirement_session(mock_ctx, mode="brainstorm")

    assert result["success"] is True
    assert result["mode"] == "brainstorm"
    assert result["total_steps"] == 100  # 动态模式，无固定步骤
    mock_ctx.set_state.assert_called_once()


@pytest.mark.asyncio
async def test_create_requirement_session_invalid_mode():
    """测试创建无效模式会话."""
    from skill_creator_mcp.tools.requirement_session_tools import create_requirement_session

    mock_ctx = MagicMock()
    mock_ctx.set_state = AsyncMock()

    result = await create_requirement_session(mock_ctx, mode="invalid_mode")

    assert result["success"] is False
    assert "error" in result
    assert "无效的模式" in result["error"]
    assert "valid_modes" in result
    mock_ctx.set_state.assert_not_called()


@pytest.mark.asyncio
async def test_create_requirement_session_custom_total_steps():
    """测试创建自定义总步骤数的会话."""
    from skill_creator_mcp.tools.requirement_session_tools import create_requirement_session

    mock_ctx = MagicMock()
    mock_ctx.set_state = AsyncMock()

    result = await create_requirement_session(mock_ctx, mode="basic", total_steps=15)

    assert result["success"] is True
    assert result["total_steps"] == 15
    mock_ctx.set_state.assert_called_once()


@pytest.mark.asyncio
async def test_create_requirement_session_progressive_mode():
    """测试创建 progressive 模式会话."""
    from skill_creator_mcp.tools.requirement_session_tools import create_requirement_session

    mock_ctx = MagicMock()
    mock_ctx.set_state = AsyncMock()

    result = await create_requirement_session(mock_ctx, mode="progressive")

    assert result["success"] is True
    assert result["mode"] == "progressive"
    assert result["total_steps"] == 100  # 动态模式
    mock_ctx.set_state.assert_called_once()


# ============================================================================
# get_requirement_session 测试
# ============================================================================


@pytest.mark.asyncio
async def test_get_requirement_session_success():
    """测试获取会话成功."""
    from skill_creator_mcp.tools.requirement_session_tools import get_requirement_session

    mock_ctx = MagicMock()
    mock_session_data = {
        "current_step_index": 2,
        "answers": {"skill_name": "test-skill", "skill_function": "测试功能"},
        "started_at": datetime.now().isoformat(),
        "completed": False,
        "mode": "basic",
        "total_steps": 5,
    }
    mock_ctx.get_state = AsyncMock(return_value=mock_session_data)

    result = await get_requirement_session(mock_ctx, "req_test_session_id")

    assert result["success"] is True
    assert result["session_id"] == "req_test_session_id"
    assert result["current_step"] == 2
    assert result["mode"] == "basic"
    assert result["total_steps"] == 5
    assert result["completed"] is False
    assert result["answers"] == {"skill_name": "test-skill", "skill_function": "测试功能"}
    mock_ctx.get_state.assert_called_once()


@pytest.mark.asyncio
async def test_get_requirement_session_not_found():
    """测试获取不存在的会话."""
    from skill_creator_mcp.tools.requirement_session_tools import get_requirement_session

    mock_ctx = MagicMock()
    mock_ctx.get_state = AsyncMock(return_value=None)

    result = await get_requirement_session(mock_ctx, "req_nonexistent")

    assert result["success"] is False
    assert "error" in result
    assert "会话不存在" in result["error"]
    assert result["error_type"] == "session_not_found"


@pytest.mark.asyncio
async def test_get_requirement_session_completed():
    """测试获取已完成的会话."""
    from skill_creator_mcp.tools.requirement_session_tools import get_requirement_session

    mock_ctx = MagicMock()
    mock_session_data = {
        "current_step_index": 5,
        "answers": {"skill_name": "test-skill"},
        "started_at": datetime.now().isoformat(),
        "completed": True,
        "mode": "basic",
        "total_steps": 5,
    }
    mock_ctx.get_state = AsyncMock(return_value=mock_session_data)

    result = await get_requirement_session(mock_ctx, "req_completed_session")

    assert result["success"] is True
    assert result["completed"] is True
    assert result["current_step"] == 5


# ============================================================================
# update_requirement_answer 测试
# ============================================================================


@pytest.mark.asyncio
async def test_update_requirement_answer_success():
    """测试更新答案成功."""
    from skill_creator_mcp.tools.requirement_session_tools import update_requirement_answer

    mock_ctx = MagicMock()
    mock_session_data = {
        "current_step_index": 0,
        "answers": {},
        "started_at": datetime.now().isoformat(),
        "completed": False,
        "mode": "basic",
        "total_steps": 5,
    }
    mock_ctx.get_state = AsyncMock(return_value=mock_session_data)
    mock_ctx.set_state = AsyncMock()

    result = await update_requirement_answer(mock_ctx, "req_test", "skill_name", "test-skill")

    assert result["success"] is True
    assert result["session_id"] == "req_test"
    assert result["updated"] is True
    assert result["completed"] is False
    mock_ctx.get_state.assert_called_once()
    mock_ctx.set_state.assert_called_once()


@pytest.mark.asyncio
async def test_update_requirement_answer_session_not_found():
    """测试更新不存在的会话答案."""
    from skill_creator_mcp.tools.requirement_session_tools import update_requirement_answer

    mock_ctx = MagicMock()
    mock_ctx.get_state = AsyncMock(return_value=None)

    result = await update_requirement_answer(mock_ctx, "req_nonexistent", "skill_name", "test-skill")

    assert result["success"] is False
    assert "error" in result
    assert "会话不存在" in result["error"]
    assert result["error_type"] == "session_not_found"
    mock_ctx.set_state.assert_not_called()


@pytest.mark.asyncio
async def test_update_requirement_answer_preserves_history():
    """测试更新答案保留已有答案."""
    from skill_creator_mcp.tools.requirement_session_tools import update_requirement_answer

    mock_ctx = MagicMock()
    mock_session_data = {
        "current_step_index": 1,
        "answers": {"skill_name": "test-skill"},
        "started_at": datetime.now().isoformat(),
        "completed": False,
        "mode": "basic",
        "total_steps": 5,
    }
    mock_ctx.get_state = AsyncMock(return_value=mock_session_data)
    mock_ctx.set_state = AsyncMock()

    result = await update_requirement_answer(mock_ctx, "req_test", "skill_function", "测试功能")

    assert result["success"] is True
    assert result["updated"] is True
    # 验证 set_state 被调用，且包含了新旧答案
    call_args = mock_ctx.set_state.call_args
    updated_state = call_args[0][1]
    assert updated_state["answers"]["skill_name"] == "test-skill"
    assert updated_state["answers"]["skill_function"] == "测试功能"


@pytest.mark.asyncio
async def test_update_requirement_answer_overwrite_existing():
    """测试覆盖已存在的答案."""
    from skill_creator_mcp.tools.requirement_session_tools import update_requirement_answer

    mock_ctx = MagicMock()
    mock_session_data = {
        "current_step_index": 1,
        "answers": {"skill_name": "old-name"},
        "started_at": datetime.now().isoformat(),
        "completed": False,
        "mode": "basic",
        "total_steps": 5,
    }
    mock_ctx.get_state = AsyncMock(return_value=mock_session_data)
    mock_ctx.set_state = AsyncMock()

    result = await update_requirement_answer(mock_ctx, "req_test", "skill_name", "new-name")

    assert result["success"] is True
    assert result["updated"] is True
    call_args = mock_ctx.set_state.call_args
    updated_state = call_args[0][1]
    assert updated_state["answers"]["skill_name"] == "new-name"


# ============================================================================
# session_state_management_flow 测试
# ============================================================================


@pytest.mark.asyncio
async def test_session_state_management_flow():
    """测试完整的会话状态管理流程."""
    from skill_creator_mcp.tools.requirement_session_tools import (
        create_requirement_session,
        get_requirement_session,
        update_requirement_answer,
    )

    mock_ctx = MagicMock()
    mock_ctx.set_state = AsyncMock()
    mock_ctx.get_state = AsyncMock()

    # 1. 创建会话
    create_result = await create_requirement_session(mock_ctx, mode="basic")
    assert create_result["success"] is True
    session_id = create_result["session_id"]

    # 2. 获取会话状态
    mock_session_data = {
        "current_step_index": 0,
        "answers": {},
        "started_at": create_result["started_at"],
        "completed": False,
        "mode": "basic",
        "total_steps": 5,
    }
    mock_ctx.get_state = AsyncMock(return_value=mock_session_data)

    get_result = await get_requirement_session(mock_ctx, session_id)
    assert get_result["success"] is True
    assert get_result["current_step"] == 0

    # 3. 更新答案
    update_result = await update_requirement_answer(mock_ctx, session_id, "skill_name", "test-skill")
    assert update_result["success"] is True
    assert update_result["updated"] is True

    # 4. 再次获取会话状态，验证答案已更新
    updated_session_data = mock_session_data.copy()
    updated_session_data["answers"] = {"skill_name": "test-skill"}
    mock_ctx.get_state = AsyncMock(return_value=updated_session_data)

    final_result = await get_requirement_session(mock_ctx, session_id)
    assert final_result["success"] is True
    assert final_result["answers"]["skill_name"] == "test-skill"
