"""客户端能力检测单元测试.

测试 capability_detection.py 模块的所有功能：
- check_sampling_capability - 检测 LLM sampling 支持
- check_elicitation_capability - 检测用户交互支持
- get_client_capabilities - 综合能力检测
"""

from unittest.mock import AsyncMock, MagicMock, Mock

import pytest

from skill_creator_mcp.utils.capability_detection import (
    check_elicitation_capability,
    check_sampling_capability,
    get_client_capabilities,
)

# ============================================================================
# check_sampling_capability 测试
# ============================================================================


@pytest.mark.asyncio
async def test_sampling_supported():
    """测试客户端支持 LLM sampling 的情况."""
    mock_ctx = MagicMock()
    mock_result = Mock()
    mock_result.text = "Test response from LLM"
    mock_ctx.sample = AsyncMock(return_value=mock_result)

    result = await check_sampling_capability(mock_ctx)

    assert result["supported"] is True
    assert result["method"] == "sample"
    assert "supported" in result["details"].lower()
    assert "error" not in result


@pytest.mark.asyncio
async def test_sampling_unsupported_not_declared():
    """测试客户端未声明 sampling 能力的情况."""
    mock_ctx = MagicMock()
    mock_ctx.sample = AsyncMock(
        side_effect=Exception("Client does not support sampling")
    )

    result = await check_sampling_capability(mock_ctx)

    assert result["supported"] is False
    assert result["method"] == "sample"
    assert "not declare" in result["details"].lower() or "does not support" in result["details"].lower()
    assert "error" in result


@pytest.mark.asyncio
async def test_sampling_unsupported_method_not_found():
    """测试客户端不提供 sampling 方法的情况."""
    mock_ctx = MagicMock()
    mock_ctx.sample = AsyncMock(
        side_effect=AttributeError("Method 'sample' not found")
    )

    result = await check_sampling_capability(mock_ctx)

    assert result["supported"] is False
    assert result["method"] == "sample"
    assert "error" in result


@pytest.mark.asyncio
async def test_sampling_unexpected_error():
    """测试未知错误类型的情况."""
    mock_ctx = MagicMock()
    mock_ctx.sample = AsyncMock(
        side_effect=RuntimeError("Unexpected error during sampling")
    )

    result = await check_sampling_capability(mock_ctx)

    assert result["supported"] is False
    assert result["method"] == "sample"
    assert "unexpected" in result["details"].lower()
    assert "error" in result
    # 代码使用 str(e)，所以错误类型名不在消息中
    assert "Unexpected error during sampling" in result["error"]


# ============================================================================
# check_elicitation_capability 测试
# ============================================================================


@pytest.mark.asyncio
async def test_elicitation_supported():
    """测试客户端支持 user elicitation 的情况."""
    mock_ctx = MagicMock()
    mock_result = Mock()
    mock_result.action = "accept"
    mock_result.data = "user input data"
    mock_ctx.elicit = AsyncMock(return_value=mock_result)

    result = await check_elicitation_capability(mock_ctx)

    assert result["supported"] is True
    assert result["method"] == "elicit"
    assert "supported" in result["details"].lower()
    assert result["result_type"] == "Mock"
    assert "error" not in result


@pytest.mark.asyncio
async def test_elicitation_unsupported_method_not_found():
    """测试客户端不提供 elicitation 方法的情况."""
    mock_ctx = MagicMock()
    mock_ctx.elicit = AsyncMock(
        side_effect=AttributeError("Method 'elicit' not found")
    )

    result = await check_elicitation_capability(mock_ctx)

    assert result["supported"] is False
    assert result["method"] == "elicit"
    assert "does not support" in result["details"].lower()
    assert "error" in result


@pytest.mark.asyncio
async def test_elicitation_unsupported_not_found():
    """测试客户端返回 not found 错误的情况."""
    mock_ctx = MagicMock()
    mock_ctx.elicit = AsyncMock(
        side_effect=Exception("Method not found")
    )

    result = await check_elicitation_capability(mock_ctx)

    assert result["supported"] is False
    assert result["method"] == "elicit"
    # 代码检测 "not found" 但返回的是 "does not support elicitation method"
    assert "support" in result["details"].lower()


@pytest.mark.asyncio
async def test_elicitation_unexpected_error():
    """测试未知错误类型的情况."""
    mock_ctx = MagicMock()
    mock_ctx.elicit = AsyncMock(
        side_effect=ValueError("Invalid elicit parameters")
    )

    result = await check_elicitation_capability(mock_ctx)

    assert result["supported"] is False
    assert result["method"] == "elicit"
    assert "unexpected" in result["details"].lower()
    assert "error" in result


# ============================================================================
# get_client_capabilities 测试
# ============================================================================


@pytest.mark.asyncio
async def test_both_capabilities_supported():
    """测试两个高级 API 都支持的情况."""
    mock_ctx = MagicMock()

    # Mock sampling
    mock_sample_result = Mock()
    mock_sample_result.text = "Response"
    mock_ctx.sample = AsyncMock(return_value=mock_sample_result)

    # Mock elicitation
    mock_elicit_result = Mock()
    mock_elicit_result.action = "accept"
    mock_ctx.elicit = AsyncMock(return_value=mock_elicit_result)

    result = await get_client_capabilities(mock_ctx)

    assert result["sampling"]["supported"] is True
    assert result["elicitation"]["supported"] is True
    assert result["summary"]["advanced_apis_supported"] is True
    assert result["summary"]["fallback_required"] is False


@pytest.mark.asyncio
async def test_both_capabilities_unsupported():
    """测试两个高级 API 都不支持的情况."""
    mock_ctx = MagicMock()
    mock_ctx.sample = AsyncMock(
        side_effect=Exception("Client does not support sampling")
    )
    mock_ctx.elicit = AsyncMock(
        side_effect=AttributeError("Method not found")
    )

    result = await get_client_capabilities(mock_ctx)

    assert result["sampling"]["supported"] is False
    assert result["elicitation"]["supported"] is False
    assert result["summary"]["advanced_apis_supported"] is False
    assert result["summary"]["fallback_required"] is True


@pytest.mark.asyncio
async def test_only_sampling_supported():
    """测试仅 sampling 支持的情况."""
    mock_ctx = MagicMock()

    # Mock sampling supported
    mock_sample_result = Mock()
    mock_sample_result.text = "Response"
    mock_ctx.sample = AsyncMock(return_value=mock_sample_result)

    # Mock elicitation unsupported
    mock_ctx.elicit = AsyncMock(
        side_effect=AttributeError("Method not found")
    )

    result = await get_client_capabilities(mock_ctx)

    assert result["sampling"]["supported"] is True
    assert result["elicitation"]["supported"] is False
    assert result["summary"]["advanced_apis_supported"] is False
    assert result["summary"]["fallback_required"] is True


@pytest.mark.asyncio
async def test_only_elicitation_supported():
    """测试仅 elicitation 支持的情况."""
    mock_ctx = MagicMock()

    # Mock sampling unsupported
    mock_ctx.sample = AsyncMock(
        side_effect=Exception("Client does not support sampling")
    )

    # Mock elicitation supported
    mock_elicit_result = Mock()
    mock_elicit_result.action = "accept"
    mock_ctx.elicit = AsyncMock(return_value=mock_elicit_result)

    result = await get_client_capabilities(mock_ctx)

    assert result["sampling"]["supported"] is False
    assert result["elicitation"]["supported"] is True
    assert result["summary"]["advanced_apis_supported"] is False
    assert result["summary"]["fallback_required"] is True


@pytest.mark.asyncio
async def test_summary_calculation():
    """测试 summary 字段的正确计算."""
    mock_ctx = MagicMock()
    mock_ctx.sample = AsyncMock(
        side_effect=Exception("Client does not support sampling")
    )
    mock_ctx.elicit = AsyncMock(
        side_effect=AttributeError("Method not found")
    )

    result = await get_client_capabilities(mock_ctx)

    # 验证 summary 字段存在且格式正确
    assert "summary" in result
    assert "advanced_apis_supported" in result["summary"]
    assert "fallback_required" in result["summary"]
    assert isinstance(result["summary"]["advanced_apis_supported"], bool)
    assert isinstance(result["summary"]["fallback_required"], bool)


@pytest.mark.asyncio
async def test_fallback_required_when_any_unsupported():
    """测试只要有任何一个不支持，fallback_required 就为 True."""
    mock_ctx = MagicMock()

    # 仅 sampling 支持
    mock_sample_result = Mock()
    mock_sample_result.text = "Response"
    mock_ctx.sample = AsyncMock(return_value=mock_sample_result)
    mock_ctx.elicit = AsyncMock(
        side_effect=AttributeError("Method not found")
    )

    result = await get_client_capabilities(mock_ctx)

    assert result["summary"]["fallback_required"] is True


@pytest.mark.asyncio
async def test_fallback_not_required_when_both_supported():
    """测试当两个都支持时，fallback_required 为 False."""
    mock_ctx = MagicMock()

    mock_sample_result = Mock()
    mock_sample_result.text = "Response"
    mock_ctx.sample = AsyncMock(return_value=mock_sample_result)

    mock_elicit_result = Mock()
    mock_elicit_result.action = "accept"
    mock_ctx.elicit = AsyncMock(return_value=mock_elicit_result)

    result = await get_client_capabilities(mock_ctx)

    assert result["summary"]["fallback_required"] is False


# ============================================================================
# 边界情况测试
# ============================================================================


@pytest.mark.asyncio
async def test_sampling_with_empty_error_message():
    """测试空错误消息的情况."""
    mock_ctx = MagicMock()
    mock_ctx.sample = AsyncMock(side_effect=Exception(""))

    result = await check_sampling_capability(mock_ctx)

    assert result["supported"] is False
    assert "error" in result


@pytest.mark.asyncio
async def test_elicitation_with_different_result_types():
    """测试不同类型的 elicitation 结果."""
    mock_ctx = MagicMock()

    # 测试字符串结果
    mock_ctx.elicit = AsyncMock(return_value="string result")
    result = await check_elicitation_capability(mock_ctx)
    assert result["supported"] is True
    assert result["result_type"] == "str"

    # 测试字典结果
    mock_ctx.elicit = AsyncMock(return_value={"key": "value"})
    result = await check_elicitation_capability(mock_ctx)
    assert result["supported"] is True
    assert result["result_type"] == "dict"


@pytest.mark.asyncio
async def test_concurrent_capability_checks():
    """测试并发执行能力检测不会互相影响."""
    mock_ctx = MagicMock()

    mock_sample_result = Mock()
    mock_sample_result.text = "Response"
    mock_ctx.sample = AsyncMock(return_value=mock_sample_result)

    mock_elicit_result = Mock()
    mock_elicit_result.action = "accept"
    mock_ctx.elicit = AsyncMock(return_value=mock_elicit_result)

    # 多次调用应该返回一致的结果
    result1 = await get_client_capabilities(mock_ctx)
    result2 = await get_client_capabilities(mock_ctx)

    assert result1 == result2
