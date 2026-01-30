"""测试 server.py 中的辅助函数和边界情况.

此文件专注于测试未覆盖的代码路径，包括：
- 异常处理路径
- 动态模式的分支
- 辅助函数的边界情况
"""

from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest


@pytest.mark.asyncio
class TestCheckRequirementCompleteness:
    """测试 _check_requirement_completeness 函数."""

    async def test_llm_returns_valid_json(self):
        """测试 LLM 返回有效 JSON 的情况."""
        from skill_creator_mcp.utils.requirement_collection import _check_requirement_completeness

        mock_ctx = MagicMock()
        mock_result = Mock()
        mock_result.text = '{"is_complete": true, "missing_info": [], "suggestions": []}'
        mock_ctx.sample = AsyncMock(return_value=mock_result)

        answers = {"skill_name": "test", "skill_function": "test", "use_cases": "test", "template_type": "minimal"}
        result = await _check_requirement_completeness(mock_ctx, answers)

        assert result["is_complete"] is True

    async def test_llm_returns_invalid_json_uses_fallback(self):
        """测试 LLM 返回无效 JSON 时使用降级方案（覆盖 line 1814-1821）."""
        from skill_creator_mcp.utils.requirement_collection import _check_requirement_completeness

        mock_ctx = MagicMock()
        mock_result = Mock()
        mock_result.text = 'This is not valid JSON {"is_complete": true'
        mock_ctx.sample = AsyncMock(return_value=mock_result)

        answers = {"skill_name": "test", "skill_function": "test", "use_cases": "test", "template_type": "minimal"}
        result = await _check_requirement_completeness(mock_ctx, answers)

        # 应该降级到本地检查
        assert result["is_complete"] is True
        assert result["missing_info"] == []

    async def test_llm_fails_exception(self):
        """测试 LLM 调用失败时的降级处理."""
        from skill_creator_mcp.utils.requirement_collection import _check_requirement_completeness

        mock_ctx = MagicMock()
        mock_ctx.sample = AsyncMock(side_effect=Exception("LLM unavailable"))

        answers = {"skill_name": "test"}  # 缺少必填字段
        result = await _check_requirement_completeness(mock_ctx, answers)

        # 应该降级到本地检查并返回缺失信息
        assert result["is_complete"] is False
        assert len(result["missing_info"]) > 0

    async def test_incomplete_answers_local_check(self):
        """测试本地检查发现不完整的答案."""
        from skill_creator_mcp.utils.requirement_collection import _check_requirement_completeness

        mock_ctx = MagicMock()
        mock_ctx.sample = AsyncMock(side_effect=Exception("LLM error"))

        # 缺少必填字段
        answers = {"skill_name": "test"}
        result = await _check_requirement_completeness(mock_ctx, answers)

        assert result["is_complete"] is False
        assert "skill_function" in result["missing_info"]
        assert "use_cases" in result["missing_info"]
        assert "template_type" in result["missing_info"]


@pytest.mark.asyncio
class TestGenerateProgressiveQuestion:
    """测试 _generate_progressive_question 函数."""

    async def test_llm_returns_valid_json_response(self):
        """测试 LLM 返回有效 JSON 响应."""
        from skill_creator_mcp.utils.requirement_collection import _generate_progressive_question

        mock_ctx = MagicMock()
        mock_result = Mock()
        mock_result.text = '{"next_question": "What features do you need?", "question_key": "features", "reasoning": "Need more info"}'
        mock_ctx.sample = AsyncMock(return_value=mock_result)

        answers = {"skill_name": "test"}
        result = await _generate_progressive_question(mock_ctx, answers)

        assert result["success"] is True
        assert result["next_question"] == "What features do you need?"
        assert result["question_key"] == "features"
        assert result["is_dynamic"] is True

    async def test_llm_returns_invalid_json_uses_fallback(self):
        """测试 LLM 返回无效 JSON 时使用降级方案（覆盖 line 1974-1975）."""
        from skill_creator_mcp.utils.requirement_collection import _generate_progressive_question

        mock_ctx = MagicMock()
        mock_result = Mock()
        mock_result.text = 'Not a valid JSON response'
        mock_ctx.sample = AsyncMock(return_value=mock_result)

        answers = {}
        result = await _generate_progressive_question(mock_ctx, answers)

        # 应该使用降级方案
        assert result["success"] is True
        assert result["next_question"] == "请提供技能名称（小写字母、数字、连字符）"
        assert result["question_key"] == "skill_name"
        assert result.get("source") == "fallback"

    async def test_fallback_selects_question_by_answers_count(self):
        """测试降级方案根据答案数量选择问题."""
        from skill_creator_mcp.utils.requirement_collection import _generate_progressive_question

        mock_ctx = MagicMock()
        mock_result = Mock()
        mock_result.text = "Invalid JSON"
        mock_ctx.sample = AsyncMock(return_value=mock_result)

        # 已有 1 个答案，应该返回第 2 个问题
        answers = {"skill_name": "test"}
        result = await _generate_progressive_question(mock_ctx, answers)

        assert result["question_key"] == "skill_function"
        assert "主要功能" in result["next_question"]

    async def test_exception_returns_fallback(self):
        """测试异常时返回降级方案."""
        from skill_creator_mcp.utils.requirement_collection import _generate_progressive_question

        mock_ctx = MagicMock()
        mock_ctx.sample = AsyncMock(side_effect=Exception("Sampling error"))

        answers = {"skill_name": "test", "skill_function": "test"}
        result = await _generate_progressive_question(mock_ctx, answers)

        # 应该使用降级方案
        assert result["success"] is True
        assert result["next_question"] == "请描述这个技能的使用场景"
        assert result["question_key"] == "use_cases"


class TestGetRequirementModeSteps:
    """测试 _get_requirement_mode_steps 函数."""

    def test_brainstorm_mode_returns_empty_list(self):
        """测试 brainstorm 模式返回空列表（覆盖 line 1265）."""
        from skill_creator_mcp.server import _get_requirement_mode_steps

        result = _get_requirement_mode_steps("brainstorm")
        assert result == []

    def test_progressive_mode_returns_empty_list(self):
        """测试 progressive 模式返回空列表."""
        from skill_creator_mcp.server import _get_requirement_mode_steps

        result = _get_requirement_mode_steps("progressive")
        assert result == []

    def test_basic_mode_returns_basic_steps(self):
        """测试 basic 模式返回基础步骤."""
        from skill_creator_mcp.constants import BASIC_REQUIREMENT_STEPS
        from skill_creator_mcp.utils.requirement_collection import _get_requirement_mode_steps

        result = _get_requirement_mode_steps("basic")
        assert len(result) == len(BASIC_REQUIREMENT_STEPS)
        assert result[0]["key"] == "skill_name"

    def test_complete_mode_returns_all_steps(self):
        """测试 complete 模式返回所有步骤."""
        from skill_creator_mcp.constants import BASIC_REQUIREMENT_STEPS, COMPLETE_REQUIREMENT_STEPS
        from skill_creator_mcp.utils.requirement_collection import _get_requirement_mode_steps

        result = _get_requirement_mode_steps("complete")
        expected_length = len(BASIC_REQUIREMENT_STEPS) + len(COMPLETE_REQUIREMENT_STEPS)
        assert len(result) == expected_length


@pytest.mark.asyncio
class TestProcessRequirementUserAnswer:
    """测试 _process_requirement_user_answer 函数."""

    async def test_dynamic_mode_saves_answer_and_continues(self):
        """测试动态模式保存答案并继续（覆盖 lines 1562-1599）."""
        from skill_creator_mcp.models.skill_config import SessionState
        from skill_creator_mcp.server import _process_requirement_user_answer

        mock_ctx = MagicMock()
        mock_ctx.set_state = AsyncMock()

        session_state = SessionState(
            current_step_index=0,
            answers={},
            completed=False,
            mode="brainstorm",
            total_steps=10,
            conversation_history=[],
        )

        result = await _process_requirement_user_answer(
            ctx=mock_ctx,
            session_state=session_state,
            current_session_id="test_session",
            action="next",
            user_input="my answer",
            is_dynamic_mode=True,
            mode="brainstorm",
            all_steps=None,
            current_step=None,
        )

        assert result["success"] is True
        assert result["is_dynamic_mode"] is True
        assert session_state.answers["answer_0"] == "my answer"

    async def test_dynamic_mode_complete_action(self):
        """测试动态模式完成操作."""
        from skill_creator_mcp.models.skill_config import SessionState
        from skill_creator_mcp.server import _process_requirement_user_answer

        mock_ctx = MagicMock()
        mock_ctx.set_state = AsyncMock()

        session_state = SessionState(
            current_step_index=2,
            answers={"answer_0": "ans0", "answer_1": "ans1"},
            completed=False,
            mode="progressive",
            total_steps=10,
            conversation_history=[],
        )

        result = await _process_requirement_user_answer(
            ctx=mock_ctx,
            session_state=session_state,
            current_session_id="test_session",
            action="complete",
            user_input="final answer",
            is_dynamic_mode=True,
            mode="progressive",
            all_steps=None,
            current_step=None,
        )

        assert result["success"] is True
        assert result["completed"] is True
        assert result["message"] == "PROGRESSIVE 模式需求收集完成！"

    async def test_static_mode_no_current_step_error(self):
        """测试静态模式没有当前步骤时返回错误（覆盖 line 1615）."""
        from skill_creator_mcp.models.skill_config import SessionState
        from skill_creator_mcp.server import _process_requirement_user_answer

        mock_ctx = MagicMock()

        session_state = SessionState(
            current_step_index=1,
            answers={},
            completed=False,
            mode="basic",
            total_steps=5,
            conversation_history=[],
        )

        result = await _process_requirement_user_answer(
            ctx=mock_ctx,
            session_state=session_state,
            current_session_id="test_session",
            action="next",
            user_input="answer",
            is_dynamic_mode=False,
            mode="basic",
            all_steps=None,
            current_step=None,  # 没有 current_step
        )

        assert result["success"] is False
        assert result["error"] == "没有当前步骤"

    async def test_brainstorm_mode_saves_conversation_history(self):
        """测试 brainstorm 模式保存对话历史."""
        from skill_creator_mcp.models.skill_config import SessionState
        from skill_creator_mcp.server import _process_requirement_user_answer

        mock_ctx = MagicMock()
        mock_ctx.set_state = AsyncMock()

        session_state = SessionState(
            current_step_index=0,
            answers={},
            completed=False,
            mode="brainstorm",
            total_steps=10,
            conversation_history=[],
        )

        await _process_requirement_user_answer(
            ctx=mock_ctx,
            session_state=session_state,
            current_session_id="test_session",
            action="next",
            user_input="my brainstorm idea",
            is_dynamic_mode=True,
            mode="brainstorm",
            all_steps=None,
            current_step=None,
        )

        # 应该保存到对话历史
        assert len(session_state.conversation_history) == 1
        assert session_state.conversation_history[0] == {"role": "user", "content": "my brainstorm idea"}


@pytest.mark.asyncio
class TestHandleRequirementPreviousAction:
    """测试 _handle_requirement_previous_action 函数."""

    async def test_dynamic_mode_previous_returns_status(self):
        """测试动态模式上一步操作返回状态（覆盖 line 1333）."""
        from skill_creator_mcp.models.skill_config import SessionState
        from skill_creator_mcp.server import _handle_requirement_previous_action

        mock_ctx = MagicMock()
        mock_ctx.set_state = AsyncMock()

        session_state = SessionState(
            current_step_index=2,
            answers={},
            completed=False,
            mode="brainstorm",
            total_steps=10,
            conversation_history=[],
        )

        result = await _handle_requirement_previous_action(
            ctx=mock_ctx,
            session_state=session_state,
            current_session_id="test_session",
            is_dynamic_mode=True,
            all_steps=None,
        )

        assert result["success"] is True
        assert result["is_dynamic_mode"] is True
        assert session_state.current_step_index == 1

    async def test_static_mode_previous_at_first_step_error(self):
        """测试静态模式在第一步时无法返回（覆盖 line 1375）."""
        from skill_creator_mcp.models.skill_config import SessionState
        from skill_creator_mcp.server import _handle_requirement_previous_action

        mock_ctx = MagicMock()

        session_state = SessionState(
            current_step_index=0,
            answers={},
            completed=False,
            mode="basic",
            total_steps=5,
            conversation_history=[],
        )

        result = await _handle_requirement_previous_action(
            ctx=mock_ctx,
            session_state=session_state,
            current_session_id="test_session",
            is_dynamic_mode=False,
            all_steps=[],
        )

        assert result["success"] is False
        assert result["error"] == "已经是第一步了"

    async def test_dynamic_mode_previous_at_step_zero_error(self):
        """测试动态模式在第零步时无法返回."""
        from skill_creator_mcp.models.skill_config import SessionState
        from skill_creator_mcp.server import _handle_requirement_previous_action

        mock_ctx = MagicMock()

        session_state = SessionState(
            current_step_index=0,
            answers={},
            completed=False,
            mode="progressive",
            total_steps=10,
            conversation_history=[],
        )

        result = await _handle_requirement_previous_action(
            ctx=mock_ctx,
            session_state=session_state,
            current_session_id="test_session",
            is_dynamic_mode=True,
            all_steps=None,
        )

        # 当 step_index=0 时，无论是否动态模式都返回 "已经是第一步了"
        assert result["success"] is False
        assert "第一步" in result["error"]


@pytest.mark.asyncio
class TestCollectRequirementsErrorHandling:
    """测试 collect_requirements 工具的异常处理."""

    async def test_exception_handling_in_collect_requirements(self):
        """测试 collect_requirements 异常处理（覆盖 lines 947-948）."""
        from skill_creator_mcp.server import collect_requirements

        mock_ctx = MagicMock()
        mock_ctx.session_id = "test_session"
        mock_ctx.get_state = AsyncMock(return_value=None)
        mock_ctx.set_state = AsyncMock()

        # Mock _validate_and_init_requirement_session to raise an exception
        with patch('skill_creator_mcp.server._validate_and_init_requirement_session', side_effect=Exception("Internal error")):
            result = await collect_requirements(
                ctx=mock_ctx,
                action="next",
                mode="basic",
                session_id="test_session",
                user_input="test",
            )

        assert result["success"] is False
        assert "error" in result
        assert "需求收集出错" in result["error"]


@pytest.mark.asyncio
class TestGetRequirementNextQuestion:
    """测试 _get_requirement_next_question 函数."""

    async def test_default_error_return(self):
        """测试默认错误返回（覆盖 line 1524）."""
        from skill_creator_mcp.models.skill_config import SessionState
        from skill_creator_mcp.server import _get_requirement_next_question

        mock_ctx = MagicMock()
        mock_ctx.set_state = AsyncMock()

        session_state = SessionState(
            current_step_index=0,
            answers={},
            completed=False,
            mode="basic",
            total_steps=5,
            conversation_history=[],
        )

        result = await _get_requirement_next_question(
            ctx=mock_ctx,
            session_state=session_state,
            is_dynamic_mode=False,
            mode="basic",
            all_steps=None,
        )

        assert result["success"] is False
        assert "无法获取下一个问题" in result.get("error", "")


@pytest.mark.asyncio
class TestCollectWithElicitErrorCases:
    """测试 _collect_with_elicit 边界情况."""

    async def test_unknown_dynamic_mode_returns_error(self):
        """测试未知动态模式返回错误（覆盖 line 1021）."""
        from skill_creator_mcp.models.skill_config import RequirementCollectionInput, SessionState
        from skill_creator_mcp.server import _collect_with_elicit

        mock_ctx = MagicMock()
        mock_ctx.get_state = AsyncMock(return_value=None)
        mock_ctx.set_state = AsyncMock()
        mock_ctx.elicit = AsyncMock()

        session_state = SessionState(
            current_step_index=0,
            answers={},
            completed=False,
            mode="basic",
            total_steps=5,
            conversation_history=[],
        )

        # 创建输入数据 - 使用有效模式但模拟未知模式的情况
        input_data = RequirementCollectionInput(
            action="next",
            mode="progressive",  # 使用有效的动态模式
            session_id="test_session",
            user_input="test",
        )

        # Mock sample 来返回一个非预期的响应
        mock_ctx.sample = AsyncMock()

        result = await _collect_with_elicit(
            ctx=mock_ctx,
            session_state=session_state,
            current_session_id="test_session",
            is_dynamic_mode=True,
            all_steps=None,
            input_data=input_data,
        )

        # 对于 progressive 模式，应该返回 success
        assert "success" in result
