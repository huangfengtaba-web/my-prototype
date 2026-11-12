# -*- coding: utf-8 -*-
"""MCP 工具清单与 HTTP 能力清单的同源断言。

不启动 MCP 进程、不联网，直接比对两边数据结构。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app import registry                                    # noqa: E402
from backend.mcp_server.server import build_server                  # noqa: E402


def test_mcp_server_builds():
    srv = build_server()
    assert srv is not None


def test_mcp_tool_names_match_registry():
    mcp_names = {t["name"] for t in registry.to_mcp_tools()}
    assert mcp_names == set(registry.names())


def test_mcp_schema_identical_to_registry():
    """逐字段同一对象：MCP 的 inputSchema 必须与注册表完全一致。"""
    for t in registry.to_mcp_tools():
        assert t["inputSchema"] == registry.get(t["name"]).input_schema


def test_mcp_and_http_panel_same_skills():
    """MCP 清单与前端能力面板（/api/capabilities 的数据源）必须同源。"""
    mcp_names = {t["name"] for t in registry.to_mcp_tools()}
    panel_names = {s["name"] for c in registry.to_panel() for s in c["skills"]}
    assert mcp_names == panel_names


def test_every_tool_has_description_and_schema():
    for t in registry.to_mcp_tools():
        assert t["description"].strip(), t["name"]
        assert t["inputSchema"]["type"] == "object", t["name"]
