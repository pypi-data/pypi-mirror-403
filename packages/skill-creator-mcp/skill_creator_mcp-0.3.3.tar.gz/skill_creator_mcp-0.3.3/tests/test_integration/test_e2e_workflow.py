"""端到端集成测试 - 完整工作流场景.

测试完整的 Agent-Skills 开发工作流场景：
- 创建技能 → 验证 → 分析
- 迭代改进场景
- 多技能对比场景
- 需求收集完整流程 (collect_requirements)
"""

import pytest

from skill_creator_mcp.server import _generate_skill_md_content
from skill_creator_mcp.utils.analyzers import (
    _analyze_quality,
)
from skill_creator_mcp.utils.file_ops import create_directory_structure_async, write_file_async
from skill_creator_mcp.utils.validators import validate_skill_name, validate_template_type

# ============================================================================
# Collect Requirements 端到端测试
# ============================================================================


@pytest.mark.asyncio
async def test_collect_requirements_basic_mode_full_workflow():
    """测试 basic 模式的完整需求收集流程.

    模拟从开始到完成的完整需求收集对话流程。
    注意：由于 collect_requirements 是 MCP 工具，这里测试其核心逻辑组件.
    """
    from skill_creator_mcp.constants import BASIC_REQUIREMENT_STEPS
    from skill_creator_mcp.models.skill_config import (
        RequirementCollectionInput,
    )
    from skill_creator_mcp.utils.requirement_collection import (
        _validate_requirement_answer,
    )

    # 步骤 1: 验证输入模型
    input_data = RequirementCollectionInput(
        action="start",
        mode="basic",
        session_id="test-basic-session",
    )

    assert input_data.action == "start"
    assert input_data.mode == "basic"

    # 步骤 2: 验证预定义步骤
    assert len(BASIC_REQUIREMENT_STEPS) == 5
    assert BASIC_REQUIREMENT_STEPS[0]["key"] == "skill_name"
    assert BASIC_REQUIREMENT_STEPS[4]["key"] == "additional_features"

    # 步骤 3: 验证答案验证逻辑
    validation = BASIC_REQUIREMENT_STEPS[0]["validation"]  # skill_name validation

    # 测试有效答案
    valid_result = _validate_requirement_answer("pdf-processor", validation)
    assert valid_result["valid"] is True

    # 测试无效答案（不符合命名规则）
    # 注意：验证函数会优先使用 help_text 而不是默认的 "格式不正确"
    invalid_result = _validate_requirement_answer("PDF Processor", validation)
    assert invalid_result["valid"] is False
    # 验证错误消息包含 help_text 的内容
    assert "小写字母" in invalid_result["error"] or "格式" in invalid_result["error"]


@pytest.mark.asyncio
async def test_collect_requirements_session_state_management():
    """测试会话状态管理功能.

    验证会话状态的保存和恢复逻辑。
    """
    from skill_creator_mcp.models.skill_config import SessionState

    # 步骤 1: 创建新会话状态
    session_state = SessionState(
        current_step_index=0,
        answers={},
        started_at="2026-01-23T10:00:00Z",
        completed=False,
        mode="basic",
        total_steps=5,
    )

    assert session_state.current_step_index == 0
    assert len(session_state.answers) == 0
    assert session_state.completed is False

    # 步骤 2: 模拟添加答案后的状态更新
    session_state.answers["skill_name"] = "data-analyzer"
    session_state.current_step_index = 1

    assert session_state.answers["skill_name"] == "data-analyzer"
    assert session_state.current_step_index == 1

    # 步骤 3: 验证状态可以序列化和反序列化
    state_dict = session_state.model_dump()
    restored_state = SessionState.model_validate(state_dict)

    assert restored_state.current_step_index == session_state.current_step_index
    assert restored_state.answers == session_state.answers


@pytest.mark.asyncio
async def test_collect_requirements_brainstorm_mode_dynamic_generation():
    """测试 brainstorm 模式的动态问题生成逻辑.

    验证 LLM 问题生成函数的功能.
    """
    from unittest.mock import AsyncMock, MagicMock, Mock

    from fastmcp import Context

    mock_ctx = MagicMock(spec=Context)

    # 模拟 ctx.sample() 返回 LLM 生成的问题
    mock_sampling_result = Mock()
    mock_sampling_result.text = "您希望这个技能解决用户什么样的痛点？"
    mock_ctx.sample = AsyncMock(return_value=mock_sampling_result)

    from skill_creator_mcp.utils.requirement_collection import _generate_brainstorm_question

    # 调用问题生成函数
    result = await _generate_brainstorm_question(
        ctx=mock_ctx,
        answers={},
        conversation_history=None,
    )

    assert result["success"] is True
    assert "question" in result
    assert result["is_dynamic"] is True
    assert result["source"] == "llm_generated"


@pytest.mark.asyncio
async def test_collect_requirements_progressive_mode_adaptive_questions():
    """测试 progressive 模式的自适应问题生成逻辑.

    验证根据已收集信息生成针对性问题.
    """
    from unittest.mock import AsyncMock, MagicMock, Mock

    from fastmcp import Context

    mock_ctx = MagicMock(spec=Context)

    # 模拟已有部分答案的会话状态
    partial_answers = {
        "skill_name": "api-integrator",
    }

    # 模拟 LLM 返回针对性的下一个问题
    mock_sampling_result = Mock()
    mock_sampling_result.text = """
    {"next_question": "这个技能需要集成哪些 API？",
    "question_key": "api_targets",
    "reasoning": "需要了解集成目标"}
    """
    mock_ctx.sample = AsyncMock(return_value=mock_sampling_result)

    from skill_creator_mcp.utils.requirement_collection import _generate_progressive_question

    # 调用问题生成函数
    result = await _generate_progressive_question(
        ctx=mock_ctx,
        answers=partial_answers,
    )

    assert result["success"] is True
    assert "next_question" in result
    assert result["is_dynamic"] is True


@pytest.mark.asyncio
async def test_collect_requirements_integration_with_init_skill(temp_dir):
    """测试需求收集与技能创建的集成.

    验证需求收集的结果结构符合 init_skill 的输入要求.
    """
    # 模拟完成需求收集后得到的结果
    collected_requirements = {
        "skill_name": "task-automation",
        "skill_function": "自动化任务执行",
        "use_cases": "定时任务、事件触发任务",
        "template_type": "workflow-based",
        "additional_features": "任务状态跟踪",
    }

    # 步骤 1: 使用收集到的需求创建技能目录
    skill_dir = await create_directory_structure_async(
        name=collected_requirements["skill_name"],
        template_type=collected_requirements["template_type"],
        output_dir=temp_dir,
    )

    assert skill_dir is not None

    # 注意：create_directory_structure_async() 只创建目录，不创建 SKILL.md
    # 需要额外调用 _generate_skill_md_content() 和 write_file_async() 来创建 SKILL.md
    skill_md_content = _generate_skill_md_content(
        collected_requirements["skill_name"],
        collected_requirements["template_type"],
    )
    await write_file_async(skill_dir / "SKILL.md", skill_md_content)

    # 步骤 2: 验证创建的技能名称符合需求
    assert (skill_dir / "SKILL.md").exists()
    skill_content = (skill_dir / "SKILL.md").read_text()
    assert collected_requirements["skill_name"] in skill_content

    # 步骤 3: 验证模板类型符合需求
    # workflow-based 模板应该包含特定的工具列表
    assert "Glob" in skill_content or "Grep" in skill_content


# ============================================================================
# 原有端到端测试
# ============================================================================


@pytest.mark.asyncio
async def test_iterative_improvement_scenario(temp_dir):
    """测试迭代改进场景：逐步改进技能质量."""
    # 1. 创建基础技能
    validate_skill_name("iterative-skill")
    validate_template_type("workflow-based")

    skill_dir = await create_directory_structure_async(
        name="iterative-skill",
        template_type="workflow-based",
        output_dir=temp_dir,
    )

    skill_md_content = _generate_skill_md_content("iterative-skill", "workflow-based")
    await write_file_async(skill_dir / "SKILL.md", skill_md_content)

    # 2. 初始质量分析
    initial_quality = await _analyze_quality(skill_dir)
    initial_score = initial_quality.overall_score

    # 3. 添加改进（在 examples 目录添加文件）
    example_file = skill_dir / "examples" / "advanced_usage.md"
    example_file.write_text("# Advanced Usage\n\nAdvanced example here.")

    # 4. 重新分析质量
    improved_quality = await _analyze_quality(skill_dir)
    improved_score = improved_quality.overall_score

    # 改进后的分数应该更高或相等
    assert improved_score >= initial_score


@pytest.mark.asyncio
async def test_multi_template_comparison_scenario(temp_dir):
    """测试多模板对比场景：比较不同模板类型的技能."""
    results = {}

    # 创建三种不同类型的技能
    for template_type in ["minimal", "tool-based", "workflow-based"]:
        validate_skill_name(f"test-{template_type}")
        validate_template_type(template_type)

        skill_dir = await create_directory_structure_async(
            name=f"test-{template_type}",
            template_type=template_type,
            output_dir=temp_dir,
        )

        skill_md_content = _generate_skill_md_content(f"test-{template_type}", template_type)
        await write_file_async(skill_dir / "SKILL.md", skill_md_content)

        # 分析质量
        quality = await _analyze_quality(skill_dir)
        results[template_type] = {
            "score": quality.overall_score,
            "structure_score": quality.structure_score,
        }

    # minimal 应该有最少的结构分数
    # tool-based 和 workflow-based 应该有更高的结构分数
    assert results["minimal"]["structure_score"] <= results["tool-based"]["structure_score"]
    assert results["minimal"]["structure_score"] <= results["workflow-based"]["structure_score"]


@pytest.mark.asyncio
async def test_complete_lifecycle_scenario(temp_dir):
    """测试完整生命周期场景：从创建到分析."""
    # 1. 创建技能
    validate_skill_name("lifecycle-skill")
    validate_template_type("tool-based")

    skill_dir = await create_directory_structure_async(
        name="lifecycle-skill",
        template_type="tool-based",
        output_dir=temp_dir,
    )

    skill_md_content = _generate_skill_md_content("lifecycle-skill", "tool-based")
    await write_file_async(skill_dir / "SKILL.md", skill_md_content)

    # 2. 验证必需文件存在
    assert (skill_dir / "SKILL.md").exists()
    assert (skill_dir / "references").exists()

    # 3. 质量分析
    quality = await _analyze_quality(skill_dir)

    # 应该有有效的分数
    assert quality.overall_score > 0
    assert quality.structure_score > 0
    assert quality.documentation_score > 0
