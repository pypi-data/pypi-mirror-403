"""批量操作工具.

提供批量验证、批量分析等功能，使用异步处理提高性能。
"""

import asyncio
from typing import Any

from pydantic import BaseModel, Field

from skill_creator_mcp.logging_config import get_logger

logger = get_logger(__name__)


class BatchValidationInput(BaseModel):
    """批量验证输入."""

    skill_paths: list[str] = Field(..., description="技能目录路径列表")
    check_structure: bool = Field(default=True, description="是否检查目录结构")
    check_content: bool = Field(default=True, description="是否检查内容格式")


class BatchValidationResult(BaseModel):
    """批量验证结果."""

    results: list[dict[str, Any]] = Field(description="每个技能的验证结果")
    summary: dict[str, Any] = Field(description="汇总信息")


class BatchAnalysisInput(BaseModel):
    """批量分析输入."""

    skill_paths: list[str] = Field(..., description="技能目录路径列表")
    analyze_structure: bool = Field(default=True, description="是否分析代码结构")
    analyze_complexity: bool = Field(default=True, description="是否分析代码复杂度")
    analyze_quality: bool = Field(default=True, description="是否分析代码质量")


class BatchAnalysisResult(BaseModel):
    """批量分析结果."""

    results: list[dict[str, Any]] = Field(description="每个技能的分析结果")
    summary: dict[str, Any] = Field(description="汇总信息")


async def batch_validate_skills(
    skill_paths: list[str],
    check_structure: bool = True,
    check_content: bool = True,
    concurrent_limit: int = 5,
) -> BatchValidationResult:
    """批量验证技能.

    Args:
        skill_paths: 技能目录路径列表
        check_structure: 是否检查目录结构
        check_content: 是否检查内容格式
        concurrent_limit: 并发限制

    Returns:
        批量验证结果
    """
    logger.info(f"Starting batch validation of {len(skill_paths)} skills")

    # 创建信号量限制并发数
    semaphore = asyncio.Semaphore(concurrent_limit)

    async def validate_one(path: str) -> dict[str, Any]:
        async with semaphore:
            try:
                logger.info(f"Validating: {path}")
                # 调用验证函数
                from skill_creator_mcp.server import validate_skill

                result = await validate_skill(  # type: ignore[operator]
                    skill_path=path,
                    check_structure=check_structure,
                    check_content=check_content,
                )
                return {
                    "skill_path": path,
                    "success": True,
                    "result": result,
                }
            except Exception as e:
                logger.error(f"Error validating {path}: {e}")
                return {
                    "skill_path": path,
                    "success": False,
                    "error": str(e),
                }

    # 并发执行验证
    results = await asyncio.gather(*[validate_one(path) for path in skill_paths])

    # 计算汇总信息
    success_count = sum(1 for r in results if r.get("success"))
    total_count = len(results)

    summary = {
        "total": total_count,
        "successful": success_count,
        "failed": total_count - success_count,
        "success_rate": success_count / total_count * 100 if total_count > 0 else 0,
    }

    logger.info(f"Batch validation complete: {success_count}/{total_count} successful")

    return BatchValidationResult(results=results, summary=summary)


async def batch_analyze_skills(
    skill_paths: list[str],
    analyze_structure: bool = True,
    analyze_complexity: bool = True,
    analyze_quality: bool = True,
    concurrent_limit: int = 5,
) -> BatchAnalysisResult:
    """批量分析技能.

    Args:
        skill_paths: 技能目录路径列表
        analyze_structure: 是否分析代码结构
        analyze_complexity: 是否分析代码复杂度
        analyze_quality: 是否分析代码质量
        concurrent_limit: 并发限制

    Returns:
        批量分析结果
    """
    logger.info(f"Starting batch analysis of {len(skill_paths)} skills")

    semaphore = asyncio.Semaphore(concurrent_limit)

    async def analyze_one(path: str) -> dict[str, Any]:
        async with semaphore:
            try:
                logger.info(f"Analyzing: {path}")
                # 调用分析函数
                from skill_creator_mcp.server import analyze_skill

                result = await analyze_skill(  # type: ignore[operator]
                    skill_path=path,
                    analyze_structure=analyze_structure,
                    analyze_complexity=analyze_complexity,
                    analyze_quality=analyze_quality,
                )
                return {
                    "skill_path": path,
                    "success": True,
                    "result": result,
                }
            except Exception as e:
                logger.error(f"Error analyzing {path}: {e}")
                return {
                    "skill_path": path,
                    "success": False,
                    "error": str(e),
                }

    # 并发执行分析
    results = await asyncio.gather(*[analyze_one(path) for path in skill_paths])

    # 计算汇总信息
    success_count = sum(1 for r in results if r.get("success"))

    summary = {
        "total": len(results),
        "successful": success_count,
        "failed": len(results) - success_count,
        "success_rate": success_count / len(results) * 100 if results else 0,
    }

    logger.info(f"Batch analysis complete: {success_count}/{len(results)} successful")

    return BatchAnalysisResult(results=results, summary=summary)


def batch_validate_skills_sync(
    skill_paths: list[str],
    check_structure: bool = True,
    check_content: bool = True,
) -> BatchValidationResult:
    """批量验证技能（同步版本）.

    Args:
        skill_paths: 技能目录路径列表
        check_structure: 是否检查目录结构
        check_content: 是否检查内容格式

    Returns:
        批量验证结果
    """
    return asyncio.run(
        batch_validate_skills(
            skill_paths=skill_paths,
            check_structure=check_structure,
            check_content=check_content,
        )
    )


def batch_analyze_skills_sync(
    skill_paths: list[str],
    analyze_structure: bool = True,
    analyze_complexity: bool = True,
    analyze_quality: bool = True,
) -> BatchAnalysisResult:
    """批量分析技能（同步版本）.

    Args:
        skill_paths: 技能目录路径列表
        analyze_structure: 是否分析代码结构
        analyze_complexity: 是否分析代码复杂度
        analyze_quality: 是否分析代码质量

    Returns:
        批量分析结果
    """
    return asyncio.run(
        batch_analyze_skills(
            skill_paths=skill_paths,
            analyze_structure=analyze_structure,
            analyze_complexity=analyze_complexity,
            analyze_quality=analyze_quality,
        )
    )
