"""代码分析工具函数."""

import ast
import asyncio
import logging
from pathlib import Path
from typing import TYPE_CHECKING

from ..constants import (
    CODE_SIZE_MANY_LINES_THRESHOLD,
    MI_AVG_COMPLEXITY_COEFFICIENT,
    MI_BASE_CONSTANT,
    MI_COMPLEXITY_SCALE,
    MI_TOTAL_COMPLEXITY_COEFFICIENT,
)

if TYPE_CHECKING:
    from ..models.skill_config import (
        ComplexityMetrics,
        QualityScore,
        StructureAnalysis,
    )

logger = logging.getLogger(__name__)


async def _analyze_structure(skill_dir: Path) -> "StructureAnalysis":
    """分析代码结构.

    Args:
        skill_dir: 技能目录路径

    Returns:
        结构分析结果
    """
    from ..models.skill_config import StructureAnalysis

    total_files = 0
    total_lines = 0
    file_breakdown: dict[str, int] = {}

    # 遍历所有 Python 文件
    for py_file in skill_dir.rglob("*.py"):
        if "__pycache__" in str(py_file):
            continue

        total_files += 1
        try:
            # 使用 asyncio.to_thread 避免阻塞事件循环
            lines = await asyncio.to_thread(py_file.read_text, encoding="utf-8")
            total_lines += len(lines.splitlines())
        except (OSError, UnicodeDecodeError) as e:
            logger.debug(f"无法读取文件 {py_file}: {e}")

        # 分类统计
        category = _categorize_file(py_file, skill_dir)
        file_breakdown[category] = file_breakdown.get(category, 0) + 1

    return StructureAnalysis(
        total_files=total_files,
        total_lines=total_lines,
        file_breakdown=file_breakdown,
    )


def _categorize_file(file_path: Path, base_dir: Path) -> str:
    """对文件进行分类.

    Args:
        file_path: 文件路径
        base_dir: 基础目录

    Returns:
        文件类别
    """
    relative_path = file_path.relative_to(base_dir)

    if "tests" in str(relative_path):
        return "tests"
    elif relative_path.name.startswith("test_"):
        return "tests"
    elif relative_path.name == "__init__.py":
        return "module_init"
    elif "models" in str(relative_path):
        return "models"
    elif "utils" in str(relative_path):
        return "utils"
    elif "server.py" in str(relative_path):
        return "server"
    elif "scripts" in str(relative_path):
        return "scripts"
    else:
        return "other"


async def _analyze_complexity(skill_dir: Path) -> "ComplexityMetrics":
    """分析代码复杂度.

    Args:
        skill_dir: 技能目录路径

    Returns:
        复杂度指标
    """
    from ..models.skill_config import ComplexityMetrics

    total_complexity = 0
    file_count = 0
    trees: list[ast.AST] = []  # 收集所有 AST 树用于代码重复检测

    for py_file in skill_dir.rglob("*.py"):
        if "__pycache__" in str(py_file) or ".venv" in str(py_file):
            continue

        try:
            # 使用 asyncio.to_thread 避免阻塞事件循环
            content = await asyncio.to_thread(py_file.read_text, encoding="utf-8")

            # 使用 AST 分析圈复杂度
            tree = ast.parse(content)
            trees.append(tree)  # 收集树
            complexity = _calculate_cyclomatic_complexity(tree)
            total_complexity += complexity
            file_count += 1
        except (SyntaxError, ValueError) as e:
            logger.debug(f"无法解析文件 {py_file}: {e}")

    avg_complexity = total_complexity / file_count if file_count > 0 else 0

    # 可维护性指数（简化计算）
    maintainability = max(
        0,
        MI_BASE_CONSTANT
        - MI_AVG_COMPLEXITY_COEFFICIENT * avg_complexity
        - MI_TOTAL_COMPLEXITY_COEFFICIENT * (total_complexity / MI_COMPLEXITY_SCALE),
    )

    return ComplexityMetrics(
        cyclomatic_complexity=int(avg_complexity) if avg_complexity > 0 else None,
        maintainability_index=float(maintainability) if file_count > 0 else None,
        code_duplication=_detect_code_duplication(trees) if trees else None,
    )


def _detect_code_duplication(trees: list[ast.AST]) -> float:
    """检测代码重复率.

    使用基于 AST 结构相似度的算法检测重复代码。

    Args:
        trees: 所有 Python 文件的 AST 列表

    Returns:
        重复代码百分比 (0-100)
    """
    if not trees:
        return 0.0

    # 1. 提取所有函数定义的 AST 节点
    function_nodes = []
    for tree in trees:
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                # 只分析有一定长度的函数（过滤掉简单的单行函数）
                node_length = _count_ast_nodes(node)
                if node_length >= 5:  # 至少 5 个 AST 节点才考虑
                    function_nodes.append(node)

    if len(function_nodes) < 2:
        return 0.0

    # 2. 使用集合跟踪已处理的函数索引
    processed_indices: set[int] = set()

    # 3. 规范化 AST 并比较相似度
    duplicates = 0
    total_lines = 0

    for i, func1 in enumerate(function_nodes):
        if i in processed_indices:
            continue

        normalized1 = _normalize_ast(func1)
        lines1 = _count_ast_nodes(func1)

        for j in range(i + 1, len(function_nodes)):
            func2 = function_nodes[j]
            if j in processed_indices:
                continue

            normalized2 = _normalize_ast(func2)
            lines2 = _count_ast_nodes(func2)

            # 计算相似度（使用简单的节点类型序列匹配）
            similarity = _calculate_ast_similarity(normalized1, normalized2)

            # 如果相似度超过 80%，认为是重复代码
            if similarity >= 0.8 and min(lines1, lines2) >= 10:
                duplicates += min(lines1, lines2)
                processed_indices.add(j)  # 标记为重复，避免重复计数
                total_lines += max(lines1, lines2)

    # 4. 计算总代码行数和重复行数
    total_code_lines = sum(_count_ast_nodes(tree) for tree in trees)
    if total_code_lines == 0:
        return 0.0

    # 重复率 = 重复行数 / 总行数 * 100
    return round((duplicates / total_code_lines) * 100, 2)


def _count_ast_nodes(node: ast.AST) -> int:
    """计算 AST 节点数量."""
    return len(list(ast.walk(node)))


def _normalize_ast(node: ast.AST) -> list[str]:
    """规范化 AST，提取结构特征。

    移除字面量、变量名等，只保留结构信息。
    """
    normalized = []

    for child in ast.walk(node):
        # 记录节点类型
        normalized.append(type(child).__name__)

        # 跳过字面量和变量名（这些在比较时应该被忽略）
        # ast.Str 和 ast.Num 在 Python 3.8+ 已合并到 ast.Constant
        if isinstance(child, ast.Constant):
            continue
        if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Store):
            continue

    return normalized


def _calculate_ast_similarity(ast1: list[str], ast2: list[str]) -> float:
    """计算两个 AST 序列的相似度.

    使用最长公共子序列 (LCS) 算法。
    """
    if not ast1 or not ast2:
        return 0.0

    # 使用简单的 Jaccard 相似度（交集 / 并集）
    set1 = set(ast1)
    set2 = set(ast2)

    intersection = len(set1 & set2)
    union = len(set1 | set2)

    if union == 0:
        return 0.0

    return intersection / union


def _calculate_cyclomatic_complexity(tree: ast.AST) -> int:
    """计算圈复杂度.

    Args:
        tree: AST 树

    Returns:
        圈复杂度
    """
    complexity = 1  # 基础复杂度

    for node in ast.walk(tree):
        if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
            complexity += 1
        elif isinstance(node, (ast.And, ast.Or)):
            complexity += 1
        elif isinstance(node, ast.ListComp):
            complexity += 1
        elif isinstance(node, ast.DictComp):
            complexity += 1

    return complexity


async def _analyze_quality(skill_dir: Path) -> "QualityScore":
    """分析代码质量.

    Args:
        skill_dir: 技能目录路径

    Returns:
        质量评分
    """
    from ..models.skill_config import QualityScore

    # 结构评分 (0-40)
    structure_score = _calculate_structure_score(skill_dir)

    # 文档评分 (0-30) - 现在是异步的
    documentation_score = await _calculate_documentation_score(skill_dir)

    # 测试覆盖率评分 (0-30)
    test_score = _calculate_test_score(skill_dir)

    overall = structure_score + documentation_score + test_score

    return QualityScore(
        overall_score=float(overall),
        structure_score=float(structure_score),
        documentation_score=float(documentation_score),
        test_coverage_score=float(test_score),
    )


def _calculate_structure_score(skill_dir: Path) -> float:
    """计算结构评分 (0-40).

    Args:
        skill_dir: 技能目录路径

    Returns:
        结构评分
    """
    score = 0.0

    # 检查是否有 SKILL.md (10 分)
    if (skill_dir / "SKILL.md").exists():
        score += 10

    # 检查是否有 references 目录 (5 分)
    if (skill_dir / "references").exists():
        score += 5

    # 检查是否有 examples 目录 (5 分)
    if (skill_dir / "examples").exists():
        score += 5

    # 检查是否有 scripts 目录 (5 分)
    if (skill_dir / "scripts").exists():
        score += 5

    # 检查是否使用模块化结构 (10 分)
    # 检查是否有 src 目录且包含 models 和 utils 子目录
    src_dir = skill_dir / "src"
    if src_dir.exists():
        # 检查任意子目录是否有 models 和 utils
        has_modular_structure = False
        for sub_dir in src_dir.iterdir():
            if sub_dir.is_dir():
                has_models = (sub_dir / "models").exists()
                has_utils = (sub_dir / "utils").exists()
                if has_models and has_utils:
                    has_modular_structure = True
                    break
        if has_modular_structure:
            score += 10

    # 检查是否配置了项目工具 (5 分)
    if (skill_dir / "pyproject.toml").exists():
        score += 5

    return min(score, 40.0)


async def _calculate_documentation_score(skill_dir: Path) -> float:
    """计算文档评分 (0-30).

    Args:
        skill_dir: 技能目录路径

    Returns:
        文档评分
    """
    score = 0.0

    # 检查 SKILL.md 质量 (20 分)
    skill_md = skill_dir / "SKILL.md"
    if skill_md.exists():
        # 使用 asyncio.to_thread 避免阻塞事件循环
        content = await asyncio.to_thread(skill_md.read_text, encoding="utf-8")
        if len(content) > 200:
            score += 10  # 有足够的内容
        if "##" in content:
            score += 5  # 有二级标题
        if "```" in content:
            score += 5  # 有代码示例

    # 检查 references 文档 (10 分)
    refs_dir = skill_dir / "references"
    if refs_dir.exists():
        ref_files = list(refs_dir.glob("*.md"))
        if len(ref_files) >= 2:
            score += 10

    return min(score, 30.0)


def _calculate_test_score(skill_dir: Path) -> float:
    """计算测试评分 (0-30).

    Args:
        skill_dir: 技能目录路径

    Returns:
        测试评分
    """
    score = 0.0

    # 检查是否有 tests 目录 (10 分)
    tests_dir = skill_dir / "tests"
    if not tests_dir.exists():
        # 尝试在其他位置查找
        possible_tests = [
            skill_dir / "src" / "tests",
            skill_dir / "test",
        ]
        for possible in possible_tests:
            if possible.exists():
                tests_dir = possible
                break

    if tests_dir.exists():
        score += 10

        # 检查测试文件数量 (10 分)
        test_files = list(tests_dir.rglob("test_*.py"))
        if len(test_files) >= 3:
            score += 10

        # 检查测试覆盖率 (10 分)
        # 这里简化处理，实际应该运行 pytest --cov
        if len(test_files) > 0:
            score += 10

    return min(score, 30.0)


def _generate_suggestions(
    structure: "StructureAnalysis",
    complexity: "ComplexityMetrics",
    quality: "QualityScore",
) -> list[str]:
    """生成改进建议.

    Args:
        structure: 结构分析结果
        complexity: 复杂度指标
        quality: 质量评分

    Returns:
        建议列表
    """
    suggestions: list[str] = []

    # 基于质量评分生成建议
    if quality.structure_score < 20:
        suggestions.append("建议完善项目结构，添加必要的目录和文件")

    if quality.documentation_score < 15:
        suggestions.append("建议增加文档和示例，提高代码可读性")

    if quality.test_coverage_score < 15:
        suggestions.append("建议增加测试用例，提高测试覆盖率")

    # 基于复杂度生成建议
    if complexity.cyclomatic_complexity and complexity.cyclomatic_complexity > 10:
        suggestions.append(
            f"代码圈复杂度为 {complexity.cyclomatic_complexity}，建议重构简化复杂逻辑"
        )

    if complexity.maintainability_index and complexity.maintainability_index < 50:
        suggestions.append(
            f"可维护性指数为 {complexity.maintainability_index:.1f}，建议优化代码结构"
        )

    # 基于结构生成建议
    if structure.total_files > 20:
        suggestions.append(f"文件数量较多 ({structure.total_files})，建议考虑模块化拆分")

    if structure.total_lines > CODE_SIZE_MANY_LINES_THRESHOLD:
        suggestions.append(f"代码行数较多 ({structure.total_lines})，建议考虑拆分模块")

    return suggestions


def _generate_analysis_summary(quality: "QualityScore", complexity: "ComplexityMetrics") -> str:
    """生成分析摘要.

    Args:
        quality: 质量评分
        complexity: 复杂度指标

    Returns:
        分析摘要文本
    """
    summary_parts = []

    # 总体评分
    score = quality.overall_score
    if score >= 80:
        summary_parts.append(f"代码质量优秀（{score:.0f}/100）")
    elif score >= 60:
        summary_parts.append(f"代码质量良好（{score:.0f}/100）")
    elif score >= 40:
        summary_parts.append(f"代码质量一般（{score:.0f}/100）")
    else:
        summary_parts.append(f"代码质量需要改进（{score:.0f}/100）")

    # 复杂度评价
    if complexity.cyclomatic_complexity:
        if complexity.cyclomatic_complexity <= 5:
            summary_parts.append("代码复杂度低")
        elif complexity.cyclomatic_complexity <= 10:
            summary_parts.append("代码复杂度中等")
        else:
            summary_parts.append("代码复杂度较高")

    return "，".join(summary_parts) + "。"
