"""测试需求收集验证工具.

测试 requirement_validation_tools.py 模块的所有功能：
- validate_answer_format - 验证答案格式
- check_requirement_completeness - 检查完整性
"""

from unittest.mock import AsyncMock, MagicMock, Mock

import pytest

# ============================================================================
# validate_answer_format 测试
# ============================================================================


@pytest.mark.asyncio
async def test_validate_answer_format_valid_text():
    """测试验证有效文本答案."""
    from skill_creator_mcp.tools.requirement_validation_tools import validate_answer_format

    mock_ctx = MagicMock()
    validation = {
        "field": "skill_name",
        "required": True,
        "min_length": 3,
        "max_length": 50,
    }

    result = await validate_answer_format(mock_ctx, "test-skill", validation)

    assert result["valid"] is True
    assert result["error"] is None
    assert result["formatted_answer"] == "test-skill"


@pytest.mark.asyncio
async def test_validate_answer_format_valid_with_whitespace():
    """测试验证带空白字符的答案（自动去除）."""
    from skill_creator_mcp.tools.requirement_validation_tools import validate_answer_format

    mock_ctx = MagicMock()
    validation = {"field": "skill_name", "required": True}

    result = await validate_answer_format(mock_ctx, "  test-skill  ", validation)

    assert result["valid"] is True
    assert result["formatted_answer"] == "test-skill"


@pytest.mark.asyncio
async def test_validate_answer_format_required_empty():
    """测试必填字段为空."""
    from skill_creator_mcp.tools.requirement_validation_tools import validate_answer_format

    mock_ctx = MagicMock()
    validation = {"field": "skill_name", "required": True}

    result = await validate_answer_format(mock_ctx, "", validation)

    assert result["valid"] is False
    assert "必填项" in result["error"]
    assert result["formatted_answer"] is None


@pytest.mark.asyncio
async def test_validate_answer_format_required_whitespace_only():
    """测试必填字段只有空白字符."""
    from skill_creator_mcp.tools.requirement_validation_tools import validate_answer_format

    mock_ctx = MagicMock()
    validation = {"field": "skill_name", "required": True}

    result = await validate_answer_format(mock_ctx, "   ", validation)

    assert result["valid"] is False
    assert "必填项" in result["error"]


@pytest.mark.asyncio
async def test_validate_answer_format_optional_empty():
    """测试可选字段为空（应该通过）."""
    from skill_creator_mcp.tools.requirement_validation_tools import validate_answer_format

    mock_ctx = MagicMock()
    validation = {"field": "additional_features", "required": False}

    result = await validate_answer_format(mock_ctx, "", validation)

    assert result["valid"] is True
    assert result["error"] is None
    assert result["formatted_answer"] == ""


@pytest.mark.asyncio
async def test_validate_answer_format_min_length():
    """测试最小长度验证."""
    from skill_creator_mcp.tools.requirement_validation_tools import validate_answer_format

    mock_ctx = MagicMock()
    validation = {"field": "skill_function", "required": True, "min_length": 10}

    # 太短
    result = await validate_answer_format(mock_ctx, "短", validation)
    assert result["valid"] is False
    assert "最少需要" in result["error"]
    assert "10" in result["error"]

    # 正好达到最小长度
    result = await validate_answer_format(mock_ctx, "x" * 10, validation)
    assert result["valid"] is True


@pytest.mark.asyncio
async def test_validate_answer_format_max_length():
    """测试最大长度验证."""
    from skill_creator_mcp.tools.requirement_validation_tools import validate_answer_format

    mock_ctx = MagicMock()
    validation = {"field": "skill_name", "required": True, "max_length": 20}

    # 超过最大长度
    result = await validate_answer_format(mock_ctx, "x" * 25, validation)
    assert result["valid"] is False
    assert "最多允许" in result["error"]
    assert "20" in result["error"]

    # 正好等于最大长度
    result = await validate_answer_format(mock_ctx, "x" * 20, validation)
    assert result["valid"] is True


@pytest.mark.asyncio
async def test_validate_answer_format_options_valid():
    """测试选项验证（有效选项）."""
    from skill_creator_mcp.tools.requirement_validation_tools import validate_answer_format

    mock_ctx = MagicMock()
    validation = {
        "field": "template_type",
        "required": True,
        "options": ["minimal", "tool-based", "workflow-based", "analyzer-based"],
    }

    result = await validate_answer_format(mock_ctx, "tool-based", validation)

    assert result["valid"] is True
    assert result["formatted_answer"] == "tool-based"


@pytest.mark.asyncio
async def test_validate_answer_format_options_invalid():
    """测试选项验证（无效选项）."""
    from skill_creator_mcp.tools.requirement_validation_tools import validate_answer_format

    mock_ctx = MagicMock()
    validation = {
        "field": "template_type",
        "required": True,
        "options": ["minimal", "tool-based", "workflow-based", "analyzer-based"],
    }

    result = await validate_answer_format(mock_ctx, "invalid-option", validation)

    assert result["valid"] is False
    assert "无效的选项" in result["error"]
    assert "minimal" in result["error"]


@pytest.mark.asyncio
async def test_validate_answer_format_options_case_insensitive():
    """测试选项验证（大小写不敏感）."""
    from skill_creator_mcp.tools.requirement_validation_tools import validate_answer_format

    mock_ctx = MagicMock()
    validation = {
        "field": "template_type",
        "required": True,
        "options": ["minimal", "tool-based"],
    }

    # 大写应该也接受
    result = await validate_answer_format(mock_ctx, "MINIMAL", validation)
    assert result["valid"] is True


@pytest.mark.asyncio
async def test_validate_answer_format_pattern_valid():
    """测试正则表达式验证（有效）."""
    from skill_creator_mcp.tools.requirement_validation_tools import validate_answer_format

    mock_ctx = MagicMock()
    validation = {
        "field": "skill_name",
        "required": True,
        "pattern": r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
    }

    result = await validate_answer_format(mock_ctx, "test-skill-123", validation)

    assert result["valid"] is True
    assert result["formatted_answer"] == "test-skill-123"


@pytest.mark.asyncio
async def test_validate_answer_format_pattern_invalid():
    """测试正则表达式验证（无效）."""
    from skill_creator_mcp.tools.requirement_validation_tools import validate_answer_format

    mock_ctx = MagicMock()
    validation = {
        "field": "skill_name",
        "required": True,
        "pattern": r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
    }

    # 包含大写字母
    result = await validate_answer_format(mock_ctx, "Test-Skill", validation)
    assert result["valid"] is False
    assert "格式不正确" in result["error"]

    # 以下划线开头
    result = await validate_answer_format(mock_ctx, "_test-skill", validation)
    assert result["valid"] is False


@pytest.mark.asyncio
async def test_validate_answer_format_custom_help_text():
    """测试自定义帮助文本."""
    from skill_creator_mcp.tools.requirement_validation_tools import validate_answer_format

    mock_ctx = MagicMock()
    validation = {
        "field": "skill_name",
        "required": True,
        "min_length": 5,
        "help_text": "技能名称至少需要5个字符",
    }

    result = await validate_answer_format(mock_ctx, "abc", validation)

    assert result["valid"] is False
    assert "至少需要5个字符" in result["error"]


@pytest.mark.asyncio
async def test_validate_answer_format_returns_bool():
    """测试返回值包含 valid 布尔字段."""
    from skill_creator_mcp.tools.requirement_validation_tools import validate_answer_format

    mock_ctx = MagicMock()
    validation = {"field": "test", "required": False}

    result = await validate_answer_format(mock_ctx, "any answer", validation)

    assert isinstance(result["valid"], bool)
    assert "error" in result
    assert "formatted_answer" in result


# ============================================================================
# check_requirement_completeness 测试
# ============================================================================


@pytest.mark.asyncio
async def test_check_requirement_completeness_complete():
    """测试需求完整性检查（完整）."""
    from skill_creator_mcp.tools.requirement_validation_tools import check_requirement_completeness

    mock_ctx = MagicMock()
    mock_result = Mock()
    mock_result.text = '{"complete": true, "missing_items": [], "suggestions": []}'
    mock_ctx.sample = AsyncMock(return_value=mock_result)

    answers = {
        "skill_name": "test-skill",
        "skill_function": "测试功能",
        "use_cases": "测试场景",
        "template_type": "minimal",
    }

    result = await check_requirement_completeness(mock_ctx, answers)

    assert result["success"] is True
    assert result["complete"] is True
    assert result["missing_items"] == []
    assert result["suggestions"] == []


@pytest.mark.asyncio
async def test_check_requirement_completeness_incomplete():
    """测试需求完整性检查（不完整）."""
    from skill_creator_mcp.tools.requirement_validation_tools import check_requirement_completeness

    mock_ctx = MagicMock()
    mock_result = Mock()
    mock_result.text = '{"complete": false, "missing_items": ["skill_name", "skill_function"], "suggestions": ["请提供技能名称和功能"]}'
    mock_ctx.sample = AsyncMock(return_value=mock_result)

    answers = {"use_cases": "测试场景"}

    result = await check_requirement_completeness(mock_ctx, answers)

    assert result["success"] is True
    assert result["complete"] is False
    assert "skill_name" in result["missing_items"]
    assert "skill_function" in result["missing_items"]
    assert len(result["suggestions"]) > 0


@pytest.mark.asyncio
async def test_check_requirement_completeness_llm_json_parse_failed():
    """测试 LLM 返回 JSON 解析失败的降级处理."""
    from skill_creator_mcp.tools.requirement_validation_tools import check_requirement_completeness

    mock_ctx = MagicMock()
    mock_result = Mock()
    mock_result.text = "This is not valid JSON"
    mock_ctx.sample = AsyncMock(return_value=mock_result)

    answers = {"skill_name": "test"}

    result = await check_requirement_completeness(mock_ctx, answers)

    # 应该降级到简单的完整性检查
    assert result["success"] is True
    assert "complete" in result
    assert "missing_items" in result
    # 缺少 skill_function, use_cases, template_type
    assert len(result["missing_items"]) == 3


@pytest.mark.asyncio
async def test_check_requirement_completeness_llm_failure():
    """测试 LLM 调用完全失败的降级处理."""
    from skill_creator_mcp.tools.requirement_validation_tools import check_requirement_completeness

    mock_ctx = MagicMock()
    mock_ctx.sample = AsyncMock(side_effect=Exception("LLM service down"))

    answers = {}

    result = await check_requirement_completeness(mock_ctx, answers)

    # 应该降级到简单的完整性检查
    assert result["success"] is True
    assert result["complete"] is False
    assert "error" in result
    assert len(result["missing_items"]) == 4  # 所有必需字段都缺失


@pytest.mark.asyncio
async def test_check_requirement_completeness_partial_answers():
    """测试部分答案的情况."""
    from skill_creator_mcp.tools.requirement_validation_tools import check_requirement_completeness

    mock_ctx = MagicMock()
    mock_result = Mock()
    mock_result.text = '{"complete": false, "missing_items": ["use_cases", "template_type"], "suggestions": ["请补充使用场景和模板类型"]}'
    mock_ctx.sample = AsyncMock(return_value=mock_result)

    answers = {"skill_name": "test", "skill_function": "功能"}

    result = await check_requirement_completeness(mock_ctx, answers)

    assert result["success"] is True
    assert result["complete"] is False
    assert "use_cases" in result["missing_items"]
    assert "template_type" in result["missing_items"]


@pytest.mark.asyncio
async def test_check_requirement_completeness_returns_valid_structure():
    """测试返回有效的数据结构."""
    from skill_creator_mcp.tools.requirement_validation_tools import check_requirement_completeness

    mock_ctx = MagicMock()
    mock_result = Mock()
    mock_result.text = '{"complete": true, "missing_items": [], "suggestions": []}'
    mock_ctx.sample = AsyncMock(return_value=mock_result)

    result = await check_requirement_completeness(mock_ctx, {})

    assert result["success"] is True
    assert "complete" in result
    assert "missing_items" in result
    assert "suggestions" in result
    assert isinstance(result["complete"], bool)
    assert isinstance(result["missing_items"], list)
    assert isinstance(result["suggestions"], list)


@pytest.mark.asyncio
async def test_check_requirement_completeness_with_suggestions():
    """测试带改进建议的完整性检查."""
    from skill_creator_mcp.tools.requirement_validation_tools import check_requirement_completeness

    mock_ctx = MagicMock()
    mock_result = Mock()
    mock_result.text = '{"complete": false, "missing_items": ["target_users"], "suggestions": ["建议添加目标用户描述", "可以包括用户画像和使用场景"]}'
    mock_ctx.sample = AsyncMock(return_value=mock_result)

    answers = {"skill_name": "test"}

    result = await check_requirement_completeness(mock_ctx, answers)

    assert result["success"] is True
    assert result["complete"] is False
    assert len(result["suggestions"]) == 2


# ============================================================================
# validation_tools_error_handling 测试
# ============================================================================


@pytest.mark.asyncio
async def test_validation_tools_error_handling():
    """测试验证工具的错误处理."""
    from skill_creator_mcp.tools.requirement_validation_tools import validate_answer_format

    mock_ctx = MagicMock()

    # 测试 None 值处理 - 代码会捕获异常并返回错误
    result = await validate_answer_format(mock_ctx, None, {"field": "test", "required": False})
    # None 值会导致 AttributeError，被 try-except 捕获
    assert result["valid"] is False
    assert "error" in result

    # 测试无效的正则表达式处理
    result = await validate_answer_format(mock_ctx, "test", {"field": "test", "required": False, "pattern": "[invalid"})
    # 无效的正则表达式会导致验证失败
    assert result["valid"] is False
    assert "error" in result


@pytest.mark.asyncio
async def test_check_requirement_completeness_empty_json_extraction():
    """测试 LLM 返回空 JSON 的情况."""
    from skill_creator_mcp.tools.requirement_validation_tools import check_requirement_completeness

    mock_ctx = MagicMock()
    mock_result = Mock()
    mock_result.text = "Prefix text {} suffix text"
    mock_ctx.sample = AsyncMock(return_value=mock_result)

    result = await check_requirement_completeness(mock_ctx, {})

    # 应该能提取到空对象并降级处理
    assert result["success"] is True
    assert "complete" in result


@pytest.mark.asyncio
async def test_check_requirement_completeness_malformed_json():
    """测试 LLM 返回格式错误的 JSON."""
    from skill_creator_mcp.tools.requirement_validation_tools import check_requirement_completeness

    mock_ctx = MagicMock()
    mock_result = Mock()
    mock_result.text = '{complete: true, missing_items: []}'  # 无效的 JSON（键没有引号）
    mock_ctx.sample = AsyncMock(return_value=mock_result)

    result = await check_requirement_completeness(mock_ctx, {})

    # JSON 解析失败，应该降级
    assert result["success"] is True
    assert "complete" in result
