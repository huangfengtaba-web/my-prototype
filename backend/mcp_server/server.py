# -*- coding: utf-8 -*-
"""MCP Server：把能力注册表暴露为标准 MCP 工具。

设计要点：
  - 用官方**低层 Server API**，不用 FastMCP 装饰器 —— 后者靠函数签名推断 schema，
    而我们的 handler 是 Callable[..., dict]，推断结果不可靠。
  - inputSchema 直接从注册表取，与 /api/capabilities 逐字段同源。
  - call_tool(validate_input=False)：MCP 自带的 jsonschema 校验会拒绝我们 schema 里的
    自定义字段，改由 registry.validate_args 自己校验（行为可测）。
"""
import json

import anyio
import mcp.types as types
from mcp.server import Server

from backend.app import registry
from backend.app.registry import validate_args

SERVER_NAME = "gtx-fso-litho"


def _text(payload) -> list[types.TextContent]:
    text = payload if isinstance(payload, str) else json.dumps(
        payload, ensure_ascii=False, default=str)
    return [types.TextContent(type="text", text=text)]


def build_server() -> Server:
    server = Server(SERVER_NAME)

    @server.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name=s.name,
                title=s.title,
                description=s.description,
                inputSchema=s.input_schema,
            )
            for s in (registry.get(n) for n in registry.names())
        ]

    @server.call_tool(validate_input=False)
    async def call_tool(name: str, arguments: dict | None):
        skill = registry.get(name)
        if skill is None:
            return _text({"error": f"未知工具 {name}",
                          "available": registry.names()})

        args = arguments or {}
        errs = validate_args(skill, args)
        if errs:
            return _text({"error": "参数校验失败", "details": errs})

        try:
            result = await anyio.to_thread.run_sync(lambda: skill.handler(**args))
        except Exception as e:                       # noqa: BLE001  工具异常不炸协议
            result = {"error": f"{type(e).__name__}: {e}"}

        if isinstance(result, dict):
            raw = json.dumps(result, ensure_ascii=False, default=str)
        else:
            raw = str(result)
        return _text(raw[: skill.max_result_chars])

    return server


async def selftest() -> int:
    """不依赖 MCP 客户端的自检：列出工具 + 调一次 list_cases。"""
    server = build_server()
    # 直接调用注册的处理器（绕过协议层，验证核心逻辑）
    tools_ = [types.Tool(
        name=s.name, title=s.title, description=s.description,
        inputSchema=s.input_schema,
    ) for s in (registry.get(n) for n in registry.names())]

    print(f"[selftest] server={SERVER_NAME}  mcp_tools={len(tools_)}")
    for t in tools_:
        req = ", ".join(t.inputSchema.get("required") or []) or "-"
        print(f"  - {t.name:<16} required=[{req}]  {t.description[:40]}...")

    cases = registry.get("list_cases").handler()
    n = len(cases.get("cases") or [])
    print(f"[selftest] list_cases -> {n} 个用例: {', '.join((cases.get('cases') or [])[:6])}")

    ok = len(tools_) > 0 and n > 0
    print("[selftest]", "PASS" if ok else "FAIL")
    return 0 if ok else 1
