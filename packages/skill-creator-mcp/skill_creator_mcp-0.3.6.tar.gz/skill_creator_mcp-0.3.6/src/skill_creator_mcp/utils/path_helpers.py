"""路径处理辅助函数.

提供统一的路径处理工具，确保跨平台兼容性和配置一致性。
"""

from pathlib import Path


def normalize_path(path: str | Path) -> Path:
    """规范化路径，处理 ~ 和相对路径.

    Args:
        path: 输入路径

    Returns:
        规范化后的绝对路径
    """
    return Path(path).expanduser().resolve(strict=False)


def ensure_output_dir(output_dir: str | Path) -> Path:
    """确保输出目录存在，不存在则自动创建.

    Args:
        output_dir: 输出目录路径（支持相对路径、绝对路径、~路径）

    Returns:
        已验证/创建的绝对路径

    Raises:
        ValueError: 目录创建失败或无权限

    Examples:
        >>> # 默认 ~/skills
        >>> ensure_output_dir("~/skills")
        Path("/home/user/skills")

        >>> # 自定义目录
        >>> ensure_output_dir("~/.claude/skills")
        Path("/home/user/.claude/skills")
    """
    import os

    # 转换为 Path 对象
    dir_path = Path(output_dir)

    # 1. 展开 ~ 为用户主目录
    expanded_dir = dir_path.expanduser()

    # 2. 解析为绝对路径
    absolute_dir = expanded_dir.resolve(strict=False)

    # 3. 检查目录是否存在
    if not absolute_dir.exists():
        # 4. 不存在则自动创建（包括父目录）
        try:
            absolute_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise ValueError(
                f"无法创建输出目录 {absolute_dir}: {e}"
            ) from e

    # 5. 验证是否为目录
    if not absolute_dir.is_dir():
        raise ValueError(
            f"输出路径不是目录: {absolute_dir}"
        )

    # 6. 验证可写性
    if not os.access(absolute_dir, os.W_OK):
        raise ValueError(
            f"输出目录不可写: {absolute_dir}"
        )

    return absolute_dir


def get_output_dir(fallback: bool = True) -> Path:
    """获取输出目录.

    Args:
        fallback: 如果未设置，是否使用默认值 ~/skills

    Returns:
        输出目录路径

    Raises:
        ValueError: 如果未设置且 fallback=False
    """
    import os

    output_dir_value = os.getenv("SKILL_CREATOR_OUTPUT_DIR")
    if output_dir_value:
        return Path(output_dir_value).expanduser().resolve(strict=False)
    if fallback:
        return Path("~/skills").expanduser().resolve(strict=False)
    raise ValueError("必须设置 SKILL_CREATOR_OUTPUT_DIR 环境变量")


def join_paths(*parts: str | Path) -> Path:
    """安全地拼接多个路径部分.

    Args:
        *parts: 路径部分

    Returns:
        拼接后的路径
    """
    result = Path(parts[0])
    for part in parts[1:]:
        result = result / part
    return result


def split_path_parts(path: str | Path) -> tuple[str, ...]:
    """获取路径的各个部分.

    Args:
        path: 输入路径

    Returns:
        路径的各个部分组成的元组
    """
    return Path(path).parts
