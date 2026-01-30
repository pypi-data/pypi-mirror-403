"""批量操作工具单元测试."""

import asyncio
from unittest.mock import AsyncMock

import pytest

from skill_creator_mcp.tools.batch_operations import (
    BatchAnalysisInput,
    BatchValidationInput,
    batch_analyze_skills,
    batch_analyze_skills_sync,
    batch_validate_skills,
    batch_validate_skills_sync,
)


class TestBatchValidation:
    """批量验证测试."""

    @pytest.mark.asyncio
    async def test_batch_validate_success(self):
        """测试批量验证成功场景."""
        mock_validate = AsyncMock(
            return_value={
                "success": True,
                "valid": True,
                "skill_path": "/test/skill",
            }
        )

        # Mock validate_skill
        import skill_creator_mcp.server
        original = skill_creator_mcp.server.validate_skill
        skill_creator_mcp.server.validate_skill = mock_validate

        try:
            result = await batch_validate_skills(
                skill_paths=["/skill1", "/skill2"],
                check_structure=True,
                check_content=True,
                concurrent_limit=2,
            )

            assert result.summary["total"] == 2
            assert result.summary["successful"] == 2
            assert len(result.results) == 2
        finally:
            skill_creator_mcp.server.validate_skill = original

    @pytest.mark.asyncio
    async def test_batch_validate_with_errors(self):
        """测试批量验证包含错误."""
        async def mock_validate_error(skill_path, **kwargs):
            if "error" in skill_path:
                raise ValueError("Invalid skill")
            return {
                "success": True,
                "valid": True,
                "skill_path": skill_path,
            }

        import skill_creator_mcp.server
        original = skill_creator_mcp.server.validate_skill
        skill_creator_mcp.server.validate_skill = mock_validate_error

        try:
            result = await batch_validate_skills(
                skill_paths=["/skill1", "/error", "/skill2"],
                concurrent_limit=2,
            )

            assert result.summary["total"] == 3
            assert result.summary["successful"] == 2
            assert result.summary["failed"] == 1
        finally:
            skill_creator_mcp.server.validate_skill = original

    def test_batch_validate_sync(self):
        """测试同步版本的批量验证."""
        mock_validate = AsyncMock(
            return_value={
                "success": True,
                "valid": True,
                "skill_path": "/test/skill",
            }
        )

        import skill_creator_mcp.server
        original = skill_creator_mcp.server.validate_skill
        skill_creator_mcp.server.validate_skill = mock_validate

        try:
            result = batch_validate_skills_sync(
                skill_paths=["/skill1"],
                check_structure=True,
            )

            assert result.summary["total"] == 1
            assert result.summary["successful"] == 1
        finally:
            skill_creator_mcp.server.validate_skill = original


class TestBatchAnalysis:
    """批量分析测试."""

    @pytest.mark.asyncio
    async def test_batch_analyze_success(self):
        """测试批量分析成功场景."""
        mock_analyze = AsyncMock(
            return_value={
                "success": True,
                "structure": {"total_files": 10},
                "skill_path": "/test/skill",
            }
        )

        import skill_creator_mcp.server
        original = skill_creator_mcp.server.analyze_skill
        skill_creator_mcp.server.analyze_skill = mock_analyze

        try:
            result = await batch_analyze_skills(
                skill_paths=["/skill1", "/skill2"],
                concurrent_limit=2,
            )

            assert result.summary["total"] == 2
            assert result.summary["successful"] == 2
        finally:
            skill_creator_mcp.server.analyze_skill = original

    def test_batch_analyze_sync(self):
        """测试同步版本的批量分析."""
        mock_analyze = AsyncMock(
            return_value={
                "success": True,
                "quality": {"overall_score": 75},
                "skill_path": "/test/skill",
            }
        )

        import skill_creator_mcp.server
        original = skill_creator_mcp.server.analyze_skill
        skill_creator_mcp.server.analyze_skill = mock_analyze

        try:
            result = batch_analyze_skills_sync(
                skill_paths=["/skill1"],
                analyze_structure=True,
            )

            assert result.summary["total"] == 1
            assert result.summary["successful"] == 1
        finally:
            skill_creator_mcp.server.analyze_skill = original


class TestBatchOperationModels:
    """批量操作数据模型测试."""

    def test_batch_validation_input(self):
        """测试批量验证输入模型."""
        input_data = BatchValidationInput(
            skill_paths=["/skill1", "/skill2"],
            check_structure=True,
            check_content=False,
        )

        assert input_data.skill_paths == ["/skill1", "/skill2"]
        assert input_data.check_structure is True
        assert input_data.check_content is False

    def test_batch_analysis_input(self):
        """测试批量分析输入模型."""
        input_data = BatchAnalysisInput(
            skill_paths=["/skill1", "/skill2"],
            analyze_structure=True,
            analyze_complexity=False,
            analyze_quality=True,
        )

        assert len(input_data.skill_paths) == 2
        assert input_data.analyze_structure is True
        assert input_data.analyze_complexity is False


class TestConcurrencyLimit:
    """并发限制测试."""

    @pytest.mark.asyncio
    async def test_concurrent_limit(self):
        """测试并发限制."""
        call_count = 0
        max_concurrent = 0

        async def mock_validate(path, **kwargs):
            nonlocal call_count, max_concurrent
            call_count += 1
            current_concurrent = call_count
            if current_concurrent > max_concurrent:
                max_concurrent = current_concurrent
            await asyncio.sleep(0.01)
            current_concurrent -= 1
            return {"success": True}

        import skill_creator_mcp.server
        original = skill_creator_mcp.server.validate_skill
        skill_creator_mcp.server.validate_skill = mock_validate

        try:
            result = await batch_validate_skills(
                skill_paths=["/skill1", "/skill2", "/skill3", "/skill4"],
                concurrent_limit=2,
            )

            # 验证并发限制生效
            assert max_concurrent <= 2
            # 验证结果数量
            assert len(result.results) == 4
        finally:
            skill_creator_mcp.server.validate_skill = original
