"""测试 collect_requirements 集成功能 - Session State 管理."""

from datetime import datetime, timezone

import pytest

from skill_creator_mcp.models.skill_config import SessionState


@pytest.mark.asyncio
class TestSessionStateManagement:
    """测试 Session State 管理功能."""

    async def test_session_state_initialization(self):
        """测试会话状态初始化."""
        session_state = SessionState(
            current_step_index=0,
            answers={},
            started_at=datetime.now(timezone.utc).isoformat(),
            completed=False,
            mode="basic",
            total_steps=5,
        )

        assert session_state.current_step_index == 0
        assert session_state.answers == {}
        assert session_state.completed is False
        assert session_state.mode == "basic"
        assert session_state.total_steps == 5

    async def test_session_state_serialization(self):
        """测试会话状态序列化和反序列化."""
        original_state = SessionState(
            current_step_index=2,
            answers={"skill_name": "test-skill", "skill_function": "测试功能"},
            completed=False,
            mode="basic",
            total_steps=5,
        )

        # 序列化
        serialized = original_state.model_dump()

        # 反序列化
        restored_state = SessionState.model_validate(serialized)

        assert restored_state.current_step_index == original_state.current_step_index
        assert restored_state.answers == original_state.answers
        assert restored_state.completed == original_state.completed
        assert restored_state.total_steps == original_state.total_steps

    async def test_session_state_progress_tracking(self):
        """测试会话进度跟踪."""
        session_state = SessionState(
            current_step_index=0,
            answers={},
            total_steps=5,
            completed=False,
            mode="basic",
        )

        # 初始进度
        progress = (session_state.current_step_index / session_state.total_steps) * 100
        assert progress == 0.0

        # 前进两步
        session_state.current_step_index = 2
        progress = (session_state.current_step_index / session_state.total_steps) * 100
        assert progress == 40.0

        # 完成
        session_state.current_step_index = 5
        session_state.completed = True
        progress = (session_state.current_step_index / session_state.total_steps) * 100
        assert progress == 100.0

    async def test_session_state_answer_accumulation(self):
        """测试答案累积."""
        session_state = SessionState(
            current_step_index=0,
            answers={},
            total_steps=5,
            completed=False,
            mode="basic",
        )

        # 添加第一个答案
        session_state.answers["skill_name"] = "test-skill"
        assert len(session_state.answers) == 1

        # 添加第二个答案
        session_state.answers["skill_function"] = "这是一个测试技能"
        assert len(session_state.answers) == 2

        # 验证所有答案
        assert session_state.answers["skill_name"] == "test-skill"
        assert session_state.answers["skill_function"] == "这是一个测试技能"


@pytest.mark.asyncio
class TestSessionStateIsolation:
    """测试 Session 隔离性."""

    async def test_different_sessions_have_different_states(self):
        """测试不同会话有不同的状态."""
        session_1 = SessionState(
            current_step_index=1,
            answers={"skill_name": "skill-1"},
            total_steps=5,
            completed=False,
            mode="basic",
        )

        session_2 = SessionState(
            current_step_index=3,
            answers={"skill_name": "skill-2"},
            total_steps=5,
            completed=False,
            mode="complete",
        )

        # 验证两个会话状态不同
        assert session_1.current_step_index != session_2.current_step_index
        assert session_1.answers["skill_name"] != session_2.answers["skill_name"]
        assert session_1.mode != session_2.mode

    async def test_session_state_does_not_affect_others(self):
        """测试会话状态不会相互影响."""
        session_1 = SessionState(
            current_step_index=0,
            answers={},
            total_steps=5,
            completed=False,
            mode="basic",
        )

        session_2 = SessionState(
            current_step_index=0,
            answers={},
            total_steps=5,
            completed=False,
            mode="basic",
        )

        # 修改 session_1
        session_1.current_step_index = 2
        session_1.answers["skill_name"] = "skill-1"

        # 验证 session_2 未受影响
        assert session_2.current_step_index == 0
        assert len(session_2.answers) == 0


@pytest.mark.asyncio
class TestSessionStateRecovery:
    """测试会话恢复功能."""

    async def test_session_can_be_restored_from_serialized_state(self):
        """测试会话可以从序列化状态恢复."""
        # 原始会话
        original_session = SessionState(
            current_step_index=3,
            answers={
                "skill_name": "pdf-parser",
                "skill_function": "解析PDF文件",
                "use_cases": "文档分析、数据提取",
            },
            completed=False,
            mode="basic",
            total_steps=5,
        )

        # 模拟保存到 state storage
        serialized_state = original_session.model_dump()

        # 模拟从 state storage 恢复
        restored_session = SessionState.model_validate(serialized_state)

        # 验证恢复正确
        assert restored_session.current_step_index == 3
        assert restored_session.answers["skill_name"] == "pdf-parser"
        assert restored_session.answers["skill_function"] == "解析PDF文件"
        assert restored_session.completed is False

    async def test_session_can_continue_after_interruption(self):
        """测试会话可以在中断后继续."""
        # 模拟用户在第 2 步中断
        interrupted_state = SessionState(
            current_step_index=2,
            answers={
                "skill_name": "test-skill",
                "skill_function": "测试功能",
            },
            completed=False,
            mode="basic",
            total_steps=5,
        )

        # 序列化并保存
        serialized = interrupted_state.model_dump()

        # 用户稍后恢复会话
        restored_state = SessionState.model_validate(serialized)

        # 验证会话状态正确恢复
        assert restored_state.current_step_index == 2
        assert len(restored_state.answers) == 2

        # 用户继续添加下一个答案
        restored_state.answers["use_cases"] = "测试场景1、测试场景2"
        restored_state.current_step_index = 3

        assert len(restored_state.answers) == 3
        assert restored_state.current_step_index == 3


@pytest.mark.asyncio
class TestSessionStateExpiration:
    """测试会话过期机制（概念测试，实际过期由 FastMCP 处理）。"""

    async def test_session_state_includes_timestamp(self):
        """测试会话状态包含时间戳."""
        started_at = datetime.now(timezone.utc).isoformat()

        session_state = SessionState(
            current_step_index=0,
            answers={},
            started_at=started_at,
            completed=False,
            mode="basic",
            total_steps=5,
        )

        assert session_state.started_at is not None
        assert isinstance(session_state.started_at, str)

    async def test_completed_sessions_can_be_identified(self):
        """测试已完成的会话可以被识别."""
        completed_session = SessionState(
            current_step_index=5,
            answers={"skill_name": "test"},
            completed=True,
            mode="basic",
            total_steps=5,
        )

        incomplete_session = SessionState(
            current_step_index=2,
            answers={"skill_name": "test"},
            completed=False,
            mode="basic",
            total_steps=5,
        )

        assert completed_session.completed is True
        assert incomplete_session.completed is False


@pytest.mark.asyncio
class TestDifferentModes:
    """测试不同收集模式."""

    async def test_basic_mode_has_5_steps(self):
        """测试基础模式有 5 个步骤."""
        from skill_creator_mcp.constants import BASIC_REQUIREMENT_STEPS

        assert len(BASIC_REQUIREMENT_STEPS) == 5

        basic_state = SessionState(
            current_step_index=0,
            answers={},
            total_steps=5,
            completed=False,
            mode="basic",
        )

        assert basic_state.total_steps == 5
        assert basic_state.mode == "basic"

    async def test_complete_mode_has_10_steps(self):
        """测试完整模式有 10 个步骤."""
        from skill_creator_mcp.constants import BASIC_REQUIREMENT_STEPS, COMPLETE_REQUIREMENT_STEPS

        total_steps = len(BASIC_REQUIREMENT_STEPS) + len(COMPLETE_REQUIREMENT_STEPS)
        assert total_steps == 10

        complete_state = SessionState(
            current_step_index=0,
            answers={},
            total_steps=total_steps,
            completed=False,
            mode="complete",
        )

        assert complete_state.total_steps == 10
        assert complete_state.mode == "complete"

    async def test_progress_calculation_for_different_modes(self):
        """测试不同模式的进度计算."""
        # 基础模式：5 步，在 第 2 步
        basic_state = SessionState(
            current_step_index=2,
            answers={},
            total_steps=5,
            completed=False,
            mode="basic",
        )
        basic_progress = (basic_state.current_step_index / basic_state.total_steps) * 100
        assert basic_progress == 40.0

        # 完整模式：10 步，在第 2 步
        complete_state = SessionState(
            current_step_index=2,
            answers={},
            total_steps=10,
            completed=False,
            mode="complete",
        )
        complete_progress = (complete_state.current_step_index / complete_state.total_steps) * 100
        assert complete_progress == 20.0
