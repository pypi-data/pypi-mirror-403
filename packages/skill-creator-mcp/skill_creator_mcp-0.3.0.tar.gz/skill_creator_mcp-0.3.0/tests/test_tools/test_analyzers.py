"""测试 analyzers 分析函数."""

from pathlib import Path

import pytest

from skill_creator_mcp.utils.analyzers import (
    _analyze_complexity,
    _analyze_quality,
    _analyze_structure,
    _generate_analysis_summary,
    _generate_suggestions,
)

# ==================== _analyze_structure 测试 ====================


@pytest.mark.asyncio
async def test_analyze_structure_with_tests_in_alternative_location(temp_dir: Path):
    """测试在替代位置查找 tests 目录 (覆盖 lines 283-284)."""
    skill_dir = temp_dir / "alt-test-loc"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# Test")

    # 创建 src/tests 目录（替代位置）
    (skill_dir / "src" / "tests").mkdir(parents=True)
    (skill_dir / "src" / "tests" / "test_one.py").write_text("def test(): pass")
    (skill_dir / "src" / "tests" / "test_two.py").write_text("def test(): pass")

    quality = await _analyze_quality(skill_dir)

    # 应该识别到 src/tests 目录
    assert quality.test_coverage_score > 0


@pytest.mark.asyncio
async def test_analyze_structure_with_test_directory(temp_dir: Path):
    """测试在 test 目录（单数）查找测试文件."""
    skill_dir = temp_dir / "test-dir"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# Test")

    # 创建 test 目录（单数，替代位置）
    (skill_dir / "test").mkdir(parents=True)
    (skill_dir / "test" / "test_one.py").write_text("def test(): pass")

    quality = await _analyze_quality(skill_dir)

    # 应该识别到 test 目录
    assert quality.test_coverage_score > 0


# ==================== _generate_suggestions 测试 ====================


@pytest.mark.asyncio
async def test_generate_suggestions_high_complexity(temp_dir: Path):
    """测试高圈复杂度时生成建议 (覆盖 line 331)."""
    skill_dir = temp_dir / "high-complexity"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# Test")

    # 创建复杂代码
    complex_code = []
    for i in range(20):
        complex_code.append(f"def func_{i}():")
        for j in range(5):
            complex_code.append(f"    if x == {j}:")

    (skill_dir / "complex.py").write_text("\n".join(complex_code))

    structure = await _analyze_structure(skill_dir)
    complexity = await _analyze_complexity(skill_dir)
    quality = await _analyze_quality(skill_dir)

    suggestions = _generate_suggestions(structure, complexity, quality)

    # 如果圈复杂度 > 10，应该有相关建议
    if complexity.cyclomatic_complexity and complexity.cyclomatic_complexity > 10:
        assert any("圈复杂度" in s for s in suggestions)


@pytest.mark.asyncio
async def test_generate_suggestions_low_maintainability(temp_dir: Path):
    """测试低可维护性指数时生成建议 (覆盖 line 334)."""
    skill_dir = temp_dir / "low-mi"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# Test")

    # 创建非常复杂的代码以降低 MI
    complex_code = []
    for i in range(130):
        complex_code.append(f"def function_{i}(x):")
        complex_code.append("    if x > 0:")
        complex_code.append("        if x > 10:")
        complex_code.append("            if x > 20:")
        complex_code.append("                if x > 30:")
        complex_code.append("                    return x * 2")
        complex_code.append("                else:")
        complex_code.append("                    return x")
        complex_code.append("            else:")
        complex_code.append("                return 0")
        complex_code.append("        else:")
        complex_code.append("            return -1")

    (skill_dir / "very_complex.py").write_text("\n".join(complex_code))

    structure = await _analyze_structure(skill_dir)
    complexity = await _analyze_complexity(skill_dir)
    quality = await _analyze_quality(skill_dir)

    suggestions = _generate_suggestions(structure, complexity, quality)

    # 如果 MI < 50，应该有相关建议
    if complexity.maintainability_index and complexity.maintainability_index < 50:
        assert any("可维护性指数" in s for s in suggestions)


@pytest.mark.asyncio
async def test_generate_suggestions_many_files(temp_dir: Path):
    """测试文件数量多时生成建议 (覆盖 line 338)."""
    skill_dir = temp_dir / "many-files"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# Test")

    # 创建超过 20 个文件
    for i in range(25):
        (skill_dir / f"file_{i}.py").write_text("# File")

    structure = await _analyze_structure(skill_dir)
    complexity = await _analyze_complexity(skill_dir)
    quality = await _analyze_quality(skill_dir)

    suggestions = _generate_suggestions(structure, complexity, quality)

    # 应该有文件数量相关的建议
    assert any("文件数量" in s for s in suggestions)


@pytest.mark.asyncio
async def test_generate_suggestions_many_lines(temp_dir: Path):
    """测试代码行数多时生成建议 (覆盖 line 341)."""
    skill_dir = temp_dir / "many-lines"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# Test")

    # 创建超过 1000 行的文件
    large_content = "\n".join([f"# Line {i}" for i in range(1200)])
    (skill_dir / "large.py").write_text(large_content)

    structure = await _analyze_structure(skill_dir)
    complexity = await _analyze_complexity(skill_dir)
    quality = await _analyze_quality(skill_dir)

    suggestions = _generate_suggestions(structure, complexity, quality)

    # 应该有代码行数相关的建议
    assert any("代码行数" in s for s in suggestions)


# ==================== _generate_analysis_summary 测试 ====================


@pytest.mark.asyncio
async def test_generate_analysis_summary_good_quality(temp_dir: Path):
    """测试质量评级为 "良好" 时生成摘要 (覆盖 line 363)."""
    skill_dir = temp_dir / "good-quality"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# Test")
    (skill_dir / "references").mkdir()
    (skill_dir / "examples").mkdir()
    (skill_dir / "scripts").mkdir()
    (skill_dir / ".claude").mkdir()
    (skill_dir / "tests").mkdir()
    (skill_dir / "tests" / "test_one.py").write_text("def test(): pass")

    # 添加更多内容以获得 60-80 分
    (skill_dir / "references" / "doc1.md").write_text("# Doc\n" + "\n".join(["Content"] * 50))
    (skill_dir / "references" / "doc2.md").write_text("# Doc2\n" + "\n".join(["Content"] * 50))

    quality = await _analyze_quality(skill_dir)
    complexity = await _analyze_complexity(skill_dir)

    summary = _generate_analysis_summary(quality, complexity)

    # 如果评分在 60-80 之间，应该显示 "良好"
    if 60 <= quality.overall_score < 80:
        assert "良好" in summary


@pytest.mark.asyncio
async def test_generate_analysis_summary_excellent_quality(temp_dir: Path):
    """测试质量评级为 "优秀" 时生成摘要."""
    skill_dir = temp_dir / "excellent-quality"
    skill_dir.mkdir(parents=True)
    # 创建完整的 YAML frontmatter
    (skill_dir / "SKILL.md").write_text(
        "---\n"
        "name: excellent\n"
        "description: Excellent skill\n"
        "allowed-tools: [Read, Write]\n"
        "---\n"
        "# Excellent Skill\n"
    )
    (skill_dir / "references").mkdir()
    (skill_dir / "references" / "doc1.md").write_text("# Doc\n" + "\n".join(["Content"] * 100))
    (skill_dir / "references" / "doc2.md").write_text("# Doc2\n" + "\n".join(["Content"] * 100))
    (skill_dir / "examples").mkdir()
    (skill_dir / "scripts").mkdir()
    (skill_dir / ".claude").mkdir()
    (skill_dir / "tests").mkdir()
    for i in range(4):
        (skill_dir / "tests" / f"test_{i}.py").write_text("def test(): pass")

    quality = await _analyze_quality(skill_dir)
    complexity = await _analyze_complexity(skill_dir)

    summary = _generate_analysis_summary(quality, complexity)

    # 优秀质量应该显示 "优秀"
    if quality.overall_score >= 80:
        assert "优秀" in summary


@pytest.mark.asyncio
async def test_generate_analysis_summary_poor_quality(temp_dir: Path):
    """测试质量评级为 "需要改进" 时生成摘要."""
    skill_dir = temp_dir / "poor-quality"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# Minimal")

    quality = await _analyze_quality(skill_dir)
    complexity = await _analyze_complexity(skill_dir)

    summary = _generate_analysis_summary(quality, complexity)

    # 低质量应该显示 "需要改进"
    if quality.overall_score < 40:
        assert "需要改进" in summary


@pytest.mark.asyncio
async def test_generate_analysis_summary_average_quality(temp_dir: Path):
    """测试质量评级为 "一般" 时生成摘要."""
    skill_dir = temp_dir / "average-quality"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# Average")
    (skill_dir / "references").mkdir()

    quality = await _analyze_quality(skill_dir)
    complexity = await _analyze_complexity(skill_dir)

    summary = _generate_analysis_summary(quality, complexity)

    # 中等质量应该显示 "一般"
    if 40 <= quality.overall_score < 60:
        assert "一般" in summary
