"""验证器工具函数."""

import re
from pathlib import Path

from skill_creator_mcp.logging_config import get_logger

logger = get_logger(__name__)

# 模板特定必需文件映射
TEMPLATE_REQUIREMENTS = {
    "minimal": [],
    "tool-based": ["tool-integration.md", "usage-examples.md"],
    "workflow-based": ["workflow-steps.md", "decision-points.md"],
    "analyzer-based": ["analysis-methods.md", "metrics.md"],
}

# 有效工具名称列表
VALID_TOOLS = [
    "Read",
    "Write",
    "Edit",
    "Bash",
    "Glob",
    "Grep",
    "AskUserQuestion",
    "TodoWrite",
    "Skill",
]


def validate_skill_name(name: str) -> None:
    """验证技能名称符合规范.

    规范：
    - 只能包含小写字母、数字、连字符
    - 不能以连字符开头或结尾
    - 不能有连续的连字符

    Args:
        name: 技能名称

    Raises:
        ValueError: 名称不符合规范时抛出
    """
    pattern = r"^[a-z0-9]+(?:-[a-z0-9]+)*$"
    if not re.match(pattern, name):
        raise ValueError(
            f"技能名称 '{name}' 不符合规范。"
            "要求：小写字母、数字、单个连字符，不能以连字符开头或结尾，不能有连续连字符"
        )


def validate_skill_directory(skill_dir: Path) -> None:
    """验证技能目录是否存在且结构正确.

    Args:
        skill_dir: 技能目录路径

    Raises:
        ValueError: 目录结构不正确时抛出
    """
    if not skill_dir.exists():
        raise ValueError(f"技能目录不存在: {skill_dir}")

    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        raise ValueError(f"SKILL.md 不存在于: {skill_dir}")


def validate_template_type(template: str) -> str:
    """验证模板类型是否有效.

    Args:
        template: 模板类型

    Returns:
        验证通过的模板类型

    Raises:
        ValueError: 模板类型无效时抛出
    """
    valid_templates = ["minimal", "tool-based", "workflow-based", "analyzer-based"]
    if template not in valid_templates:
        raise ValueError(f"无效的模板类型: {template}。有效值: {', '.join(valid_templates)}")
    return template


# ==================== validate_skill 专用验证函数 ====================


def _validate_structure(skill_dir: Path) -> list[str]:
    """验证技能目录结构.

    Args:
        skill_dir: 技能目录路径

    Returns:
        错误列表，空列表表示无错误
    """
    logger.debug("Validating structure for: %s", skill_dir)
    errors = []

    # 检查必需文件
    required_files = ["SKILL.md"]
    for file_name in required_files:
        if not (skill_dir / file_name).exists():
            error_msg = f"缺少必需文件: {file_name}"
            logger.warning(error_msg)
            errors.append(error_msg)

    # 检查必需目录
    required_dirs = ["references", "examples", "scripts", ".claude"]
    for dir_name in required_dirs:
        if not (skill_dir / dir_name).exists():
            error_msg = f"缺少必需目录: {dir_name}"
            logger.warning(error_msg)
            errors.append(error_msg)

    if not errors:
        logger.info("Structure validation passed for: %s", skill_dir)

    return errors


def _validate_naming(skill_dir: Path) -> list[str]:
    """验证技能命名规范.

    Args:
        skill_dir: 技能目录路径

    Returns:
        错误列表，空列表表示无错误
    """
    errors = []
    skill_name = skill_dir.name

    # 验证目录名格式
    try:
        validate_skill_name(skill_name)
    except ValueError as e:
        errors.append(str(e))

    # 验证 SKILL.md 中的 name 字段与目录名一致
    skill_md = skill_dir / "SKILL.md"
    if skill_md.exists():
        content = skill_md.read_text(encoding="utf-8")
        # 提取 YAML frontmatter 中的 name 字段
        for line in content.split("\n"):
            if line.startswith("name:"):
                yaml_name = line.split(":", 1)[1].strip().strip("\"'")
                if yaml_name != skill_name:
                    errors.append(
                        f"SKILL.md 中的 name 字段 '{yaml_name}' 与目录名 '{skill_name}' 不一致"
                    )
                break

    return errors


def _validate_skill_md(skill_dir: Path) -> tuple[list[str], list[str], str | None]:
    """验证 SKILL.md 内容格式.

    Args:
        skill_dir: 技能目录路径

    Returns:
        (错误列表, 警告列表, 模板类型)
    """
    errors: list[str] = []
    warnings: list[str] = []
    template_type = None

    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        errors.append("SKILL.md 文件不存在")
        return errors, warnings, template_type

    content = skill_md.read_text(encoding="utf-8")

    # 检查 YAML frontmatter
    if not content.startswith("---"):
        errors.append("SKILL.md 缺少 YAML frontmatter（应以 --- 开头）")
        return errors, warnings, template_type

    # 解析 frontmatter 内容
    frontmatter_lines = []
    for line in content.split("\n")[1:]:
        if line.strip() == "---":
            break
        frontmatter_lines.append(line)

    frontmatter = "\n".join(frontmatter_lines)

    # 检查必需字段
    required_fields = {
        "name": "name:",
        "description": "description:",
        "allowed-tools": "allowed-tools:",
    }

    for field_name, field_marker in required_fields.items():
        if field_marker not in frontmatter:
            errors.append(f"SKILL.md 缺少必需字段: {field_name}")

    # 提取模板类型（如果有）
    for line in frontmatter_lines:
        if line.strip().startswith("template:"):
            template_value = line.split(":", 1)[1].strip().strip("\"'")
            if template_value in TEMPLATE_REQUIREMENTS:
                template_type = template_value
            break

    # 验证 allowed-tools
    if "allowed-tools:" in frontmatter:
        # 提取 allowed-tools 的值
        in_allowed_tools = False
        tools_value = ""
        for line in frontmatter_lines:
            if line.strip().startswith("allowed-tools:"):
                in_allowed_tools = True
                if ":" in line:
                    tools_value = line.split(":", 1)[1].strip()
                continue
            if in_allowed_tools:
                if line.startswith("  ") or line.startswith("\t"):
                    tools_value += " " + line.strip()
                else:
                    break

        # 解析工具列表
        if tools_value:
            # 处理方括号格式 [Read, Write, Edit]
            tools_value = tools_value.strip("[]")
            tools_list = [t.strip().strip(",'\"") for t in tools_value.split(",") if t.strip()]

            invalid_tools = [t for t in tools_list if t and t not in VALID_TOOLS]
            if invalid_tools:
                warnings.append(f"allowed-tools 包含可能无效的工具: {', '.join(invalid_tools)}")

    return errors, warnings, template_type


def _validate_template_requirements(skill_dir: Path, template_type: str | None) -> list[str]:
    """验证模板特定要求.

    Args:
        skill_dir: 技能目录路径
        template_type: 模板类型

    Returns:
        错误列表，空列表表示无错误
    """
    errors: list[str] = []

    if not template_type or template_type not in TEMPLATE_REQUIREMENTS:
        return errors

    required_files = TEMPLATE_REQUIREMENTS[template_type]
    refs_dir = skill_dir / "references"

    for file_name in required_files:
        ref_file = refs_dir / file_name
        if not ref_file.exists():
            errors.append(f"模板 '{template_type}' 缺少必需引用文件: references/{file_name}")

    return errors
