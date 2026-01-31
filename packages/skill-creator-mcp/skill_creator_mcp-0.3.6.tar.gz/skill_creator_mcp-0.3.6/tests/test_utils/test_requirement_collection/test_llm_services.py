"""测试 LLM 服务模块.

测试 llm_services.py 的功能：
- check_requirement_completeness - 使用 LLM 检查需求完整性
"""

from unittest.mock import AsyncMock, MagicMock, Mock

import pytest

# ============================================================================
# check_requirement_completeness 成功情况测试
# ============================================================================


@pytest.mark.asyncio
async def test_check_requirement_completeness_complete():
    """测试检查完整的需求."""
    from skill_creator_mcp.utils.requirement_collection.llm_services import (
        check_requirement_completeness,
    )

    mock_ctx = MagicMock()
    mock_result = Mock()
    mock_result.text = """{
        "complete": true,
        "missing_items": [],
        "suggestions": []
    }"""
    mock_ctx.sample = AsyncMock(return_value=mock_result)

    answers = {
        "skill_name": "my-skill",
        "skill_function": "perform tasks",
        "use_cases": ["case1", "case2"],
        "template_type": "minimal",
    }

    result = await check_requirement_completeness(mock_ctx, answers)

    assert result["complete"] is True
    assert result["missing_items"] == []
    assert result["suggestions"] == []


@pytest.mark.asyncio
async def test_check_requirement_completeness_incomplete():
    """测试检查不完整的需求."""
    from skill_creator_mcp.utils.requirement_collection.llm_services import (
        check_requirement_completeness,
    )

    mock_ctx = MagicMock()
    mock_result = Mock()
    mock_result.text = """{
        "complete": false,
        "missing_items": ["skill_name", "use_cases"],
        "suggestions": ["请补充技能名称和使用场景"]
    }"""
    mock_ctx.sample = AsyncMock(return_value=mock_result)

    answers = {
        "skill_function": "perform tasks",
    }

    result = await check_requirement_completeness(mock_ctx, answers)

    assert result["complete"] is False
    assert "skill_name" in result["missing_items"]
    assert "use_cases" in result["missing_items"]
    assert len(result["suggestions"]) > 0


@pytest.mark.asyncio
async def test_check_requirement_completeness_with_suggestions():
    """测试检查需求并获取建议."""
    from skill_creator_mcp.utils.requirement_collection.llm_services import (
        check_requirement_completeness,
    )

    mock_ctx = MagicMock()
    mock_result = Mock()
    mock_result.text = """{
        "complete": false,
        "missing_items": ["use_cases"],
        "suggestions": ["建议描述具体的使用场景", "可以包括输入输出示例"]
    }"""
    mock_ctx.sample = AsyncMock(return_value=mock_result)

    answers = {
        "skill_name": "my-skill",
        "skill_function": "perform tasks",
    }

    result = await check_requirement_completeness(mock_ctx, answers)

    assert result["complete"] is False
    assert len(result["suggestions"]) == 2


# ============================================================================
# check_requirement_completeness LLM 解析失败测试
# ============================================================================


@pytest.mark.asyncio
async def test_check_requirement_completeness_llm_json_parse_error():
    """测试 LLM 返回无效 JSON 时的降级处理."""
    from skill_creator_mcp.utils.requirement_collection.llm_services import (
        check_requirement_completeness,
    )

    mock_ctx = MagicMock()
    mock_result = Mock()
    mock_result.text = "This is not valid JSON"
    mock_ctx.sample = AsyncMock(return_value=mock_result)

    answers = {
        "skill_name": "my-skill",
        "skill_function": "perform tasks",
        "use_cases": ["case1"],
        "template_type": "minimal",
    }

    result = await check_requirement_completeness(mock_ctx, answers)

    # 应该降级到简单的完整性检查
    assert result["complete"] is True
    assert result["missing_items"] == []


@pytest.mark.asyncio
async def test_check_requirement_completeness_llm_no_json_found():
    """测试 LLM 返回文本中找不到 JSON 时的降级处理."""
    from skill_creator_mcp.utils.requirement_collection.llm_services import (
        check_requirement_completeness,
    )

    mock_ctx = MagicMock()
    mock_result = Mock()
    mock_result.text = "Based on my analysis, you need more information."
    mock_ctx.sample = AsyncMock(return_value=mock_result)

    answers = {
        "skill_name": "my-skill",
    }

    result = await check_requirement_completeness(mock_ctx, answers)

    # 应该降级到简单的完整性检查
    assert result["complete"] is False
    assert "missing_items" in result


@pytest.mark.asyncio
async def test_check_requirement_completeness_llm_partial_json():
    """测试 LLM 返回包含 JSON 的文本."""
    from skill_creator_mcp.utils.requirement_collection.llm_services import (
        check_requirement_completeness,
    )

    mock_ctx = MagicMock()
    mock_result = Mock()
    mock_result.text = """分析结果如下：

{
    "complete": false,
    "missing_items": ["template_type"],
    "suggestions": ["请选择模板类型"]
}

以上是分析结果。"""
    mock_ctx.sample = AsyncMock(return_value=mock_result)

    answers = {
        "skill_name": "my-skill",
        "skill_function": "perform tasks",
    }

    result = await check_requirement_completeness(mock_ctx, answers)

    # 应该能提取 JSON
    assert result["complete"] is False
    assert "template_type" in result["missing_items"]


# ============================================================================
# check_requirement_completeness 异常处理测试
# ============================================================================


@pytest.mark.asyncio
async def test_check_requirement_completeness_exception_handling():
    """测试 LLM 调用异常时的处理."""
    from skill_creator_mcp.utils.requirement_collection.llm_services import (
        check_requirement_completeness,
    )

    mock_ctx = MagicMock()
    mock_ctx.sample = AsyncMock(side_effect=Exception("LLM service unavailable"))

    answers = {
        "skill_name": "my-skill",
    }

    result = await check_requirement_completeness(mock_ctx, answers)

    # 应该降级到简单的完整性检查
    assert result["complete"] is False
    assert "missing_items" in result


@pytest.mark.asyncio
async def test_check_requirement_completeness_empty_answers():
    """测试空答案列表的完整性检查."""
    from skill_creator_mcp.utils.requirement_collection.llm_services import (
        check_requirement_completeness,
    )

    mock_ctx = MagicMock()
    mock_result = Mock()
    mock_result.text = """{
        "complete": false,
        "missing_items": ["skill_name", "skill_function", "use_cases", "template_type"],
        "suggestions": ["请提供所有必要信息"]
    }"""
    mock_ctx.sample = AsyncMock(return_value=mock_result)

    answers = {}

    result = await check_requirement_completeness(mock_ctx, answers)

    assert result["complete"] is False
    assert len(result["missing_items"]) == 4


# ============================================================================
# check_requirement_completeness 降级行为测试
# ============================================================================


@pytest.mark.asyncio
async def test_check_requirement_completeness_fallback_complete():
    """测试降级行为 - 完整的答案."""
    from skill_creator_mcp.utils.requirement_collection.llm_services import (
        check_requirement_completeness,
    )

    mock_ctx = MagicMock()
    mock_ctx.sample = AsyncMock(side_effect=Exception("LLM error"))

    answers = {
        "skill_name": "my-skill",
        "skill_function": "perform tasks",
        "use_cases": ["case1"],
        "template_type": "minimal",
    }

    result = await check_requirement_completeness(mock_ctx, answers)

    # 降级检查应该认为完整
    assert result["complete"] is True
    assert result["missing_items"] == []
    assert result["suggestions"] == []


@pytest.mark.asyncio
async def test_check_requirement_completeness_fallback_incomplete():
    """测试降级行为 - 不完整的答案."""
    from skill_creator_mcp.utils.requirement_collection.llm_services import (
        check_requirement_completeness,
    )

    mock_ctx = MagicMock()
    mock_ctx.sample = AsyncMock(side_effect=Exception("LLM error"))

    answers = {
        "skill_name": "my-skill",
        # 缺少其他必需字段
    }

    result = await check_requirement_completeness(mock_ctx, answers)

    # 降级检查应该发现缺失字段
    assert result["complete"] is False
    assert "skill_function" in result["missing_items"]
    assert len(result["suggestions"]) > 0


# ============================================================================
# check_requirement_completeness LLM 调用参数测试
# ============================================================================


@pytest.mark.asyncio
async def test_check_requirement_completeness_llm_parameters():
    """测试 LLM 调用使用的参数."""
    from skill_creator_mcp.utils.requirement_collection.llm_services import (
        check_requirement_completeness,
    )

    mock_ctx = MagicMock()
    mock_result = Mock()
    mock_result.text = '{"complete": true, "missing_items": [], "suggestions": []}'
    mock_ctx.sample = AsyncMock(return_value=mock_result)

    answers = {"skill_name": "test"}

    await check_requirement_completeness(mock_ctx, answers)

    # 验证 LLM 调用参数
    mock_ctx.sample.assert_called_once()
    call_kwargs = mock_ctx.sample.call_args.kwargs
    assert "messages" in call_kwargs
    assert "system_prompt" in call_kwargs
    assert call_kwargs["temperature"] == 0.3


@pytest.mark.asyncio
async def test_check_requirement_completeness_prompt_contains_answers():
    """测试提示词包含答案信息."""
    from skill_creator_mcp.utils.requirement_collection.llm_services import (
        check_requirement_completeness,
    )

    mock_ctx = MagicMock()
    mock_result = Mock()
    mock_result.text = '{"complete": true, "missing_items": [], "suggestions": []}'
    mock_ctx.sample = AsyncMock(return_value=mock_result)

    answers = {
        "skill_name": "my-skill",
        "skill_function": "do something",
    }

    await check_requirement_completeness(mock_ctx, answers)

    # 验证提示词包含答案
    call_kwargs = mock_ctx.sample.call_args.kwargs
    prompt = call_kwargs["messages"]
    assert "my-skill" in prompt
    assert "do something" in prompt
