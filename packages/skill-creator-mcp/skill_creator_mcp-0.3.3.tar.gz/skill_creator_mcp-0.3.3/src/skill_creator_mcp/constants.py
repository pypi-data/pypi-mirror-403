"""常量定义模块.

定义项目中使用的各种常量，避免魔法数字。
"""

from typing import Any

# ==================== SKILL.md 行数限制 ====================

# SKILL.md 推荐最大行数
SKILL_MD_RECOMMENDED_MAX_LINES: int = 150

# SKILL.md 良好最大行数
SKILL_MD_GOOD_MAX_LINES: int = 200

# SKILL.md 及格最大行数
SKILL_MD_ACCEPTABLE_MAX_LINES: int = 350

# SKILL.md 不及格行数阈值
SKILL_MD_POOR_THRESHOLD_LINES: int = 500

# 引用文件推荐行数范围
REFERENCE_FILE_MIN_LINES: int = 200
REFERENCE_FILE_MAX_LINES: int = 300

# 引用文件过长阈值
REFERENCE_FILE_LONG_THRESHOLD: int = 400

# 引用文件最大数量
REFERENCE_FILE_MAX_COUNT: int = 5

# ==================== Token 效率阈值 ====================

# 优秀首次加载 tokens
EXCELLENT_TOKENS: int = 1000

# 良好首次加载 tokens
GOOD_TOKENS: int = 2000

# 及格首次加载 tokens
ACCEPTABLE_TOKENS: int = 3500

# 不及格首次加载 tokens
POOR_TOKENS: int = 5000

# 内容密度百分比阈值
CONTENT_DENSITY_EXCELLENT: float = 0.70  # 70%
CONTENT_DENSITY_GOOD: float = 0.50  # 50%
CONTENT_DENSITY_ACCEPTABLE: float = 0.30  # 30%

# ==================== 代码大小阈值 ====================

# 代码总行数较多阈值（用于生成建议）
CODE_SIZE_MANY_LINES_THRESHOLD: int = 1000

# 代码总行数过多阈值（用于重构建议）
CODE_SIZE_LARGE_THRESHOLD: int = 2000

# 代码总行数非常大阈值
CODE_SIZE_VERY_LARGE_THRESHOLD: int = 5000

# ==================== 复杂度阈值 ====================

# 圈复杂度低阈值
CYCLOMATIC_COMPLEXITY_LOW: int = 5

# 圈复杂度中等阈值
CYCLOMATIC_COMPLEXITY_MEDIUM: int = 15

# 圈复杂度高阈值
CYCLOMATIC_COMPLEXITY_HIGH: int = 25

# 可维护性指数低阈值
MAINTAINABILITY_INDEX_LOW: int = 50

# 可维护性指数良好阈值
MAINTAINABILITY_INDEX_GOOD: int = 70

# ==================== 可维护性指数计算常量 ====================#

# MI = max(0, 171 - 0.23*avg_complexity - 16.2*total_complexity/1000)
MI_BASE_CONSTANT: float = 171.0
MI_AVG_COMPLEXITY_COEFFICIENT: float = 0.23
MI_TOTAL_COMPLEXITY_COEFFICIENT: float = 16.2
MI_COMPLEXITY_SCALE: float = 1000.0

# ==================== 质量评分权重 ====================

NAMING_WEIGHT: float = 0.15
DESCRIPTION_WEIGHT: float = 0.25
STRUCTURE_WEIGHT: float = 0.30
CONTENT_WEIGHT: float = 0.20
TOKEN_EFFICIENCY_WEIGHT: float = 0.10

# ==================== 质量分数 ====================

# SKILL.md 行数评分
SKILL_MD_SCORE_EXCELLENT: int = 30
SKILL_MD_SCORE_GOOD: int = 25
SKILL_MD_SCORE_ACCEPTABLE: int = 15
SKILL_MD_SCORE_MINIMAL: int = 10

# 文档评分
DOCUMENTATION_SCORE_EXCELLENT: int = 30
DOCUMENTATION_SCORE_GOOD: int = 25
DOCUMENTATION_SCORE_ACCEPTABLE: int = 15
DOCUMENTATION_SCORE_MINIMAL: int = 10

# 测试覆盖率评分
TEST_COVERAGE_SCORE_EXCELLENT: int = 30
TEST_COVERAGE_SCORE_GOOD: int = 25
TEST_COVERAGE_SCORE_ACCEPTABLE: int = 15
TEST_COVERAGE_SCORE_MINIMAL: int = 5

# ==================== 文件大小限制 ====================

# 单个文件最大行数
SINGLE_FILE_MAX_LINES: int = 500

# ==================== 描述长度限制 ====================

# 描述最小字符数
DESCRIPTION_MIN_CHARS: int = 50

# 描述推荐字符数范围
DESCRIPTION_RECOMMENDED_MIN_CHARS: int = 150
DESCRIPTION_RECOMMENDED_MAX_CHARS: int = 300

# 描述最大字符数
DESCRIPTION_MAX_CHARS: int = 1024

# ==================== 技能名称限制 ====================

# 技能名称最小长度
SKILL_NAME_MIN_LENGTH: int = 3

# 技能名称最大长度
SKILL_NAME_MAX_LENGTH: int = 50

# ==================== 重构工作量估算 ====================

# 重构工作量估算（小时）
EFFORT_HIGH: int = 8
EFFORT_MEDIUM: int = 4
EFFORT_LOW: int = 1

# ==================== 需求收集相关常量 ====================

# 基础模式需求收集步骤（5步）
BASIC_REQUIREMENT_STEPS: list[dict[str, Any]] = [
    {
        "key": "skill_name",
        "title": "技能名称",
        "prompt": "请输入技能名称（小写字母、数字、连字符，如：pdf-parser、git-helper）",
        "validation": {
            "field": "skill_name",
            "required": True,
            "pattern": r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
            "min_length": 1,
            "max_length": 64,
            "help_text": "技能名称只能包含小写字母、数字和连字符，不能以连字符开头或结尾",
        },
        "modes": ["basic", "complete", "brainstorm", "progressive"],
    },
    {
        "key": "skill_function",
        "title": "主要功能",
        "prompt": "请描述这个技能的主要功能是什么？",
        "validation": {
            "field": "skill_function",
            "required": True,
            "min_length": 10,
            "help_text": "请详细描述技能的主要功能，至少10个字符",
        },
        "modes": ["basic", "complete", "brainstorm", "progressive"],
    },
    {
        "key": "use_cases",
        "title": "使用场景",
        "prompt": "请描述这个技能的使用场景（至少2个）",
        "validation": {
            "field": "use_cases",
            "required": True,
            "min_length": 20,
            "help_text": "请提供至少2个具体的使用场景",
        },
        "modes": ["basic", "complete", "brainstorm", "progressive"],
    },
    {
        "key": "template_type",
        "title": "模板类型",
        "prompt": "选择技能模板类型：minimal（最小化）、tool-based（工具封装）、workflow-based（工作流）、analyzer-based（分析器）",
        "validation": {
            "field": "template_type",
            "required": True,
            "options": ["minimal", "tool-based", "workflow-based", "analyzer-based"],
            "help_text": "请选择一个有效的模板类型",
        },
        "modes": ["basic", "complete", "brainstorm", "progressive"],
    },
    {
        "key": "additional_features",
        "title": "额外需求",
        "prompt": "是否有其他额外功能需求？（可选）",
        "validation": {
            "field": "additional_features",
            "required": False,
            "help_text": "可选：描述任何额外功能需求",
        },
        "modes": ["basic", "complete", "brainstorm", "progressive"],
    },
]

# 完整模式额外步骤（5步）
COMPLETE_REQUIREMENT_STEPS: list[dict[str, Any]] = [
    {
        "key": "target_users",
        "title": "目标用户",
        "prompt": "这个技能的目标用户是谁？",
        "validation": {
            "field": "target_users",
            "required": True,
            "min_length": 10,
            "help_text": "请描述目标用户群体",
        },
        "modes": ["complete"],
    },
    {
        "key": "tech_stack",
        "title": "技术栈偏好",
        "prompt": "是否有技术栈偏好或限制？（可选）",
        "validation": {
            "field": "tech_stack",
            "required": False,
            "help_text": "可选：描述技术栈偏好",
        },
        "modes": ["complete"],
    },
    {
        "key": "dependencies",
        "title": "外部依赖",
        "prompt": "是否需要外部依赖或 API？（可选）",
        "validation": {
            "field": "dependencies",
            "required": False,
            "help_text": "可选：列出所需的外部依赖",
        },
        "modes": ["complete"],
    },
    {
        "key": "testing_requirements",
        "title": "测试要求",
        "prompt": "有什么特殊的测试要求？（可选）",
        "validation": {
            "field": "testing_requirements",
            "required": False,
            "help_text": "可选：描述测试要求",
        },
        "modes": ["complete"],
    },
    {
        "key": "documentation_level",
        "title": "文档级别",
        "prompt": "期望的文档详细程度？基础/标准/详细",
        "validation": {
            "field": "documentation_level",
            "required": False,
            "options": ["基础", "标准", "详细"],
            "help_text": "选择文档详细程度",
        },
        "modes": ["complete"],
    },
]

__all__ = [
    # SKILL.md 行数限制
    "SKILL_MD_RECOMMENDED_MAX_LINES",
    "SKILL_MD_GOOD_MAX_LINES",
    "SKILL_MD_ACCEPTABLE_MAX_LINES",
    "SKILL_MD_POOR_THRESHOLD_LINES",
    "REFERENCE_FILE_MIN_LINES",
    "REFERENCE_FILE_MAX_LINES",
    "REFERENCE_FILE_LONG_THRESHOLD",
    "REFERENCE_FILE_MAX_COUNT",
    # Token 效率阈值
    "EXCELLENT_TOKENS",
    "GOOD_TOKENS",
    "ACCEPTABLE_TOKENS",
    "POOR_TOKENS",
    "CONTENT_DENSITY_EXCELLENT",
    "CONTENT_DENSITY_GOOD",
    "CONTENT_DENSITY_ACCEPTABLE",
    # 代码大小阈值
    "CODE_SIZE_LARGE_THRESHOLD",
    "CODE_SIZE_VERY_LARGE_THRESHOLD",
    # 复杂度阈值
    "CYCLOMATIC_COMPLEXITY_LOW",
    "CYCLOMATIC_COMPLEXITY_MEDIUM",
    "CYCLOMATIC_COMPLEXITY_HIGH",
    "MAINTAINABILITY_INDEX_LOW",
    "MAINTAINABILITY_INDEX_GOOD",
    # 可维护性指数计算常量
    "MI_BASE_CONSTANT",
    "MI_AVG_COMPLEXITY_COEFFICIENT",
    "MI_TOTAL_COMPLEXITY_COEFFICIENT",
    "MI_COMPLEXITY_SCALE",
    # 质量评分权重
    "NAMING_WEIGHT",
    "DESCRIPTION_WEIGHT",
    "STRUCTURE_WEIGHT",
    "CONTENT_WEIGHT",
    "TOKEN_EFFICIENCY_WEIGHT",
    # 质量分数
    "SKILL_MD_SCORE_EXCELLENT",
    "SKILL_MD_SCORE_GOOD",
    "SKILL_MD_SCORE_ACCEPTABLE",
    "SKILL_MD_SCORE_MINIMAL",
    "DOCUMENTATION_SCORE_EXCELLENT",
    "DOCUMENTATION_SCORE_GOOD",
    "DOCUMENTATION_SCORE_ACCEPTABLE",
    "DOCUMENTATION_SCORE_MINIMAL",
    "TEST_COVERAGE_SCORE_EXCELLENT",
    "TEST_COVERAGE_SCORE_GOOD",
    "TEST_COVERAGE_SCORE_ACCEPTABLE",
    "TEST_COVERAGE_SCORE_MINIMAL",
    # 文件大小限制
    "SINGLE_FILE_MAX_LINES",
    # 描述长度限制
    "DESCRIPTION_MIN_CHARS",
    "DESCRIPTION_RECOMMENDED_MIN_CHARS",
    "DESCRIPTION_RECOMMENDED_MAX_CHARS",
    "DESCRIPTION_MAX_CHARS",
    # 技能名称限制
    "SKILL_NAME_MIN_LENGTH",
    "SKILL_NAME_MAX_LENGTH",
    # 重构工作量估算
    "EFFORT_HIGH",
    "EFFORT_MEDIUM",
    "EFFORT_LOW",
    # 需求收集相关常量
    "BASIC_REQUIREMENT_STEPS",
    "COMPLETE_REQUIREMENT_STEPS",
]
