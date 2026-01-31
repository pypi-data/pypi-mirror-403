"""打包工具函数."""

import tarfile
import zipfile
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..models.skill_config import PackageResult


def package_skill(
    skill_path: str,
    output_dir: str,
    package_format: str = "zip",
    include_tests: bool = True,
    validate_before_package: bool = True,
) -> "PackageResult":
    """打包技能为分发格式.

    Args:
        skill_path: 技能目录路径
        output_dir: 输出目录路径
        package_format: 打包格式（zip/tar.gz/tar.bz2）
        include_tests: 是否包含测试文件
        validate_before_package: 打包前是否验证

    Returns:
        打包结果
    """
    from ..models.skill_config import PackageResult

    skill_dir = Path(skill_path).resolve()
    out_dir = Path(output_dir).resolve()

    # 检查技能目录是否存在
    if not skill_dir.exists():
        return PackageResult(
            success=False,
            skill_path=str(skill_dir),
            error=f"技能目录不存在: {skill_dir}",
            error_type="path_error",
        )

    if not skill_dir.is_dir():
        return PackageResult(
            success=False,
            skill_path=str(skill_dir),
            error=f"路径不是目录: {skill_dir}",
            error_type="path_error",
        )

    validation_passed = None
    validation_errors = []

    # 如果需要，在打包前进行验证
    if validate_before_package:
        from .validators import (
            _validate_naming,
            _validate_skill_md,
            _validate_structure,
            _validate_template_requirements,
        )

        structure_errors = _validate_structure(skill_dir)
        naming_errors = _validate_naming(skill_dir)
        content_errors, content_warnings, template_type = _validate_skill_md(skill_dir)

        all_errors = structure_errors + naming_errors + content_errors
        if template_type:
            template_errors = _validate_template_requirements(skill_dir, template_type)
            all_errors.extend(template_errors)

        validation_passed = len(all_errors) == 0
        validation_errors = all_errors

        # 如果验证失败，可以选择不继续打包
        if not validation_passed:
            return PackageResult(
                success=False,
                skill_path=str(skill_dir),
                validation_passed=validation_passed,
                validation_errors=validation_errors,
                error=f"验证失败，发现 {len(all_errors)} 个错误",
                error_type="validation_error",
            )

    # 确保输出目录存在
    out_dir.mkdir(parents=True, exist_ok=True)

    # 确定包文件名
    skill_name = skill_dir.name
    if package_format == "tar.gz":
        package_filename = f"{skill_name}.tar.gz"
    elif package_format == "tar.bz2":
        package_filename = f"{skill_name}.tar.bz2"
    else:  # zip
        package_filename = f"{skill_name}.zip"

    package_path = out_dir / package_filename

    # 收集要打包的文件
    files_to_package = _collect_files(skill_dir, include_tests)

    # 执行打包
    try:
        if package_format == "zip":
            _create_zip_package(skill_dir, files_to_package, package_path)
        elif package_format in ("tar.gz", "tar.bz2"):
            _create_tar_package(skill_dir, files_to_package, package_path, package_format)
        else:
            return PackageResult(
                success=False,
                skill_path=str(skill_dir),
                error=f"不支持的打包格式: {package_format}",
                error_type="format_error",
            )

        # 获取包大小
        package_size = package_path.stat().st_size if package_path.exists() else None

        return PackageResult(
            success=True,
            skill_path=str(skill_dir),
            package_path=str(package_path),
            format=package_format,
            files_included=len(files_to_package),
            package_size=package_size,
            validation_passed=validation_passed,
            validation_errors=validation_errors,
        )

    except Exception as e:
        return PackageResult(
            success=False,
            skill_path=str(skill_dir),
            error=f"打包过程出错: {e}",
            error_type="internal_error",
        )


def _collect_files(skill_dir: Path, include_tests: bool) -> list[Path]:
    """收集要打包的文件.

    Args:
        skill_dir: 技能目录
        include_tests: 是否包含测试文件

    Returns:
        要打包的文件列表（相对于 skill_dir 的路径）
    """
    files_to_include = []

    # 要排除的目录和文件模式
    exclude_patterns = [
        "__pycache__",
        "*.pyc",
        ".pytest_cache",
        "*.egg-info",
        ".venv",
        "venv",
        ".env",
        ".coverage",
        "htmlcov",
        ".mypy_cache",
        ".ruff_cache",
        "dist",
        "build",
        "*.log",
    ]

    # 遍历所有文件
    for item in skill_dir.rglob("*"):
        if not item.is_file():
            continue

        relative_path = item.relative_to(skill_dir)

        # 检查是否应该排除
        if _should_exclude(relative_path, exclude_patterns, include_tests):
            continue

        files_to_include.append(relative_path)

    return files_to_include


def _should_exclude(
    relative_path: Path,
    exclude_patterns: list[str],
    include_tests: bool,
) -> bool:
    """判断文件是否应该被排除.

    Args:
        relative_path: 相对路径
        exclude_patterns: 排除模式列表
        include_tests: 是否包含测试文件

    Returns:
        是否应该排除
    """
    from .path_helpers import split_path_parts

    path_str = str(relative_path)
    path_parts = split_path_parts(relative_path)

    # 检查排除模式
    for pattern in exclude_patterns:
        if pattern.startswith("*"):
            # 通配符模式 - 匹配后缀
            suffix = pattern[1:]
            # 检查完整路径后缀
            if path_str.endswith(suffix):
                return True
            # 检查文件名后缀
            if relative_path.name.endswith(suffix):
                return True
            # 检查路径中任何部分是否以后缀结尾
            if any(part.endswith(suffix) for part in path_parts):
                return True
        else:
            # 精确匹配或目录匹配
            # 检查路径中是否包含该模式
            if pattern in path_str:
                return True
            # 也检查各部分是否精确匹配
            if pattern in path_parts:
                return True

    # 检查是否排除测试文件
    if not include_tests:
        if "tests" in path_parts or "test" in path_parts:
            return True
        if relative_path.name.startswith("test_"):
            return True

    return False


def _create_zip_package(
    skill_dir: Path,
    files_to_package: list[Path],
    package_path: Path,
) -> None:
    """创建 ZIP 格式的包.

    Args:
        skill_dir: 技能目录
        files_to_package: 要打包的文件列表
        package_path: 包文件路径
    """
    with zipfile.ZipFile(package_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for relative_path in files_to_package:
            full_path = skill_dir / relative_path
            arcname = str(relative_path)
            zf.write(full_path, arcname)


def _create_tar_package(
    skill_dir: Path,
    files_to_package: list[Path],
    package_path: Path,
    package_format: str,
) -> None:
    """创建 TAR 格式的包.

    Args:
        skill_dir: 技能目录
        files_to_package: 要打包的文件列表
        package_path: 包文件路径
        package_format: 打包格式（tar.gz 或 tar.bz2）
    """
    mode: str = "w:gz" if package_format == "tar.gz" else "w:bz2"

    with tarfile.open(str(package_path), mode) as tf:  # type: ignore[call-overload]
        for relative_path in files_to_package:
            full_path = skill_dir / relative_path
            arcname = str(relative_path)
            tf.add(full_path, arcname)
def _collect_agent_skill_files(
    skill_dir: Path,
    include_tests: bool = False,
) -> list[Path]:
    """收集 Agent-Skill 文件（专门用于打包标准 Agent-Skill）.

    Args:
        skill_dir: Agent-Skill 目录路径
        include_tests: 是否包含测试文件

    Returns:
        要打包的文件列表（相对于 skill_dir 的路径）

    Raises:
        ValueError: 如果 skill_dir 不是有效的 Agent-Skill 目录
    """
    # 验证是否为有效的 Agent-Skill 目录
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        raise ValueError("不是有效的 Agent-Skill 目录: 缺少 SKILL.md")

    files_to_include = []

    # Agent-Skill 专用的排除模式（更严格）
    from ..config import get_config
    plan_archive_dir = str(get_config().plan_archive_dir)
    exclude_patterns = [
        # 版本控制
        ".git",
        ".gitignore",
        ".gitattributes",
        # 开发环境
        ".vscode",
        ".idea",
        "*.swp",
        "*.swo",
        # 计划和归档（关键！）
        # 从配置获取计划归档目录
        plan_archive_dir,  # 如 ".claude/plans/archive"
        ".claude/archive",
        # 项目级文档（不属于单个 Agent-Skill）
        "README.md",
        "CHANGELOG.md",
        "CONTRIBUTING.md",
        "LICENSE",
        # MCP Server 代码（应该单独打包）- 使用更精确的模式
        "*-mcp",
        "*_mcp",
        "mcp-server",
        # 测试和覆盖率
        "tests",
        ".pytest_cache",
        "htmlcov",
        ".coverage",
        "coverage.xml",
        # Python 构建产物
        "__pycache__",
        "*.pyc",
        "*.pyo",
        "*.pyd",
        ".mypy_cache",
        ".ruff_cache",
        "*.egg-info",
        "dist",
        "build",
        ".DS_Store",
        # 虚拟环境
        ".venv",
        "venv",
        "env",
        ".env",
        # 日志和临时文件
        "*.log",
        "*.tmp",
        "*.bak",
    ]

    # 遍历所有文件
    for item in skill_dir.rglob("*"):
        if not item.is_file():
            continue

        relative_path = item.relative_to(skill_dir)

        # 检查是否应该排除
        if _should_exclude(relative_path, exclude_patterns, include_tests):
            continue

        files_to_include.append(relative_path)

    return files_to_include
