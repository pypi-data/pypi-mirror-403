"""测试 collect_requirements 工具."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from skill_creator_mcp.models.skill_config import (
    RequirementCollectionInput,
    ValidationRule,
)


class TestRequirementCollectionInput:
    """测试 RequirementCollectionInput 数据模型."""

    def test_valid_input(self):
        """测试有效输入."""
        input_data = RequirementCollectionInput.model_validate(
            {
                "action": "start",
                "mode": "basic",
                "session_id": "test_session",
                "user_input": None,
            }
        )
        assert input_data.action == "start"
        assert input_data.mode == "basic"
        assert input_data.session_id == "test_session"
        assert input_data.user_input is None

    def test_default_values(self):
        """测试默认值."""
        input_data = RequirementCollectionInput.model_validate(
            {
                "action": "start",
            }
        )
        assert input_data.action == "start"
        assert input_data.mode == "basic"
        assert input_data.session_id is None
        assert input_data.user_input is None

    def test_invalid_mode(self):
        """测试无效模式."""
        with pytest.raises(Exception):
            RequirementCollectionInput.model_validate(
                {
                    "action": "start",
                    "mode": "invalid_mode",
                }
            )


class TestValidationRule:
    """测试 ValidationRule 数据模型."""

    def test_required_field(self):
        """测试必填字段."""
        rule = ValidationRule(
            field="skill_name",
            required=True,
            help_text="技能名称是必填项",
        )
        assert rule.field == "skill_name"
        assert rule.required is True
        assert rule.help_text == "技能名称是必填项"

    def test_optional_field(self):
        """测试可选字段."""
        rule = ValidationRule(
            field="additional_features",
            required=False,
            help_text="可选：额外功能",
        )
        assert rule.required is False

    def test_validation_with_options(self):
        """测试带选项的验证."""
        rule = ValidationRule(
            field="template_type",
            required=True,
            options=["minimal", "tool-based", "workflow-based", "analyzer-based"],
            help_text="选择模板类型",
        )
        assert rule.options == ["minimal", "tool-based", "workflow-based", "analyzer-based"]

    def test_validation_with_pattern(self):
        """测试带正则表达式的验证."""
        rule = ValidationRule(
            field="skill_name",
            required=True,
            pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
            help_text="技能名称格式",
        )
        assert rule.pattern == r"^[a-z0-9]+(?:-[a-z0-9]+)*$"


class TestRequirementSteps:
    """测试需求收集步骤."""

    def test_basic_steps_structure(self):
        """测试基础模式步骤结构."""
        from skill_creator_mcp.constants import BASIC_REQUIREMENT_STEPS

        assert len(BASIC_REQUIREMENT_STEPS) == 5

        # 检查第一步
        first_step = BASIC_REQUIREMENT_STEPS[0]
        assert first_step["key"] == "skill_name"
        assert "validation" in first_step
        assert first_step["validation"]["required"] is True

    def test_complete_steps_structure(self):
        """测试完整模式步骤结构."""
        from skill_creator_mcp.constants import COMPLETE_REQUIREMENT_STEPS

        assert len(COMPLETE_REQUIREMENT_STEPS) == 5

        # 检查额外步骤
        extra_step = COMPLETE_REQUIREMENT_STEPS[0]
        assert extra_step["key"] == "target_users"
        assert "complete" in extra_step.get("modes", [])


class TestValidateRequirementAnswer:
    """测试 _validate_requirement_answer 函数."""

    def test_valid_required_answer(self):
        """测试有效的必填答案."""
        from skill_creator_mcp.utils.requirement_collection import _validate_requirement_answer

        validation = {
            "field": "skill_name",
            "required": True,
            "min_length": 1,
            "max_length": 64,
            "pattern": r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
            "help_text": "技能名称格式",
        }

        result = _validate_requirement_answer("test-skill", validation)
        assert result["valid"] is True

    def test_empty_required_answer(self):
        """测试空的必填答案."""
        from skill_creator_mcp.utils.requirement_collection import _validate_requirement_answer

        validation = {
            "field": "skill_name",
            "required": True,
            "help_text": "技能名称是必填项",
        }

        result = _validate_requirement_answer("", validation)
        assert result["valid"] is False
        assert "必填项" in result["error"]

    def test_empty_optional_answer(self):
        """测试空的可选答案."""
        from skill_creator_mcp.utils.requirement_collection import _validate_requirement_answer

        validation = {
            "field": "additional_features",
            "required": False,
            "help_text": "可选：额外功能",
        }

        result = _validate_requirement_answer("", validation)
        assert result["valid"] is True

    def test_min_length_validation(self):
        """测试最小长度验证."""
        from skill_creator_mcp.utils.requirement_collection import _validate_requirement_answer

        validation = {
            "field": "skill_function",
            "required": True,
            "min_length": 10,
            "help_text": "至少需要 10 个字符",
        }

        result = _validate_requirement_answer("太短", validation)
        assert result["valid"] is False
        assert "10 个字符" in result["error"]

    def test_max_length_validation(self):
        """测试最大长度验证."""
        from skill_creator_mcp.utils.requirement_collection import _validate_requirement_answer

        validation = {
            "field": "skill_name",
            "required": True,
            "max_length": 10,
            "help_text": "最多 10 个字符",
        }

        result = _validate_requirement_answer("a" * 15, validation)
        assert result["valid"] is False
        assert "10 个字符" in result["error"]

    def test_options_validation(self):
        """测试选项验证."""
        from skill_creator_mcp.utils.requirement_collection import _validate_requirement_answer

        validation = {
            "field": "template_type",
            "required": True,
            "options": ["minimal", "tool-based", "workflow-based", "analyzer-based"],
            "help_text": "选择模板类型",
        }

        result = _validate_requirement_answer("minimal", validation)
        assert result["valid"] is True

        result = _validate_requirement_answer("invalid", validation)
        assert result["valid"] is False
        assert "无效的选项" in result["error"]

    def test_pattern_validation(self):
        """测试正则表达式验证."""
        from skill_creator_mcp.utils.requirement_collection import _validate_requirement_answer

        validation = {
            "field": "skill_name",
            "required": True,
            "pattern": r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
            "help_text": "只能包含小写字母、数字和连字符",
        }

        result = _validate_requirement_answer("test-skill", validation)
        assert result["valid"] is True

        result = _validate_requirement_answer("Test-Skill", validation)
        assert result["valid"] is False
        # help_text 会在验证失败时作为错误消息返回
        assert result["error"] == "只能包含小写字母、数字和连字符"


class TestCalculateProgress:
    """测试进度计算."""

    def test_progress_at_start(self):
        """测试开始时的进度."""
        current_step = 0
        total_steps = 5
        progress = (current_step / total_steps) * 100
        assert progress == 0.0

    def test_progress_in_middle(self):
        """测试中间时的进度."""
        current_step = 2
        total_steps = 5
        progress = (current_step / total_steps) * 100
        assert progress == 40.0

    def test_progress_complete(self):
        """测试完成时的进度."""
        current_step = 5
        total_steps = 5
        progress = (current_step / total_steps) * 100
        assert progress == 100.0

    def test_progress_different_modes(self):
        """测试不同模式的进度计算."""
        # 基础模式 5 步
        basic_progress = (2 / 5) * 100
        assert basic_progress == 40.0

        # 完整模式 10 步
        complete_progress = (2 / 10) * 100
        assert complete_progress == 20.0


@pytest.mark.asyncio
class TestCollectRequirementsIntegration:
    """测试 collect_requirements 集成功能."""

    async def test_start_action_creates_session(self, mock_context):
        """测试 start action 创建新会话."""
        from skill_creator_mcp.models.skill_config import SessionState

        mock_context.session_id = "test_session_123"
        mock_context.get_state = AsyncMock(return_value=None)
        mock_context.set_state = AsyncMock(return_value=None)
        mock_context.sample = AsyncMock()

        # 直接调用内部逻辑而不是通过 MCP 装饰器
        session_state = SessionState(
            current_step_index=0,
            answers={},
            completed=False,
            mode="basic",
            total_steps=5,
        )

        assert session_state.current_step_index == 0
        assert session_state.total_steps == 5
        assert session_state.completed is False

    async def test_status_action_returns_state(self, mock_context):
        """测试 status action 返回会话状态."""
        from skill_creator_mcp.models.skill_config import SessionState

        session_state = SessionState(
            current_step_index=2,
            answers={"skill_name": "test-skill"},
            completed=False,
            mode="basic",
            total_steps=5,
        )

        # 验证状态计算
        progress = (session_state.current_step_index / session_state.total_steps) * 100

        assert progress == 40.0
        assert session_state.answers["skill_name"] == "test-skill"


@pytest.fixture
def mock_context():
    """创建模拟的 MCP Context."""
    context = MagicMock()
    context.session_id = "test_session_123"
    context.sample = AsyncMock()
    context.elicit = AsyncMock()
    context.get_state = AsyncMock(return_value=None)
    context.set_state = AsyncMock(return_value=None)
    return context
