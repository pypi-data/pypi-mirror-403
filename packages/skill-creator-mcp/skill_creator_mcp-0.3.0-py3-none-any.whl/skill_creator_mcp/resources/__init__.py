"""MCP Resources 模块.

提供静态资源访问，包括：
- 技能模板 (skill://templates/{type})
- 最佳实践 (skill://best-practices)
- 验证规则 (skill://validation-rules)
"""

from skill_creator_mcp.resources.best_practices import get_best_practices
from skill_creator_mcp.resources.templates import (
    get_template_content,
    list_templates,
)
from skill_creator_mcp.resources.validation_rules import get_validation_rules

__all__ = [
    "get_template_content",
    "list_templates",
    "get_best_practices",
    "get_validation_rules",
]
