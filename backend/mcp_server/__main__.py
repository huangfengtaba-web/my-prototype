# -*- coding: utf-8 -*-
"""MCP Server 进程入口。

用法：
    python -m backend.mcp_server --transport stdio              # Claude Desktop / Cursor
    python -m backend.mcp_server --transport http --port 8765   # 远程/调试
    python -m backend.mcp_server --selftest                     # 自检，不起服务

⚠️ stdio 传输下 stdout 是 JSON-RPC 通道，任何 print() 都会破坏协议。
   因此本文件最早期就把 stdout 重定向到 stderr（在 import backend 之前完成）。
"""
import argparse
import builtins
import contextlib
import os
import sys

# ---- 必须在任何 backend 导入之前执行：保护 stdout ----
_REAL_PRINT = builtins.print


def _safe_print(*args, **kwargs):
    kwargs.pop("file", None)
    _REAL_PRINT(*args, file=sys.stderr, **kwargs)


builtins.print = _safe_print
contextlib.redirect_stdout(sys.stderr)

# Windows 控制台编码保护（与 solver_runner 保持一致）
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
os.environ.setdefault("PYTHONUTF8", "1")


def _run_stdio(server) -> int:
    import anyio
    from mcp.server.stdio import stdio_server

    async def _main():
        async with stdio_server() as (read, write):
            await server.run(read, write, server.create_initialization_options())

    anyio.run(_main)
    return 0


def _run_http(server, port: int) -> int:
    """streamable-http 传输（可选）。失败时明确退出，不影响 stdio 主路径。"""
    try:
        import anyio
        import uvicorn
        from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
        from starlette.applications import Starlette
        from starlette.routing import Mount
    except Exception as e:                            # noqa: BLE001
        sys.stderr.write(f"[mcp] http 传输依赖缺失: {e}\n")
        return 2

    manager = StreamableHTTPSessionManager(app=server, json_response=True, stateless=True)

    async def _serve():
        async with manager.run():
            app = Starlette(routes=[Mount("/mcp", app=manager.handle_request)])
            config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="info")
            await uvicorn.Server(config).serve()

    anyio.run(_serve)
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="backend.mcp_server", description="GTX FSO Litho MCP Server")
    parser.add_argument("--transport", choices=["stdio", "http"], default="stdio")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--selftest", action="store_true", help="只做自检，不启动服务")
    args = parser.parse_args(argv)

    from backend.mcp_server.server import build_server, selftest

    if args.selftest:
        import anyio
        return anyio.run(selftest)

    server = build_server()
    if args.transport == "stdio":
        return _run_stdio(server)
    return _run_http(server, args.port)


if __name__ == "__main__":
    raise SystemExit(main())
