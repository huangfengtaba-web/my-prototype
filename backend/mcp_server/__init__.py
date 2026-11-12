# -*- coding: utf-8 -*-
"""MCP Server 包：把排程系统能力暴露给任意 MCP 客户端（Claude Desktop / Cursor / Inspector）。

可选依赖：pip install -r backend/requirements-mcp.txt
主 requirements.txt 不含 mcp，Render 镜像体积与内存不受影响。
"""
from backend.mcp_server.server import SERVER_NAME, build_server, selftest  # noqa: F401

__all__ = ["SERVER_NAME", "build_server", "selftest"]
