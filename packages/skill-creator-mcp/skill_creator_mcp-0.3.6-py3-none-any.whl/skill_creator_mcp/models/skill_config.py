"""技能配置数据模型."""

import re
from pathlib import Path
from typing import Any, Literal, TypeVar, cast

from pydantic import BaseModel, Field, field_validator, model_validator

# 模板类型字面量
SkillTemplateType = Literal["minimal", "tool-based", "workflow-based", "analyzer-based"]

# 类型变量用于泛型Mixin
T = TypeVar("T", bound="OutputDirMixin")


# ==================== 共享验证 Mixin ====================


class OutputDirMixin(BaseModel):
    """输出目录验证共享 Mixin.

    提供统一的 output_dir 字段验证逻辑，避免在多个模型中重复代码。

    注意：子类必须定义 output_dir 字段并使用 field_validator 调用
    _apply_default_output_dir 方法。
    """

    # 类型存根：子类需要定义此字段
    output_dir: str

    def _ensure_output_dir_validated(self) -> "OutputDirMixin":
        """验证并确保 output_dir 字段有效.

        在所有字段验证后调用，确保 output_dir 有值且路径有效。

        Returns:
            验证后的模型实例
        """
        # 获取output_dir值（使用getattr避免类型检查错误）
        output_dir_value: str | None = getattr(self, "output_dir", None)

        # 如果 output_dir 为 None 或空，应用默认值
        if not output_dir_value:
            from ..utils.path_helpers import get_output_dir
            # 使用 object.__setattr__ 避免 validate_assignment 触发
            default_dir = str(get_output_dir(fallback=True))
            object.__setattr__(self, "output_dir", default_dir)
            output_dir_value = default_dir

        # 验证路径有效性
        from ..utils.path_helpers import ensure_output_dir

        try:
            validated_path = ensure_output_dir(output_dir_value)
            object.__setattr__(self, "output_dir", str(validated_path))
        except ValueError as e:
            raise ValueError(f"输出目录验证失败: {e}") from e

        return self

    @classmethod
    def _apply_default_output_dir(cls, v: Any) -> str:
        """应用默认输出目录（共享方法）.

        如果 v 为 None 或未提供，从配置获取默认值。

        Args:
            v: 输入值

        Returns:
            验证后的输出目录路径
        """
        # Pydantic 可能传递 PydanticUndefined 或其他特殊值
        if v is None or v == "" or not isinstance(v, (str, Path)):
            from ..utils.path_helpers import get_output_dir
            return str(get_output_dir(fallback=True))
        # 确保 v 是字符串
        return str(v) if isinstance(v, (str, Path)) else str(get_output_dir(fallback=True))


class InitSkillInput(OutputDirMixin):
    """初始化技能输入参数模型."""

    name: str = Field(
        ...,
        description="技能名称（小写字母、数字、连字符，1-64字符）",
        min_length=1,
        max_length=64,
    )
    template: SkillTemplateType = Field(
        default="minimal",
        description="技能模板类型",
    )
    output_dir: str = Field(
        default="",
        description="输出目录路径（默认使用 SKILL_CREATOR_OUTPUT_DIR 环境变量）",
    )
    with_scripts: bool = Field(
        default=False,
        description="是否包含示例脚本",
    )
    with_examples: bool = Field(
        default=False,
        description="是否包含使用示例",
    )

    @field_validator("output_dir", mode="before")
    @classmethod
    def _apply_output_dir_default(cls, v: Any) -> str:
        """应用默认输出目录."""
        return cls._apply_default_output_dir(v)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """验证技能名称符合规范.

        规范：
        - 只能包含小写字母、数字、连字符
        - 不能以连字符开头或结尾
        - 不能有连续的连字符

        Args:
            v: 技能名称

        Returns:
            验证通过的技能名称

        Raises:
            ValueError: 名称不符合规范时抛出
        """
        pattern = r"^[a-z0-9]+(?:-[a-z0-9]+)*$"
        if not re.match(pattern, v):
            raise ValueError(
                f"技能名称 '{v}' 不符合规范。"
                "要求：小写字母、数字、单个连字符，不能以连字符开头或结尾，不能有连续连字符"
            )
        return v

    @model_validator(mode="after")
    def validate_output_dir_model(self) -> "InitSkillInput":
        """验证 output_dir 字段（模型级别验证，确保默认值也被处理）."""
        # 调用 Mixin 的验证方法，使用 cast 确保返回类型正确
        return cast("InitSkillInput", self._ensure_output_dir_validated())



class InitResult(BaseModel):
    """初始化技能结果模型."""

    success: bool = Field(
        ...,
        description="操作是否成功",
    )
    skill_path: str = Field(
        ...,
        description="技能目录路径",
    )
    skill_name: str = Field(
        ...,
        description="技能名称",
    )
    template: SkillTemplateType = Field(
        ...,
        description="使用的模板类型",
    )
    message: str = Field(
        ...,
        description="操作消息",
    )
    next_steps: list[str] = Field(
        default_factory=list,
        description="后续步骤",
    )
    error: str | None = Field(
        default=None,
        description="错误信息",
    )
    error_type: str | None = Field(
        default=None,
        description="错误类型",
    )


class SkillConfig(BaseModel):
    """技能配置模型."""

    name: str
    template: SkillTemplateType
    description: str | None = None
    author: str | None = None
    version: str = "0.1.0"
    allowed_tools: list[str] | None = None
    mcp_servers: list[str] | None = None


class ValidateSkillInput(BaseModel):
    """验证技能输入参数模型."""

    skill_path: str = Field(
        ...,
        description="技能目录路径",
    )
    check_structure: bool = Field(
        default=True,
        description="是否检查目录结构",
    )
    check_content: bool = Field(
        default=True,
        description="是否检查内容格式",
    )


class ValidationResult(BaseModel):
    """验证结果模型."""

    valid: bool = Field(
        ...,
        description="验证是否通过",
    )
    skill_path: str = Field(
        ...,
        description="技能目录路径",
    )
    skill_name: str | None = Field(
        default=None,
        description="技能名称",
    )
    template_type: SkillTemplateType | None = Field(
        default=None,
        description="模板类型",
    )
    errors: list[str] = Field(
        default_factory=list,
        description="错误信息列表",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="警告信息列表",
    )
    checks: dict[str, bool] = Field(
        default_factory=dict,
        description="各项检查结果",
    )


class AnalyzeSkillInput(BaseModel):
    """分析技能输入参数模型."""

    skill_path: str = Field(
        ...,
        description="技能目录路径",
    )
    analyze_structure: bool = Field(
        default=True,
        description="是否分析代码结构",
    )
    analyze_complexity: bool = Field(
        default=True,
        description="是否分析代码复杂度",
    )
    analyze_quality: bool = Field(
        default=True,
        description="是否分析代码质量",
    )


class StructureAnalysis(BaseModel):
    """结构分析结果模型."""

    total_files: int = Field(
        default=0,
        description="文件总数",
    )
    total_lines: int = Field(
        default=0,
        description="代码总行数",
    )
    file_breakdown: dict[str, int] = Field(
        default_factory=dict,
        description="文件分类统计",
    )


class ComplexityMetrics(BaseModel):
    """复杂度指标模型."""

    cyclomatic_complexity: int | None = Field(
        default=None,
        description="圈复杂度",
    )
    maintainability_index: float | None = Field(
        default=None,
        description="可维护性指数",
    )
    code_duplication: float | None = Field(
        default=None,
        description="代码重复率",
    )


class QualityScore(BaseModel):
    """质量评分模型."""

    overall_score: float = Field(
        ...,
        description="总体评分 (0-100)",
        ge=0,
        le=100,
    )
    structure_score: float = Field(
        default=0,
        description="结构评分",
    )
    documentation_score: float = Field(
        default=0,
        description="文档评分",
    )
    test_coverage_score: float = Field(
        default=0,
        description="测试覆盖率评分",
    )


class AnalyzeResult(BaseModel):
    """分析结果模型."""

    skill_path: str = Field(
        ...,
        description="技能目录路径",
    )
    skill_name: str | None = Field(
        default=None,
        description="技能名称",
    )
    structure: StructureAnalysis = Field(
        default_factory=StructureAnalysis,
        description="结构分析结果",
    )
    complexity: ComplexityMetrics = Field(
        default_factory=ComplexityMetrics,
        description="复杂度指标",
    )
    quality: QualityScore = Field(
        ...,
        description="质量评分",
    )
    suggestions: list[str] = Field(
        default_factory=list,
        description="改进建议列表",
    )


# ==================== 重构相关模型 ====================


class RefactorSuggestion(BaseModel):
    """重构建议模型."""

    priority: Literal["P0", "P1", "P2"] = Field(
        ...,
        description="优先级（P0=必须，P1=建议，P2=可选）",
    )
    category: str = Field(
        ...,
        description="问题类别",
    )
    issue: str = Field(
        ...,
        description="问题描述",
    )
    suggestion: str = Field(
        ...,
        description="改进建议",
    )
    impact: Literal["high", "medium", "low"] = Field(
        default="medium",
        description="影响程度",
    )
    effort: Literal["low", "medium", "high"] = Field(
        default="medium",
        description="工作量",
    )


class RefactorSkillInput(BaseModel):
    """重构技能输入参数模型."""

    skill_path: str = Field(
        ...,
        description="技能目录路径",
    )
    focus: list[str] | None = Field(
        default=None,
        description="重点关注领域（如 structure、documentation、testing）",
    )
    analyze_structure: bool = Field(
        default=True,
        description="是否分析代码结构",
    )
    analyze_complexity: bool = Field(
        default=True,
        description="是否分析代码复杂度",
    )
    analyze_quality: bool = Field(
        default=True,
        description="是否分析代码质量",
    )


class RefactorResult(BaseModel):
    """重构结果模型."""

    success: bool = Field(
        ...,
        description="操作是否成功",
    )
    skill_path: str = Field(
        ...,
        description="技能目录路径",
    )
    skill_name: str | None = Field(
        default=None,
        description="技能名称",
    )
    structure: StructureAnalysis = Field(
        default_factory=StructureAnalysis,
        description="结构分析结果",
    )
    complexity: ComplexityMetrics = Field(
        default_factory=ComplexityMetrics,
        description="复杂度指标",
    )
    quality: QualityScore | None = Field(
        default=None,
        description="质量评分",
    )
    suggestions: list[RefactorSuggestion] = Field(
        default_factory=list,
        description="重构建议列表",
    )
    report: str = Field(
        default="",
        description="重构报告（Markdown 格式）",
    )
    effort_estimate: dict[str, int] = Field(
        default_factory=dict,
        description="工作量估算（小时）",
    )
    error: str | None = Field(
        default=None,
        description="错误信息",
    )
    error_type: str | None = Field(
        default=None,
        description="错误类型",
    )


# ==================== 打包相关模型 ====================


class PackageSkillInput(OutputDirMixin):
    """打包技能输入参数模型."""

    skill_path: str = Field(
        ...,
        description="技能目录路径",
    )
    output_dir: str = Field(
        default="",
        description="输出目录路径（默认使用 SKILL_CREATOR_OUTPUT_DIR 环境变量）",
    )
    format: Literal["zip", "tar.gz", "tar.bz2"] = Field(
        default="zip",
        description="打包格式",
    )
    include_tests: bool = Field(
        default=True,
        description="是否包含测试文件",
    )
    validate_before_package: bool = Field(
        default=True,
        description="打包前是否验证",
    )

    @field_validator("output_dir", mode="before")
    @classmethod
    def _apply_output_dir_default(cls, v: Any) -> str:
        """应用默认输出目录."""
        return cls._apply_default_output_dir(v)

    @model_validator(mode="after")
    def validate_output_dir_model(self) -> "PackageSkillInput":
        """验证 output_dir 字段（模型级别验证，确保默认值也被处理）."""
        # 调用 Mixin 的验证方法，使用 cast 确保返回类型正确
        return cast("PackageSkillInput", self._ensure_output_dir_validated())


class PackageResult(BaseModel):
    """打包结果模型."""

    success: bool = Field(
        ...,
        description="操作是否成功",
    )
    skill_path: str = Field(
        ...,
        description="技能目录路径",
    )
    package_path: str | None = Field(
        default=None,
        description="生成的包文件路径",
    )
    format: str | None = Field(
        default=None,
        description="打包格式",
    )
    files_included: int = Field(
        default=0,
        description="包含的文件数量",
    )
    package_size: int | None = Field(
        default=None,
        description="包大小（字节）",
    )
    validation_passed: bool | None = Field(
        default=None,
        description="打包前验证是否通过",
    )
    validation_errors: list[str] = Field(
        default_factory=list,
        description="验证错误列表",
    )
    error: str | None = Field(
        default=None,
        description="错误信息",
    )
    error_type: str | None = Field(
        default=None,
        description="错误类型",
    )


# ==================== 需求收集相关模型 ====================


RequirementCollectionMode = Literal["basic", "complete", "brainstorm", "progressive"]
RequirementAction = Literal["start", "next", "previous", "status", "complete"]


class ValidationRule(BaseModel):
    """验证规则模型."""

    field: str = Field(
        ...,
        description="字段名称",
    )
    required: bool = Field(
        default=True,
        description="是否必填",
    )
    validator: str | None = Field(
        default=None,
        description="验证函数名称",
    )
    options: list[str] | None = Field(
        default=None,
        description="可选项列表",
    )
    min_length: int | None = Field(
        default=None,
        description="最小长度",
    )
    max_length: int | None = Field(
        default=None,
        description="最大长度",
    )
    pattern: str | None = Field(
        default=None,
        description="正则表达式模式",
    )
    help_text: str = Field(
        ...,
        description="帮助文本",
    )


class RequirementStep(BaseModel):
    """需求收集步骤模型."""

    key: str = Field(
        ...,
        description="步骤键名",
    )
    title: str = Field(
        ...,
        description="步骤标题",
    )
    prompt: str = Field(
        ...,
        description="询问用户的提示文本",
    )
    validation: ValidationRule = Field(
        ...,
        description="验证规则",
    )
    depends_on: list[str] | None = Field(
        default=None,
        description="依赖的其他步骤键名",
    )
    modes: list[RequirementCollectionMode] = Field(
        default_factory=list,
        description="适用的收集模式",
    )


class SessionState(BaseModel):
    """需求收集会话状态模型."""

    current_step_index: int = Field(
        default=0,
        description="当前步骤索引",
    )
    answers: dict[str, str] = Field(
        default_factory=dict,
        description="已收集的答案",
    )
    conversation_history: list[dict[str, str]] = Field(
        default_factory=list,
        description="对话历史（用于 brainstorm/progressive 模式）",
    )
    started_at: str | None = Field(
        default=None,
        description="会话开始时间（ISO 8601）",
    )
    completed: bool = Field(
        default=False,
        description="是否已完成",
    )
    mode: RequirementCollectionMode = Field(
        default="basic",
        description="收集模式",
    )
    total_steps: int = Field(
        default=0,
        description="总步骤数",
    )


class RequirementCollectionInput(BaseModel):
    """需求收集输入参数模型."""

    action: RequirementAction = Field(
        default="start",
        description="执行动作：start=开始，next=下一步，previous=上一步，status=查询状态，complete=完成",
    )
    mode: RequirementCollectionMode = Field(
        default="basic",
        description="收集模式：basic=基础（5步），complete=完整（10步），brainstorm=头脑风暴，progressive=渐进式",
    )
    session_id: str | None = Field(
        default=None,
        description="会话ID（自动生成，用于多轮对话）",
    )
    user_input: str | None = Field(
        default=None,
        description="用户输入（用于 next/complete 动作）",
    )


class RequirementCollectionResult(BaseModel):
    """需求收集结果模型."""

    success: bool = Field(
        ...,
        description="操作是否成功",
    )
    session_id: str = Field(
        ...,
        description="会话ID",
    )
    action: RequirementAction = Field(
        ...,
        description="执行的Action",
    )
    mode: RequirementCollectionMode = Field(
        ...,
        description="收集模式",
    )
    current_step: RequirementStep | None = Field(
        default=None,
        description="当前步骤信息",
    )
    step_index: int = Field(
        default=0,
        description="当前步骤索引",
    )
    total_steps: int = Field(
        default=0,
        description="总步骤数",
    )
    progress: float = Field(
        default=0.0,
        description="进度百分比（0-100）",
    )
    answers: dict[str, str] = Field(
        default_factory=dict,
        description="已收集的答案",
    )
    message: str = Field(
        ...,
        description="响应消息",
    )
    completed: bool = Field(
        default=False,
        description="是否已完成收集",
    )
    is_complete: bool = Field(
        default=False,
        description="需求是否完整（用于 LLM 判断）",
    )
    missing_info: list[str] = Field(
        default_factory=list,
        description="缺失的关键信息列表",
    )
    suggestions: list[str] = Field(
        default_factory=list,
        description="补充建议列表",
    )
    error: str | None = Field(
        default=None,
        description="错误信息",
    )
