"""打包工具模块.

包含打包 Agent-Skill 的 MCP 工具函数。

统一的打包工具，支持通用和Agent-Skill标准两种模式。
"""

from typing import Any

from fastmcp import Context, FastMCP


async def package_skill(
    ctx: Context,
    mcp: FastMCP,
    skill_path: str,
    output_dir: str | None = None,
    version: str | None = None,
    format: str = "zip",
    include_tests: bool = False,
    strict: bool = False,
    validate_before_package: bool = True,
) -> dict[str, Any]:
    """
    打包 Agent-Skill 为分发格式.

    这是统一的打包工具，支持两种模式：
    - strict=False (默认): 通用打包模式，使用灵活排除模式
    - strict=True: Agent-Skill标准打包模式，使用严格排除模式，支持version参数

    Args:
        ctx: MCP 上下文
        mcp: FastMCP 实例
        skill_path: 技能目录路径
        output_dir: 输出目录路径（可选，优先级：参数 > 环境变量 SKILL_CREATOR_OUTPUT_DIR > 默认值）
        version: 版本号（可选，格式如 "0.3.1"，仅在strict=True时使用）
        format: 打包格式（zip/tar.gz/tar.bz2，默认：zip）
        include_tests: 是否包含测试文件（默认：False）
        strict: 是否使用Agent-Skill标准打包模式（默认：False）
        validate_before_package: 打包前是否验证（默认：True）

    Returns:
        包含打包结果的字典

    Examples:
        >>> # 通用打包模式
        >>> await package_skill(ctx, mcp, skill_path="/path/to/skill", format="zip")
        >>>
        >>> # Agent-Skill标准打包模式（带版本号）
        >>> await package_skill(ctx, mcp, skill_path="/path/to/skill",
        ...                      version="0.3.1", strict=True)
        >>> # 生成: skill-v0.3.1.zip
    """
    from pydantic import ValidationError

    from ..config import get_config
    from ..models.skill_config import PackageSkillInput
    from ..utils.packagers import (
        _collect_agent_skill_files,
        _create_tar_package,
        _create_zip_package,
    )
    from ..utils.packagers import (
        package_skill as package_skill_impl,
    )
    from ..utils.path_helpers import normalize_path

    try:
        # 优先级：工具参数 > 环境变量 > 默认值
        config = get_config()
        if output_dir is None:
            output_dir = str(config.output_dir)

        # 根据strict参数选择打包方式
        if strict:
            # Agent-Skill标准打包模式
            # 验证version参数
            if version is None:
                return {
                    "success": False,
                    "error": "strict模式需要version参数",
                    "error_type": "validation_error",
                }


            from ..models.skill_config import PackageResult

            # 规范化路径
            skill_dir = normalize_path(skill_path)
            out_dir = normalize_path(output_dir)

            # 检查技能目录是否存在
            if not skill_dir.exists():
                return {
                    "success": False,
                    "error": f"技能目录不存在: {skill_dir}",
                    "error_type": "path_error",
                }

            # 确定包文件名（带版本号）
            skill_name = skill_dir.name
            base_name = f"{skill_name}-v{version}"

            if format == "tar.gz":
                package_filename = f"{base_name}.tar.gz"
            elif format == "tar.bz2":
                package_filename = f"{base_name}.tar.bz2"
            else:  # zip
                package_filename = f"{base_name}.zip"

            package_path = out_dir / package_filename

            # 收集要打包的文件（使用 Agent-Skill 专用函数）
            try:
                files_to_package = _collect_agent_skill_files(skill_dir, include_tests)
            except ValueError as e:
                return {
                    "success": False,
                    "error": str(e),
                    "error_type": "validation_error",
                }

            # 执行打包
            try:
                if format == "zip":
                    _create_zip_package(skill_dir, files_to_package, package_path)
                elif format in ("tar.gz", "tar.bz2"):
                    _create_tar_package(skill_dir, files_to_package, package_path, format)
                else:
                    return {
                        "success": False,
                        "error": f"不支持的打包格式: {format}",
                        "error_type": "format_error",
                    }

                # 获取包大小
                package_size = package_path.stat().st_size if package_path.exists() else None

                result = PackageResult(
                    success=True,
                    skill_path=str(skill_dir),
                    package_path=str(package_path),
                    format=format,
                    files_included=len(files_to_package),
                    package_size=package_size,
                    validation_passed=None,
                    validation_errors=[],
                )
            except Exception as e:
                result = PackageResult(
                    success=False,
                    skill_path=str(skill_dir),
                    error=f"打包过程出错: {e}",
                    error_type="internal_error",
                )
        else:
            # 通用打包模式
            input_data = PackageSkillInput.model_validate(
                {
                    "skill_path": skill_path,
                    "output_dir": output_dir,
                    "format": format,
                    "include_tests": include_tests,
                    "validate_before_package": validate_before_package,
                }
            )

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


__all__ = ["package_skill"]
