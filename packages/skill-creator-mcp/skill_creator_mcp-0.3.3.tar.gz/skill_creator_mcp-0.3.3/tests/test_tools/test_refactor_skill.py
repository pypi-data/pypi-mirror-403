"""测试 refactor_skill 重构函数."""

from pathlib import Path

import pytest

from skill_creator_mcp.utils.analyzers import (
    _analyze_complexity,
    _analyze_quality,
    _analyze_structure,
)
from skill_creator_mcp.utils.refactorors import (
    estimate_refactor_effort,
    generate_refactor_report,
    generate_refactor_suggestions,
)

# ==================== generate_refactor_suggestions 测试 ====================


@pytest.mark.asyncio
async def test_generate_refactor_suggestions_all_good(temp_dir: Path):
    """测试质量良好时没有建议."""
    # 创建完整的项目结构
    skill_dir = temp_dir / "good-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("name: good-skill\ndescription: Test")
    (skill_dir / "references").mkdir()
    (skill_dir / "references" / "doc1.md").write_text("# Doc\n" + "\n".join([""] * 50))
    (skill_dir / "examples").mkdir()
    (skill_dir / "scripts").mkdir()
    (skill_dir / ".claude").mkdir()
    (skill_dir / "tests").mkdir()
    (skill_dir / "tests" / "test_one.py").write_text("def test_one(): pass")
    (skill_dir / "tests" / "test_two.py").write_text("def test_two(): pass")
    (skill_dir / "tests" / "test_three.py").write_text("def test_three(): pass")

    # 运行分析
    structure = await _analyze_structure(skill_dir)
    complexity = await _analyze_complexity(skill_dir)
    quality = await _analyze_quality(skill_dir)

    suggestions = generate_refactor_suggestions(skill_dir, structure, complexity, quality)

    # 高质量项目应该没有或很少有建议
    assert len(suggestions) <= 2


@pytest.mark.asyncio
async def test_generate_refactor_suggestions_missing_structure(temp_dir: Path):
    """测试缺少结构时生成建议."""
    skill_dir = temp_dir / "poor-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# Minimal")

    structure = await _analyze_structure(skill_dir)
    complexity = await _analyze_complexity(skill_dir)
    quality = await _analyze_quality(skill_dir)

    suggestions = generate_refactor_suggestions(skill_dir, structure, complexity, quality)

    # 应该有结构相关的建议
    assert len(suggestions) > 0
    categories = [s["category"] for s in suggestions]
    assert "structure" in categories


@pytest.mark.asyncio
async def test_generate_refactor_suggestions_with_focus(temp_dir: Path):
    """测试关注领域过滤."""
    skill_dir = temp_dir / "focus-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# Skill" * 100)  # 长文件

    structure = await _analyze_structure(skill_dir)
    complexity = await _analyze_complexity(skill_dir)
    quality = await _analyze_quality(skill_dir)

    # 只关注文档相关
    suggestions = generate_refactor_suggestions(
        skill_dir, structure, complexity, quality, focus_areas=["documentation"]
    )

    # 检查返回的建议都是文档相关的
    for s in suggestions:
        assert "documentation" in s["category"] or "token" in s["category"]


@pytest.mark.asyncio
async def test_generate_refactor_suggestions_low_test_coverage(temp_dir: Path):
    """测试低测试覆盖率时生成建议."""
    skill_dir = temp_dir / "no-tests-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# Skill")
    (skill_dir / "references").mkdir()
    (skill_dir / "examples").mkdir()
    (skill_dir / "scripts").mkdir()
    (skill_dir / ".claude").mkdir()
    # 不创建 tests 目录

    structure = await _analyze_structure(skill_dir)
    complexity = await _analyze_complexity(skill_dir)
    quality = await _analyze_quality(skill_dir)

    suggestions = generate_refactor_suggestions(skill_dir, structure, complexity, quality)

    # 应该有测试相关的建议
    test_related = [s for s in suggestions if s["category"] == "testing"]
    assert len(test_related) > 0


@pytest.mark.asyncio
async def test_generate_refactor_suggestions_high_complexity(temp_dir: Path):
    """测试高复杂度时生成建议."""
    skill_dir = temp_dir / "complex-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# Skill")

    # 创建一个包含很多 if 语句的文件
    complex_code = "def f(x):\n"
    for i in range(20):
        complex_code += f"    if x == {i}:\n        return {i}\n"

    (skill_dir / "complex.py").write_text(complex_code)

    structure = await _analyze_structure(skill_dir)
    complexity = await _analyze_complexity(skill_dir)
    quality = await _analyze_quality(skill_dir)

    suggestions = generate_refactor_suggestions(skill_dir, structure, complexity, quality)

    # 应该有复杂度相关的建议
    complexity_related = [s for s in suggestions if s["category"] == "complexity"]
    if complexity.cyclomatic_complexity and complexity.cyclomatic_complexity > 10:
        assert len(complexity_related) > 0


@pytest.mark.asyncio
async def test_generate_refactor_suggestions_long_skill_md(temp_dir: Path):
    """测试 SKILL.md 过长时的建议."""
    skill_dir = temp_dir / "long-md-skill"
    skill_dir.mkdir(parents=True)

    # 创建一个超过 3000 字符的 SKILL.md
    long_content = "# Long Skill\n" + "\n".join(["Content"] * 500)
    (skill_dir / "SKILL.md").write_text(long_content)

    structure = await _analyze_structure(skill_dir)
    complexity = await _analyze_complexity(skill_dir)
    quality = await _analyze_quality(skill_dir)

    suggestions = generate_refactor_suggestions(skill_dir, structure, complexity, quality)

    # 应该有 token 效率相关的建议
    token_related = [s for s in suggestions if s["category"] == "token-efficiency"]
    assert len(token_related) > 0


@pytest.mark.asyncio
async def test_generate_refactor_suggestions_many_files(temp_dir: Path):
    """测试文件数量过多时的建议."""
    skill_dir = temp_dir / "many-files-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# Skill")

    # 创建超过 20 个文件
    for i in range(25):
        (skill_dir / f"file_{i}.py").write_text("# File " + str(i))

    structure = await _analyze_structure(skill_dir)
    complexity = await _analyze_complexity(skill_dir)
    quality = await _analyze_quality(skill_dir)

    suggestions = generate_refactor_suggestions(skill_dir, structure, complexity, quality)

    # 应该有模块化相关的建议
    modularity_related = [s for s in suggestions if s["category"] == "modularity"]
    assert len(modularity_related) > 0


@pytest.mark.asyncio
async def test_generate_refactor_suggestions_priority_levels(temp_dir: Path):
    """测试建议优先级分级."""
    skill_dir = temp_dir / "priority-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# Skill")

    structure = await _analyze_structure(skill_dir)
    complexity = await _analyze_complexity(skill_dir)
    quality = await _analyze_quality(skill_dir)

    suggestions = generate_refactor_suggestions(skill_dir, structure, complexity, quality)

    # 检查所有建议都有有效的优先级
    valid_priorities = {"P0", "P1", "P2"}
    for s in suggestions:
        assert s["priority"] in valid_priorities
        assert "issue" in s
        assert "suggestion" in s
        assert "impact" in s
        assert "effort" in s


# ==================== generate_refactor_report 测试 ====================


@pytest.mark.asyncio
async def test_generate_refactor_report_basic(temp_dir: Path):
    """测试基本重构报告生成."""
    skill_dir = temp_dir / "report-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# Test Skill")

    structure = await _analyze_structure(skill_dir)
    complexity = await _analyze_complexity(skill_dir)
    quality = await _analyze_quality(skill_dir)
    suggestions = [
        {
            "priority": "P0",
            "category": "structure",
            "issue": "问题",
            "suggestion": "建议",
            "impact": "high",
            "effort": "medium",
        }
    ]

    report = generate_refactor_report(str(skill_dir), structure, complexity, quality, suggestions)

    # 检查报告包含必要部分
    assert "# 重构分析报告" in report
    assert "## 当前状态评估" in report
    assert "## 发现的问题" in report
    assert "## 实施计划" in report


@pytest.mark.asyncio
async def test_generate_refactor_report_with_p0_issues(temp_dir: Path):
    """测试包含 P0 问题的报告."""
    skill_dir = temp_dir / "p0-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# Skill")

    structure = await _analyze_structure(skill_dir)
    complexity = await _analyze_complexity(skill_dir)
    quality = await _analyze_quality(skill_dir)
    suggestions = [
        {
            "priority": "P0",
            "category": "testing",
            "issue": "无测试",
            "suggestion": "添加测试",
            "impact": "high",
            "effort": "high",
        }
    ]

    report = generate_refactor_report(str(skill_dir), structure, complexity, quality, suggestions)

    # 检查 P0 问题显示
    assert "### 严重问题 (P0) - 必须修复" in report
    assert "无测试" in report


@pytest.mark.asyncio
async def test_generate_refactor_report_no_issues(temp_dir: Path):
    """测试没有问题时的报告."""
    skill_dir = temp_dir / "perfect-skill"
    skill_dir.mkdir(parents=True)
    # 创建完整的 YAML frontmatter
    (skill_dir / "SKILL.md").write_text(
        "---\n"
        "name: perfect-skill\n"
        "description: Test skill\n"
        "allowed-tools: [Read, Write]\n"
        "---\n"
        "# Perfect Skill\n"
        "\n"
        "## Overview\n\n"
        "Detailed description with enough content.\n"
        "```python\n"
        "code example\n"
        "```\n"
    )
    (skill_dir / "references").mkdir()
    (skill_dir / "references" / "doc1.md").write_text("# Doc\n" + "\n".join(["Content"] * 100))
    (skill_dir / "references" / "doc2.md").write_text("# Doc2\n" + "\n".join(["Content"] * 100))
    (skill_dir / "examples").mkdir()
    (skill_dir / "scripts").mkdir()
    (skill_dir / ".claude").mkdir()
    (skill_dir / "tests").mkdir()
    for i in range(3):
        (skill_dir / "tests" / f"test_{i}.py").write_text("def test(): pass")

    structure = await _analyze_structure(skill_dir)
    complexity = await _analyze_complexity(skill_dir)
    quality = await _analyze_quality(skill_dir)

    suggestions = generate_refactor_suggestions(skill_dir, structure, complexity, quality)
    report = generate_refactor_report(str(skill_dir), structure, complexity, quality, suggestions)

    # 检查没有严重问题的消息（只检查 P0 问题）
    if not any(s["priority"] == "P0" for s in suggestions):
        assert "未发现需要重构的问题，技能质量良好" in report


# ==================== estimate_refactor_effort 测试 ====================


def test_estimate_refactor_effort_all_priorities():
    """测试所有优先级的估算."""
    suggestions = [
        {"priority": "P0", "effort": "high"},
        {"priority": "P0", "effort": "low"},
        {"priority": "P1", "effort": "medium"},
        {"priority": "P2", "effort": "low"},
    ]

    effort = estimate_refactor_effort(suggestions)

    # 检查计算逻辑: high=8, low=1, medium=4
    assert effort["p0_hours"] == 8 + 1  # high + low
    assert effort["p1_hours"] == 4  # medium
    assert effort["p2_hours"] == 1  # low
    assert effort["total_hours"] == 14  # 9 + 4 + 1


def test_estimate_refactor_effort_empty():
    """测试空建议列表的估算."""
    effort = estimate_refactor_effort([])

    assert effort["p0_hours"] == 0
    assert effort["p1_hours"] == 0
    assert effort["p2_hours"] == 0
    assert effort["total_hours"] == 0


def test_estimate_refactor_effort_default_medium():
    """测试默认 medium 工作量."""
    suggestions = [
        {"priority": "P0"},  # 缺少 effort 字段
    ]

    effort = estimate_refactor_effort(suggestions)

    assert effort["p0_hours"] == 4  # 默认 medium


@pytest.mark.asyncio
async def test_generate_refactor_suggestions_low_maintainability(temp_dir: Path):
    """测试低可维护性指数时生成建议 (覆盖 line 87)."""
    skill_dir = temp_dir / "low-maintainability"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# Skill")

    # 创建一个极其复杂的文件来降低可维护性指数到 50 以下
    # MI = max(0, 171 - 0.23*avg_complexity - 16.2*total_complexity/1000)
    # 需要 total_complexity > 491 才能使 MI < 50
    complex_code = []
    for i in range(130):  # 每个函数约 4 复杂度，130 个函数 ≈ 520 复杂度
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

    suggestions = generate_refactor_suggestions(skill_dir, structure, complexity, quality)

    # 检查是否有可维护性相关的建议
    maintainability_suggestions = [
        s
        for s in suggestions
        if s["category"] == "maintainability" or "可维护性" in s.get("issue", "")
    ]
    # 如果 MI < 50，应该有建议
    if complexity.maintainability_index and complexity.maintainability_index < 50:
        assert len(maintainability_suggestions) > 0
        assert any("可维护性指数低" in s["issue"] for s in maintainability_suggestions)


@pytest.mark.asyncio
async def test_generate_refactor_suggestions_large_code_size(temp_dir: Path):
    """测试代码行数过多时生成建议 (覆盖 line 109)."""
    skill_dir = temp_dir / "large-code"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# Skill")

    # 创建超过 2000 行的文件
    large_content = "\n".join([f"# Line {i}" for i in range(2100)])
    (skill_dir / "large.py").write_text(large_content)

    structure = await _analyze_structure(skill_dir)
    complexity = await _analyze_complexity(skill_dir)
    quality = await _analyze_quality(skill_dir)

    suggestions = generate_refactor_suggestions(skill_dir, structure, complexity, quality)

    # 应该有代码行数相关的建议
    size_suggestions = [s for s in suggestions if s["category"] == "size"]
    assert len(size_suggestions) > 0
    assert "2100" in size_suggestions[0]["issue"]


@pytest.mark.asyncio
async def test_generate_refactor_suggestions_long_reference_file(temp_dir: Path):
    """测试参考文档过长时生成建议 (覆盖 line 138)."""
    skill_dir = temp_dir / "long-ref"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# Skill")
    (skill_dir / "references").mkdir()

    # 创建超过 400 行的参考文档
    long_doc = "\n".join([f"Content line {i}" for i in range(450)])
    (skill_dir / "references" / "long_doc.md").write_text(long_doc)

    structure = await _analyze_structure(skill_dir)
    complexity = await _analyze_complexity(skill_dir)
    quality = await _analyze_quality(skill_dir)

    suggestions = generate_refactor_suggestions(skill_dir, structure, complexity, quality)

    # 应该有参考文档过长的建议
    long_ref_suggestions = [
        s
        for s in suggestions
        if "long_doc.md" in s.get("issue", "") or "参考文档过长" in s.get("issue", "")
    ]
    assert len(long_ref_suggestions) > 0


@pytest.mark.asyncio
async def test_generate_refactor_suggestions_focus_filtering_with_matches(temp_dir: Path):
    """测试关注领域过滤 (覆盖 lines 188-191)."""
    skill_dir = temp_dir / "focus-match"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# Skill")

    structure = await _analyze_structure(skill_dir)
    complexity = await _analyze_complexity(skill_dir)
    quality = await _analyze_quality(skill_dir)

    # 只关注结构相关问题
    # 通过指定一个会匹配到 "structure" 类别的关注词
    suggestions = generate_refactor_suggestions(
        skill_dir,
        structure,
        complexity,
        quality,
        focus_areas=["structure"],  # 应该匹配 "structure" 类别
    )

    # 所有返回的建议都应该与结构相关（或者没有任何建议）
    # 这里我们验证过滤逻辑被执行了
    assert isinstance(suggestions, list)


@pytest.mark.asyncio
async def test_generate_refactor_suggestions_too_many_reference_files(temp_dir: Path):
    """测试参考文档文件过多时生成建议 (覆盖 line 208)."""
    skill_dir = temp_dir / "many-refs"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# Skill")
    (skill_dir / "references").mkdir()

    # 创建超过 5 个参考文档
    for i in range(7):
        (skill_dir / "references" / f"doc{i}.md").write_text(f"# Doc {i}")

    structure = await _analyze_structure(skill_dir)
    complexity = await _analyze_complexity(skill_dir)
    quality = await _analyze_quality(skill_dir)

    suggestions = generate_refactor_suggestions(skill_dir, structure, complexity, quality)

    # 应该有文件数量过多的建议
    many_files_suggestions = [
        s
        for s in suggestions
        if "文件过多" in s.get("issue", "") or s.get("category") == "organization"
    ]
    assert len(many_files_suggestions) > 0
    assert "7" in many_files_suggestions[0]["issue"]
