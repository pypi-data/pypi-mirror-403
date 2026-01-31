"""测试数据模型."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from skill_creator_mcp.models.skill_config import (
    InitSkillInput,
    SkillConfig,
    ValidateSkillInput,
    ValidationResult,
)


def test_init_skill_input_valid():
    """测试有效的 InitSkillInput."""
    # 最小有效输入 - output_dir 会被验证器转换为绝对路径
    input_data = {
        "name": "test-skill",
        "template": "minimal",
        "output_dir": ".",
        "with_scripts": False,
        "with_examples": False,
    }
    model = InitSkillInput(**input_data)
    assert model.name == "test-skill"
    assert model.template == "minimal"
    # 验证器会将相对路径转换为绝对路径
    assert Path(model.output_dir).is_absolute()
    assert model.with_scripts is False
    assert model.with_examples is False


def test_init_skill_input_defaults():
    """测试 InitSkillInput 默认值."""
    model = InitSkillInput(name="test")
    assert model.template == "minimal"
    # 验证器会将默认值 "." 转换为绝对路径
    assert Path(model.output_dir).is_absolute()
    assert model.with_scripts is False
    assert model.with_examples is False


def test_init_skill_input_name_validation():
    """测试技能名称验证."""
    # 有效名称
    valid_names = [
        "test",
        "test-skill",
        "test123",
        "test-skill-123",
        "a",
        "test-skill-123-v2",
    ]
    for name in valid_names:
        model = InitSkillInput(name=name)
        assert model.name == name

    # 无效名称
    invalid_names = [
        "Invalid_Name",  # 大写字母
        "-invalid",  # 以连字符开头
        "invalid-",  # 以连字符结尾
        "Test",  # 大写字母开头
        "test--skill",  # 连续连字符
    ]

    # 空字符串单独测试（min_length=1 处理）
    with pytest.raises(ValidationError):
        InitSkillInput(name="")
    for name in invalid_names:
        with pytest.raises(ValidationError):
            InitSkillInput(name=name)


def test_init_skill_input_template_validation():
    """测试模板类型验证."""
    valid_templates = ["minimal", "tool-based", "workflow-based", "analyzer-based"]
    for template in valid_templates:
        model = InitSkillInput(name="test", template=template)
        assert model.template == template


def test_skill_config():
    """测试 SkillConfig."""
    config = SkillConfig(
        name="test-skill",
        template="minimal",
        description="测试技能",
        author="Test Author",
        version="0.1.0",
    )
    assert config.name == "test-skill"
    assert config.template == "minimal"
    assert config.description == "测试技能"
    assert config.author == "Test Author"
    assert config.version == "0.1.0"


def test_skill_config_optional_fields():
    """测试 SkillConfig 可选字段."""
    config = SkillConfig(
        name="test-skill",
        template="minimal",
    )
    assert config.name == "test-skill"
    assert config.description is None
    assert config.author is None
    assert config.version == "0.1.0"
    assert config.allowed_tools is None
    assert config.mcp_servers is None


# ==================== ValidateSkillInput 测试 ====================


def test_validate_skill_input_valid():
    """测试有效的 ValidateSkillInput."""
    input_data = {
        "skill_path": "/path/to/skill",
        "check_structure": True,
        "check_content": True,
    }
    model = ValidateSkillInput(**input_data)
    assert model.skill_path == "/path/to/skill"
    assert model.check_structure is True
    assert model.check_content is True


def test_validate_skill_input_defaults():
    """测试 ValidateSkillInput 默认值."""
    model = ValidateSkillInput(skill_path="/path/to/skill")
    assert model.skill_path == "/path/to/skill"
    assert model.check_structure is True
    assert model.check_content is True


def test_validate_skill_input_path_required():
    """测试 skill_path 必需字段."""
    with pytest.raises(ValidationError):
        ValidateSkillInput()


# ==================== ValidationResult 测试 ====================


def test_validation_result_valid():
    """测试有效的 ValidationResult."""
    result = ValidationResult(
        valid=True,
        skill_path="/path/to/skill",
        skill_name="test-skill",
        template_type="minimal",
    )
    assert result.valid is True
    assert result.skill_path == "/path/to/skill"
    assert result.skill_name == "test-skill"
    assert result.template_type == "minimal"
    assert result.errors == []
    assert result.warnings == []
    assert result.checks == {}


def test_validation_result_with_errors():
    """测试带错误的 ValidationResult."""
    result = ValidationResult(
        valid=False,
        skill_path="/path/to/skill",
        errors=["缺少 SKILL.md", "缺少 references 目录"],
        warnings=["描述为空"],
        checks={"structure": False, "naming": True},
    )
    assert result.valid is False
    assert len(result.errors) == 2
    assert len(result.warnings) == 1
    assert result.checks["structure"] is False
    assert result.checks["naming"] is True


def test_validation_result_optional_fields():
    """测试 ValidationResult 可选字段."""
    result = ValidationResult(
        valid=True,
        skill_path="/path/to/skill",
    )
    assert result.skill_name is None
    assert result.template_type is None
    assert result.errors == []
    assert result.warnings == []
    assert result.checks == {}
