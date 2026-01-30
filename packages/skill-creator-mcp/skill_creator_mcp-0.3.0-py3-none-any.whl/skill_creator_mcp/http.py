"""HTTP/SSE 传输入口点（远程部署）.

这是用于远程部署的 HTTP 入口点，通过 SSE (Server-Sent Events) 与 Claude Code 通信。

使用方式：
    uv run python -m skill_creator_mcp.http

或在 Docker/Kubernetes 中：
    uvicorn skill_creator_mcp.http:app --host 0.0.0.0 --port 8000
"""

import sys

from .server import mcp


def main() -> int:
    """启动 MCP Server (HTTP/SSE 模式).

    FastMCP 的 run() 方法支持多种传输协议。
    传入 transport="sse" 即可启动 SSE HTTP 服务器。

    Returns:
        退出码（0 表示成功，非 0 表示错误）
    """
    try:
        # FastMCP.run() 支持传输协议参数
        # transport="sse" 会启动 uvicorn SSE 服务器
        mcp.run(transport="sse")  # type: ignore[func-returns-value]
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
