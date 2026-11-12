# -*- coding: utf-8 -*-
"""Loop Engineering 的目标解析与**确定性判定**。

设计铁律：
    goal_met 必须由本模块的确定性函数给出，LLM 只能解释差距（gap），
    不能翻转判定结果 —— 否则会出现「模型自评自夸」的不可审计行为。

支持四类目标：
    urgent_deadline  急货 Lot 必须在某时刻前上机      「让急货 10 点前上机」
    makespan_le      整体完工时间不超过某分钟数        「MakeSpan 不超过 12:35」
    on_time_ge       仿真准时率不低于某比例            「准时率 95% 以上」
    freeform         其它（交 LLM 判定，标 llm_judged，可审计）
"""
import re
from dataclasses import dataclass

from backend.app.registry.types import Goal


def to_min(hm) -> int | None:
    """'HH:MM' 或 'H:MM' → 当日分钟数。无效返回 None。"""
    if not hm or not isinstance(hm, str):
        return None
    m = re.match(r"^\s*(\d{1,2}):(\d{2})\s*$", hm)
    if not m:
        return None
    h, mi = int(m.group(1)), int(m.group(2))
    if h > 23 or mi > 59:
        return None
    return h * 60 + mi


_TIME_RE = re.compile(r"(\d{1,2})\s*[:：点]\s*(\d{2})?")
_PCT_RE = re.compile(r"(\d{1,3}(?:\.\d+)?)\s*%")
_MAKESPAN_RE = re.compile(r"(?:makespan|完工|完成时间).{0,8}?(\d{1,2})\s*[:：]\s*(\d{2})", re.I)


def parse_goal(text: str) -> Goal:
    """把自然语言目标解析成结构化 Goal。顺序重要：先匹配更具体的形态。"""
    raw = (text or "").strip()
    low = raw.lower()

    # 1) 急货截止时间：「急货 10 点前上机」「LOT-A01 必须在 09:30 开工」
    if "急货" in raw or "lot-a01" in low:
        deadline = None
        m = _TIME_RE.search(raw)
        if m:
            h = int(m.group(1))
            mi = int(m.group(2) or 0)
            if h <= 23 and mi <= 59:
                deadline = h * 60 + mi
        return Goal("urgent_deadline",
                    {"lot": "LOT-A01", "deadline_min": deadline if deadline is not None else 600},
                    raw)

    # 2) MakeSpan 上限：「MakeSpan 不超过 12:35」
    m = _MAKESPAN_RE.search(raw)
    if m:
        h, mi = int(m.group(1)), int(m.group(2))
        if h <= 23 and mi <= 59:
            return Goal("makespan_le", {"limit_min": h * 60 + mi}, raw)
    if "makespan" in low and (n := re.search(r"(\d{2,4})", raw)):
        v = int(n.group(1))
        return Goal("makespan_le", {"limit_min": v if v > 240 else None}, raw)

    # 3) 准时率下限：「准时率 95% 以上」
    if "准时率" in raw or "on_time" in low:
        m = _PCT_RE.search(raw)
        rate = float(m.group(1)) / 100 if m else 0.95
        return Goal("on_time_ge", {"rate": min(max(rate, 0.0), 1.0)}, raw)

    return Goal("freeform", {"text": raw}, raw)


# ---------------------------------------------------------------- 判定
def _sched_of(solve_record) -> list[dict]:
    """取排程行。兼容两种输入：
    1) 求解原始 record（有 summary.schedule）
    2) run_solve 工具返回的压缩摘要（只有 urgent_a01_start / makespan）
    """
    rec = solve_record or {}
    s = rec.get("summary") or {}
    sched = [r for r in (s.get("schedule") or []) if r.get("start")]
    if sched:
        return sched
    if rec.get("urgent_a01_start"):
        return [{"lot": "LOT-A01", "start": rec.get("urgent_a01_start"),
                 "eqp": rec.get("urgent_a01_eqp"), "end": rec.get("makespan")}]
    return []


def _makespan_of(solve_record) -> int | None:
    """优先用摘要里的 makespan，其次从 schedule 算。"""
    rec = solve_record or {}
    ms = rec.get("makespan")
    if ms:
        return to_min(ms)
    ends = [to_min(r.get("end")) for r in _sched_of(rec)]
    ends = [e for e in ends if e is not None]
    return max(ends) if ends else None


def evaluate(goal: Goal, ctx: dict) -> tuple[bool, dict]:
    """确定性判定。

    ctx 约定：
        {"solve": <run_solve 的原始 record>, "sim": <run_sim 的原始 record>, "observations": [...]}

    Returns: (goal_met, evidence)
        evidence 会被写进 trace，供人审计「为什么判定达成/未达成」
    """
    solve = ctx.get("solve") or {}
    sim = ctx.get("sim") or {}
    sched = _sched_of(solve)

    if goal.kind == "urgent_deadline":
        lot = goal.params.get("lot", "LOT-A01")
        deadline = goal.params.get("deadline_min")
        row = next((r for r in sched if r.get("lot") == lot), None)
        start = to_min(row.get("start")) if row else None
        if start is None:
            return False, {"reason": f"{lot} 未排产", "lot": lot,
                           "deadline_min": deadline, "actual_min": None}
        met = deadline is not None and start <= deadline
        return met, {
            "reason": "达成" if met else "上机晚于截止时间",
            "lot": lot,
            "start": row.get("start"),
            "eqp": row.get("eqp"),
            "actual_min": start,
            "deadline_min": deadline,
            "slack_min": (deadline - start) if deadline is not None else None,
        }

    if goal.kind == "makespan_le":
        limit = goal.params.get("limit_min")
        actual = _makespan_of(solve)
        if actual is None:
            return False, {"reason": "无有效排程", "limit_min": limit}
        met = limit is not None and actual <= limit
        return met, {"reason": "达成" if met else "完工晚于上限",
                     "actual_min": actual, "limit_min": limit,
                     "slack_min": (limit - actual) if limit is not None else None}

    if goal.kind == "on_time_ge":
        kpis = (sim or {}).get("sim", {}).get("kpis") or sim.get("kpis") or {}
        rate = kpis.get("on_time_rate")
        target = goal.params.get("rate", 0.95)
        if rate is None:
            return False, {"reason": "未找到仿真 KPI，请先跑 run_sim", "target": target}
        met = float(rate) >= float(target)
        return met, {"reason": "达成" if met else "准时率低于目标",
                     "actual": rate, "target": target}

    # freeform：不在这里编造判定
    return False, {"reason": "无法确定性判定，需 LLM 解释（标记 llm_judged）",
                   "llm_judged": True, "goal": goal.text}


def describe(goal: Goal) -> str:
    """给 trace / 前端看的一句话目标描述。"""
    if goal.kind == "urgent_deadline":
        d = goal.params.get("deadline_min")
        hm = f"{d // 60:02d}:{d % 60:02d}" if d is not None else "?"
        return f"{goal.params.get('lot')} 需在 {hm} 前上机"
    if goal.kind == "makespan_le":
        d = goal.params.get("limit_min")
        hm = f"{d // 60:02d}:{d % 60:02d}" if d is not None else "?"
        return f"整体完工（MakeSpan）不晚于 {hm}"
    if goal.kind == "on_time_ge":
        return f"仿真准时率不低于 {goal.params.get('rate', 0):.0%}"
    return f"自由目标：{goal.text}"


__all__ = ["Goal", "parse_goal", "evaluate", "describe", "to_min"]
