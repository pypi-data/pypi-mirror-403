"""Skill tools for Agent-Skill operations.

This module contains MCP tools for creating, validating, analyzing,
and refactoring Agent-Skills.
"""

from pathlib import Path
from typing import Any

from fastmcp import Context

from ..utils import skill_generators
from ..utils.analyzers import (
    _analyze_complexity,
    _analyze_quality,
    _analyze_structure,
    _generate_analysis_summary,
    _generate_suggestions,
)
from ..utils.file_ops import create_directory_structure_async, write_file_async
from ..utils.refactorors import (
    estimate_refactor_effort,
    generate_refactor_report,
    generate_refactor_suggestions,
)
from ..utils.validators import (
    _validate_naming,
    _validate_skill_md,
    _validate_structure,
    _validate_template_requirements,
)


def _generate_skill_md_content(name: str, template: str) -> str:
    """生成 SKILL.md 内容."""
    return skill_generators._generate_skill_md_content(name, template)


async def _create_reference_files(skill_dir: Path, template_type: str) -> None:
    """创建引用文件."""
    await skill_generators._create_reference_files(skill_dir, template_type)


async def _create_example_scripts(skill_dir: Path) -> None:
    """创建示例脚本."""
    await skill_generators._create_example_scripts(skill_dir)


async def _create_example_examples(skill_dir: Path, name: str) -> None:
    """创建使用示例."""
    await skill_generators._create_example_examples(skill_dir, name)


async def init_skill(
    ctx: Context,
    name: str,
    template: str = "minimal",
    output_dir: str | None = None,
    with_scripts: bool = False,
    with_examples: bool = False,
) -> dict[str, Any]:
    """
    初始化新的 Agent-Skill.

    创建符合规范的技能目录结构和模板文件。

    Args:
        ctx: MCP 上下文
        name: 技能名称（小写字母、数字、连字符，1-64字符）
        template: 模板类型（minimal/tool-based/workflow-based/analyzer-based）
        output_dir: 输出目录路径（可选，优先级：参数 > 环境变量 SKILL_CREATOR_OUTPUT_DIR > 默认值）
        with_scripts: 是否包含示例脚本
        with_examples: 是否包含使用示例

    Returns:
        包含创建结果的字典（Pydantic 模型的 JSON 序列化）
    """
    from ..config import get_config
    from ..models.skill_config import InitResult, InitSkillInput

    try:
        # 优先级：工具参数 > 环境变量 > 默认值
        config = get_config()
        if output_dir is None:
            output_dir = str(config.output_dir)

        # 使用 Pydantic model_validate 方法进行输入验证
        # 这种方法可以处理类型转换和验证，避免静态类型检查错误
        input_data = InitSkillInput.model_validate(
            {
                "name": name,
                "template": template,
                "output_dir": output_dir,
                "with_scripts": with_scripts,
                "with_examples": with_examples,
            }
        )

        # 使用验证后的数据
        skill_dir = await create_directory_structure_async(
            name=input_data.name,
            template_type=input_data.template,
            output_dir=Path(input_data.output_dir),
        )

        # 3. 生成 SKILL.md 内容
        skill_md_content = _generate_skill_md_content(input_data.name, input_data.template)
        await write_file_async(
            skill_dir / "SKILL.md",
            skill_md_content,
        )

        # 4. 创建引用文件（非 minimal 模板）
        if input_data.template != "minimal":
            await _create_reference_files(skill_dir, input_data.template)

        # 5. 创建示例脚本
        if input_data.with_scripts:
            await _create_example_scripts(skill_dir)

        # 6. 创建使用示例
        if input_data.with_examples:
            await _create_example_examples(skill_dir, input_data.name)

        result = InitResult(
            success=True,
            skill_path=str(skill_dir),
            skill_name=input_data.name,
            template=input_data.template,
            message=f"技能 '{input_data.name}' 已创建在：{skill_dir}",
            next_steps=[
                f"1. 编辑 {skill_dir / 'SKILL.md'} 完善技能描述",
                f"2. 运行验证：python scripts/validate.py {skill_dir}",
            ],
        )
        return {"success": True, **result.model_dump()}

    except ValueError as e:
        # 错误情况下使用默认模板 "minimal"
        result = InitResult(
            success=False,
            skill_path="",
            skill_name=name if name else "",
            template="minimal",
            message=f"验证失败: {e}",
            next_steps=[],
            error=str(e),
            error_type="validation_error",
        )
        return {"success": False, **result.model_dump()}

    except Exception as e:
        # 错误情况下使用默认模板 "minimal"
        result = InitResult(
            success=False,
            skill_path="",
            skill_name=name if name else "",
            template="minimal",
            message=f"内部错误: {e}",
            next_steps=[],
            error=str(e),
            error_type="internal_error",
        )
        return {"success": False, **result.model_dump()}


async def validate_skill(
    ctx: Context,
    skill_path: str,
    check_structure: bool = True,
    check_content: bool = True,
) -> dict[str, Any]:
    """
    验证 Agent-Skill 的结构和内容.

    Args:
        ctx: MCP 上下文
        skill_path: 技能目录路径
        check_structure: 是否检查目录结构
        check_content: 是否检查内容格式

    Returns:
        包含验证结果的字典（Pydantic 模型的 JSON 序列化）
    """
    from ..models.skill_config import ValidateSkillInput, ValidationResult

    try:
        # 使用 Pydantic 验证输入参数
        input_data = ValidateSkillInput.model_validate(
            {
                "skill_path": skill_path,
                "check_structure": check_structure,
                "check_content": check_content,
            }
        )

        skill_dir = Path(input_data.skill_path)

        # 初始化结果
        errors = []
        warnings = []
        checks = {}
        template_type = None
        skill_name = skill_dir.name

        # 检查目录是否存在
        if not skill_dir.exists():
            result = ValidationResult(
                valid=False,
                skill_path=skill_path,
                skill_name=skill_name,
                errors=[f"目录不存在: {skill_path}"],
                warnings=[],
                checks={},
            )
            return {"success": False, **result.model_dump()}

        if not skill_dir.is_dir():
            result = ValidationResult(
                valid=False,
                skill_path=skill_path,
                skill_name=skill_name,
                errors=[f"路径不是目录: {skill_path}"],
                warnings=[],
                checks={},
            )
            return {"success": False, **result.model_dump()}

        # 1. 检查目录结构
        if input_data.check_structure:
            structure_errors = _validate_structure(skill_dir)
            errors.extend(structure_errors)
            checks["structure"] = len(structure_errors) == 0

        # 2. 检查命名规范
        naming_errors = _validate_naming(skill_dir)
        errors.extend(naming_errors)
        checks["naming"] = len(naming_errors) == 0

        # 3. 检查内容格式
        if input_data.check_content:
            content_errors, content_warnings, detected_template = _validate_skill_md(skill_dir)
            errors.extend(content_errors)
            warnings.extend(content_warnings)
            checks["content"] = len(content_errors) == 0

            # 确保 template_type 类型正确
            if detected_template and detected_template in (
                "minimal",
                "tool-based",
                "workflow-based",
                "analyzer-based",
            ):
                template_type = detected_template  # type: ignore[assignment]

            # 4. 检查模板特定要求
            if template_type:
                template_errors = _validate_template_requirements(skill_dir, template_type)
                errors.extend(template_errors)
                checks["template_requirements"] = len(template_errors) == 0

        # 判断验证是否通过
        valid = len(errors) == 0

        result = ValidationResult(
            valid=valid,
            skill_path=str(skill_dir),
            skill_name=skill_name,
            template_type=template_type,  # type: ignore[arg-type]
            errors=errors,
            warnings=warnings,
            checks=checks,
        )

        return {
            "success": True,
            "message": "验证通过" if valid else f"验证失败，发现 {len(errors)} 个错误",
            **result.model_dump(),
        }

    except Exception as e:
        result = ValidationResult(
            valid=False,
            skill_path=skill_path,
            errors=[f"验证过程出错: {e}"],
            warnings=[],
            checks={},
        )
        return {"success": False, "error_type": "internal_error", **result.model_dump()}


async def _perform_analysis(
    skill_dir: Path,
    analyze_structure: bool,
    analyze_complexity: bool,
    analyze_quality: bool,
) -> tuple[Any, Any, Any]:
    """
    执行完整的技能分析（公共逻辑）.

    这个函数被 analyze_skill 和 refactor_skill 共同使用，
    避免代码重复。

    Args:
        skill_dir: 技能目录路径
        analyze_structure: 是否分析代码结构
        analyze_complexity: 是否分析代码复杂度
        analyze_quality: 是否分析代码质量

    Returns:
        包含 (structure, complexity, quality) 的元组
    """
    from ..models.skill_config import (
        ComplexityMetrics,
        QualityScore,
        StructureAnalysis,
    )

    # 1. 结构分析（异步）
    if analyze_structure:
        structure = await _analyze_structure(skill_dir)
    else:
        structure = StructureAnalysis(total_files=0, total_lines=0, file_breakdown={})

    # 2. 复杂度分析（异步）
    if analyze_complexity:
        complexity = await _analyze_complexity(skill_dir)
    else:
        complexity = ComplexityMetrics(
            cyclomatic_complexity=None,
            maintainability_index=None,
            code_duplication=None,
        )

    # 3. 质量分析（异步）
    if analyze_quality:
        quality = await _analyze_quality(skill_dir)
    else:
        quality = QualityScore(
            overall_score=0.0,
            structure_score=0.0,
            documentation_score=0.0,
            test_coverage_score=0.0,
        )

    return structure, complexity, quality


async def analyze_skill(
    ctx: Context,
    skill_path: str,
    analyze_structure: bool = True,
    analyze_complexity: bool = True,
    analyze_quality: bool = True,
) -> dict[str, Any]:
    """
    分析 Agent-Skill 的代码质量和结构.

    Args:
        ctx: MCP 上下文
        skill_path: 技能目录路径
        analyze_structure: 是否分析代码结构
        analyze_complexity: 是否分析代码复杂度
        analyze_quality: 是否分析代码质量

    Returns:
        包含分析结果的字典（Pydantic 模型的 JSON 序列化）
    """
    from ..models.skill_config import (
        AnalyzeResult,
        AnalyzeSkillInput,
    )

    try:
        # 使用 Pydantic 验证输入参数
        input_data = AnalyzeSkillInput.model_validate(
            {
                "skill_path": skill_path,
                "analyze_structure": analyze_structure,
                "analyze_complexity": analyze_complexity,
                "analyze_quality": analyze_quality,
            }
        )

        skill_dir = Path(input_data.skill_path)

        # 检查目录是否存在
        if not skill_dir.exists():
            return {
                "success": False,
                "error": f"目录不存在: {skill_path}",
                "error_type": "path_error",
            }

        if not skill_dir.is_dir():
            return {
                "success": False,
                "error": f"路径不是目录: {skill_path}",
                "error_type": "path_error",
            }

        # 使用公共分析函数执行分析
        structure, complexity, quality = await _perform_analysis(
            skill_dir,
            input_data.analyze_structure,
            input_data.analyze_complexity,
            input_data.analyze_quality,
        )

        # 生成改进建议
        suggestions = _generate_suggestions(structure, complexity, quality)

        # 创建 AnalyzeResult 模型实例
        result = AnalyzeResult(
            skill_path=str(skill_dir),
            skill_name=skill_dir.name,
            structure=structure,
            complexity=complexity,
            quality=quality,
            suggestions=suggestions,
        )

        return {
            "success": True,
            "summary": _generate_analysis_summary(quality, complexity),
            **result.model_dump(),
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"分析过程出错: {e}",
            "error_type": "internal_error",
        }


async def refactor_skill(
    ctx: Context,
    skill_path: str,
    focus: list[str] | None = None,
    analyze_structure: bool = True,
    analyze_complexity: bool = True,
    analyze_quality: bool = True,
) -> dict[str, Any]:
    """
    生成 Agent-Skill 的重构建议.

    基于代码分析生成具体的重构建议，包括优先级、影响评估和工作量估算。

    Args:
        ctx: MCP 上下文
        skill_path: 技能目录路径
        focus: 重点关注领域（可选，如 structure、documentation、testing）
        analyze_structure: 是否分析代码结构
        analyze_complexity: 是否分析代码复杂度
        analyze_quality: 是否分析代码质量

    Returns:
        包含重构建议的字典
    """
    from ..models.skill_config import (
        RefactorResult,
        RefactorSkillInput,
    )

    try:
        # 使用 Pydantic 验证输入参数
        input_data = RefactorSkillInput.model_validate(
            {
                "skill_path": skill_path,
                "focus": focus,
                "analyze_structure": analyze_structure,
                "analyze_complexity": analyze_complexity,
                "analyze_quality": analyze_quality,
            }
        )

        skill_dir = Path(input_data.skill_path)

        # 检查目录是否存在
        if not skill_dir.exists():
            return {
                "success": False,
                "error": f"目录不存在: {skill_path}",
                "error_type": "path_error",
            }

        if not skill_dir.is_dir():
            return {
                "success": False,
                "error": f"路径不是目录: {skill_path}",
                "error_type": "path_error",
            }

        # 使用公共分析函数执行分析
        structure, complexity, quality = await _perform_analysis(
            skill_dir,
            input_data.analyze_structure,
            input_data.analyze_complexity,
            input_data.analyze_quality,
        )

        # 生成重构建议
        suggestions = generate_refactor_suggestions(
            skill_dir, structure, complexity, quality, input_data.focus
        )

        # 5. 生成重构报告
        report = generate_refactor_report(
            str(skill_dir), structure, complexity, quality, suggestions
        )

        # 6. 估算工作量
        effort = estimate_refactor_effort(suggestions)

        # 创建 RefactorResult 模型实例
        result = RefactorResult(
            success=True,
            skill_path=str(skill_dir),
            skill_name=skill_dir.name,
            structure=structure,
            complexity=complexity,
            quality=quality,
            suggestions=suggestions,  # type: ignore[arg-type]
            report=report,
            effort_estimate=effort,
        )

        return {"success": True, **result.model_dump()}

    except Exception as e:
        return {
            "success": False,
            "error": f"重构分析出错: {e}",
            "error_type": "internal_error",
        }


__all__ = [
    "init_skill",
    "validate_skill",
    "analyze_skill",
    "refactor_skill",
    # 辅助函数（供测试使用）
    "_generate_skill_md_content",
    "_create_reference_files",
    "_create_example_scripts",
    "_create_example_examples",
]
