"""重构建议工具函数."""

from pathlib import Path
from typing import TYPE_CHECKING

from ..constants import (
    CODE_SIZE_LARGE_THRESHOLD,
    REFERENCE_FILE_LONG_THRESHOLD,
    REFERENCE_FILE_MAX_LINES,
    REFERENCE_FILE_MIN_LINES,
    SKILL_MD_RECOMMENDED_MAX_LINES,
)

if TYPE_CHECKING:
    from ..models.skill_config import (
        ComplexityMetrics,
        QualityScore,
        StructureAnalysis,
    )


def generate_refactor_suggestions(
    skill_dir: Path,
    structure: "StructureAnalysis",
    complexity: "ComplexityMetrics",
    quality: "QualityScore",
    focus_areas: list[str] | None = None,
) -> list[dict]:
    """生成重构建议.

    Args:
        skill_dir: 技能目录路径
        structure: 结构分析结果
        complexity: 复杂度指标
        quality: 质量评分
        focus_areas: 重点关注领域（可选）

    Returns:
        重构建议列表（字典格式）
    """
    suggestions: list[dict] = []

    # 如果指定了关注领域，只生成相关建议
    if focus_areas:
        focus_set = set(area.lower() for area in focus_areas)
        if "structure" not in focus_set and "结构" not in focus_set:
            return _filter_suggestions_by_focus(suggestions, focus_set)

    # 1. 基于结构评分生成建议
    if quality.structure_score < 20:
        suggestions.append(
            {
                "priority": "P0",
                "category": "structure",
                "issue": "项目结构不完整",
                "suggestion": (
                    "完善项目结构，添加必需的目录和文件（references、examples、scripts、.claude）"
                ),
                "impact": "high",
                "effort": "medium",
            }
        )

    # 2. 基于文档评分生成建议
    if quality.documentation_score < 15:
        suggestions.append(
            {
                "priority": "P1",
                "category": "documentation",
                "issue": "文档不足",
                "suggestion": "增加文档和示例，提高代码可读性",
                "impact": "medium",
                "effort": "low",
            }
        )

    # 3. 基于测试评分生成建议
    if quality.test_coverage_score < 15:
        suggestions.append(
            {
                "priority": "P0",
                "category": "testing",
                "issue": "测试覆盖率低",
                "suggestion": "增加测试用例，提高测试覆盖率至 95% 以上",
                "impact": "high",
                "effort": "high",
            }
        )

    # 4. 基于复杂度生成建议
    if complexity.cyclomatic_complexity and complexity.cyclomatic_complexity > 10:
        suggestions.append(
            {
                "priority": "P1",
                "category": "complexity",
                "issue": f"代码圈复杂度过高 ({complexity.cyclomatic_complexity})",
                "suggestion": "重构简化复杂逻辑，拆分大函数，减少嵌套层级",
                "impact": "high",
                "effort": "medium",
            }
        )

    # 5. 基于可维护性指数生成建议
    if complexity.maintainability_index and complexity.maintainability_index < 50:
        suggestions.append(
            {
                "priority": "P1",
                "category": "maintainability",
                "issue": f"可维护性指数低 ({complexity.maintainability_index:.1f})",
                "suggestion": "优化代码结构，增加注释，提高代码可读性",
                "impact": "medium",
                "effort": "medium",
            }
        )

    # 6. 基于文件数量生成建议
    if structure.total_files > 20:
        suggestions.append(
            {
                "priority": "P2",
                "category": "modularity",
                "issue": f"文件数量较多 ({structure.total_files})",
                "suggestion": "考虑模块化拆分，将相关功能组织到独立模块",
                "impact": "low",
                "effort": "high",
            }
        )

    # 7. 基于代码行数生成建议
    if structure.total_lines > CODE_SIZE_LARGE_THRESHOLD:
        suggestions.append(
            {
                "priority": "P2",
                "category": "size",
                "issue": f"代码行数较多 ({structure.total_lines})",
                "suggestion": "考虑拆分模块或提取独立包",
                "impact": "low",
                "effort": "high",
            }
        )

    # 8. SKILL.md 特定建议
    skill_md = skill_dir / "SKILL.md"
    if skill_md.exists():
        content = skill_md.read_text(encoding="utf-8")
        if len(content) > 3000:
            suggestions.append(
                {
                    "priority": "P2",
                    "category": "token-efficiency",
                    "issue": "SKILL.md 过长",
                    "suggestion": (
                        f"将详细内容移至 references/ 目录，"
                        f"保持 SKILL.md 在 {SKILL_MD_RECOMMENDED_MAX_LINES} 行以内"
                    ),
                    "impact": "medium",
                    "effort": "low",
                }
            )

    # 9. 检查 references 目录结构
    refs_dir = skill_dir / "references"
    if refs_dir.exists():
        for ref_file in refs_dir.glob("*.md"):
            content = ref_file.read_text(encoding="utf-8")
            if len(content.split("\n")) > REFERENCE_FILE_LONG_THRESHOLD:
                suggestions.append(
                    {
                        "priority": "P2",
                        "category": "documentation",
                        "issue": f"参考文档过长: {ref_file.name}",
                        "suggestion": (
                            f"拆分 {ref_file.name} 为多个小文件"
                            f"（每个 {REFERENCE_FILE_MIN_LINES}-"
                            f"{REFERENCE_FILE_MAX_LINES} 行）"
                        ),
                        "impact": "low",
                        "effort": "low",
                    }
                )

    # 10. 检查是否有重复的模式或代码
    _check_duplication_patterns(skill_dir, suggestions)

    focus_areas_set = set(area.lower() for area in (focus_areas or []))
    return _filter_suggestions_by_focus(suggestions, focus_areas_set)


def _filter_suggestions_by_focus(
    suggestions: list[dict],
    focus_set: set[str],
) -> list[dict]:
    """根据关注领域过滤建议.

    Args:
        suggestions: 所有建议
        focus_set: 关注领域集合

    Returns:
        过滤后的建议列表
    """
    if not focus_set:
        return suggestions

    # 创建映射关系
    focus_map: dict[str, set[str]] = {
        "structure": {"structure", "结构", "modularity", "模块化", "size", "大小"},
        "documentation": {"documentation", "文档", "token-efficiency", "token效率"},
        "testing": {"testing", "测试"},
        "complexity": {"complexity", "复杂度", "maintainability", "可维护性"},
        "code": {"duplication", "重复", "quality", "质量"},
    }

    # 收合所有匹配的关注领域
    matched_categories = set()
    for focus in focus_set:
        for category, keywords in focus_map.items():
            if focus in keywords:
                matched_categories.update(keywords)

    # 过滤建议
    filtered = []
    for suggestion in suggestions:
        category_lower = suggestion["category"].lower()
        issue_lower = suggestion["issue"].lower()
        # 检查是否有匹配的关注领域
        has_match = any(
            keyword in category_lower or keyword in issue_lower for keyword in matched_categories
        )
        if has_match:
            filtered.append(suggestion)

    return filtered


def _check_duplication_patterns(skill_dir: Path, suggestions: list[dict]) -> None:
    """检查重复的模式或代码.

    Args:
        skill_dir: 技能目录路径
        suggestions: 建议列表（会直接修改）
    """
    # 检查是否有重复的文档内容
    refs_dir = skill_dir / "references"
    if refs_dir.exists():
        ref_files = list(refs_dir.glob("*.md"))
        if len(ref_files) > 5:
            suggestions.append(
                {
                    "priority": "P2",
                    "category": "organization",
                    "issue": f"参考文档文件过多 ({len(ref_files)})",
                    "suggestion": "考虑合并相似主题的文档，或使用子目录组织",
                    "impact": "low",
                    "effort": "low",
                }
            )


def generate_refactor_report(
    skill_path: str,
    structure: "StructureAnalysis",
    complexity: "ComplexityMetrics",
    quality: "QualityScore",
    suggestions: list[dict],
) -> str:
    """生成重构报告.

    Args:
        skill_path: 技能路径
        structure: 结构分析结果
        complexity: 复杂度指标
        quality: 质量评分
        suggestions: 重构建议

    Returns:
        重构报告（Markdown 格式）
    """
    skill_dir = Path(skill_path)
    skill_name = skill_dir.name

    lines = []
    lines.append("# 重构分析报告\n")
    lines.append("## 当前状态评估\n")
    lines.append("### 基本信息")
    lines.append(f"- 技能名称：`{skill_name}`")
    lines.append(f"- 路径：`{skill_path}`")
    lines.append(f"- 文件数量：{structure.total_files}")
    lines.append(f"- 代码行数：{structure.total_lines}\n")

    lines.append("### 质量评分")
    lines.append(f"- 结构质量：{quality.structure_score:.0f}/100")
    lines.append(f"- 文档质量：{quality.documentation_score:.0f}/100")
    lines.append(f"- 测试质量：{quality.test_coverage_score:.0f}/100")
    lines.append(f"- **总体评分：{quality.overall_score:.0f}/100**\n")

    if complexity.cyclomatic_complexity:
        lines.append("### 复杂度指标")
        lines.append(f"- 圈复杂度：{complexity.cyclomatic_complexity}")
        if complexity.maintainability_index:
            lines.append(f"- 可维持性指数：{complexity.maintainability_index:.1f}")
        lines.append("")

    # 按优先级分组建议
    p0_suggestions = [s for s in suggestions if s["priority"] == "P0"]
    p1_suggestions = [s for s in suggestions if s["priority"] == "P1"]
    p2_suggestions = [s for s in suggestions if s["priority"] == "P2"]

    lines.append("## 发现的问题\n")

    if p0_suggestions:
        lines.append("### 严重问题 (P0) - 必须修复")
        for i, s in enumerate(p0_suggestions, 1):
            lines.append(f"{i}. **{s['issue']}**")
            lines.append(f"   - 类别：{s['category']}")
            lines.append(f"   - 建议：{s['suggestion']}")
            lines.append(f"   - 影响：{s['impact']} | 工作量：{s['effort']}\n")

    if p1_suggestions:
        lines.append("### 重要问题 (P1) - 建议修复")
        for i, s in enumerate(p1_suggestions, 1):
            lines.append(f"{i}. **{s['issue']}**")
            lines.append(f"   - 类别：{s['category']}")
            lines.append(f"   - 建议：{s['suggestion']}")
            lines.append(f"   - 影响：{s['impact']} | 工作量：{s['effort']}\n")

    if p2_suggestions:
        lines.append("### 优化建议 (P2) - 可选优化")
        for i, s in enumerate(p2_suggestions, 1):
            lines.append(f"{i}. **{s['issue']}**")
            lines.append(f"   - 类别：{s['category']}")
            lines.append(f"   - 建议：{s['suggestion']}")
            lines.append(f"   - 影响：{s['impact']} | 工作量：{s['effort']}\n")

    if not suggestions:
        lines.append("*未发现需要重构的问题，技能质量良好！*\n")

    lines.append("## 实施计划\n")

    if p0_suggestions:
        lines.append("### 第一阶段（必须）")
        for s in p0_suggestions:
            lines.append(f"- [ ] 修复：{s['issue']}")
        lines.append("")

    if p1_suggestions:
        lines.append("### 第二阶段（建议）")
        for s in p1_suggestions:
            lines.append(f"- [ ] 修复：{s['issue']}")
        lines.append("")

    if p2_suggestions:
        lines.append("### 第三阶段（可选）")
        for s in p2_suggestions:
            lines.append(f"- [ ] 优化：{s['issue']}")
        lines.append("")

    return "\n".join(lines)


def estimate_refactor_effort(suggestions: list[dict]) -> dict[str, int]:
    """估算重构工作量.

    Args:
        suggestions: 重构建议列表

    Returns:
        工作量估算（按优先级分组的小时数）
    """
    effort_map = {"low": 1, "medium": 4, "high": 8}

    p0_effort = sum(
        effort_map.get(s.get("effort", "medium"), 4) for s in suggestions if s["priority"] == "P0"
    )
    p1_effort = sum(
        effort_map.get(s.get("effort", "medium"), 4) for s in suggestions if s["priority"] == "P1"
    )
    p2_effort = sum(
        effort_map.get(s.get("effort", "medium"), 4) for s in suggestions if s["priority"] == "P2"
    )

    return {
        "p0_hours": p0_effort,
        "p1_hours": p1_effort,
        "p2_hours": p2_effort,
        "total_hours": p0_effort + p1_effort + p2_effort,
    }
