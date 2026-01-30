"""Skill Creator MCP Server.

这是一个基于 FastMCP SDK 开发的 MCP Server，用于创建、验证、
分析和重构 Agent-Skills。
"""

from pathlib import Path
from typing import Any

from fastmcp import Context, FastMCP

from .prompts import (
    get_create_skill_prompt,
    get_refactor_skill_prompt,
    get_validate_skill_prompt,
)
from .resources import (
    get_best_practices,
    get_template_content,
    get_validation_rules,
    list_templates,
)
from .tools.batch_operations import (
    batch_analyze_skills,
    batch_validate_skills,
)
from .tools.health_check import (
    get_quick_status,
    health_check,
    is_healthy,
)

# 新模块导入（第二阶段重构：替换函数体）
# 使用模块导入避免函数名冲突
from .utils import skill_generators, testing
from .utils.analyzers import (
    _analyze_complexity,
    _analyze_quality,
    _analyze_structure,
    _generate_analysis_summary,
    _generate_suggestions,
)
from .utils.file_ops import create_directory_structure_async, write_file_async
from .utils.packagers import package_agent_skill as package_agent_skill_impl
from .utils.packagers import package_skill as package_skill_impl
from .utils.refactorors import (
    estimate_refactor_effort,
    generate_refactor_report,
    generate_refactor_suggestions,
)
from .utils.requirement_collection import (
    _collect_with_elicit,
    _get_requirement_mode_steps,
    _get_requirement_next_question,
    _handle_requirement_previous_action,
    _handle_requirement_start_action,
    _handle_requirement_status_action,
    _process_requirement_user_answer,
    _validate_and_init_requirement_session,
)
from .utils.validators import (
    _validate_naming,
    _validate_skill_md,
    _validate_structure,
    _validate_template_requirements,
)

# 创建 MCP Server
mcp = FastMCP(
    name="skill-creator",
    instructions="""
    Skill Creator MCP Server - Agent-Skills 开发工具

    这个服务器提供创建、验证、分析、重构和打包 Agent-Skills 的工具。

    ## 可用工具

    ### init_skill
    初始化新的 Agent-Skill。

    参数：
    - name (str): 技能名称（小写字母、数字、连字符，1-64字符）
    - template (str): 模板类型（minimal/tool-based/workflow-based/analyzer-based）
    - output_dir (str): 输出目录路径
    - with_scripts (bool): 是否包含示例脚本
    - with_examples (bool): 是否包含使用示例

    ### validate_skill
    验证 Agent-Skill 的结构和内容。

    参数：
    - skill_path (str): 技能目录路径
    - check_structure (bool): 是否检查目录结构（默认 True）
    - check_content (bool): 是否检查内容格式（默认 True）

    ### analyze_skill
    分析 Agent-Skill 的代码质量、复杂度和结构。

    参数：
    - skill_path (str): 技能目录路径
    - analyze_structure (bool): 是否分析代码结构（默认 True）
    - analyze_complexity (bool): 是否分析代码复杂度（默认 True）
    - analyze_quality (bool): 是否分析代码质量（默认 True）

    ### refactor_skill
    生成 Agent-Skill 的重构建议。

    参数：
    - skill_path (str): 技能目录路径
    - focus (list[str]): 重点关注领域（可选，如 structure、documentation、testing）
    - analyze_structure (bool): 是否分析代码结构（默认 True）
    - analyze_complexity (bool): 是否分析代码复杂度（默认 True）
    - analyze_quality (bool): 是否分析代码质量（默认 True）

    ### package_skill
    打包 Agent-Skill 为分发格式。

    参数：
    - skill_path (str): 技能目录路径
    - output_dir (str): 输出目录路径（默认：当前目录）
    - format (str): 打包格式（zip/tar.gz/tar.bz2，默认：zip）
    - include_tests (bool): 是否包含测试文件（默认：True）
    - validate_before_package (bool): 打包前是否验证（默认：True）

    ### package_agent_skill
    打包 Agent-Skill 为标准分发格式（推荐使用）。

    与 package_skill 的区别：
    - 使用更严格的排除模式
    - 支持版本号参数，生成标准化包名
    - 默认不包含测试文件
    - 确保符合 Agent-Skill 规范

    参数：
    - skill_path (str): Agent-Skill 目录路径
    - output_dir (str): 输出目录路径（默认：当前目录）
    - version (str): 版本号（可选，格式如 "0.3.1"）
    - format (str): 打包格式（zip/tar.gz/tar.bz2，默认：zip）
    - include_tests (bool): 是否包含测试文件（默认：False）
    - validate_before_package (bool): 打包前是否验证（默认：True）
    """,
)


@mcp.tool()
async def init_skill(
    ctx: Context,
    name: str,
    template: str = "minimal",
    output_dir: str = ".",
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
        output_dir: 输出目录路径
        with_scripts: 是否包含示例脚本
        with_examples: 是否包含使用示例

    Returns:
        包含创建结果的字典（Pydantic 模型的 JSON 序列化）
    """
    from .models.skill_config import InitResult, InitSkillInput

    try:
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


@mcp.tool()
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
    from .models.skill_config import ValidateSkillInput, ValidationResult

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
            if detected_template and detected_template in ("minimal", "tool-based", "workflow-based", "analyzer-based"):
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

        return {"success": True, "message": "验证通过" if valid else f"验证失败，发现 {len(errors)} 个错误", **result.model_dump()}

    except Exception as e:
        result = ValidationResult(
            valid=False,
            skill_path=skill_path,
            errors=[f"验证过程出错: {e}"],
            warnings=[],
            checks={},
        )
        return {"success": False, "error_type": "internal_error", **result.model_dump()}


@mcp.tool()
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
    from .models.skill_config import (
        AnalyzeResult,
        AnalyzeSkillInput,
        ComplexityMetrics,
        QualityScore,
        StructureAnalysis,
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

        # 1. 结构分析（异步）
        if input_data.analyze_structure:
            structure = await _analyze_structure(skill_dir)
        else:
            from .models.skill_config import StructureAnalysis

            structure = StructureAnalysis(total_files=0, total_lines=0, file_breakdown={})

        # 2. 复杂度分析（异步）
        if input_data.analyze_complexity:
            complexity = await _analyze_complexity(skill_dir)
        else:
            from .models.skill_config import ComplexityMetrics

            complexity = ComplexityMetrics(
                cyclomatic_complexity=None,
                maintainability_index=None,
                code_duplication=None,
            )

        # 3. 质量分析（异步）
        if input_data.analyze_quality:
            quality = await _analyze_quality(skill_dir)
        else:
            # 如果不分析质量，使用默认值
            quality = QualityScore(
                overall_score=0.0,
                structure_score=0.0,
                documentation_score=0.0,
                test_coverage_score=0.0,
            )

        # 4. 生成改进建议
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


@mcp.tool()
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
    from .models.skill_config import RefactorResult, RefactorSkillInput

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

        # 1. 结构分析（异步）
        if input_data.analyze_structure:
            structure = await _analyze_structure(skill_dir)
        else:
            from .models.skill_config import StructureAnalysis

            structure = StructureAnalysis(total_files=0, total_lines=0, file_breakdown={})

        # 2. 复杂度分析（异步）
        if input_data.analyze_complexity:
            complexity = await _analyze_complexity(skill_dir)
        else:
            from .models.skill_config import ComplexityMetrics

            complexity = ComplexityMetrics(
                cyclomatic_complexity=None,
                maintainability_index=None,
                code_duplication=None,
            )

        # 3. 质量分析（异步）
        if input_data.analyze_quality:
            quality = await _analyze_quality(skill_dir)
        else:
            from .models.skill_config import QualityScore

            quality = QualityScore(
                overall_score=0.0,
                structure_score=0.0,
                documentation_score=0.0,
                test_coverage_score=0.0,
            )

        # 4. 生成重构建议
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


@mcp.tool()
async def package_skill(
    ctx: Context,
    skill_path: str,
    output_dir: str = ".",
    format: str = "zip",
    include_tests: bool = True,
    validate_before_package: bool = True,
) -> dict[str, Any]:
    """
    打包 Agent-Skill 为分发格式.

    创建包含技能文件的压缩包，支持 zip、tar.gz 和 tar.bz2 格式。

    Args:
        ctx: MCP 上下文
        skill_path: 技能目录路径
        output_dir: 输出目录路径
        format: 打包格式（zip/tar.gz/tar.bz2）
        include_tests: 是否包含测试文件
        validate_before_package: 打包前是否验证

    Returns:
        包含打包结果的字典
    """
    from pydantic import ValidationError

    from .models.skill_config import PackageSkillInput

    try:
        # 使用 Pydantic 验证输入参数
        # 注意：format 是 Python 保留字，在模型中映射到 format 字段
        input_data = PackageSkillInput.model_validate(
            {
                "skill_path": skill_path,
                "output_dir": output_dir,
                "format": format,
                "include_tests": include_tests,
                "validate_before_package": validate_before_package,
            }
        )

        # 调用打包函数
        result = package_skill_impl(
            skill_path=input_data.skill_path,
            output_dir=input_data.output_dir,
            package_format=input_data.format,
            include_tests=input_data.include_tests,
            validate_before_package=input_data.validate_before_package,
        )

        # 转换为字典格式返回
        return {
            "success": result.success,
            "skill_path": result.skill_path,
            "package_path": result.package_path,
            "format": result.format,
            "files_included": result.files_included,
            "package_size": result.package_size,
            "validation_passed": result.validation_passed,
            "validation_errors": result.validation_errors,
            "error": result.error,
            "error_type": result.error_type,
        }

    except ValidationError as e:
        # 检查是否是 format 字段的验证错误
        errors = e.errors()
        for error in errors:
            if error.get("loc") == ("format",):
                return {
                    "success": False,
                    "error": f"无效的打包格式: {format}",
                    "error_type": "format_error",
                }
        # 其他验证错误
        return {
            "success": False,
            "error": f"输入验证失败: {e}",
            "error_type": "validation_error",
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"打包过程出错: {e}",
            "error_type": "internal_error",
        }


@mcp.tool()
async def package_agent_skill(
    ctx: Context,
    skill_path: str,
    output_dir: str = ".",
    version: str | None = None,
    format: str = "zip",
    include_tests: bool = False,
    validate_before_package: bool = True,
) -> dict[str, Any]:
    """
    打包 Agent-Skill 为标准分发格式.

    这是专门用于打包标准 Agent-Skill 的函数。
    与 package_skill 的区别：
    - 使用更严格的排除模式
    - 支持版本号参数，生成标准化包名
    - 默认不包含测试文件
    - 确保符合 Agent-Skill 规范

    Args:
        ctx: MCP 上下文
        skill_path: Agent-Skill 目录路径
        output_dir: 输出目录路径
        version: 版本号（可选，格式如 "0.3.1"）
        format: 打包格式（zip/tar.gz/tar.bz2）
        include_tests: 是否包含测试文件（默认 False）
        validate_before_package: 打包前是否验证

    Returns:
        包含打包结果的字典

    Examples:
        >>> result = await package_agent_skill(
        ...     ctx,
        ...     skill_path="/path/to/skill-creator",
        ...     output_dir="/output",
        ...     version="0.3.1",
        ...     format="zip"
        ... )
        >>> # 生成: skill-creator-v0.3.1.zip
    """
    from pydantic import ValidationError

    try:
        # 调用打包函数
        result = package_agent_skill_impl(
            skill_path=skill_path,
            output_dir=output_dir,
            version=version,
            package_format=format,
            include_tests=include_tests,
            validate_before_package=validate_before_package,
        )

        # 转换为字典格式返回
        return {
            "success": result.success,
            "skill_path": result.skill_path,
            "package_path": result.package_path,
            "format": result.format,
            "files_included": result.files_included,
            "package_size": result.package_size,
            "validation_passed": result.validation_passed,
            "validation_errors": result.validation_errors,
            "error": result.error,
            "error_type": result.error_type,
        }

    except ValidationError as e:
        return {
            "success": False,
            "error": f"输入验证失败: {e}",
            "error_type": "validation_error",
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"打包过程出错: {e}",
            "error_type": "internal_error",
        }


# ==================== 需求收集工具 ====================
# 常量 (BASIC_REQUIREMENT_STEPS, COMPLETE_REQUIREMENT_STEPS) 已在文件顶部导入


@mcp.tool()
async def collect_requirements(
    ctx: Context,
    action: str = "start",
    mode: str = "basic",
    session_id: str | None = None,
    user_input: str | None = None,
    use_elicit: bool = False,
) -> dict[str, Any]:
    """
    AI 驱动的需求澄清/收集工具.

    通过对话方式逐步收集创建 Agent-Skill 所需的关键信息。
    支持 session state 管理，可以中断后恢复。

    Args:
        ctx: MCP 上下文
        action: 执行动作（start=开始，next=下一步，previous=上一步，status=查询状态，complete=完成）
        mode: 收集模式（basic=基础5步，complete=完整10步，brainstorm=头脑风暴，progressive=渐进式）
        session_id: 会话ID（自动生成，用于多轮对话）
        user_input: 用户输入（用于 next/complete 动作，use_elicit=False 时使用）
        use_elicit: 是否使用 ctx.elicit() 自动收集输入（默认 False）。True 时会自动调用
                   ctx.elicit() 收集所有必需的输入，无需手动调用 action="next"。

    Returns:
        包含收集结果的字典

    Examples:
        传统模式（两步调用）:
            # 获取第一个问题
            result = await collect_requirements(ctx, action="start", mode="basic")
            # 提供答案并获取下一个问题
            result = await collect_requirements(ctx, action="next", user_input="my-skill")

        Elicit 模式（一步调用）:
            # 自动收集所有输入
            result = await collect_requirements(ctx, action="start", mode="basic", use_elicit=True)
    """
    try:
        # 1. 验证输入参数并初始化会话状态
        (
            input_data,
            is_dynamic_mode,
            total_steps,
            current_session_id,
            session_state,
        ) = await _validate_and_init_requirement_session(ctx, action, mode, session_id, user_input)

        # 获取当前模式的步骤（静态模式）
        all_steps = _get_requirement_mode_steps(input_data.mode) if not is_dynamic_mode else None

        # 2. Elicit 模式：自动收集所有输入
        if use_elicit and input_data.action == "start":
            # 首先检测客户端是否支持 elicitation
            from .utils.capability_detection import check_elicitation_capability
            capability = await check_elicitation_capability(ctx)
            if not capability.get("supported"):
                return {
                    "success": False,
                    "error": "elicit_mode_not_supported",
                    "message": "当前 MCP 客户端不支持交互式输入模式 (use_elicit=True)。",
                    "fallback_mode": "traditional",
                    "traditional_usage": {
                        "step_1": "调用 collect_requirements(action='start', mode='basic')",
                        "step_2": "使用返回的 session_id 调用 collect_requirements(action='next', session_id='...', user_input='...')",
                        "step_3": "重复步骤 2 直到所有问题完成",
                        "example": {
                            "start": "collect_requirements(action='start', mode='basic')",
                            "next": "collect_requirements(action='next', session_id='req_xxx', user_input='my-skill')",
                        }
                    },
                    "capability_error": capability.get("error"),
                    "details": capability.get("details"),
                }
            return await _collect_with_elicit(
                ctx=ctx,
                session_state=session_state,
                current_session_id=current_session_id,
                is_dynamic_mode=is_dynamic_mode,
                all_steps=all_steps,
                input_data=input_data,
            )

        # 3. 处理不同的 action
        if input_data.action == "status":
            return _handle_requirement_status_action(
                session_state, current_session_id, is_dynamic_mode
            )

        elif input_data.action == "previous":
            return await _handle_requirement_previous_action(
                ctx, session_state, current_session_id, is_dynamic_mode, all_steps
            )

        elif input_data.action == "start":
            # 开始新会话或重置
            await _handle_requirement_start_action(
                ctx, session_state, current_session_id, total_steps, input_data.mode
            )

        # 4. 处理用户输入（next/complete action）
        if input_data.action in ("next", "complete") and input_data.user_input:
            # 获取当前步骤（仅静态模式需要）
            current_step = None
            if not is_dynamic_mode and all_steps:
                from .models.skill_config import RequirementStep, ValidationRule
                if session_state.current_step_index < len(all_steps):
                    step_data = all_steps[session_state.current_step_index]
                    validation_data: dict[str, Any] = dict(step_data["validation"])  # type: ignore[arg-type]
                    current_step = RequirementStep(
                        key=str(step_data["key"]),
                        title=str(step_data["title"]),
                        prompt=str(step_data["prompt"]),
                        validation=ValidationRule(**validation_data),
                    )

            result = await _process_requirement_user_answer(
                ctx=ctx,
                session_state=session_state,
                current_session_id=current_session_id,
                action=input_data.action,
                user_input=input_data.user_input,
                is_dynamic_mode=is_dynamic_mode,
                mode=input_data.mode,
                all_steps=all_steps,
                current_step=current_step.model_dump() if current_step else None,
            )

            # 如果处理完成或验证失败，直接返回
            if result.get("completed") or not result.get("success"):
                return result

            # 如果只是处理了用户输入（非完成），继续获取下一个问题
            if result.get("processed"):
                # 继续获取下一个问题
                pass

        # 5. 获取并返回下一个问题
        question_result = await _get_requirement_next_question(
            ctx=ctx,
            session_state=session_state,
            is_dynamic_mode=is_dynamic_mode,
            mode=input_data.mode,
            all_steps=all_steps,
        )

        # 添加会话信息到问题结果
        question_result["session_id"] = current_session_id
        question_result["action"] = input_data.action
        question_result["mode"] = session_state.mode

        return question_result

    except Exception as e:
        return {
            "success": False,
            "error": f"需求收集出错: {e}",
            "error_type": "internal_error",
            "message": f"内部错误: {e}",
        }


# ============================================================================
# Phase 0: 技术验证工具
# 这些工具用于验证 FastMCP Context API 的可用性
# ============================================================================


@mcp.tool()
async def check_client_capabilities(ctx: Context) -> dict[str, Any]:
    """检测 MCP 客户端的能力支持情况.

    检测客户端是否支持高级 MCP 功能，如 sampling 和 elicitation。

    Returns:
        包含客户端能力检测结果的字典
    """
    from .utils.capability_detection import get_client_capabilities

    return await get_client_capabilities(ctx)


@mcp.tool()
async def test_llm_sampling(ctx: Context, prompt: str) -> dict[str, Any]:
    """测试 LLM Sampling 能力.

    验证 MCP Server 可以通过 ctx.sample() 调用客户端 LLM。

    Args:
        ctx: MCP 上下文
        prompt: 要发送给 LLM 的提示文本

    Returns:
        包含测试结果的字典，包括 LLM 响应文本和历史记录
    """
    from .utils import testing

    return await testing.test_llm_sampling(ctx, prompt)


@mcp.tool()
async def test_user_elicitation(
    ctx: Context, prompt: str = "请提供技能名称（小写字母、数字、连字符）"
) -> dict[str, Any]:
    """测试用户征询 (User Elicitation) 能力.

    验证可以通过 ctx.elicit() 请求用户输入结构化数据。

    Args:
        ctx: MCP 上下文
        prompt: 向用户显示的提示文本

    Returns:
        包含测试结果的字典
    """
    return await testing.test_user_elicitation(ctx, prompt)


@mcp.tool()
async def test_conversation_loop(ctx: Context, user_input: str) -> dict[str, Any]:
    """测试对话循环和状态管理能力.

    验证可以在对话循环中使用 session state 保存历史，
    并且 LLM 可以利用对话历史生成更连贯的响应。

    Args:
        ctx: MCP 上下文
        user_input: 用户输入的文本

    Returns:
        包含测试结果的字典，包括 LLM 响应和会话状态
    """
    return await testing.test_conversation_loop(ctx, user_input)


@mcp.tool()
async def test_requirement_completeness(ctx: Context, requirement: str) -> dict[str, Any]:
    """测试需求完整性判断能力.

    验证 LLM 能够判断需求是否完整，并识别缺失的关键信息。

    Args:
        ctx: MCP 上下文
        requirement: 技能创建需求描述

    Returns:
        包含测试结果的字典，包括完整性分析和缺失信息列表
    """
    return await testing.test_requirement_completeness(ctx, requirement)


# ==================== 批量操作工具 ====================


@mcp.tool()
async def batch_validate_skills_tool(
    ctx: Context,
    skill_paths: list[str],
    check_structure: bool = True,
    check_content: bool = True,
    concurrent_limit: int = 5,
) -> dict[str, Any]:
    """批量验证多个Agent-Skill.

    并发验证多个技能的结构和内容，提高验证效率。

    Args:
        ctx: MCP 上下文
        skill_paths: 技能目录路径列表
        check_structure: 是否检查目录结构（默认 True）
        check_content: 是否检查内容格式（默认 True）
        concurrent_limit: 并发限制（默认 5）

    Returns:
        包含批量验证结果的字典，包括每个技能的验证结果和汇总信息
    """
    try:
        result = await batch_validate_skills(
            skill_paths=skill_paths,
            check_structure=check_structure,
            check_content=check_content,
            concurrent_limit=concurrent_limit,
        )
        return {
            "success": True,
            "results": result.results,
            "summary": result.summary,
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"批量验证出错: {e}",
            "error_type": "internal_error",
        }


@mcp.tool()
async def batch_analyze_skills_tool(
    ctx: Context,
    skill_paths: list[str],
    analyze_structure: bool = True,
    analyze_complexity: bool = True,
    analyze_quality: bool = True,
    concurrent_limit: int = 5,
) -> dict[str, Any]:
    """批量分析多个Agent-Skill.

    并发分析多个技能的代码质量、复杂度和结构。

    Args:
        ctx: MCP 上下文
        skill_paths: 技能目录路径列表
        analyze_structure: 是否分析代码结构（默认 True）
        analyze_complexity: 是否分析代码复杂度（默认 True）
        analyze_quality: 是否分析代码质量（默认 True）
        concurrent_limit: 并发限制（默认 5）

    Returns:
        包含批量分析结果的字典，包括每个技能的分析结果和汇总信息
    """
    try:
        result = await batch_analyze_skills(
            skill_paths=skill_paths,
            analyze_structure=analyze_structure,
            analyze_complexity=analyze_complexity,
            analyze_quality=analyze_quality,
            concurrent_limit=concurrent_limit,
        )
        return {
            "success": True,
            "results": result.results,
            "summary": result.summary,
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"批量分析出错: {e}",
            "error_type": "internal_error",
        }


# ==================== 健康检查工具 ====================


@mcp.tool()
async def health_check_tool(ctx: Context) -> dict[str, Any]:
    """执行完整健康检查.

    返回系统健康状态、系统指标、缓存指标和性能指标。

    Args:
        ctx: MCP 上下文

    Returns:
        包含完整健康检查结果的字典
    """
    try:
        result = health_check()
        return {
            "success": True,
            **result.model_dump(),
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"健康检查出错: {e}",
            "error_type": "internal_error",
        }


@mcp.tool()
async def quick_status_tool(ctx: Context) -> dict[str, Any]:
    """获取快速状态摘要.

    返回简化的系统状态信息字符串。

    Args:
        ctx: MCP 上下文

    Returns:
        包含状态摘要字符串的字典
    """
    try:
        status = get_quick_status()
        return {
            "success": True,
            "status": status,
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"获取状态出错: {e}",
            "error_type": "internal_error",
        }


@mcp.tool()
async def is_healthy_tool(ctx: Context) -> dict[str, Any]:
    """快速检查系统是否健康.

    返回布尔值表示系统健康状态。

    Args:
        ctx: MCP 上下文

    Returns:
        包含健康状态布尔值的字典
    """
    try:
        healthy = is_healthy()
        return {
            "success": True,
            "healthy": healthy,
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"健康检查出错: {e}",
            "error_type": "internal_error",
        }


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


# ==================== MCP Resources ====================


@mcp.resource("http://skills/schema/templates")
def list_templates_resource() -> str:
    """列出所有可用的技能模板."""
    templates = list_templates()
    result = "# 技能模板列表\n\n"
    for t in templates:
        result += f"## {t['type']}\n"
        result += f"{t['description']}\n\n"
    return result


@mcp.resource("http://skills/schema/templates/{type}")
def get_template_resource(type: str) -> str:
    """获取指定类型的技能模板内容."""
    from .resources.templates import TemplateType

    # 验证模板类型
    valid_types = ["minimal", "tool-based", "workflow-based", "analyzer-based"]
    if type not in valid_types:
        return f"# 错误\n\n未知的模板类型: {type}\n\n有效类型: {', '.join(valid_types)}"

    return get_template_content(TemplateType(type))  # type: ignore


@mcp.resource("http://skills/schema/best-practices")
def best_practices_resource() -> str:
    """获取 Agent-Skills 开发最佳实践."""
    return get_best_practices()


@mcp.resource("http://skills/schema/validation-rules")
def validation_rules_resource() -> str:
    """获取 Agent-Skills 验证规则."""
    return get_validation_rules()


# ==================== MCP Prompts ====================


@mcp.prompt("create-skill")
def create_skill_prompt(
    name: str,
    template: str = "minimal",
) -> str:
    """创建新技能的 Prompt 模板.

    Args:
        name: 技能名称
        template: 模板类型（默认：minimal）

    Returns:
        Prompt 模板内容
    """
    return get_create_skill_prompt(name, template)


@mcp.prompt("validate-skill")
def validate_skill_prompt(
    skill_path: str,
    template: str | None = None,
) -> str:
    """验证技能的 Prompt 模板.

    Args:
        skill_path: 技能目录路径
        template: 模板类型（可选）

    Returns:
        Prompt 模板内容
    """
    return get_validate_skill_prompt(skill_path, template)


@mcp.prompt("refactor-skill")
def refactor_skill_prompt(
    skill_path: str,
    focus: list[str] | None = None,
) -> str:
    """重构技能的 Prompt 模板.

    Args:
        skill_path: 技能目录路径
        focus: 重点关注领域（可选）

    Returns:
        Prompt 模板内容
    """
    return get_refactor_skill_prompt(skill_path, focus)


__all__ = ["mcp"]
