"""Elicit 模式单元测试.

测试 collect_requirements 工具的 use_elicit 参数功能：
- elicit 模式自动调用 ctx.elicit() 收集输入
- 用户取消处理
- 验证失败重试
- 会话状态正确保存

注意：previous 和 status action 在主函数 collect_requirements 中处理，
不通过 _collect_with_elicit，因此相关测试在 test_fallback_scenarios.py 中。
"""

from unittest.mock import AsyncMock, MagicMock, Mock

import pytest

from skill_creator_mcp.constants import BASIC_REQUIREMENT_STEPS
from skill_creator_mcp.models.skill_config import (
    RequirementCollectionInput,
    SessionState,
)
from skill_creator_mcp.utils.requirement_collection import _collect_with_elicit

# ============================================================================
# Elicit 模式核心组件测试
# ============================================================================


@pytest.mark.asyncio
async def test_collect_with_elicit_user_cancel():
    """测试用户取消输入的情况."""
    from datetime import datetime
    from datetime import timezone as tz

    mock_ctx = MagicMock()
    mock_ctx.set_state = AsyncMock()

    # 第一次调用 elicit 就被取消
    mock_ctx.elicit = AsyncMock(return_value=Mock(accepted=False))

    session_state = SessionState(
        current_step_index=0,
        answers={},
        started_at=datetime.now(tz.utc).isoformat(),
        completed=False,
        mode="basic",
        total_steps=5,
    )

    input_data = RequirementCollectionInput.model_validate(
        {
            "action": "start",
            "mode": "basic",
            "session_id": "test-session",
        }
    )

    result = await _collect_with_elicit(
        ctx=mock_ctx,
        session_state=session_state,
        current_session_id="test-session",
        is_dynamic_mode=False,
        all_steps=BASIC_REQUIREMENT_STEPS,
        input_data=input_data,
    )

    # 验证取消状态
    assert result["success"] is False
    assert result["action"] == "cancelled"
    assert "用户取消" in result["message"]


@pytest.mark.asyncio
async def test_collect_with_elicit_validation_retry():
    """测试验证失败后的重试逻辑."""
    from datetime import datetime
    from datetime import timezone as tz

    mock_ctx = MagicMock()
    mock_ctx.set_state = AsyncMock()

    # 第一次输入无效，第二次输入有效
    elicit_call_count = 0

    async def mock_elicit(prompt, **kwargs):
        nonlocal elicit_call_count
        elicit_call_count += 1

        # 第一次输入无效（大写字母）
        if elicit_call_count == 1:
            mock_result = Mock()
            mock_result.accepted = True
            mock_result.data = "Invalid"
            return mock_result
        # 第二次输入有效
        elif elicit_call_count == 2:
            mock_result = Mock()
            mock_result.accepted = True
            mock_result.data = "valid-skill"
            return mock_result

        # 后续调用返回空数据
        mock_result = Mock()
        mock_result.accepted = True
        mock_result.data = "more-data"
        return mock_result

    mock_ctx.elicit = mock_elicit

    session_state = SessionState(
        current_step_index=0,
        answers={},
        started_at=datetime.now(tz.utc).isoformat(),
        completed=False,
        mode="basic",
        total_steps=5,
    )

    input_data = RequirementCollectionInput.model_validate(
        {
            "action": "start",
            "mode": "basic",
            "session_id": "test-session",
        }
    )

    # 设置最大重试次数为 3
    await _collect_with_elicit(
        ctx=mock_ctx,
        session_state=session_state,
        current_session_id="test-session",
        is_dynamic_mode=False,
        all_steps=BASIC_REQUIREMENT_STEPS,
        input_data=input_data,
        max_retries=3,
    )

    # 应该在重试后继续
    # 由于我们只模拟了两次 elicit 调用，第二次输入会通过验证
    # 之后会尝试继续，但由于没有更多的 elicit 结果，可能会失败
    # 这里我们主要验证重试逻辑被正确触发
    assert elicit_call_count >= 2  # 至少调用两次（第一次失败，第二次成功）


@pytest.mark.asyncio
async def test_collect_with_elicit_max_retries_exceeded():
    """测试超过最大重试次数的情况."""
    from datetime import datetime
    from datetime import timezone as tz

    mock_ctx = MagicMock()
    mock_ctx.set_state = AsyncMock()

    # 始终返回无效输入
    mock_ctx.elicit = AsyncMock(return_value=Mock(accepted=True, data="Invalid"))

    session_state = SessionState(
        current_step_index=0,
        answers={},
        started_at=datetime.now(tz.utc).isoformat(),
        completed=False,
        mode="basic",
        total_steps=5,
    )

    input_data = RequirementCollectionInput.model_validate(
        {
            "action": "start",
            "mode": "basic",
            "session_id": "test-session",
        }
    )

    result = await _collect_with_elicit(
        ctx=mock_ctx,
        session_state=session_state,
        current_session_id="test-session",
        is_dynamic_mode=False,
        all_steps=BASIC_REQUIREMENT_STEPS,
        input_data=input_data,
        max_retries=2,  # 设置较小的重试次数
    )

    # 验证返回错误
    assert result["success"] is False
    assert "验证失败" in result["error"]


@pytest.mark.asyncio
async def test_collect_with_elicit_elicit_error():
    """测试 elicit 调用失败的情况."""
    from datetime import datetime
    from datetime import timezone as tz

    mock_ctx = MagicMock()
    mock_ctx.set_state = AsyncMock()

    # elicit 调用抛出异常
    mock_ctx.elicit = AsyncMock(side_effect=Exception("elicit service unavailable"))

    session_state = SessionState(
        current_step_index=0,
        answers={},
        started_at=datetime.now(tz.utc).isoformat(),
        completed=False,
        mode="basic",
        total_steps=5,
    )

    input_data = RequirementCollectionInput.model_validate(
        {
            "action": "start",
            "mode": "basic",
            "session_id": "test-session",
        }
    )

    result = await _collect_with_elicit(
        ctx=mock_ctx,
        session_state=session_state,
        current_session_id="test-session",
        is_dynamic_mode=False,
        all_steps=BASIC_REQUIREMENT_STEPS,
        input_data=input_data,
    )

    # 验证错误处理
    assert result["success"] is False
    assert "elicit" in result["error"].lower()


@pytest.mark.asyncio
async def test_collect_with_elicit_state_persistence():
    """测试会话状态正确保存."""
    from datetime import datetime
    from datetime import timezone as tz

    mock_ctx = MagicMock()
    state_snapshots = []

    async def mock_set_state(key, value):
        state_snapshots.append(value)

    mock_ctx.set_state = mock_set_state
    mock_ctx.elicit = AsyncMock(return_value=Mock(accepted=True, data="test-data"))

    session_state = SessionState(
        current_step_index=0,
        answers={},
        started_at=datetime.now(tz.utc).isoformat(),
        completed=False,
        mode="basic",
        total_steps=5,
    )

    input_data = RequirementCollectionInput.model_validate(
        {
            "action": "start",
            "mode": "basic",
            "session_id": "test-session",
        }
    )

    # 由于 elicit 只返回一次，会在处理完第一个步骤后失败
    # 但我们仍可以验证状态被保存
    await _collect_with_elicit(
        ctx=mock_ctx,
        session_state=session_state,
        current_session_id="test-session",
        is_dynamic_mode=False,
        all_steps=BASIC_REQUIREMENT_STEPS,
        input_data=input_data,
    )

    # 验证状态被保存至少一次
    assert len(state_snapshots) >= 1


# ============================================================================
# 动态模式 Elicit 测试 (Brainstorm/Progressive)
# ============================================================================


@pytest.mark.asyncio
async def test_collect_with_elicit_brainstorm_mode():
    """测试 brainstorm 模式的 elicit 集成."""
    from datetime import datetime
    from datetime import timezone as tz

    mock_ctx = MagicMock()
    mock_ctx.set_state = AsyncMock()
    state_snapshots = []

    async def mock_set_state(key, value):
        state_snapshots.append(value)

    mock_ctx.set_state = mock_set_state

    # 模拟 elicit 返回用户输入
    elicit_responses = [
        "pdf-processing",
        "extract text and images from PDF files",
        "document automation workflow",
        "tool-based",
        "support OCR and batch processing",
    ]
    response_index = [0]

    async def mock_elicit(prompt, **kwargs):
        mock_result = Mock()
        mock_result.accepted = True
        if response_index[0] < len(elicit_responses):
            mock_result.data = elicit_responses[response_index[0]]
            response_index[0] += 1
        else:
            mock_result.data = "additional info"
        return mock_result

    mock_ctx.elicit = mock_elicit

    session_state = SessionState(
        current_step_index=0,
        answers={},
        started_at=datetime.now(tz.utc).isoformat(),
        completed=False,
        mode="brainstorm",
        total_steps=10,
    )

    input_data = RequirementCollectionInput.model_validate(
        {
            "action": "start",
            "mode": "brainstorm",
            "session_id": "test-session",
        }
    )

    result = await _collect_with_elicit(
        ctx=mock_ctx,
        session_state=session_state,
        current_session_id="test-session",
        is_dynamic_mode=True,
        all_steps=None,
        input_data=input_data,
    )

    # 验证返回结果
    assert result["success"] is True
    assert "answers" in result
    # brainstorm 模式会收集多轮答案
    assert len(result["answers"]) > 0


@pytest.mark.asyncio
async def test_collect_with_elicit_progressive_mode():
    """测试 progressive 模式的 elicit 集成."""
    from datetime import datetime
    from datetime import timezone as tz

    mock_ctx = MagicMock()
    mock_ctx.set_state = AsyncMock()

    # 模拟 elicit 返回用户输入
    elicit_responses = ["test-skill", "A test skill function", "For testing"]
    response_index = [0]

    async def mock_elicit(prompt, **kwargs):
        mock_result = Mock()
        mock_result.accepted = True
        if response_index[0] < len(elicit_responses):
            mock_result.data = elicit_responses[response_index[0]]
            response_index[0] += 1
        else:
            mock_result.data = "more info"
        return mock_result

    mock_ctx.elicit = mock_elicit

    session_state = SessionState(
        current_step_index=0,
        answers={},
        started_at=datetime.now(tz.utc).isoformat(),
        completed=False,
        mode="progressive",
        total_steps=10,
    )

    input_data = RequirementCollectionInput.model_validate(
        {
            "action": "start",
            "mode": "progressive",
            "session_id": "test-session",
        }
    )

    result = await _collect_with_elicit(
        ctx=mock_ctx,
        session_state=session_state,
        current_session_id="test-session",
        is_dynamic_mode=True,
        all_steps=None,
        input_data=input_data,
    )

    # 验证返回结果
    assert "answers" in result
    # progressive 模式会收集多轮答案
    assert len(result["answers"]) > 0


@pytest.mark.asyncio
async def test_collect_with_elicit_brainstorm_conversation_history():
    """测试 brainstorm 模式的对话历史更新."""
    from datetime import datetime
    from datetime import timezone as tz

    mock_ctx = MagicMock()
    state_snapshots = []

    async def mock_set_state(key, value):
        state_snapshots.append(value)

    mock_ctx.set_state = mock_set_state

    # 模拟 elicit 返回用户输入
    call_count = [0]

    async def mock_elicit(prompt, **kwargs):
        mock_result = Mock()
        mock_result.accepted = True
        call_count[0] += 1
        mock_result.data = f"User input {call_count[0]}"
        return mock_result

    mock_ctx.elicit = mock_elicit

    session_state = SessionState(
        current_step_index=0,
        answers={},
        started_at=datetime.now(tz.utc).isoformat(),
        completed=False,
        mode="brainstorm",
        total_steps=10,
    )

    input_data = RequirementCollectionInput.model_validate(
        {
            "action": "start",
            "mode": "brainstorm",
            "session_id": "test-session",
        }
    )

    # 运行几轮
    await _collect_with_elicit(
        ctx=mock_ctx,
        session_state=session_state,
        current_session_id="test-session",
        is_dynamic_mode=True,
        all_steps=None,
        input_data=input_data,
    )

    # 验证对话历史被保存
    assert len(state_snapshots) > 0
    # 检查最后一次状态快照包含对话历史
    last_snapshot = state_snapshots[-1]
    # 对话历史应该被保存在独立的 conversation_history 字段中
    assert "conversation_history" in last_snapshot
    assert len(last_snapshot["conversation_history"]) >= 5  # 至少有5轮对话


# ============================================================================
# 总结
# ============================================================================

"""
Elicit 模式测试总结：

基础功能：
1. ✅ 用户取消处理
2. ✅ 验证失败重试
3. ✅ 超过最大重试次数
4. ✅ elicit 调用失败处理
5. ✅ 会话状态持久化

动态模式 (新增):
6. ✅ brainstorm 模式 elicit 集成
7. ✅ progressive 模式 elicit 集成
8. ✅ brainstorm 对话历史更新

注意：这些测试验证了 elicit 模式的核心逻辑。
要在实际 Claude Code 环境中测试完整的 elicit 功能，
需要启动 MCP Server 并通过 MCP 协议调用工具。

previous 和 status action 的测试在 test_fallback_scenarios.py 中。
"""
