"""打包工具函数."""

import os
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
    path_str = str(relative_path)

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
            parts = path_str.split("/") if "/" in path_str else path_str.split(os.sep)
            if any(part.endswith(suffix) for part in parts):
                return True
        else:
            # 精确匹配或目录匹配
            # 检查路径中是否包含该模式（支持 / 和 os.sep）
            if pattern in path_str or pattern in path_str.replace("/", os.sep):
                return True
            # 也检查各部分是否精确匹配
            parts = path_str.split("/") if "/" in path_str else path_str.split(os.sep)
            if pattern in parts:
                return True

    # 检查是否排除测试文件
    if not include_tests:
        parts = path_str.split("/") if "/" in path_str else path_str.split(os.sep)
        if "tests" in parts or "test" in parts:
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


def generate_package_manifest(
    skill_path: str,
    package_path: str,
    files_included: int,
    package_size: int,
) -> str:
    """生成打包清单.

    Args:
        skill_path: 技能路径
        package_path: 包文件路径
        files_included: 包含的文件数量
        package_size: 包大小（字节）

    Returns:
        清单内容（Markdown 格式）
    """
    lines = []
    lines.append("# 技能打包清单\n")
    lines.append("## 基本信息")
    lines.append(f"- 技能路径：`{skill_path}`")
    lines.append(f"- 包文件：`{package_path}`")
    lines.append(f"- 文件数量：{files_included}")
    lines.append(f"- 包大小：{_format_size(package_size)}\n")

    lines.append("## 安装说明")
    lines.append("```bash")
    lines.append("# 解压包文件")
    if package_path.endswith(".zip"):
        lines.append(f"unzip {package_path}")
    elif package_path.endswith(".tar.gz"):
        lines.append(f"tar -xzf {package_path}")
    elif package_path.endswith(".tar.bz2"):
        lines.append(f"tar -xjf {package_path}")
    lines.append("")
    lines.append("# 进入技能目录")
    lines.append(f"cd $(basename {package_path} .{{zip,tar.gz,tar.bz2}})")
    lines.append("")
    lines.append("# 验证技能")
    lines.append("python scripts/validate_skill.py .")
    lines.append("```\n")

    return "\n".join(lines)


def _format_size(size_bytes: int) -> str:
    """格式化文件大小.

    Args:
        size_bytes: 字节数

    Returns:
        格式化后的大小字符串
    """
    size = float(size_bytes)
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def _is_project_root(path: Path) -> bool:
    """判断路径是否为项目根目录.

    Args:
        path: 要检查的路径

    Returns:
        是否为项目根目录
    """
    # 检查是否存在项目根目录的特征文件/目录
    indicators = [
        "skill-creator",      # Agent-Skill 目录
        "skill-creator-mcp",  # MCP Server 目录
        ".claude",           # Claude 配置
        "pyproject.toml",    # Python 项目配置
        "CHANGELOG.md",      # 项目变更日志
    ]
    return any((path / indicator).exists() for indicator in indicators)


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
        ".claude/plans/archive",
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


def package_agent_skill(
    skill_path: str,
    output_dir: str = ".",
    version: str | None = None,
    package_format: str = "zip",
    include_tests: bool = False,
    validate_before_package: bool = True,
) -> "PackageResult":
    """打包 Agent-Skill 为标准分发格式.

    这是专门用于打包标准 Agent-Skill 的函数。
    与 package_skill() 的区别：
    - 使用更严格的排除模式
    - 支持版本号参数，生成标准化包名
    - 默认不包含测试文件
    - 确保符合 Agent-Skill 规范

    Args:
        skill_path: Agent-Skill 目录路径
        output_dir: 输出目录路径
        version: 版本号（可选，格式如 "0.3.1"）
        package_format: 打包格式（zip/tar.gz/tar.bz2）
        include_tests: 是否包含测试文件（默认 False）
        validate_before_package: 打包前是否验证

    Returns:
        打包结果

    Examples:
        >>> result = package_agent_skill(
        ...     skill_path="/path/to/skill-creator",
        ...     output_dir="/output",
        ...     version="0.3.1",
        ...     package_format="zip"
        ... )
        >>> # 生成: skill-creator-v0.3.1.zip
    """
    from ..models.skill_config import PackageResult

    skill_dir = Path(skill_path).resolve()
    out_dir = Path(output_dir).resolve()

    # 检查技能目录是否存在
    if not skill_dir.exists():
        return PackageResult(
            success=False,
            skill_path=str(skill_dir),
            error=f"Agent-Skill 目录不存在: {skill_dir}",
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

    # 确定包文件名（带版本号）
    skill_name = skill_dir.name
    if version:
        base_name = f"{skill_name}-v{version}"
    else:
        base_name = skill_name

    if package_format == "tar.gz":
        package_filename = f"{base_name}.tar.gz"
    elif package_format == "tar.bz2":
        package_filename = f"{base_name}.tar.bz2"
    else:  # zip
        package_filename = f"{base_name}.zip"

    package_path = out_dir / package_filename

    # 收集要打包的文件（使用 Agent-Skill 专用函数）
    try:
        files_to_package = _collect_agent_skill_files(skill_dir, include_tests)
    except ValueError as e:
        return PackageResult(
            success=False,
            skill_path=str(skill_dir),
            error=str(e),
            error_type="validation_error",
        )

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
