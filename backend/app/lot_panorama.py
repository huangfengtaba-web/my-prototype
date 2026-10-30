# -*- coding: utf-8 -*-
"""单 Lot 全景聚合（Q1：排程/Lot 数据可查看性）。

GET /api/solve/lot/{run_id}/{lot_id}
返回该 Lot 在系统中的全部痕迹：基础属性（mock 宽表口径）→ 排程结果 → BARC 放货窗口
→ 后处理说明 → 所属光罩状态 → 六步执行时间线。只读聚合，不做任何覆盖。
"""
from typing import Any, Dict

from fastapi import HTTPException

from backend.app import solver_runner
from backend.solver.mock_data import LOTS, RETICLES


def lot_panorama(run_id: str, lot_id: str) -> Dict[str, Any]:
    rec = solver_runner.get_result(run_id)
    if rec is None:
        raise HTTPException(404, detail=f"run_id 不存在或已过期: {run_id}")
    summary = rec.get("summary") or {}

    base = next((l for l in LOTS if l["lot"] == lot_id), None)
    if base is None:
        raise HTTPException(404, detail=f"未知 Lot: {lot_id}")

    sched = next((r for r in summary.get("schedule") or [] if r.get("lot") == lot_id), None)
    reticle_id = (sched or {}).get("reticle") or base.get("reticle")
    # ready 在求解进程内推演（step6），只能从 run_summary 取；mock RETICLES 无此字段
    summary_reticle = (summary.get("reticles") or {}).get(reticle_id, {})
    reticle = {**RETICLES.get(reticle_id, {}), "ready": summary_reticle.get("ready")}

    return {
        "run_id": run_id,
        "case": rec.get("case"),
        "lot_id": lot_id,
        "base": base,                                   # 宽表口径：优先级/温层/QTime/到站/BARC 参数/打标
        "schedule": sched,                              # ③细排程结果（含 ④后处理说明）
        "barc": {                                       # ⑤反推的放货窗口
            "batch_id": f"B-{summary.get('date', '').replace('-', '')}-{reticle_id[-4:]}",
            "er": (sched or {}).get("barc_er"),
            "lr": (sched or {}).get("barc_lr"),
        },
        "reticle": {                                    # ⑥光罩五态（就绪链路）
            "id": reticle_id,
            "status": reticle.get("status"),
            "note": reticle.get("note"),
            "ready": reticle.get("ready"),
        },
        "milp": summary.get("milp_status"),
        "steps": summary.get("steps") or [],
        "qtms_over": base.get("qtms_over", False),
    }
