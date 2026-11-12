# -*- coding: utf-8 -*-
"""Agent 轨迹落盘（jsonl，逐行 flush）。

补齐本项目此前完全缺失的「可审计轨迹」：
改造前 tool_trace 只是响应里的一个内存数组，请求结束就没了，
无法回答「上周那次为什么判断达成」「哪个阶段最耗时」这类问题。

目录：.runtime/traces/YYYY-MM-DD/{trace_id}.jsonl
每行一个事件：{"ts": "...", "phase": "plan", "payload": {...}}
"""
import json
import os
import time
import uuid
from datetime import datetime, timezone


def _today() -> str:
    return time.strftime("%Y-%m-%d")


def _root() -> str:
    return os.getenv("AGENT_TRACE_DIR", ".runtime/traces")


class Trace:
    """一次循环执行的事件流。写失败不影响主链路（演示优先）。"""

    def __init__(self, trace_id: str | None = None, root: str | None = None):
        self.trace_id = trace_id or uuid.uuid4().hex[:8]
        self.dir = os.path.join(root or _root(), _today())
        self.path = os.path.join(self.dir, f"{self.trace_id}.jsonl")
        try:
            os.makedirs(self.dir, exist_ok=True)
        except OSError:
            pass

    # ---- 写
    def write(self, phase: str, payload: dict) -> None:
        rec = {
            "ts": datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%dT%H:%M:%S"),
            "phase": phase,
            "payload": payload,
        }
        try:
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")
                f.flush()
        except OSError:
            pass

    def phase(self, phase: str, **payload) -> None:
        self.write(phase, payload)

    # ---- 读
    def events(self) -> list[dict]:
        return read_trace(self.trace_id)

    def exists(self) -> bool:
        return os.path.exists(self.path)


def _find(trace_id: str) -> str | None:
    """按 trace_id 在所有日期目录里找（跨天可查）。"""
    root = _root()
    if not os.path.isdir(root):
        return None
    direct = os.path.join(root, _today(), f"{trace_id}.jsonl")
    if os.path.exists(direct):
        return direct
    for day in sorted(os.listdir(root), reverse=True):
        p = os.path.join(root, day, f"{trace_id}.jsonl")
        if os.path.exists(p):
            return p
    return None


def read_trace(trace_id: str) -> list[dict]:
    path = _find(trace_id)
    if not path:
        return []
    out = []
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except OSError:
        return []
    return out


def summarize(events: list[dict]) -> dict:
    """汇总：各阶段事件数、工具调用次数、总耗时（首末时间戳差）。"""
    by_phase: dict[str, int] = {}
    tools: list[str] = []
    for e in events:
        p = e.get("phase") or "unknown"
        by_phase[p] = by_phase.get(p, 0) + 1
        pl = e.get("payload") or {}
        if p == "act":
            # loop.py 写的是 step，兼容早期写 skill 的事件
            name = pl.get("skill") or pl.get("step")
            if name:
                tools.append(name)

    span = None
    if len(events) >= 2:
        try:
            t0 = datetime.strptime(events[0]["ts"], "%Y-%m-%dT%H:%M:%S")
            t1 = datetime.strptime(events[-1]["ts"], "%Y-%m-%dT%H:%M:%S")
            span = int((t1 - t0).total_seconds())
        except (KeyError, ValueError):
            span = None

    return {"events": len(events), "by_phase": by_phase,
            "tool_calls": tools, "span_seconds": span}


__all__ = ["Trace", "read_trace", "summarize"]
