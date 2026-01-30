"""测试 analyze_skill 分析函数."""

from pathlib import Path

import pytest

from skill_creator_mcp.utils.analyzers import (
    _analyze_complexity,
    _analyze_quality,
    _analyze_structure,
    _calculate_structure_score,
    _categorize_file,
    _generate_analysis_summary,
)

# ==================== _categorize_file 测试 ====================


def test_categorize_file_tests(temp_dir: Path):
    """测试测试文件分类."""
    tests_dir = temp_dir / "tests"
    tests_dir.mkdir()

    # 创建测试文件
    test_file = tests_dir / "test_example.py"
    test_file.write_text("def test(): pass")

    category = _categorize_file(test_file, temp_dir)
    assert category == "tests"


def test_categorize_file_models(temp_dir: Path):
    """测试模型文件分类."""
    src_dir = temp_dir / "src" / "test_skill" / "models"
    src_dir.mkdir(parents=True)

    model_file = src_dir / "skill_model.py"
    model_file.write_text("class Model: pass")

    category = _categorize_file(model_file, temp_dir / "src" / "test_skill")
    assert category == "models"


def test_categorize_file_server(temp_dir: Path):
    """测试服务器文件分类."""
    src_dir = temp_dir / "src" / "test_skill"
    src_dir.mkdir(parents=True)

    server_file = src_dir / "server.py"
    server_file.write_text("# Server")

    category = _categorize_file(server_file, temp_dir / "src" / "test_skill")
    assert category == "server"


def test_categorize_file_other(temp_dir: Path):
    """测试其他文件分类."""
    src_dir = temp_dir / "src" / "test_skill"
    src_dir.mkdir(parents=True)

    other_file = src_dir / "helper.py"
    other_file.write_text("# Helper")

    category = _categorize_file(other_file, temp_dir / "src" / "test_skill")
    assert category == "other"


# ==================== _analyze_structure 测试 ====================


@pytest.mark.asyncio
async def test_analyze_structure_basic(temp_dir: Path):
    """测试基本结构分析."""
    # 创建项目结构
    src_dir = temp_dir / "test_skill"
    src_dir.mkdir(parents=True)
    (src_dir / "__init__.py").write_text("")
    (src_dir / "server.py").write_text("# " + "\n# ".join([""] * 10))

    result = await _analyze_structure(temp_dir / "test_skill")

    assert result.total_files == 2
    assert result.total_lines == 10  # 0 空行 + 10 # 行
    assert "server" in result.file_breakdown


@pytest.mark.asyncio
async def test_analyze_structure_empty(temp_dir: Path):
    """测试空目录结构分析."""
    empty_dir = temp_dir / "empty"
    empty_dir.mkdir()

    result = await _analyze_structure(empty_dir)

    assert result.total_files == 0
    assert result.total_lines == 0
    assert result.file_breakdown == {}


# ==================== _analyze_complexity 测试 ====================


@pytest.mark.asyncio
async def test_analyze_complexity_basic(temp_dir: Path):
    """测试基本复杂度分析."""
    src_dir = temp_dir / "test_skill"
    src_dir.mkdir(parents=True)

    # 创建简单的 Python 文件
    (src_dir / "simple.py").write_text("""
def hello():
    if True:
        return "world"
    return "done"
""")

    result = await _analyze_complexity(temp_dir / "test_skill")

    assert result.cyclomatic_complexity is not None
    assert result.cyclomatic_complexity >= 1


@pytest.mark.asyncio
async def test_analyze_complexity_no_files(temp_dir: Path):
    """测试无文件时的复杂度分析."""
    empty_dir = temp_dir / "empty"
    empty_dir.mkdir()

    result = await _analyze_complexity(empty_dir)

    assert result.cyclomatic_complexity is None


# ==================== _analyze_quality 测试 ====================


@pytest.mark.asyncio
async def test_analyze_quality_full_project(temp_dir: Path):
    """测试完整项目的质量分析."""
    # 创建完整的项目结构
    skill_dir = temp_dir / "test-skill"
    skill_dir.mkdir()

    # 创建必需目录和文件
    (skill_dir / "SKILL.md").write_text("# " + "\n## " + "\n```python\nexample\n```")
    (skill_dir / "references").mkdir()
    (skill_dir / "references" / "guide.md").write_text("# Guide\n\nContent")
    (skill_dir / "references" / "api.md").write_text("# API\n\nContent")
    (skill_dir / "examples").mkdir()
    (skill_dir / "scripts").mkdir()
    (skill_dir / ".claude").mkdir()
    (skill_dir / "src").mkdir(parents=True)
    (skill_dir / "src" / "test_skill" / "models").mkdir(parents=True)
    (skill_dir / "src" / "test_skill" / "utils").mkdir(parents=True)
    (skill_dir / "pyproject.toml").write_text("[project]")

    # 创建测试目录
    tests_dir = skill_dir / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_main.py").write_text("def test(): pass")
    (tests_dir / "test_utils.py").write_text("def test(): pass")
    (tests_dir / "test_models.py").write_text("def test(): pass")

    result = await _analyze_quality(skill_dir)

    assert result.overall_score > 0
    assert result.structure_score > 0
    assert result.documentation_score > 0
    assert result.test_coverage_score > 0


@pytest.mark.asyncio
async def test_analyze_quality_minimal(temp_dir: Path):
    """测试最小化项目的质量分析."""
    skill_dir = temp_dir / "minimal-skill"
    skill_dir.mkdir()

    # 只创建最基本的文件
    (skill_dir / "SKILL.md").write_text("# Minimal")

    result = await _analyze_quality(skill_dir)

    assert result.overall_score >= 10  # 至少有 SKILL.md


def test_calculate_structure_score(temp_dir: Path):
    """测试结构评分计算."""
    skill_dir = temp_dir / "test-skill"
    skill_dir.mkdir()

    # 创建 SKILL.md (10 分)
    (skill_dir / "SKILL.md").write_text("# Test Skill")

    # 创建完整的目录结构
    for dir_name in ["references", "examples", "scripts", ".claude"]:
        (skill_dir / dir_name).mkdir()

    # 创建 pyproject.toml (5 分)
    (skill_dir / "pyproject.toml").write_text("[project]")

    # 创建 src/test_skill 结构 (10 分)
    src_dir = skill_dir / "src" / "test_skill"
    src_dir.mkdir(parents=True)
    (src_dir / "models").mkdir()
    (src_dir / "utils").mkdir()

    score = _calculate_structure_score(skill_dir)

    assert score == 40  # 满分: 10+5+5+5+10+5 = 40


def test_calculate_structure_score_partial(temp_dir: Path):
    """测试部分项目的结构评分."""
    skill_dir = temp_dir / "partial-skill"
    skill_dir.mkdir()

    # 只创建部分目录
    (skill_dir / "SKILL.md").write_text("# Partial")
    (skill_dir / "references").mkdir()
    (skill_dir / "pyproject.toml").write_text("[project]")

    score = _calculate_structure_score(skill_dir)

    assert score < 40  # 不是满分


# ==================== _generate_analysis_summary 测试 ====================


def test_generate_analysis_summary_excellent():
    """测试优秀质量的分析摘要生成."""
    from skill_creator_mcp.models.skill_config import QualityScore

    quality = QualityScore(
        overall_score=85.0,
        structure_score=30.0,
        documentation_score=25.0,
        test_coverage_score=30.0,
    )

    complexity_with_low = type("obj", (object,), {"cyclomatic_complexity": 4})
    complexity_with_high = type("obj", (object,), {"cyclomatic_complexity": 15})

    summary_low = _generate_analysis_summary(quality, complexity_with_low)
    summary_high = _generate_analysis_summary(quality, complexity_with_high)

    assert "优秀" in summary_low
    assert "复杂度低" in summary_low

    assert "复杂度较高" in summary_high


def test_generate_analysis_summary_poor():
    """测试较差质量的分析摘要生成."""
    from skill_creator_mcp.models.skill_config import QualityScore

    quality = QualityScore(
        overall_score=30.0,
        structure_score=10.0,
        documentation_score=5.0,
        test_coverage_score=15.0,
    )

    complexity_obj = type("obj", (object,), {"cyclomatic_complexity": 8})

    summary = _generate_analysis_summary(quality, complexity_obj)

    assert "需要改进" in summary
    assert "复杂度中等" in summary
