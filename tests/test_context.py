# -*- coding: utf-8 -*-
"""上下文工程回归：token 估算、预算压缩、三级会话存储。

纯内存/临时目录，不联网、不依赖 LLM。
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.agent import context, session_store                # noqa: E402


# ---------------------------------------------------------------- token 估算
def test_estimate_tokens_cjk_vs_ascii():
    assert context.estimate_tokens("你好世界") == 4            # CJK 1 token/字
    assert context.estimate_tokens("abcdefg") == 2             # 7/3.5
    assert context.estimate_tokens("") == 0
    assert context.estimate_tokens(None) == 0


def test_count_tokens_includes_overhead():
    msgs = [{"role": "user", "content": "你好"}]
    assert context.count_tokens(msgs) == 2 + 4


# ---------------------------------------------------------------- 压缩
def test_short_dialog_not_compressed():
    msgs = [{"role": "user", "content": "跑急货"}, {"role": "assistant", "content": "好的"}]
    out, summary = context.compress(msgs, budget=6000, keep_turns=4)
    assert len(out) == 2 and summary == ""


def test_over_keep_turns_drops_oldest_and_summarizes():
    msgs = []
    for i in range(10):
        msgs.append({"role": "user", "content": f"问题{i}"})
        msgs.append({"role": "assistant", "content": f"回答{i}"})
    out, summary = context.compress(msgs, budget=100000, keep_turns=2)
    dialog = [m for m in out if m.get("role") != "system"]     # 摘要是 system 消息，不计条数
    assert len(dialog) == 4                                     # 只留最近 2 轮
    assert dialog[-1]["content"] == "回答9"
    assert "问题0" in summary                                   # 丢掉的进了摘要


def test_summary_capped():
    msgs = [{"role": "user", "content": "很长的问题" * 50},
            {"role": "assistant", "content": "很长的回答" * 50}] * 20
    _, summary = context.compress(msgs, budget=200, keep_turns=1, summary_max=50)
    assert len(summary) <= 60                              # 允许 1 个省略号前缀


def test_tool_message_shrunk_when_over_budget():
    big = "数据" * 5000
    msgs = [
        {"role": "user", "content": "查询"},
        {"role": "tool", "content": big},
        {"role": "assistant", "content": "结果如上"},
    ]
    out, _ = context.compress(msgs, budget=800, keep_turns=5)
    tool_msgs = [m for m in out if m.get("role") == "tool"]
    assert tool_msgs and len(tool_msgs[0]["content"]) < len(big)


def test_budget_respected_after_compress():
    msgs = [{"role": "user", "content": "问" * 3000},
            {"role": "assistant", "content": "答" * 3000}]
    out, _ = context.compress(msgs, budget=500, keep_turns=5)
    assert context.count_tokens(out) <= 500 * 3            # 极端保护，留 3 倍余量


# ---------------------------------------------------------------- 存储
def test_memory_store_roundtrip():
    st = session_store.MemoryStore()
    st.save("s1", {"messages": [{"role": "user", "content": "hi"}], "summary": "", "mode": "rule"})
    assert st.load("s1")["messages"][0]["content"] == "hi"
    assert st.load("nope") is None


def test_jsonl_store_persists_across_instances(tmp_path):
    a = session_store.JsonlStore(str(tmp_path))
    a.save("s2", {"messages": [{"role": "user", "content": "第一句"}], "summary": "s", "mode": "llm"})
    b = session_store.JsonlStore(str(tmp_path))            # 新实例，模拟进程重启
    got = b.load("s2")
    assert got["messages"][0]["content"] == "第一句"
    assert got["mode"] == "llm"


def test_store_selection_by_env(monkeypatch):
    monkeypatch.delenv("SUPABASE_DB_URL", raising=False)
    monkeypatch.setenv("AGENT_SESSION_STORE", "memory")
    session_store.reset_store()
    assert session_store.get_store().name == "memory"

    monkeypatch.setenv("AGENT_SESSION_STORE", "jsonl")
    session_store.reset_store()
    assert session_store.get_store().name == "jsonl"

    session_store.reset_store()
    monkeypatch.delenv("AGENT_SESSION_STORE", raising=False)
