"""测试 package_skill 打包函数."""

import tarfile
import zipfile
from pathlib import Path

from skill_creator_mcp.utils.packagers import (
    _collect_files,
    _create_tar_package,
    _create_zip_package,
    _format_size,
    _should_exclude,
    generate_package_manifest,
    package_skill,
)

# ==================== _collect_files 测试 ====================


def test_collect_files_basic(temp_dir: Path):
    """测试基本文件收集."""
    skill_dir = temp_dir / "test-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# Test")
    (skill_dir / "README.md").write_text("# Readme")

    files = _collect_files(skill_dir, include_tests=True)

    assert len(files) == 2
    assert any(f.name == "SKILL.md" for f in files)
    assert any(f.name == "README.md" for f in files)


def test_collect_files_excludes_pycache(temp_dir: Path):
    """测试排除 __pycache__ 目录."""
    skill_dir = temp_dir / "test-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# Test")

    # 创建 __pycache__ 目录和文件
    pycache_dir = skill_dir / "__pycache__"
    pycache_dir.mkdir()
    (pycache_dir / "module.pyc").write_text("compiled")

    files = _collect_files(skill_dir, include_tests=True)

    # __pycache__ 文件应该被排除
    assert len(files) == 1
    assert files[0].name == "SKILL.md"


def test_collect_files_excludes_tests_when_disabled(temp_dir: Path):
    """测试排除测试文件."""
    skill_dir = temp_dir / "test-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# Test")

    tests_dir = skill_dir / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_example.py").write_text("def test(): pass")

    files = _collect_files(skill_dir, include_tests=False)

    # 测试文件应该被排除
    assert len(files) == 1
    assert files[0].name == "SKILL.md"


def test_collect_files_includes_tests_when_enabled(temp_dir: Path):
    """测试包含测试文件."""
    skill_dir = temp_dir / "test-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# Test")

    tests_dir = skill_dir / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_example.py").write_text("def test(): pass")

    files = _collect_files(skill_dir, include_tests=True)

    # 测试文件应该被包含
    assert len(files) == 2


# ==================== _should_exclude 测试 ====================


def test_should_exclude_pyc_files():
    """测试排除 .pyc 文件."""
    path = Path("module.pyc")
    patterns = ["*.pyc"]
    assert _should_exclude(path, patterns, include_tests=True) is True


def test_should_exclude_pytest_cache():
    """测试排除 .pytest_cache 目录."""
    path = Path(".pytest_cache/file.txt")
    patterns = [".pytest_cache"]
    assert _should_exclude(path, patterns, include_tests=True) is True


def test_should_exclude_tests_when_disabled():
    """测试禁用测试时排除 tests 目录."""
    path = Path("tests/test_example.py")
    patterns = []
    assert _should_exclude(path, patterns, include_tests=False) is True


def test_should_not_exclude_tests_when_enabled():
    """测试启用测试时包含 tests 目录."""
    path = Path("tests/test_example.py")
    patterns = []
    assert _should_exclude(path, patterns, include_tests=True) is False


def test_should_exclude_test_files_when_disabled():
    """测试禁用测试时排除 test_ 文件."""
    path = Path("src/test_helper.py")
    patterns = []
    assert _should_exclude(path, patterns, include_tests=False) is True


# ==================== _create_zip_package 测试 ====================


def test_create_zip_package(temp_dir: Path):
    """测试创建 ZIP 包."""
    skill_dir = temp_dir / "skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "file1.txt").write_text("content1")
    (skill_dir / "file2.txt").write_text("content2")

    package_path = temp_dir / "output.zip"
    files = [Path("file1.txt"), Path("file2.txt")]

    _create_zip_package(skill_dir, files, package_path)

    # 验证 ZIP 文件存在
    assert package_path.exists()

    # 验证内容
    with zipfile.ZipFile(package_path, "r") as zf:
        assert "file1.txt" in zf.namelist()
        assert "file2.txt" in zf.namelist()


# ==================== _create_tar_package 测试 ====================


def test_create_tar_gz_package(temp_dir: Path):
    """测试创建 tar.gz 包."""
    skill_dir = temp_dir / "skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "file1.txt").write_text("content1")

    package_path = temp_dir / "output.tar.gz"
    files = [Path("file1.txt")]

    _create_tar_package(skill_dir, files, package_path, "tar.gz")

    # 验证 TAR 文件存在
    assert package_path.exists()

    # 验证内容
    with tarfile.open(package_path, "r:gz") as tf:
        assert "file1.txt" in tf.getnames()


def test_create_tar_bz2_package(temp_dir: Path):
    """测试创建 tar.bz2 包."""
    skill_dir = temp_dir / "skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "file1.txt").write_text("content1")

    package_path = temp_dir / "output.tar.bz2"
    files = [Path("file1.txt")]

    _create_tar_package(skill_dir, files, package_path, "tar.bz2")

    # 验证 TAR 文件存在
    assert package_path.exists()

    # 验证内容
    with tarfile.open(package_path, "r:bz2") as tf:
        assert "file1.txt" in tf.getnames()


# ==================== _format_size 测试 ====================


def test_format_size_bytes():
    """测试格式化字节."""
    assert _format_size(512) == "512.0 B"


def test_format_size_kilobytes():
    """测试格式化千字节."""
    assert _format_size(2048) == "2.0 KB"


def test_format_size_megabytes():
    """测试格式化兆字节."""
    assert _format_size(3 * 1024 * 1024) == "3.0 MB"


def test_format_size_gigabytes():
    """测试格式化吉字节."""
    assert _format_size(5 * 1024 * 1024 * 1024) == "5.0 GB"


def test_format_size_terabytes():
    """测试格式化太字节."""
    size = 2 * 1024 * 1024 * 1024 * 1024
    assert _format_size(size) == "2.0 TB"


# ==================== package_skill 测试 ====================


def test_package_skill_basic_zip(temp_dir: Path):
    """测试基本 ZIP 打包."""
    skill_dir = temp_dir / "test-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# Test")
    (skill_dir / "references").mkdir()
    (skill_dir / "examples").mkdir()
    (skill_dir / "scripts").mkdir()
    (skill_dir / ".claude").mkdir()

    output_dir = temp_dir / "output"
    output_dir.mkdir()

    result = package_skill(
        skill_path=str(skill_dir),
        output_dir=str(output_dir),
        package_format="zip",
        include_tests=True,
        validate_before_package=False,
    )

    assert result.success is True
    assert result.package_path is not None
    assert result.format == "zip"
    assert result.files_included > 0
    assert Path(result.package_path).exists()


def test_package_skill_with_validation(temp_dir: Path):
    """测试带验证的打包."""
    skill_dir = temp_dir / "valid-skill"
    skill_dir.mkdir(parents=True)
    # 创建完整的 YAML frontmatter 以通过验证
    (skill_dir / "SKILL.md").write_text(
        "---\n"
        "name: valid-skill\n"
        "description: A valid test skill\n"
        "allowed-tools: [Read, Write, Edit]\n"
        "---\n"
        "# Test Skill\n"
    )
    (skill_dir / "references").mkdir()
    (skill_dir / "examples").mkdir()
    (skill_dir / "scripts").mkdir()
    (skill_dir / ".claude").mkdir()

    output_dir = temp_dir / "output"
    output_dir.mkdir()

    result = package_skill(
        skill_path=str(skill_dir),
        output_dir=str(output_dir),
        package_format="zip",
        validate_before_package=True,
    )

    assert result.success is True
    assert result.validation_passed is True


def test_package_skill_validation_fails(temp_dir: Path):
    """测试验证失败时打包失败."""
    skill_dir = temp_dir / "invalid-skill"
    skill_dir.mkdir(parents=True)
    # 缺少必需的目录

    output_dir = temp_dir / "output"
    output_dir.mkdir()

    result = package_skill(
        skill_path=str(skill_dir),
        output_dir=str(output_dir),
        package_format="zip",
        validate_before_package=True,
    )

    assert result.success is False
    assert result.validation_passed is False
    assert len(result.validation_errors) > 0


def test_package_skill_nonexistent_directory(temp_dir: Path):
    """测试不存在的目录."""
    output_dir = temp_dir / "output"
    output_dir.mkdir()

    result = package_skill(
        skill_path=str(temp_dir / "nonexistent"),
        output_dir=str(output_dir),
        package_format="zip",
        validate_before_package=False,
    )

    assert result.success is False
    assert result.error_type == "path_error"


def test_package_skill_invalid_format(temp_dir: Path):
    """测试无效的打包格式."""
    skill_dir = temp_dir / "test-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# Test")

    output_dir = temp_dir / "output"
    output_dir.mkdir()

    result = package_skill(
        skill_path=str(skill_dir),
        output_dir=str(output_dir),
        package_format="invalid",
        validate_before_package=False,
    )

    assert result.success is False
    assert result.error_type == "format_error"


def test_package_skill_tar_gz(temp_dir: Path):
    """测试 tar.gz 格式打包."""
    skill_dir = temp_dir / "test-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# Test")

    output_dir = temp_dir / "output"
    output_dir.mkdir()

    result = package_skill(
        skill_path=str(skill_dir),
        output_dir=str(output_dir),
        package_format="tar.gz",
        validate_before_package=False,
    )

    assert result.success is True
    assert result.format == "tar.gz"
    assert Path(result.package_path).exists()


def test_package_skill_excludes_tests(temp_dir: Path):
    """测试排除测试文件."""
    skill_dir = temp_dir / "test-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# Test")
    (skill_dir / "references").mkdir()
    (skill_dir / "examples").mkdir()
    (skill_dir / "scripts").mkdir()
    (skill_dir / ".claude").mkdir()

    # 创建测试文件
    tests_dir = skill_dir / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_example.py").write_text("def test(): pass")

    output_dir = temp_dir / "output"
    output_dir.mkdir()

    result = package_skill(
        skill_path=str(skill_dir),
        output_dir=str(output_dir),
        package_format="zip",
        include_tests=False,
        validate_before_package=False,
    )

    assert result.success is True
    # 测试文件应该被排除
    assert result.files_included == 1  # 只有 SKILL.md


def test_package_skill_path_not_directory(temp_dir: Path):
    """测试路径不是目录的情况 (覆盖 line 47)."""
    # 创建文件而不是目录
    file_path = temp_dir / "not-a-directory"
    file_path.write_text("content")

    output_dir = temp_dir / "output"
    output_dir.mkdir()

    result = package_skill(
        skill_path=str(file_path),
        output_dir=str(output_dir),
        package_format="zip",
        validate_before_package=False,
    )

    assert result.success is False
    assert "路径不是目录" in result.error
    assert result.error_type == "path_error"


def test_package_skill_tar_bz2(temp_dir: Path):
    """测试 tar.bz2 格式打包 (覆盖 line 97)."""
    skill_dir = temp_dir / "test-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# Test")
    (skill_dir / "references").mkdir()
    (skill_dir / "examples").mkdir()
    (skill_dir / "scripts").mkdir()
    (skill_dir / ".claude").mkdir()

    output_dir = temp_dir / "output"
    output_dir.mkdir()

    result = package_skill(
        skill_path=str(skill_dir),
        output_dir=str(output_dir),
        package_format="tar.bz2",
        validate_before_package=False,
    )

    assert result.success is True
    assert result.format == "tar.bz2"
    assert result.package_path is not None
    assert Path(result.package_path).exists()
    # 验证是 tar.bz2 文件
    assert result.package_path.endswith(".tar.bz2")


def test_package_skill_with_template_validation(temp_dir: Path):
    """测试带模板类型的验证 (覆盖 lines 72-73)."""
    from skill_creator_mcp.utils.validators import _validate_skill_md

    skill_dir = temp_dir / "template-skill"
    skill_dir.mkdir(parents=True)
    # 使用 minimal 模板
    (skill_dir / "SKILL.md").write_text(
        "---\n"
        "name: template-skill\n"
        "description: Test skill\n"
        "template: minimal\n"
        "allowed-tools: Read\n"
        "---\n"
        "# Test Skill\n"
    )
    (skill_dir / "references").mkdir()
    (skill_dir / "examples").mkdir()
    (skill_dir / "scripts").mkdir()
    (skill_dir / ".claude").mkdir()

    output_dir = temp_dir / "output"
    output_dir.mkdir()

    # 首先验证模板类型被正确识别
    _, _, template_type = _validate_skill_md(skill_dir)
    assert template_type == "minimal"

    # 然后测试打包时的验证流程
    result = package_skill(
        skill_path=str(skill_dir),
        output_dir=str(output_dir),
        package_format="zip",
        validate_before_package=True,
    )

    assert result.success is True
    assert result.validation_passed is True


def test_package_skill_exception_handling(temp_dir: Path):
    """测试打包过程的异常处理 (覆盖 lines 134-135)."""
    from unittest.mock import patch

    skill_dir = temp_dir / "test-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# Test")

    output_dir = temp_dir / "output"
    output_dir.mkdir()

    # Mock _create_zip_package 抛出异常
    with patch(
        "skill_creator_mcp.utils.packagers._create_zip_package",
        side_effect=RuntimeError("Simulated packaging error"),
    ):
        result = package_skill(
            skill_path=str(skill_dir),
            output_dir=str(output_dir),
            package_format="zip",
            validate_before_package=False,
        )

        assert result.success is False
        assert "打包过程出错" in result.error
        assert result.error_type == "internal_error"


# ==================== generate_package_manifest 测试 ====================


def test_generate_package_manifest_zip():
    """测试生成 ZIP 格式的打包清单."""
    manifest = generate_package_manifest(
        skill_path="/path/to/skill",
        package_path="/path/to/output/skill.zip",
        files_included=5,
        package_size=2048,
    )

    assert "# 技能打包清单" in manifest
    assert "/path/to/skill" in manifest
    assert "5" in manifest
    assert "2.0 KB" in manifest
    assert "unzip /path/to/output/skill.zip" in manifest


def test_generate_package_manifest_tar_gz():
    """测试生成 tar.gz 格式的打包清单."""
    manifest = generate_package_manifest(
        skill_path="/path/to/skill",
        package_path="/path/to/output/skill.tar.gz",
        files_included=3,
        package_size=1024,
    )

    assert "tar -xzf /path/to/output/skill.tar.gz" in manifest


def test_generate_package_manifest_tar_bz2():
    """测试生成 tar.bz2 格式的打包清单."""
    manifest = generate_package_manifest(
        skill_path="/path/to/skill",
        package_path="/path/to/output/skill.tar.bz2",
        files_included=3,
        package_size=1024,
    )

    assert "tar -xjf /path/to/output/skill.tar.bz2" in manifest


def test_generate_package_manifest_large_size():
    """测试大文件大小的格式化."""
    manifest = generate_package_manifest(
        skill_path="/path/to/skill",
        package_path="/path/to/output/skill.zip",
        files_included=10,
        package_size=5 * 1024 * 1024,  # 5 MB
    )

    assert "5.0 MB" in manifest
