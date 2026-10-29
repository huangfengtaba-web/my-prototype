# -*- coding: utf-8 -*-
"""把六步排程结果转成 3D 孪生时间轴事件流。

契约（冻结，前端 gtxTwinApi.loadSchedule 依赖）：
    {"run_id","baseDate","t0","t1","events":[
        {"t": int(秒,相对t0), "type": "eqp_state|reticle_move|reticle_state", ...}]}
events 必须按 t 升序；type 只允许上述三种。
"""
from typing import Any, Dict, List


def _sec(hhmm: str) -> int:
    try:
        h, m = hhmm.split(":")
        return int(h) * 3600 + int(m) * 60
    except Exception:
        return 0


def build_timeline(run_summary: Dict[str, Any], run_id: str = "") -> Dict[str, Any]:
    schedule: List[Dict[str, Any]] = run_summary.get("schedule") or []
    reticles: Dict[str, Any] = run_summary.get("reticles") or {}

    starts = [_sec(r["start"]) for r in schedule if r.get("start")]
    ends = [_sec(r["end"]) for r in schedule if r.get("end")]
    if not starts:
        return {"run_id": run_id, "baseDate": run_summary.get("date", ""),
                "t0": "00:00", "t1": "00:00", "events": []}

    t0, t1 = min(starts), max(ends)
    events: List[Dict[str, Any]] = []
    oht = 0

    for row in schedule:
        eqp = row.get("eqp")
        if not eqp or not row.get("start"):
            continue
        s = _sec(row["start"]) - t0
        e = (_sec(row["end"]) - t0) if row.get("end") else s + 25

        events.append({"t": s, "type": "eqp_state", "target": eqp,
                       "state": "Busy", "lot": row.get("lot")})
        events.append({"t": e, "type": "eqp_state", "target": eqp, "state": "Idle"})

        ret = row.get("reticle")
        if ret:
            oht += 1
            events.append({"t": max(0, s - 300), "type": "reticle_move",
                           "target": ret, "from": "STOCKER-01", "to": eqp,
                           "vehicle": f"OHT-{oht:02d}"})
            events.append({"t": max(0, s - 60), "type": "reticle_state",
                           "target": ret, "state": "装载"})

    for rid, meta in reticles.items():
        if meta.get("ready"):
            events.append({"t": 0, "type": "reticle_state",
                           "target": rid, "state": "就绪"})

    events.sort(key=lambda x: x["t"])
    return {
        "run_id": run_id,
        "baseDate": run_summary.get("date", ""),
        "t0": f"{t0 // 3600:02d}:{t0 % 3600 // 60:02d}",
        "t1": f"{t1 // 3600:02d}:{t1 % 3600 // 60:02d}",
        "events": events,
    }
