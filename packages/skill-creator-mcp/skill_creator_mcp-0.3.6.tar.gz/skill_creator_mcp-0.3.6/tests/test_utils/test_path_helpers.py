"""路径处理辅助函数测试."""

import tempfile
from pathlib import Path

import pytest

from skill_creator_mcp.utils.path_helpers import (
    ensure_output_dir,
    get_output_dir,
    join_paths,
    normalize_path,
    split_path_parts,
)


def test_normalize_path():
    """测试路径规范化."""
    # 测试 ~ 展开
    path = normalize_path("~/test")
    assert path.is_absolute()
    assert str(path) == str(Path.home() / "test")

    # 测试相对路径
    path = normalize_path("./test")
    assert path.is_absolute()


def test_ensure_output_dir_creates_missing_directory():
    """测试 ensure_output_dir 自动创建缺失目录."""
    with tempfile.TemporaryDirectory() as tmpdir:
        missing_dir = Path(tmpdir) / "a" / "b" / "skills"
        assert not missing_dir.exists()

        result = ensure_output_dir(missing_dir)

        assert result.exists()
        assert result.is_dir()


def test_ensure_output_dir_expands_tilde():
    """测试 ensure_output_dir 展开 ~."""
    result = ensure_output_dir("~/test_skills")
    assert str(Path.home()) in str(result)
    assert "test_skills" in str(result)


def test_ensure_output_dir_validates_existing_dir():
    """测试 ensure_output_dir 验证现有目录."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # 测试目录
        result = ensure_output_dir(tmpdir)
        assert result == Path(tmpdir).resolve()

        # 测试文件（应报错）
        test_file = Path(tmpdir) / "not_a_dir"
        test_file.write_text("content")

        with pytest.raises(ValueError, match="不是目录"):
            ensure_output_dir(test_file)


def test_ensure_output_dir_raises_on_not_writable():
    """测试 ensure_output_dir 对不可写目录报错."""
    import stat

    with tempfile.TemporaryDirectory() as tmpdir:
        readonly_dir = Path(tmpdir) / "readonly"
        readonly_dir.mkdir()

        try:
            # 设置只读权限
            readonly_dir.chmod(stat.S_IRUSR | stat.S_IXUSR)

            with pytest.raises(ValueError, match="不可写"):
                ensure_output_dir(readonly_dir)
        finally:
            # 恢复权限以便清理
            readonly_dir.chmod(stat.S_IRWXU)


def test_get_output_dir_with_env_var():
    """测试 get_output_dir 读取 SKILL_CREATOR_OUTPUT_DIR."""
    import os

    original_value = os.environ.get("SKILL_CREATOR_OUTPUT_DIR")
    os.environ["SKILL_CREATOR_OUTPUT_DIR"] = "/tmp/test_skills"

    try:
        result = get_output_dir()
        assert "test_skills" in str(result)
    finally:
        if original_value is None:
            del os.environ["SKILL_CREATOR_OUTPUT_DIR"]
        else:
            os.environ["SKILL_CREATOR_OUTPUT_DIR"] = original_value


def test_get_output_dir_fallback_to_home_skills():
    """测试 get_output_dir 回退到 ~/skills."""
    import os

    original_value = os.environ.get("SKILL_CREATOR_OUTPUT_DIR")
    if "SKILL_CREATOR_OUTPUT_DIR" in os.environ:
        del os.environ["SKILL_CREATOR_OUTPUT_DIR"]

    try:
        result = get_output_dir(fallback=True)
        assert "skills" in str(result).lower()
        assert str(Path.home()) in str(result)
    finally:
        if original_value is not None:
            os.environ["SKILL_CREATOR_OUTPUT_DIR"] = original_value


def test_ensure_output_dir_creation_failure():
    """测试目录创建失败（权限不足）"""
    from unittest.mock import patch

    with patch("pathlib.Path.mkdir") as mock_mkdir:
        # 模拟目录创建失败
        mock_mkdir.side_effect = OSError("Permission denied")
        with pytest.raises(ValueError, match="无法创建输出目录"):
            ensure_output_dir("/invalid/path")


def test_get_output_dir_no_fallback():
    """测试环境变量未设置且fallback=False"""
    import os

    original_value = os.environ.get("SKILL_CREATOR_OUTPUT_DIR")
    if "SKILL_CREATOR_OUTPUT_DIR" in os.environ:
        del os.environ["SKILL_CREATOR_OUTPUT_DIR"]

    try:
        with pytest.raises(ValueError, match="必须设置 SKILL_CREATOR_OUTPUT_DIR"):
            get_output_dir(fallback=False)
    finally:
        if original_value is not None:
            os.environ["SKILL_CREATOR_OUTPUT_DIR"] = original_value


def test_join_paths_multiple_parts():
    """测试多路径拼接"""
    result = join_paths("/a", "b", "c")
    assert result == Path("/a/b/c")


def test_join_paths_single_part():
    """测试单个路径"""
    result = join_paths("/a")
    assert result == Path("/a")


def test_split_path_parts():
    """测试路径分割"""
    result = split_path_parts("/a/b/c")
    assert result == ("/", "a", "b", "c")


def test_split_path_parts_relative():
    """测试相对路径分割"""
    result = split_path_parts("a/b/c")
    assert result == ("a", "b", "c")
