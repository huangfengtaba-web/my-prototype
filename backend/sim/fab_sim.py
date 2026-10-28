# -*- coding: utf-8 -*-
"""GTX FSO Litho · 仿真叙事模块（SemiconFab 叙事移植，轻量自研 DES）。

对排程结果做**执行态**离散事件仿真：计划是"应然"，仿真是"实然"。
事件步进按计划开工时间全局推进，零第三方依赖、种子确定可复现。
三类扰动：
    1. 机台故障（MTBF/MTTR，指数分布）
    2. 光罩接力搬送（跨机台使用时光罩要先运到 + 装载）
    3. 良率异常返工（按比例概率，加工时长翻倍）

数据来源：run_summary.schedule（六步 MILP 输出的计划排程）+ mock_data 的 QTime/到站字段。
用法::

    from backend.sim import run_simulation
    result = run_simulation(plan_schedule, seed=42, breakdown=True)
"""
import random

try:
    from ..solver.mock_data import CONFIG, LOTS, fmt
except ImportError:           # 脚本模式兜底
    from backend.solver.mock_data import CONFIG, LOTS, fmt

DEFAULT_PARAMS = {
    "mtbf_min": 900,          # 机台平均无故障时间（指数分布均值）
    "mttr_min": 30,           # 平均修复时长
    "rework_rate": 0.05,      # 良率异常返工概率
    "duration_cv": 0.05,      # 加工时长波动系数（正态）
    "tolerance_min": 15,      # 准时判定容差（实际晚 ≤ 容差算准时）
}

# mock_data 补充字段：到站时间与 QTime 上限（schedule 行里没有，仿真要从源头取）
_LOT_META = {l["lot"]: l for l in LOTS}


def run_simulation(plan, seed=42, breakdown=True, params=None):
    """对计划排程跑一次执行仿真。

    plan: run_summary.schedule 的行（lot/eqp/eqp_group/reticle/priority/temp/start/end/...）
    返回 {kpis, lots, params}；plan 为空时抛 ValueError。
    """
    p = dict(DEFAULT_PARAMS)
    p.update(params or {})
    jobs = [r for r in plan if r.get("eqp") and r.get("start") and r.get("end")]
    if not jobs:
        raise ValueError("plan 里没有可仿真的排程行（需含 eqp/start/end）")
    rng = random.Random(seed)

    # 光罩状态：当前挂载机台 + 释放时间（跨机台使用触发接力搬送）
    reticle_state = {}            # r -> {"at": eqp|None, "free": minute}
    breakdown_count = 0
    rows = []

    eqps = {j["eqp"] for j in jobs}
    mach_free = {e: 0.0 for e in eqps}         # 各机台自己的空闲时刻（勿用全局 env.now！）
    next_fail = {e: (rng.expovariate(1 / p["mtbf_min"]) if breakdown else float("inf"))
                 for e in eqps}

    # 按计划开工时间全局推进（事件驱动：保证 env 时钟单调，机台内顺序自然保持）
    for j in sorted(jobs, key=lambda x: _m(x["start"])):
        eqp = j["eqp"]
        plan_s, plan_e = _m(j["start"]), _m(j["end"])
        dur_plan = plan_e - plan_s
        reticle = j["reticle"]

        # --- 光罩接力：不在本机就要搬送+装载 ---
        st = reticle_state.setdefault(reticle, {"at": None, "free": 0.0})
        reticle_wait = 0.0
        if st["at"] != eqp:
            reticle_wait = CONFIG["transport_min"] + CONFIG["load_min"]
            st["at"] = eqp
        # 实际开工 = max(计划开工, 光罩就绪, 本机台释放)
        earliest = max(mach_free[eqp], st["free"] + reticle_wait)
        start = max(plan_s, earliest)
        dur = max(dur_plan * (1 + rng.gauss(0, p["duration_cv"])), 1)
        note = []
        if reticle_wait:
            note.append(f"光罩接力+{reticle_wait:.0f}min")

        # --- 机台故障：加工中故障顺延 Job；空闲期故障只在侵入开工时间时才顺延 ---
        while breakdown and next_fail[eqp] <= start + dur:
            nf = next_fail[eqp]
            downtime = rng.expovariate(1 / p["mttr_min"])
            repair_end = nf + downtime
            if nf < start:                        # 空闲期故障：机台修理不吃加工时间
                if repair_end > start:
                    note.append(f"空闲期故障波及开工+{repair_end - start:.0f}min")
                    start = repair_end
                breakdown_count += 1
                next_fail[eqp] = repair_end + rng.expovariate(1 / p["mtbf_min"])
                continue
            breakdown_count += 1
            note.append(f"故障停机{downtime:.0f}min@{fmt(nf)}")
            start = repair_end
            next_fail[eqp] = repair_end + rng.expovariate(1 / p["mtbf_min"])

        # --- 良率异常返工：净时长翻倍 ---
        if rng.random() < p["rework_rate"]:
            dur *= 2
            note.append("返工×2")

        end = start + dur
        mach_free[eqp] = end
        st["free"] = end

        # --- QTime 违约：实际开工 - 到站时间 超过 remain_qt（仅配置了 QTime 的 Lot）---
        meta = _LOT_META.get(j["lot"], {})
        qtime_breach = bool(
            meta.get("remain_qt") and start - meta["ready"] > meta["remain_qt"])

        delay = end - plan_e
        rows.append({
            "lot": j["lot"], "eqp": eqp, "reticle": reticle,
            "priority": j.get("priority"), "temp": j.get("temp"),
            "planned_start": j["start"], "planned_end": j["end"],
            "actual_start": fmt(start), "actual_end": fmt(end),
            "planned_start_m": plan_s, "planned_end_m": plan_e,
            "actual_start_m": round(start, 1), "actual_end_m": round(end, 1),
            "delay_min": round(delay, 1),
            "on_time": delay <= p["tolerance_min"],
            "qtime_breach": qtime_breach,
            "note": "; ".join(note) or "-",
        })

    kpis = {
        "makespan_planned": fmt(max(r["planned_end_m"] for r in rows)),
        "makespan_actual": fmt(max(r["actual_end_m"] for r in rows)),
        "makespan_delta_min": round(max(r["actual_end_m"] for r in rows)
                                    - max(r["planned_end_m"] for r in rows), 1),
        "on_time_rate": round(sum(1 for r in rows if r["on_time"]) / len(rows), 3),
        "avg_delay_min": round(sum(r["delay_min"] for r in rows) / len(rows), 1),
        "max_delay_min": round(max(r["delay_min"] for r in rows), 1),
        "qtime_violations": sum(1 for r in rows if r["qtime_breach"]),
        "breakdowns": breakdown_count,
        "rework_count": sum(1 for r in rows if "返工" in r["note"]),
        "lots_simulated": len(rows),
        "seed": seed,
    }
    return {"kpis": kpis, "lots": rows, "params": {k: p[k] for k in DEFAULT_PARAMS}}


def _m(hm):
    h, mi = str(hm).split(":")
    return int(h) * 60 + int(mi)
