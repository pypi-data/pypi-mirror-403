"""文件操作工具函数."""

import asyncio
from pathlib import Path


async def create_directory_structure_async(
    name: str,
    template_type: str,
    output_dir: Path,
) -> Path:
    """异步创建技能目录结构.

    Args:
        name: 技能名称
        template_type: 模板类型
        output_dir: 输出目录

    Returns:
        创建的技能目录路径
    """
    skill_dir = output_dir / name

    # 创建主目录和子目录
    directories = [
        skill_dir,
        skill_dir / "references",
        skill_dir / "examples",
        skill_dir / "scripts",
        skill_dir / ".claude",
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

    return skill_dir


def create_directory_structure(
    name: str,
    template_type: str,
    output_dir: Path,
) -> Path:
    """同步创建技能目录结构.

    Args:
        name: 技能名称
        template_type: 模板类型
        output_dir: 输出目录

    Returns:
        创建的技能目录路径
    """
    skill_dir = output_dir / name

    # 创建主目录和子目录
    directories = [
        skill_dir,
        skill_dir / "references",
        skill_dir / "examples",
        skill_dir / "scripts",
        skill_dir / ".claude",
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

    return skill_dir


async def write_file_async(
    file_path: Path,
    content: str,
    encoding: str = "utf-8",
) -> None:
    """异步写入文件.

    Args:
        file_path: 文件路径
        content: 文件内容
        encoding: 文件编码
    """
    # 使用 asyncio.to_thread 在单独的线程中执行 I/O 操作
    await asyncio.to_thread(file_path.write_text, content, encoding)


def write_file(
    file_path: Path,
    content: str,
    encoding: str = "utf-8",
) -> None:
    """同步写入文件.

    Args:
        file_path: 文件路径
        content: 文件内容
        encoding: 文件编码
    """
    file_path.write_text(content, encoding)


async def read_file_async(
    file_path: Path,
    encoding: str = "utf-8",
) -> str:
    """异步读取文件.

    Args:
        file_path: 文件路径
        encoding: 文件编码

    Returns:
        文件内容
    """
    return await asyncio.to_thread(file_path.read_text, encoding)


def read_file(
    file_path: Path,
    encoding: str = "utf-8",
) -> str:
    """同步读取文件.

    Args:
        file_path: 文件路径
        encoding: 文件编码

    Returns:
        文件内容
    """
    return file_path.read_text(encoding)
