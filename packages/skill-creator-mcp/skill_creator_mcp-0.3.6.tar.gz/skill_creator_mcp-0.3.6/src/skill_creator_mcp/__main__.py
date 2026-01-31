"""STDIO 传输入口点（本地开发）.

这是用于本地开发的主入口点，通过 STDIO 与 Claude Code 通信。

使用方式：
    uv run python -m skill_creator_mcp

或在 Claude Code 配置中：
    {
        "mcpServers": {
            "skill-creator": {
                "command": "uv",
                "args": [
                    "--directory", "/path/to/skill-creator-mcp",
                    "run", "python", "-m", "skill_creator_mcp"
                ]
            }
        }
    }
"""

import sys

from .config import get_config
from .logging_config import setup_logging
from .server import mcp


def main() -> int:
    """启动 MCP Server (STDIO 模式).

    FastMCP 的 run() 方法会自动处理 STDIO 传输协议。
    这是同步入口点，内部会处理异步循环。

    日志配置可通过环境变量设置:
        SKILL_CREATOR_LOG_LEVEL: 日志级别 (DEBUG/INFO/WARNING/ERROR/CRITICAL)
        SKILL_CREATOR_LOG_FORMAT: 日志格式 (default/simple/detailed)
        SKILL_CREATOR_LOG_FILE: 日志文件路径（可选）

    Returns:
        退出码（0 表示成功，非 0 表示错误）
    """
    # 从环境变量读取配置
    config = get_config()

    # 初始化日志系统（使用环境变量配置）
    setup_logging(
        level=config.log_level,
        log_file=config.log_file,
        format_type=config.log_format,
    )

    try:
        # FastMCP.run() 会自动检测 STDIO 环境并运行服务器
        # 这是一个同步方法，内部处理异步事件循环
        mcp.run()  # type: ignore[func-returns-value]
        return 0
    except KeyboardInterrupt:
        # 用户中断（Ctrl+C）
        return 130
    except Exception as e:
        # 其他异常
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
