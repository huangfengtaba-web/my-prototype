# -*- coding: utf-8 -*-
"""Agent 回归（规则模式路由 / 工具执行 / 会话记忆）。

LLM 模式依赖外部 Key，不在 CI 断言；规则模式必须全绿。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.agent import agent                                  # noqa: E402


def test_status_rule_mode():
    st = agent.agent_status()
    # 测试环境不配置 LLM Key（若本机误配了环境变量，则跳过模式断言）
    if os.getenv("LLM_API_KEY"):
        return
    assert st["mode"] == "rule"
    assert "run_solve" in st["tools"] and "run_sim" in st["tools"]


def test_route_solve_with_case():
    r = agent.chat("跑一下 urgent-A01 这个用例看看急货排得怎么样")
    assert r["mode"] == "rule"
    names = [t["name"] for t in r["tool_calls"]]
    assert names == ["run_solve"], names
    assert r["tool_calls"][0]["args"].get("case") == "urgent-A01"
    assert "run_id" in r["reply"]


def test_route_list_cases():
    r = agent.chat("有哪些用例？")
    assert [t["name"] for t in r["tool_calls"]] == ["list_cases"]
    assert "urgent-A01" in r["reply"]


def test_route_sim():
    r = agent.chat("帮我仿真一下 reticle-delay")
    assert [t["name"] for t in r["tool_calls"]] == ["run_sim"]
    assert "准时率" in r["reply"]


def test_route_workflow_compare():
    r = agent.chat("对比一下几个场景")
    call = r["tool_calls"][0]
    assert call["name"] == "run_workflow"
    assert call["args"]["template_id"] == "scenario-compare"
    assert "工作流" in r["reply"]


def test_unknown_intent_gives_help():
    r = agent.chat("今天天气怎么样")
    assert r["tool_calls"] == []
    assert "规则模式" in r["reply"] or "可以让我" in r["reply"]


def test_session_memory():
    a = agent.chat("有哪些用例？", session_id="t1")
    b = agent.chat("再跑一次 urgent-A01", session_id="t1")
    assert a["session_id"] == b["session_id"] == "t1"
    assert agent.SESSIONS["t1"]["messages"][-1]["role"] == "assistant"
