# -*- coding: utf-8 -*-
"""轨迹落盘回归：写入、读回、汇总、跨日期查找。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.agent import trace                                  # noqa: E402


def test_write_and_read(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_TRACE_DIR", str(tmp_path))
    tr = trace.Trace(trace_id="t1")
    tr.phase("start", goal="让急货 10 点前上机")
    tr.phase("plan", steps=[{"skill": "run_solve"}])
    tr.phase("act", skill="run_solve", ok=True)
    tr.phase("end", status="done", met=True)

    events = trace.read_trace("t1")
    assert len(events) == 4
    assert [e["phase"] for e in events] == ["start", "plan", "act", "end"]
    assert events[0]["payload"]["goal"].startswith("让急货")


def test_summarize(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_TRACE_DIR", str(tmp_path))
    tr = trace.Trace(trace_id="t2")
    tr.phase("start", goal="x")
    tr.phase("act", skill="run_solve", ok=True)
    tr.phase("act", skill="run_sim", ok=True)
    tr.phase("end", status="done")

    s = trace.summarize(trace.read_trace("t2"))
    assert s["events"] == 4
    assert s["by_phase"]["act"] == 2
    assert s["tool_calls"] == ["run_solve", "run_sim"]


def test_missing_trace_returns_empty(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_TRACE_DIR", str(tmp_path))
    assert trace.read_trace("nope") == []
    assert trace.summarize([]) == {"events": 0, "by_phase": {},
                                   "tool_calls": [], "span_seconds": None}


def test_trace_file_is_jsonl(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_TRACE_DIR", str(tmp_path))
    tr = trace.Trace(trace_id="t3")
    tr.phase("start", goal="g")
    tr.phase("end", status="done")
    with open(tr.path, encoding="utf-8") as f:
        lines = [ln for ln in f.read().splitlines() if ln.strip()]
    assert len(lines) == 2
    import json
    assert json.loads(lines[0])["phase"] == "start"
