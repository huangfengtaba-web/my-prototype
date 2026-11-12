# -*- coding: utf-8 -*-
"""能力注册表回归：三端视图同源、schema 合法、校验器行为。

纯内存断言，不依赖 LLM / 不跑求解。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app import registry                                   # noqa: E402
from backend.app.agent import tools                                # noqa: E402
from backend.app.registry import validate_args                     # noqa: E402

EXPECTED = {"list_cases", "run_solve", "get_result", "get_mock_data",
            "run_sim", "run_workflow", "list_workflows"}


def test_registry_has_seven_skills():
    assert set(registry.names()) == EXPECTED


def test_names_match_legacy_tools():
    """注册表与兼容层 TOOLS 的键必须完全一致（否则 agent 路由会崩）。"""
    assert set(registry.names()) == set(tools.TOOLS)


def test_every_skill_schema_is_object():
    for name in registry.names():
        s = registry.get(name)
        assert s.input_schema.get("type") == "object", name
        assert isinstance(s.input_schema.get("properties"), dict), name
        assert "required" in s.input_schema, name


def test_openai_and_mcp_views_are_same_set():
    oai = {t["function"]["name"] for t in registry.to_openai_tools()}
    mcp = {t["name"] for t in registry.to_mcp_tools()}
    assert oai == mcp == EXPECTED


def test_openai_parameters_carry_real_schema():
    """关键回归：参数类型必须是 integer/boolean，而不是旧实现的一律 string。"""
    spec = next(t for t in registry.to_openai_tools()
                if t["function"]["name"] == "run_sim")
    props = spec["function"]["parameters"]["properties"]
    assert props["seed"]["type"] == "integer"
    assert props["breakdown"]["type"] == "boolean"


def test_mcp_schema_is_identical_to_input_schema():
    for t in registry.to_mcp_tools():
        assert t["inputSchema"] == registry.get(t["name"]).input_schema


def test_panel_covers_all_skills():
    panel = registry.to_panel()
    got = {s["name"] for c in panel for s in c["skills"]}
    assert got == EXPECTED
    assert all(c["category"] and c["title"] for c in panel)


def test_system_prompt_lists_all_names():
    frag = registry.system_prompt_fragment()
    for n in EXPECTED:
        assert n in frag, f"系统提示缺少能力 {n}"


def test_validate_rejects_missing_required():
    errs = validate_args(registry.get("get_result"), {})
    assert errs and "run_id" in errs[0]


def test_validate_rejects_unknown_arg_and_accepts_good():
    assert validate_args(registry.get("list_cases"), {"bogus": 1})
    assert validate_args(registry.get("run_solve"), {"case": "urgent-A01", "fix": True}) == []
