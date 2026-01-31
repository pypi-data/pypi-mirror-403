"""Skill Creator MCP Server.

这是一个基于 FastMCP SDK 开发的 MCP Server，用于创建、验证、
分析和重构 Agent-Skills。
"""

import logging
import time
from collections.abc import Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any

from fastmcp import Context, FastMCP

# 导入提示和资源
from .prompts import (
    get_create_skill_prompt,
    get_refactor_skill_prompt,
    get_validate_skill_prompt,
)
from .resources import (
    get_best_practices,
    get_template_content,
    get_validation_rules,
    list_templates,
)

# 工具模块导入
from .tools.package_tools import (
    package_skill as package_skill_impl,
)
from .tools.requirement_question_tools import (
    generate_dynamic_question,
    get_static_question,
)

# 新的原子化需求收集工具（架构重构）
from .tools.requirement_session_tools import (
    create_requirement_session,
    get_requirement_session,
    update_requirement_answer,
)
from .tools.requirement_validation_tools import (
    check_requirement_completeness,
    validate_answer_format,
)
from .tools.skill_tools import (
    analyze_skill,
    init_skill,
    refactor_skill,
    validate_skill,
)

# Phase 0 验证工具已迁移到开发工具脚本
# 保留在 .tools.phase0_tools 模块中供开发工具使用
# 但不注册为MCP工具


@dataclass
class AppContext:
    """应用生命周期上下文.

    用于在MCP Server生命周期中共享状态和资源。
    """
    cache: Any = field(default_factory=dict)
    startup_time: float = 0.0
    request_count: int = 0

    def increment_request_count(self) -> int:
        """增加请求计数."""
        self.request_count += 1
        return self.request_count


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> Any:
    """应用生命周期管理钩子.

    在MCP Server启动和关闭时执行初始化和清理操作。

    Args:
        server: FastMCP服务器实例

    Yields:
        AppContext: 应用上下文对象
    """
    from .utils.cache import MemoryCache

    # 启动时初始化
    cache_instance = MemoryCache()
    context = AppContext(
        cache=cache_instance,
        startup_time=time.time(),
        request_count=0,
    )

    # 初始化资源
    yield context

    # 关闭时清理
    # 注意：cache由生命周期管理，会自动清理
    pass


# 创建 MCP Server
mcp = FastMCP(
    name="skill-creator",
    instructions="""
    Skill Creator MCP Server - Agent-Skills 开发工具

    这个服务器提供创建、验证、分析、重构和打包 Agent-Skills 的工具。

    ## 可用工具

    ### init_skill
    初始化新的 Agent-Skill。

    参数：
    - name (str): 技能名称（小写字母、数字、连字符，1-64字符）
    - template (str): 模板类型（minimal/tool-based/workflow-based/analyzer-based）
    - output_dir (str): 输出目录路径
    - with_scripts (bool): 是否包含示例脚本
    - with_examples (bool): 是否包含使用示例

    ### validate_skill
    验证 Agent-Skill 的结构和内容。

    参数：
    - skill_path (str): 技能目录路径
    - check_structure (bool): 是否检查目录结构（默认 True）
    - check_content (bool): 是否检查内容格式（默认 True）

    ### analyze_skill
    分析 Agent-Skill 的代码质量、复杂度和结构。

    参数：
    - skill_path (str): 技能目录路径
    - analyze_structure (bool): 是否分析代码结构（默认 True）
    - analyze_complexity (bool): 是否分析代码复杂度（默认 True）
    - analyze_quality (bool): 是否分析代码质量（默认 True）

    ### refactor_skill
    生成 Agent-Skill 的重构建议。

    参数：
    - skill_path (str): 技能目录路径
    - focus (list[str]): 重点关注领域（可选，如 structure、documentation、testing）
    - analyze_structure (bool): 是否分析代码结构（默认 True）
    - analyze_complexity (bool): 是否分析代码复杂度（默认 True）
    - analyze_quality (bool): 是否分析代码质量（默认 True）

    ### package_skill
    打包 Agent-Skill 为分发格式。

    统一打包工具，支持两种模式：
    - strict=False (默认): 通用打包模式
    - strict=True: Agent-Skill标准打包模式（需要version参数）

    参数：
    - skill_path (str): 技能目录路径
    - output_dir (str): 输出目录路径（默认：当前目录）
    - version (str): 版本号（可选，仅在strict=True时使用）
    - format (str): 打包格式（zip/tar.gz/tar.bz2，默认：zip）
    - include_tests (bool): 是否包含测试文件（默认：False）
    - strict (bool): 是否使用Agent-Skill标准打包模式（默认：False）
    - validate_before_package (bool): 打包前是否验证（默认：True）

    """,
    lifespan=app_lifespan,
)


# ==================== 中间件实现 ====================

class LoggingMiddleware:
    """日志记录中间件.

    记录MCP工具的调用信息。
    """

    def __init__(self) -> None:
        self._logger: logging.Logger | None = None

    async def __call__(self, context: Any, call_next: Callable) -> Any:
        """处理请求."""
        if self._logger is None:
            from .logging_config import get_logger
            self._logger = get_logger(__name__)

        tool_name = getattr(context, "name", "unknown")

        # 记录调用开始
        self._logger.info(f"Tool called: {tool_name}")

        # 执行下一个中间件或工具
        start_time = time.time()
        try:
            result = await call_next(context)
            elapsed = time.time() - start_time
            self._logger.info(f"Tool {tool_name} completed in {elapsed:.3f}s")
            return result
        except Exception as e:
            elapsed = time.time() - start_time
            self._logger.error(f"Tool {tool_name} failed after {elapsed:.3f}s: {e}")
            raise


class ErrorHandlingMiddleware:
    """错误处理中间件.

    捕获并处理工具执行过程中的异常。
    """

    async def __call__(self, context: Any, call_next: Callable) -> Any:
        """处理请求."""
        try:
            return await call_next(context)
        except Exception as e:
            # 记录错误并重新抛出
            from .logging_config import get_logger
            logger = get_logger(__name__)
            logger.error(f"Error in tool execution: {e}", exc_info=True)
            raise


class TimingMiddleware:
    """性能计时中间件.

    记录工具执行时间并收集性能统计。
    """

    def __init__(self) -> None:
        self._timings: dict[str, list[float]] = {}

    async def __call__(self, context: Any, call_next: Callable) -> Any:
        """处理请求."""
        tool_name = getattr(context, "name", "unknown")

        start_time = time.time()
        try:
            result = await call_next(context)
            return result
        finally:
            elapsed = time.time() - start_time
            if tool_name not in self._timings:
                self._timings[tool_name] = []
            self._timings[tool_name].append(elapsed)

    def get_stats(self) -> dict[str, dict[str, float]]:
        """获取性能统计."""
        stats = {}
        for tool_name, timings in self._timings.items():
            if timings:
                stats[tool_name] = {
                    "count": len(timings),
                    "min": min(timings),
                    "max": max(timings),
                    "avg": sum(timings) / len(timings),
                }
        return stats


# 注册中间件
_timing_middleware = TimingMiddleware()
mcp.add_middleware(_timing_middleware)  # type: ignore[arg-type]


# ==================== HTTP路由 ====================


@mcp.custom_route("/health", methods=["GET"])  # type: ignore[arg-type]
async def health_check_endpoint(request: Any) -> dict[str, Any]:
    """HTTP健康检查端点.

    提供简单的HTTP端点用于健康检查。

    Args:
        request: FastAPI/Starlette请求对象

    Returns:
        健康状态JSON响应
    """
    return {
        "status": "healthy",
        "service": "skill-creator-mcp",
        "version": "0.3.6",
    }


@mcp.custom_route("/metrics", methods=["GET"])  # type: ignore[arg-type]
async def metrics_endpoint(request: Any) -> dict[str, Any]:
    """性能指标端点.

    提供MCP Server的性能指标。

    Args:
        request: FastAPI/Starlette请求对象

    Returns:
        性能指标JSON响应
    """
    stats = _timing_middleware.get_stats()
    return {
        "service": "skill-creator-mcp",
        "metrics": stats,
    }

# ==================== 注册工具模块 ====================
# Phase 2.2 重构：从独立工具模块注册 MCP 工具


# 技能工具（skill_tools.py）
# 使用 @mcp.tool() 装饰器注册工具
@mcp.tool()
async def init_skill_tool(
    ctx: Context,
    name: str,
    template: str = "minimal",
    output_dir: str | None = None,
    with_scripts: bool = False,
    with_examples: bool = False,
) -> dict[str, Any]:
    """
    初始化新的 Agent-Skill.

    创建符合规范的 Agent-Skill 项目目录结构和模板文件。

    Args:
        ctx: MCP 上下文
        name: 技能名称（小写字母、数字、连字符，1-64字符）
        template: 模板类型（minimal/tool-based/workflow-based/analyzer-based）
        output_dir: 输出目录路径（可选）
        with_scripts: 是否包含示例脚本
        with_examples: 是否包含使用示例

    Returns:
        包含初始化结果的字典
    """
    return await init_skill(ctx, name, template, output_dir, with_scripts, with_examples)


@mcp.tool()
async def validate_skill_tool(
    ctx: Context,
    skill_path: str,
    check_structure: bool = True,
    check_content: bool = True,
) -> dict[str, Any]:
    """
    验证 Agent-Skill 的结构和内容.

    检查技能目录是否符合 Agent-Skill 规范。

    Args:
        ctx: MCP 上下文
        skill_path: 技能目录路径
        check_structure: 是否检查目录结构
        check_content: 是否检查内容格式

    Returns:
        包含验证结果的字典
    """
    return await validate_skill(ctx, skill_path, check_structure, check_content)


@mcp.tool()
async def analyze_skill_tool(
    ctx: Context,
    skill_path: str,
    analyze_structure: bool = True,
    analyze_complexity: bool = True,
    analyze_quality: bool = True,
) -> dict[str, Any]:
    """
    分析 Agent-Skill 的代码质量和复杂度.

    Args:
        ctx: MCP 上下文
        skill_path: 技能目录路径
        analyze_structure: 是否分析代码结构
        analyze_complexity: 是否分析代码复杂度
        analyze_quality: 是否分析代码质量

    Returns:
        包含分析结果的字典
    """
    return await analyze_skill(ctx, skill_path, analyze_structure, analyze_complexity, analyze_quality)


@mcp.tool()
async def refactor_skill_tool(
    ctx: Context,
    skill_path: str,
    focus: list[str] | None = None,
    analyze_structure: bool = True,
    analyze_complexity: bool = True,
    analyze_quality: bool = True,
) -> dict[str, Any]:
    """
    生成 Agent-Skill 的重构建议.

    Args:
        ctx: MCP 上下文
        skill_path: 技能目录路径
        focus: 重点关注领域（可选）
        analyze_structure: 是否分析代码结构
        analyze_complexity: 是否分析代码复杂度
        analyze_quality: 是否分析代码质量

    Returns:
        包含重构建议的字典
    """
    return await refactor_skill(ctx, skill_path, focus, analyze_structure, analyze_complexity, analyze_quality)


# 打包工具（package_tools.py）
# 函数签名：async def func(ctx, mcp, ...) -> dict
@mcp.tool()
async def package_skill(
    ctx: Context,
    skill_path: str,
    output_dir: str | None = None,
    version: str | None = None,
    format: str = "zip",
    include_tests: bool = False,
    strict: bool = False,
    validate_before_package: bool = True,
) -> dict[str, Any]:
    """
    打包 Agent-Skill 为分发格式.

    这是统一的打包工具，支持两种模式：
    - strict=False (默认): 通用打包模式，使用灵活排除模式
    - strict=True: Agent-Skill标准打包模式，使用严格排除模式，支持version参数

    Args:
        ctx: MCP 上下文
        skill_path: 技能目录路径
        output_dir: 输出目录路径（可选，优先级：参数 > 环境变量 SKILL_CREATOR_OUTPUT_DIR > 默认值）
        version: 版本号（可选，格式如 "0.3.1"，仅在strict=True时使用）
        format: 打包格式（zip/tar.gz/tar.bz2）
        include_tests: 是否包含测试文件（默认 False）
        strict: 是否使用Agent-Skill标准打包模式（默认 False）
        validate_before_package: 打包前是否验证

    Returns:
        包含打包结果的字典
    """
    return await package_skill_impl(ctx, mcp, skill_path, output_dir, version, format, include_tests, strict, validate_before_package)


# ==================== 需求收集原子工具 ====================
# 架构重构：将 collect_requirements 拆分为原子操作工具
# 符合 ADR 001: MCP Server 只提供原子操作，不包含工作流逻辑
# 工作流编排由 Agent-Skill 负责


@mcp.tool()
async def create_requirement_session_tool(
    ctx: Context,
    mode: str = "basic",
    total_steps: int | None = None,
) -> dict[str, Any]:
    """创建新的需求收集会话.

    这是一个原子操作工具，只负责创建会话状态。
    工作流编排由 Agent-Skill 负责。

    Args:
        ctx: MCP 上下文
        mode: 收集模式（basic/complete/brainstorm/progressive）
        total_steps: 总步骤数（可选，默认根据模式自动计算）

    Returns:
        包含会话信息的字典
    """
    return await create_requirement_session(ctx, mode, total_steps)


@mcp.tool()
async def get_requirement_session_tool(
    ctx: Context,
    session_id: str,
) -> dict[str, Any]:
    """获取需求收集会话状态.

    这是一个原子操作工具，只负责读取会话状态。

    Args:
        ctx: MCP 上下文
        session_id: 会话ID

    Returns:
        包含会话状态的字典
    """
    return await get_requirement_session(ctx, session_id)


@mcp.tool()
async def update_requirement_answer_tool(
    ctx: Context,
    session_id: str,
    question_key: str,
    answer: str,
) -> dict[str, Any]:
    """更新需求收集会话中的答案.

    这是一个原子操作工具，只负责更新单个答案。
    不包含验证逻辑，验证由专门的工具处理。

    Args:
        ctx: MCP 上下文
        session_id: 会话ID
        question_key: 问题键（如 skill_name, skill_function）
        answer: 用户答案

    Returns:
        包含更新结果的字典
    """
    return await update_requirement_answer(ctx, session_id, question_key, answer)


@mcp.tool()
async def get_static_question_tool(
    ctx: Context,
    mode: str,
    step_index: int,
) -> dict[str, Any]:
    """获取静态问题（用于 basic/complete 模式）.

    这是一个原子操作工具，只负责获取预定义的问题。
    不包含循环逻辑，循环由 Agent-Skill 编排。

    Args:
        ctx: MCP 上下文
        mode: 收集模式（basic/complete）
        step_index: 步骤索引（从0开始）

    Returns:
        包含问题信息的字典
    """
    return await get_static_question(ctx, mode, step_index)


@mcp.tool()
async def generate_dynamic_question_tool(
    ctx: Context,
    mode: str,
    answers: dict[str, str],
    conversation_history: list[dict] | None = None,
    prompt_template: str | None = None,
) -> dict[str, Any]:
    """生成动态问题（用于 brainstorm/progressive 模式）.

    这是一个原子操作工具，使用 LLM 生成下一个问题。
    不包含循环逻辑，循环由 Agent-Skill 编排。

    Args:
        ctx: MCP 上下文
        mode: 收集模式（brainstorm/progressive）
        answers: 已收集的答案
        conversation_history: 对话历史（用于 brainstorm 模式）
        prompt_template: 自定义Prompt模板（可选，用于特殊场景）。
                        Prompt模板应由Agent-Skill提供，符合ADR 001架构原则。

    Returns:
        包含生成问题的字典
    """
    return await generate_dynamic_question(ctx, mode, answers, conversation_history, prompt_template)


@mcp.tool()
async def validate_answer_format_tool(
    ctx: Context,
    answer: str,
    validation: dict[str, Any],
) -> dict[str, Any]:
    """验证答案格式.

    这是一个原子操作工具，只负责验证单个答案。
    不包含重试逻辑，重试由 Agent-Skill 编排。

    Args:
        ctx: MCP 上下文
        answer: 用户输入的答案
        validation: 验证规则字典

    Returns:
        包含验证结果的字典
    """
    return await validate_answer_format(ctx, answer, validation)


@mcp.tool()
async def check_requirement_completeness_tool(
    ctx: Context,
    answers: dict[str, str],
    prompt_template: str | None = None,
) -> dict[str, Any]:
    """检查需求完整性（使用 LLM）.

    这是一个原子操作工具，只负责完整性检查。
    不包含补充收集逻辑，补充由 Agent-Skill 编排。

    Args:
        ctx: MCP 上下文
        answers: 已收集的答案
        prompt_template: 自定义Prompt模板（可选，用于特殊场景）。
                        Prompt模板应由Agent-Skill提供，符合ADR 001架构原则。

    Returns:
        包含完整性检查结果的字典
    """
    return await check_requirement_completeness(ctx, answers, prompt_template)


# ==================== MCP Resources ====================


# ==================== MCP Resources ====================


@mcp.resource("http://skills/schema/templates", mime_type="text/markdown")
def list_templates_resource() -> str:
    """列出所有可用的技能模板."""
    templates = list_templates()
    result = "# 技能模板列表\n\n"
    for t in templates:
        result += f"## {t['type']}\n"
        result += f"{t['description']}\n\n"
    return result


@mcp.resource("http://skills/schema/templates/{type}", mime_type="text/markdown")
def get_template_resource(type: str) -> str:
    """获取指定类型的技能模板内容."""
    from .resources.templates import TemplateType

    # 验证模板类型
    valid_types = ["minimal", "tool-based", "workflow-based", "analyzer-based"]
    if type not in valid_types:
        return f"# 错误\n\n未知的模板类型: {type}\n\n有效类型: {', '.join(valid_types)}"

    return get_template_content(TemplateType(type))  # type: ignore


@mcp.resource("http://skills/schema/best-practices", mime_type="text/markdown")
def best_practices_resource() -> str:
    """获取 Agent-Skills 开发最佳实践."""
    return get_best_practices()


@mcp.resource("http://skills/schema/validation-rules", mime_type="text/markdown")
def validation_rules_resource() -> str:
    """获取 Agent-Skills 验证规则."""
    return get_validation_rules()


# ==================== MCP Prompts ====================


@mcp.prompt("create-skill")
def create_skill_prompt(
    name: str,
    template: str = "minimal",
) -> str:
    """创建新技能的 Prompt 模板.

    Args:
        name: 技能名称
        template: 模板类型（默认：minimal）

    Returns:
        Prompt 模板内容
    """
    return get_create_skill_prompt(name, template)


@mcp.prompt("validate-skill")
def validate_skill_prompt(
    skill_path: str,
    template: str | None = None,
) -> str:
    """验证技能的 Prompt 模板.

    Args:
        skill_path: 技能目录路径
        template: 模板类型（可选）

    Returns:
        Prompt 模板内容
    """
    return get_validate_skill_prompt(skill_path, template)


@mcp.prompt("refactor-skill")
def refactor_skill_prompt(
    skill_path: str,
    focus: list[str] | None = None,
) -> str:
    """重构技能的 Prompt 模板.

    Args:
        skill_path: 技能目录路径
        focus: 重点关注领域（可选）

    Returns:
        Prompt 模板内容
    """
    return get_refactor_skill_prompt(skill_path, focus)


__all__ = ["mcp"]
