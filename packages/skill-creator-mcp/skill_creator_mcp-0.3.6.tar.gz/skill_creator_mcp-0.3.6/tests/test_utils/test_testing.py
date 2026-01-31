"""测试工具函数单元测试.

测试 testing.py 模块的所有功能：
- check_client_capabilities - 检测客户端能力
- test_llm_sampling - 测试 LLM sampling
- test_user_elicitation - 测试用户交互
- test_conversation_loop - 测试对话循环
- test_requirement_completeness - 测试需求完整性检查
"""

from unittest.mock import AsyncMock, MagicMock, Mock

import pytest

# ============================================================================
# check_client_capabilities 测试
# ============================================================================


@pytest.mark.asyncio
async def test_check_client_capabilities_success():
    """测试客户端能力检测成功的情况."""
    from skill_creator_mcp.utils import testing as testing_module

    mock_ctx = MagicMock()
    mock_ctx.sample = AsyncMock(return_value=Mock(text="test"))
    mock_ctx.elicit = AsyncMock(return_value=Mock(accepted=True, data="test"))
    mock_ctx.get_state = AsyncMock(return_value=None)
    mock_ctx.set_state = AsyncMock()

    result = await testing_module.check_client_capabilities(mock_ctx)

    assert result["sampling"]["supported"] is True
    assert result["elicitation"]["supported"] is True


# ============================================================================
# test_llm_sampling 测试
# ============================================================================


@pytest.mark.asyncio
async def test_llm_sampling_tool_success():
    """测试 LLM sampling 成功的情况."""
    from skill_creator_mcp.utils import testing as testing_module

    mock_ctx = MagicMock()
    mock_result = Mock()
    mock_result.text = "Test LLM response"
    mock_result.history = [{"role": "user", "content": "test"}]
    mock_ctx.sample = AsyncMock(return_value=mock_result)

    result = await testing_module.test_llm_sampling(mock_ctx, "Test prompt")

    assert result["success"] is True
    assert result["has_response"] is True
    assert result["response_text"] == "Test LLM response"
    assert result["has_history"] is True
    assert result["history_length"] == 1


@pytest.mark.asyncio
async def test_llm_sampling_tool_failure():
    """测试 LLM sampling 失败的情况."""
    from skill_creator_mcp.utils import testing as testing_module

    mock_ctx = MagicMock()
    mock_ctx.sample = AsyncMock(side_effect=Exception("Sampling failed"))

    result = await testing_module.test_llm_sampling(mock_ctx, "Test prompt")

    assert result["success"] is False
    assert "error" in result
    assert result["error"] == "Sampling failed"


# ============================================================================
# test_user_elicitation 测试
# ============================================================================


@pytest.mark.asyncio
async def test_user_elicitation_tool_accepted():
    """测试用户接受输入请求的情况."""
    from skill_creator_mcp.utils import testing as testing_module

    mock_ctx = MagicMock()
    mock_result = Mock()
    mock_result.accepted = True
    mock_result.data = "user input data"
    mock_ctx.elicit = AsyncMock(return_value=mock_result)

    result = await testing_module.test_user_elicitation(mock_ctx, "Please provide input")

    assert result["success"] is True
    assert result["action"] == "accept"
    assert result["user_input"] == "user input data"


@pytest.mark.asyncio
async def test_user_elicitation_tool_cancelled():
    """测试用户取消输入请求的情况."""
    from skill_creator_mcp.utils import testing as testing_module

    mock_ctx = MagicMock()
    mock_result = Mock()
    mock_result.accepted = False
    mock_ctx.elicit = AsyncMock(return_value=mock_result)

    result = await testing_module.test_user_elicitation(mock_ctx, "Please provide input")

    assert result["success"] is True
    assert result["action"] == "cancel"


@pytest.mark.asyncio
async def test_user_elicitation_tool_default_prompt():
    """测试使用默认提示词的情况."""
    from skill_creator_mcp.utils import testing as testing_module

    mock_ctx = MagicMock()
    mock_result = Mock()
    mock_result.accepted = True
    mock_result.data = "test"
    mock_ctx.elicit = AsyncMock(return_value=mock_result)

    result = await testing_module.test_user_elicitation(mock_ctx)

    assert result["success"] is True
    assert result["action"] == "accept"


# ============================================================================
# test_conversation_loop 测试
# ============================================================================


@pytest.mark.asyncio
async def test_conversation_loop_tool_new_conversation():
    """测试新对话循环的情况."""
    from skill_creator_mcp.utils import testing as testing_module

    mock_ctx = MagicMock()
    mock_result = Mock()
    mock_result.text = "AI response"
    mock_result.history = []
    mock_ctx.get_state = AsyncMock(return_value=None)
    mock_ctx.sample = AsyncMock(return_value=mock_result)
    mock_ctx.set_state = AsyncMock()

    result = await testing_module.test_conversation_loop(mock_ctx, "Hello")

    assert result["success"] is True
    assert result["has_llm_response"] is True
    assert result["llm_response"] == "AI response"
    assert result["conversation_length"] == 2
    assert result["history_saved"] is True


@pytest.mark.asyncio
async def test_conversation_loop_tool_existing_history():
    """测试有历史记录的对话循环."""
    from skill_creator_mcp.utils import testing as testing_module

    mock_ctx = MagicMock()
    mock_result = Mock()
    mock_result.text = "AI response 2"
    existing_history = [{"role": "user", "content": "Previous"}]
    mock_ctx.get_state = AsyncMock(return_value=existing_history)
    mock_ctx.sample = AsyncMock(return_value=mock_result)
    mock_ctx.set_state = AsyncMock()

    result = await testing_module.test_conversation_loop(mock_ctx, "New input")

    assert result["success"] is True
    assert result["conversation_length"] == 3


# ============================================================================
# test_requirement_completeness 测试
# ============================================================================


@pytest.mark.asyncio
async def test_requirement_completeness_tool_success():
    """测试需求完整性检查成功返回 JSON 的情况."""
    from skill_creator_mcp.utils import testing as testing_module

    mock_ctx = MagicMock()
    mock_result = Mock()
    mock_result.text = '{"is_complete": true, "suggestions": []}'
    mock_ctx.sample = AsyncMock(return_value=mock_result)

    result = await testing_module.test_requirement_completeness(mock_ctx, "Create a skill")

    assert result["success"] is True
    assert result["llm_analysis"]["is_complete"] is True
    assert result["has_missing_info"] is False


@pytest.mark.asyncio
async def test_requirement_completeness_tool_incomplete():
    """测试需求不完整的情况."""
    from skill_creator_mcp.utils import testing as testing_module

    mock_ctx = MagicMock()
    mock_result = Mock()
    mock_result.text = '{"is_complete": false, "missing_info": ["skill_name"], "suggestions": ["Add name"]}'
    mock_ctx.sample = AsyncMock(return_value=mock_result)

    result = await testing_module.test_requirement_completeness(mock_ctx, "Create a skill")

    assert result["success"] is True
    assert result["llm_analysis"]["is_complete"] is False
    assert result["has_missing_info"] is True


@pytest.mark.asyncio
async def test_requirement_completeness_tool_json_parse_failed():
    """测试 JSON 解析失败的情况."""
    from skill_creator_mcp.utils import testing as testing_module

    mock_ctx = MagicMock()
    mock_result = Mock()
    mock_result.text = "This is not JSON"
    mock_ctx.sample = AsyncMock(return_value=mock_result)

    result = await testing_module.test_requirement_completeness(mock_ctx, "Create a skill")

    assert result["success"] is True
    assert result["json_parse_failed"] is True
    assert result["llm_response"] == "This is not JSON"
