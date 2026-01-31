"""测试验证模块.

测试 validation.py 的功能：
- validate_requirement_answer - 验证用户答案格式
"""



# ============================================================================
# 基本验证测试
# ============================================================================


def test_validate_with_valid_answer():
    """测试验证有效答案."""
    from skill_creator_mcp.utils.requirement_collection.validation import (
        validate_requirement_answer,
    )

    validation_rule = {
        "field": "skill_name",
        "required": True,
        "min_length": 3,
        "max_length": 50,
    }

    result = validate_requirement_answer("my-skill", validation_rule)

    assert result["valid"] is True


def test_validate_with_empty_required_answer():
    """测试验证空的必填答案."""
    from skill_creator_mcp.utils.requirement_collection.validation import (
        validate_requirement_answer,
    )

    validation_rule = {
        "field": "skill_name",
        "required": True,
    }

    result = validate_requirement_answer("   ", validation_rule)

    assert result["valid"] is False
    assert "必填项" in result["error"]


def test_validate_with_empty_optional_answer():
    """测试验证空的非必填答案."""
    from skill_creator_mcp.utils.requirement_collection.validation import (
        validate_requirement_answer,
    )

    validation_rule = {
        "field": "description",
        "required": False,
    }

    result = validate_requirement_answer("   ", validation_rule)

    assert result["valid"] is True


def test_validate_with_empty_string_optional():
    """测试验证空字符串的非必填答案."""
    from skill_creator_mcp.utils.requirement_collection.validation import (
        validate_requirement_answer,
    )

    validation_rule = {
        "field": "description",
        "required": False,
    }

    result = validate_requirement_answer("", validation_rule)

    assert result["valid"] is True


# ============================================================================
# 长度验证测试
# ============================================================================


def test_validate_min_length_too_short():
    """测试验证答案太短."""
    from skill_creator_mcp.utils.requirement_collection.validation import (
        validate_requirement_answer,
    )

    validation_rule = {
        "field": "skill_name",
        "required": True,
        "min_length": 5,
        "help_text": "技能名称至少需要5个字符",
    }

    result = validate_requirement_answer("abc", validation_rule)

    assert result["valid"] is False
    assert "5个字符" in result["error"]


def test_validate_min_length_exactly():
    """测试验证答案恰好满足最小长度."""
    from skill_creator_mcp.utils.requirement_collection.validation import (
        validate_requirement_answer,
    )

    validation_rule = {
        "field": "skill_name",
        "required": True,
        "min_length": 5,
    }

    result = validate_requirement_answer("abcde", validation_rule)

    assert result["valid"] is True


def test_validate_max_length_too_long():
    """测试验证答案太长."""
    from skill_creator_mcp.utils.requirement_collection.validation import (
        validate_requirement_answer,
    )

    validation_rule = {
        "field": "skill_name",
        "required": True,
        "max_length": 10,
        "help_text": "技能名称最多10个字符",
    }

    result = validate_requirement_answer("this-is-a-very-long-skill-name", validation_rule)

    assert result["valid"] is False
    assert "10个字符" in result["error"]


def test_validate_max_length_exactly():
    """测试验证答案恰好满足最大长度."""
    from skill_creator_mcp.utils.requirement_collection.validation import (
        validate_requirement_answer,
    )

    validation_rule = {
        "field": "skill_name",
        "required": True,
        "max_length": 10,
    }

    result = validate_requirement_answer("short-name", validation_rule)

    assert result["valid"] is True


def test_validate_with_min_and_max_length():
    """测试验证同时满足最小和最大长度."""
    from skill_creator_mcp.utils.requirement_collection.validation import (
        validate_requirement_answer,
    )

    validation_rule = {
        "field": "skill_name",
        "required": True,
        "min_length": 3,
        "max_length": 20,
    }

    # 太短
    result = validate_requirement_answer("ab", validation_rule)
    assert result["valid"] is False

    # 太长
    result = validate_requirement_answer("a" * 25, validation_rule)
    assert result["valid"] is False

    # 刚好
    result = validate_requirement_answer("perfect", validation_rule)
    assert result["valid"] is True


# ============================================================================
# 选项验证测试
# ============================================================================


def test_validate_with_valid_option():
    """测试验证有效选项."""
    from skill_creator_mcp.utils.requirement_collection.validation import (
        validate_requirement_answer,
    )

    validation_rule = {
        "field": "template_type",
        "required": True,
        "options": ["minimal", "tool-based", "workflow-based", "analyzer-based"],
    }

    result = validate_requirement_answer("minimal", validation_rule)

    assert result["valid"] is True


def test_validate_with_invalid_option():
    """测试验证无效选项."""
    from skill_creator_mcp.utils.requirement_collection.validation import (
        validate_requirement_answer,
    )

    validation_rule = {
        "field": "template_type",
        "required": True,
        "options": ["minimal", "tool-based", "workflow-based"],
    }

    result = validate_requirement_answer("invalid-option", validation_rule)

    assert result["valid"] is False
    assert "无效的选项" in result["error"]


def test_validate_with_option_case_insensitive():
    """测试验证选项不区分大小写."""
    from skill_creator_mcp.utils.requirement_collection.validation import (
        validate_requirement_answer,
    )

    validation_rule = {
        "field": "template_type",
        "required": True,
        "options": ["minimal", "tool-based", "workflow-based"],
    }

    # 大小写混合
    result = validate_requirement_answer("Minimal", validation_rule)
    assert result["valid"] is True

    # 全大写
    result = validate_requirement_answer("MINIMAL", validation_rule)
    assert result["valid"] is True

    # 带空格
    result = validate_requirement_answer("  minimal  ", validation_rule)
    assert result["valid"] is True


def test_validate_with_empty_optional_answer_with_options():
    """测试验证带选项的空非必填答案."""
    from skill_creator_mcp.utils.requirement_collection.validation import (
        validate_requirement_answer,
    )

    validation_rule = {
        "field": "template_type",
        "required": False,
        "options": ["minimal", "tool-based"],
    }

    result = validate_requirement_answer("", validation_rule)

    assert result["valid"] is True


# ============================================================================
# 正则表达式验证测试
# ============================================================================


def test_validate_with_pattern_valid():
    """测试验证符合正则表达式."""
    from skill_creator_mcp.utils.requirement_collection.validation import (
        validate_requirement_answer,
    )

    validation_rule = {
        "field": "skill_name",
        "required": True,
        "pattern": r"^[a-z0-9-]+$",
    }

    result = validate_requirement_answer("my-skill-123", validation_rule)

    assert result["valid"] is True


def test_validate_with_pattern_invalid():
    """测试验证不符合正则表达式."""
    from skill_creator_mcp.utils.requirement_collection.validation import (
        validate_requirement_answer,
    )

    validation_rule = {
        "field": "skill_name",
        "required": True,
        "pattern": r"^[a-z0-9-]+$",
    }

    result = validate_requirement_answer("My_Skill", validation_rule)

    assert result["valid"] is False
    assert "格式不正确" in result["error"]


def test_validate_with_pattern_email():
    """测试验证邮箱格式."""
    from skill_creator_mcp.utils.requirement_collection.validation import (
        validate_requirement_answer,
    )

    validation_rule = {
        "field": "email",
        "required": True,
        "pattern": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
    }

    # 有效邮箱
    result = validate_requirement_answer("user@example.com", validation_rule)
    assert result["valid"] is True

    # 无效邮箱
    result = validate_requirement_answer("not-an-email", validation_rule)
    assert result["valid"] is False


# ============================================================================
# 对象形式的验证规则测试
# ============================================================================


def test_validate_with_validation_rule_object():
    """测试使用 ValidationRule 对象（而非字典）."""
    from skill_creator_mcp.models.skill_config import ValidationRule
    from skill_creator_mcp.utils.requirement_collection.validation import (
        validate_requirement_answer,
    )

    rule = ValidationRule(
        field="skill_name",
        required=True,
        min_length=3,
        max_length=20,
        help_text="技能名称长度要求",
    )

    result = validate_requirement_answer("my-skill", rule)

    assert result["valid"] is True


def test_validate_with_object_fails_min_length():
    """测试使用 ValidationRule 对象验证最小长度失败."""
    from skill_creator_mcp.models.skill_config import ValidationRule
    from skill_creator_mcp.utils.requirement_collection.validation import (
        validate_requirement_answer,
    )

    rule = ValidationRule(
        field="skill_name",
        required=True,
        min_length=5,
        help_text="技能名称至少需要5个字符",
    )

    result = validate_requirement_answer("ab", rule)

    assert result["valid"] is False


# ============================================================================
# 组合验证测试
# ============================================================================


def test_validate_with_multiple_rules():
    """测试多个验证规则的组合."""
    from skill_creator_mcp.utils.requirement_collection.validation import (
        validate_requirement_answer,
    )

    validation_rule = {
        "field": "skill_name",
        "required": True,
        "min_length": 3,
        "max_length": 20,
        "pattern": r"^[a-z0-9-]+$",
    }

    # 满足所有条件
    result = validate_requirement_answer("my-skill", validation_rule)
    assert result["valid"] is True

    # 不满足长度
    result = validate_requirement_answer("ab", validation_rule)
    assert result["valid"] is False

    # 不满足模式
    result = validate_requirement_answer("My_Skill", validation_rule)
    assert result["valid"] is False

    # 不满足最大长度
    result = validate_requirement_answer("a" * 25, validation_rule)
    assert result["valid"] is False


def test_validate_whitespace_only_answer_required():
    """测试纯空格的必填答案."""
    from skill_creator_mcp.utils.requirement_collection.validation import (
        validate_requirement_answer,
    )

    validation_rule = {
        "field": "skill_name",
        "required": True,
    }

    result = validate_requirement_answer("     ", validation_rule)

    assert result["valid"] is False
