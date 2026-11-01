# -*- coding: utf-8 -*-
"""CIM 集成中心（全量 CIM 能力层，mock 数据版）。

覆盖半导体 CIM 体系与本系统的对接面（口径来源：半导体基本概念培训 + litho系统字段.xlsx + 需求/设计书）：
  - MES 对接：Lot 视图（MES Priority/Hold/Queue/Pilot/TrackIn-Out）
  - QTMS 水位：逐 Loop 水位管控与超水位 Lot
  - ELR/APC：24 项工艺校验状态（OOD/检查失败项）
  - SDR/EMA：光罩搬送指令队列（搬运 AMHS 执行面）
  - Model Control：Eqp Group / Data Parameter / Schedule Model（真配置管理数据）
  - 数据字典：litho系统.xlsx 8 个结果页的字段清单
"""
from fastapi import APIRouter

from backend.app import solver_runner
from backend.solver.mock_data import (APC, APC_CHECKS_TOTAL, CHAMBERS, DOMA, LOTS,
                                      MACHINES, QTMS_LOOPS)


def _apc_of(lot_id):
    """APC 状态：mock 表 + Lot 级 scenario 覆盖（apc_ood/apc_failed）。"""
    base = dict(APC.get(lot_id, {"type": "Normal", "ood": False, "failed": []}))
    lot = next((l for l in LOTS if l["lot"] == lot_id), {})
    base["ood"] = bool(lot.get("apc_ood", base["ood"]))
    base["failed"] = lot.get("apc_failed", base["failed"])
    return base

router = APIRouter(prefix="/api/cim", tags=["cim"])

# ---------------------------------------------------------------- Model Control 真配置数据
EQP_GROUPS = [
    {"name": "LITHO_IMM_A", "model": "Litho", "eqp_type": "L-IMMI-S", "running_mode": "",
     "area": "Litho", "kpi_view": "Yes", "schedule_model": "Yes", "in_use": True,
     "machines": ["IMM01", "IMM02"]},
    {"name": "LITHO_IMM_B", "model": "Litho", "eqp_type": "L-YIMMI-S", "running_mode": "",
     "area": "Litho", "kpi_view": "Yes", "schedule_model": "Yes", "in_use": True,
     "machines": ["IMM03", "IMM04", "IMM05"]},
    {"name": "LITHO_BARC", "model": "Litho", "eqp_type": "L-BARC-S", "running_mode": "",
     "area": "Litho", "kpi_view": "No", "schedule_model": "Yes", "in_use": False,
     "machines": []},
    {"name": "ETCH_DRY_A", "model": "Etch", "eqp_type": "E-ETCH-S", "running_mode": "serial",
     "area": "Etch", "kpi_view": "Yes", "schedule_model": "Yes", "in_use": False,
     "machines": []},
    {"name": "WET_BENCH_A", "model": "Wet", "eqp_type": "W-BENCH-S", "running_mode": "Bench",
     "area": "Wet", "kpi_view": "No", "schedule_model": "No", "in_use": False, "machines": []},
]

DATA_PARAMETERS = [
    {"model_type": "Scheduling", "set": "Coming", "item": "时间范围", "type": "int",
     "status": "on", "scope": "Scheduling", "mo": "M", "variable": "COMING_HOURS",
     "value": "24", "description": "Coming Lot 到站时间范围（小时）", "model": "Litho_Main"},
    {"model_type": "Scheduling", "set": "Coming", "item": "步数范围", "type": "int",
     "status": "on", "scope": "Scheduling", "mo": "M", "variable": "COMING_STEPS",
     "value": "3", "description": "Coming Lot 步数范围", "model": "Litho_Main"},
    {"model_type": "Scheduling", "set": "放货管理", "item": "FIX_LOT_COUNT", "type": "int",
     "status": "on", "scope": "Scheduling", "mo": "M", "variable": "FIX_LOT_COUNT",
     "value": "3", "description": "冻结 Lot 最小个数", "model": "Litho_Main"},
    {"model_type": "Scheduling", "set": "放货管理", "item": "FIX_LOT_MIN_TIME", "type": "int",
     "status": "on", "scope": "Scheduling", "mo": "M", "variable": "FIX_LOT_MIN_TIME",
     "value": "60", "description": "冻结 Lot 最小排程时间（分钟）", "model": "Litho_Main"},
    {"model_type": "Scheduling", "set": "放货管理", "item": "LOT_TRANS_COST_TIME", "type": "float",
     "status": "on", "scope": "Scheduling", "mo": "O", "variable": "LOT_TRANS_COST_TIME",
     "value": "5", "description": "Lot 搬送上机台平均耗时（分钟）", "model": "Litho_Main"},
]

SCHEDULE_MODELS = [
    {"name": "Litho_Main", "version": "V1.3", "eqp_group": "LITHO_IMM_A", "status": "on",
     "auto_run": True, "schedule_type": "Scheduling", "last_run": "RUN-20261024-01",
     "description": "Immersion 主排程模型（六步 MILP）"},
    {"name": "Litho_BARC", "version": "V1.1", "eqp_group": "LITHO_BARC", "status": "off",
     "auto_run": False, "schedule_type": "Scheduling", "last_run": "-",
     "description": "BARC 站点放货模型"},
]

# ---------------------------------------------------------------- 数据字典（litho系统.xlsx 8 页签）
DICTIONARY = [
    {"page": "Barc 排程", "fields": ["序号", "LotID", "BatchID", "ProductID", "Recipe",
        "站点序列", "是否放货", "最早放货时间", "最晚放货时间", "litho机台"],
     "source": "step5_barc_release.csv + /litho-schedule Barc 视图"},
    {"page": "Scanner 排程", "fields": ["EqpID", "机台类型", "机台状态", "加工类型", "recipe",
        "reticle ID", "LotID", "ProductID", "站点序列", "开始时间", "结束时间", "Process Time"],
     "kpi": ["Cycle Time", "设备效能", "Move", "WPH", "WIP"],
     "states": ["running", "jobprepare", "scheduling", "down", "setup", "reticle"],
     "source": "step3_schedule_result.csv + /litho-schedule Scanner 视图"},
    {"page": "Litho OverLap", "fields": ["时间（默认半小时维度，可调粒度）", "LP_01~LP_04 重叠段"],
     "source": "原型占位页（源表待客户确认）"},
    {"page": "Lot 加工流", "fields": ["EqpID", "Priority", "QTY", "LotID", "recipe",
        "开始时间", "结束时间", "加工时长"], "legend": ["Barc", "Scanner", "Etch"],
     "source": "Lot 全景抽屉（/api/solve/lot/{run_id}/{lot}）"},
    {"page": "Wafer 加工时间", "fields": [], "source": "源表暂无数据（缺口 C 级）"},
    {"page": "Reticle 排程", "fields": ["ReticleID", "状态", "lotID", "ProductID", "recipe",
        "站点序列", "EqpID", "机台组", "开始时间", "结束时间", "加工时长"],
     "states": ["Process", "inspection", "Starlight", "Stocker", "Transport"],
     "source": "step6_reticle_deduction.csv + /reticle-schedule"},
    {"page": "Reticle 搬送", "fields": ["EqpID", "机台类型", "lotID", "ReticleID", "起点位置",
        "终点位置", "搬送时间", "最早到达时间", "最晚到达时间"],
     "sources": ["KRF", "I-Line", "ARF", "IMMERSION"],
     "source": "/api/twin/timeline reticle_move + /reticle-schedule Transport 视图"},
    {"page": "Reticle 检测", "fields": ["ReticleID", "检测类型", "检测机台", "开始时间",
        "结束时间", "加工时长"],
     "source": "step6 五态推演（Inspection 段）"},
]


def _last_done():
    runs = sorted(solver_runner.RUNS.values(), key=lambda r: r.get("started_at", ""), reverse=True)
    return next((r for r in runs if r.get("status") in ("done", "suboptimal")), None)


# ---------------------------------------------------------------- MES 对接
@router.get("/mes")
def mes():
    lots = [{
        "lot": l["lot"], "mes_priority": l["priority"], "product": l["product"],
        "step": l["step"], "qty": l["qty"],
        "hold": l["qtms_over"] or _apc_of(l["lot"])["ood"],
        "hold_reason": "QTMS 超水位" if l["qtms_over"] else ("APC OOD" if _apc_of(l["lot"])["ood"] else ""),
        "queue": bool(l.get("queue")), "pilot": "Pilot" in l["tags"],
        "tags": l["tags"],
    } for l in LOTS]
    return {"system": "MES", "connected": True, "interface": "REST（mock）",
            "last_sync": "2026-10-24 09:00", "synced_objects": ["Lot", "Flow", "EQP Status",
            "Reticle", "QTime", "APC(ELR)"],
            "lots": lots}


# ---------------------------------------------------------------- QTMS 水位
@router.get("/qtms")
def qtms():
    rec = _last_done()
    loops = []
    for loop in QTMS_LOOPS:
        members = [l for l in LOTS if l["product"] in loop["products"]]
        released = [l for l in members
                    if rec and rec.get("summary") and any(
                        s["lot"] == l["lot"] and s.get("start")
                        for s in rec["summary"].get("schedule") or [])]
        over = [l["lot"] for l in members if l["qtms_over"]]
        loops.append({"loop": loop["loop"], "water": loop["water"],
                      "current": len(released), "over": len(released) > loop["water"],
                      "over_lots": over})
    return {"system": "QTMS", "connected": True, "loops": loops,
            "note": "排程后校验每个 Loop 放货量，超水位标记并卡控（step4）"}


# ---------------------------------------------------------------- ELR / APC
@router.get("/elr")
def elr():
    rows = [{"lot": l["lot"], "type": _apc_of(l["lot"])["type"],
             "ood": _apc_of(l["lot"])["ood"],
             "checks_passed": APC_CHECKS_TOTAL - len(_apc_of(l["lot"])["failed"]),
             "checks_total": APC_CHECKS_TOTAL, "failed": _apc_of(l["lot"])["failed"],
             "runpath": ls_runpath(l)} for l in LOTS]
    return {"system": "ELR/APC", "connected": True, "checks_total": APC_CHECKS_TOTAL,
            "lots": rows}


def ls_runpath(l):
    from backend.solver.litho_solver import capable_machines
    return capable_machines(l)


# ---------------------------------------------------------------- SDR 搬送指令
@router.get("/sdr")
def sdr():
    rec = _last_done()
    commands = []
    if rec and rec.get("summary"):
        run_id = rec["run_id"]
        try:
            from backend.app.twin_timeline import build_timeline
            tl = build_timeline(rec["summary"], run_id=run_id)
            for e in tl.get("events", []):
                if e["type"] == "reticle_move":
                    commands.append({"command_id": f"SDR-{e['vehicle']}-{e['t']}",
                                     "reticle": e["target"], "from": e["from"], "to": e["to"],
                                     "vehicle": e["vehicle"], "lot": e.get("lot"),
                                     "earliest": e["t"], "priority": "High" if e.get("lot") == "LOT-A01" else "Normal",
                                     "pod": f"POD-{e['target']}", "status": "planned"})
        except Exception:
            pass
    return {"system": "SDR/EMA", "connected": True, "commands": commands,
            "note": "全量 Scanner 接管：排程后处理规划发送指令时点（设计书口径）"}


# ---------------------------------------------------------------- Model Control / 数据字典
@router.get("/model-control")
def model_control():
    rec = _last_done()
    return {"eqp_groups": EQP_GROUPS, "data_parameters": DATA_PARAMETERS,
            "schedule_models": SCHEDULE_MODELS,
            "doma": DOMA, "chambers": CHAMBERS,
            "last_run": rec.get("run_id") if rec else None}


@router.get("/dictionary")
def dictionary():
    return {"source": "litho系统.xlsx（客户字段清单）", "pages": DICTIONARY}


@router.get("/overview")
def overview():
    return {"modules": [
        {"name": "MES", "cn": "制造执行系统", "role": "提供 Lot/Flow/状态/绑定/校验/Pilot 标识",
         "connected": True, "api": "/api/cim/mes"},
        {"name": "QTMS", "cn": "Quarter Time Management 水位管控", "role": "Loop 放货水位；超水位标记卡控",
         "connected": True, "api": "/api/cim/qtms"},
        {"name": "ELR/APC", "cn": "设备 Log 数据 + 先进工艺控制", "role": "24 项校验、OOD 卡控、RunPath 过滤",
         "connected": True, "api": "/api/cim/elr"},
        {"name": "SDR/EMA", "cn": "自动派工管理（光罩搬送）", "role": "接收搬送计划或指令，协同 Reticle 移动",
         "connected": True, "api": "/api/cim/sdr"},
        {"name": "FDC", "cn": "故障检测与分类", "role": "机况/PM 数据（路线图）", "connected": False,
         "api": None},
        {"name": "MCS", "cn": "物料控制系统", "role": "FOUP/储位物流（路线图）", "connected": False,
         "api": None},
    ]}
