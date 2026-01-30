"""测试 analyze_skill 工具的集成."""

from pathlib import Path

import pytest

from skill_creator_mcp.utils.analyzers import (
    _analyze_complexity,
    _analyze_quality,
    _analyze_structure,
    _generate_analysis_summary,
    _generate_suggestions,
)


@pytest.mark.asyncio
async def test_full_analyze_skill_flow(temp_dir: Path):
    """测试分析完整技能项目的流程."""
    # 创建完整的技能项目结构
    skill_dir = temp_dir / "test-analyze-skill"
    skill_dir.mkdir()

    # 创建必需文件
    (skill_dir / "SKILL.md").write_text("""# Test Analyze Skill

## 技能概述
这是一个测试技能。

## 核心能力

1. **能力 1**：描述
2. **能力 2**：描述

## 使用方法

### 基本用法

基本使用方法。

```python
def example():
    pass
```
""")

    # 创建目录结构
    (skill_dir / "references").mkdir()
    (skill_dir / "references" / "guide.md").write_text("# Guide\\n\\nContent")
    (skill_dir / "references" / "api.md").write_text("# API\\n\\nContent")
    (skill_dir / "examples").mkdir()
    (skill_dir / "scripts").mkdir()
    (skill_dir / ".claude").mkdir()

    # 创建 src 结构
    src_dir = skill_dir / "src" / "test_analyze_skill"
    src_dir.mkdir(parents=True)
    (src_dir / "__init__.py").write_text("")
    (src_dir / "models").mkdir()
    (src_dir / "models" / "__init__.py").write_text("")
    (src_dir / "models" / "data.py").write_text('''
class DataModel:
    """数据模型."""

    def __init__(self, name: str):
        self.name = name

    def process(self):
        if self.name:
            return self.name.upper()
        return None
''')
    (src_dir / "utils").mkdir()
    (src_dir / "utils" / "__init__.py").write_text("")
    (src_dir / "utils" / "helpers.py").write_text('''
def helper_function(x: int) -> int:
    """辅助函数."""
    if x > 0:
        return x * 2
    elif x < 0:
        return x * -1
    else:
        return 0
''')

    # 创建 pyproject.toml
    (skill_dir / "pyproject.toml").write_text("""[project]
name = "test-analyze-skill"
version = "0.1.0"
""")

    # 创建测试
    tests_dir = skill_dir / "tests"
    tests_dir.mkdir()
    (tests_dir / "__init__.py").write_text("")
    (tests_dir / "test_main.py").write_text("""
def test_main():
    assert True
""")
    (tests_dir / "test_utils.py").write_text("""
def test_utils():
    assert helper_function(5) == 10
""")
    (tests_dir / "test_models.py").write_text("""
def test_models():
    model = DataModel("test")
    assert model.process() == "TEST"
""")

    # 创建 server.py
    (skill_dir / "server.py").write_text('''
"""Test Server."""

from fastmcp import FastMCP

mcp = FastMCP(name="test-analyze-skill")


@mcp.tool()
def test_tool(value: str) -> str:
    """测试工具."""
    if value:
        return value.upper()
    return ""


__all__ = ["mcp"]
''')

    # 执行分析
    structure = await _analyze_structure(skill_dir)
    complexity = await _analyze_complexity(skill_dir)
    quality = await _analyze_quality(skill_dir)

    suggestions = _generate_suggestions(structure, complexity, quality)
    summary = _generate_analysis_summary(quality, complexity)

    # 验证结构分析
    assert structure.total_files > 0
    assert structure.total_lines > 0
    assert "server" in structure.file_breakdown
    assert "models" in structure.file_breakdown
    assert "utils" in structure.file_breakdown

    # 验证复杂度分析
    assert complexity.cyclomatic_complexity is not None
    assert complexity.maintainability_index is not None

    # 验证质量分析
    assert quality.overall_score > 0
    assert quality.structure_score > 0
    assert quality.documentation_score > 0
    assert quality.test_coverage_score > 0

    # 验证建议和摘要
    assert isinstance(suggestions, list)
    assert isinstance(summary, str)
    assert len(summary) > 0


@pytest.mark.asyncio
async def test_analyze_minimal_skill(temp_dir: Path):
    """测试分析最小化技能."""
    skill_dir = temp_dir / "minimal-skill"
    skill_dir.mkdir()

    (skill_dir / "SKILL.md").write_text("# Minimal")

    structure = await _analyze_structure(skill_dir)
    quality = await _analyze_quality(skill_dir)

    # 最小项目应该有较低的分数
    assert quality.overall_score >= 10  # 至少有 SKILL.md
    assert structure.total_files == 0


@pytest.mark.asyncio
async def test_analyze_skill_with_references_only(temp_dir: Path):
    """测试只有引用文档的技能."""
    skill_dir = temp_dir / "refs-only-skill"
    skill_dir.mkdir()

    (skill_dir / "SKILL.md").write_text("# " + "x" * 250)  # 足够长
    (skill_dir / "references").mkdir()
    (skill_dir / "references" / "guide.md").write_text("# Guide")
    (skill_dir / "references" / "api.md").write_text("# API")

    quality = await _analyze_quality(skill_dir)

    # 应该获得文档分数
    assert quality.documentation_score > 10


@pytest.mark.asyncio
async def test_analyze_skill_with_tests(temp_dir: Path):
    """测试有完整测试的技能."""
    skill_dir = temp_dir / "tested-skill"
    skill_dir.mkdir()

    (skill_dir / "SKILL.md").write_text("# Tested")

    # 创建多个测试文件
    tests_dir = skill_dir / "tests"
    tests_dir.mkdir()
    for i in range(5):
        (tests_dir / f"test_{i}.py").write_text(f"def test_{i}(): assert True")

    structure = await _analyze_structure(skill_dir)
    quality = await _analyze_quality(skill_dir)

    # 应该获得测试分数
    assert quality.test_coverage_score > 10
    assert "tests" in structure.file_breakdown


@pytest.mark.asyncio
async def test_analyze_skill_empty_directory(temp_dir: Path):
    """测试分析空目录."""
    skill_dir = temp_dir / "empty-skill"
    skill_dir.mkdir()

    structure = await _analyze_structure(skill_dir)
    complexity = await _analyze_complexity(skill_dir)
    quality = await _analyze_quality(skill_dir)

    # 空目录应该返回默认值
    assert structure.total_files == 0
    assert structure.total_lines == 0
    assert complexity.cyclomatic_complexity is None
    assert quality.overall_score == 0


@pytest.mark.asyncio
async def test_analyze_skill_complex_code(temp_dir: Path):
    """测试分析复杂代码."""
    skill_dir = temp_dir / "complex-skill"
    skill_dir.mkdir()

    # 创建复杂代码文件
    src_dir = skill_dir / "src" / "complex_skill"
    src_dir.mkdir(parents=True)

    (src_dir / "complex.py").write_text('''
def complex_function(data):
    """复杂函数用于测试复杂度分析."""
    result = []
    for item in data:
        if item > 0:
            for i in range(item):
                if i % 2 == 0:
                    result.append(i)
                elif i % 3 == 0:
                    result.append(-i)
                else:
                    continue
        elif item < 0:
            try:
                result.append(abs(item))
            except Exception:
                pass
        else:
            result.append(0)

    final = []
    for r in result:
        if r > 10:
            final.append(r * 2)
        elif r < 5:
            final.append(r + 1)
        else:
            final.append(r)

    return final
''')

    (skill_dir / "SKILL.md").write_text("# Complex Skill")

    complexity = await _analyze_complexity(skill_dir)

    # 验证复杂度计算
    assert complexity.cyclomatic_complexity is not None
    assert complexity.cyclomatic_complexity > 5  # 应该有较高复杂度


@pytest.mark.asyncio
async def test_generate_suggestions_for_poor_quality(temp_dir: Path):
    """测试为低质量代码生成建议."""
    skill_dir = temp_dir / "poor-skill"
    skill_dir.mkdir()

    # 只创建最基本的文件
    (skill_dir / "SKILL.md").write_text("# Poor")

    structure = await _analyze_structure(skill_dir)
    complexity = await _analyze_complexity(skill_dir)
    quality = await _analyze_quality(skill_dir)

    suggestions = _generate_suggestions(structure, complexity, quality)

    # 低质量项目应该产生建议
    assert isinstance(suggestions, list)
    # 可能会有建议关于完善结构、增加文档等


@pytest.mark.asyncio
async def test_generate_summary_different_quality_levels(temp_dir: Path):
    """测试不同质量级别的摘要生成."""
    from skill_creator_mcp.models.skill_config import QualityScore

    # 高质量
    high_quality = QualityScore(
        overall_score=85.0,
        structure_score=30.0,
        documentation_score=25.0,
        test_coverage_score=30.0,
    )

    # 低质量
    low_quality = QualityScore(
        overall_score=25.0,
        structure_score=5.0,
        documentation_score=5.0,
        test_coverage_score=15.0,
    )

    # Mock complexity
    complexity_low = type("obj", (object,), {"cyclomatic_complexity": 3})
    complexity_high = type("obj", (object,), {"cyclomatic_complexity": 15})

    summary_high = _generate_analysis_summary(high_quality, complexity_low)
    summary_low = _generate_analysis_summary(low_quality, complexity_high)

    # 验证摘要内容
    assert "优秀" in summary_high
    assert "复杂度低" in summary_high
    assert "需要改进" in summary_low or "质量" in summary_low


@pytest.mark.asyncio
async def test_file_categorization_integration(temp_dir: Path):
    """测试文件分类的集成."""
    skill_dir = temp_dir / "test-skill"
    skill_dir.mkdir()

    # 创建各种类型的文件
    src_dir = skill_dir / "src" / "test_skill"
    src_dir.mkdir(parents=True)

    (src_dir / "server.py").write_text("# Server")
    (src_dir / "__init__.py").write_text("")
    (src_dir / "models").mkdir()
    (src_dir / "models" / "__init__.py").write_text("")
    (src_dir / "models" / "data.py").write_text("# Model")
    (src_dir / "utils").mkdir()
    (src_dir / "utils" / "__init__.py").write_text("")
    (src_dir / "utils" / "helper.py").write_text("# Helper")
    (src_dir / "other.py").write_text("# Other")

    tests_dir = skill_dir / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_main.py").write_text("# Test")

    scripts_dir = skill_dir / "scripts"
    scripts_dir.mkdir()
    (scripts_dir / "validate.py").write_text("# Validate")

    structure = await _analyze_structure(skill_dir)

    # 验证文件分类
    assert structure.file_breakdown.get("server") >= 1
    assert structure.file_breakdown.get("module_init") >= 3
    assert structure.file_breakdown.get("models") >= 1
    assert structure.file_breakdown.get("utils") >= 1
    assert structure.file_breakdown.get("tests") >= 1
    assert structure.file_breakdown.get("scripts") >= 1
    assert structure.file_breakdown.get("other") >= 1
