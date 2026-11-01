# -*- coding: utf-8 -*-
"""CIM 运行时状态（MES Hold / ELR OOD / QTMS 水位的持久化层）。

文件：backend/solver/runtime_state.json（gitignore，不入库）
结构：{"lot_overrides": {lot: {hold/apc_ood/apc_failed}}, "qtms_water": {loop: water}}
写入方：/api/cim/* 的操作接口；读取方：cli.py（每次求解前应用到 mock_data）。
"""
import json
import os

_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                     "backend", "solver", "runtime_state.json")


def load():
    if os.path.exists(_FILE):
        try:
            with open(_FILE, encoding="utf-8") as f:
                return json.load(f) or {}
        except Exception:
            return {}
    return {}


def save(state):
    os.makedirs(os.path.dirname(_FILE), exist_ok=True)
    with open(_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=1)


def lot_overrides():
    return load().get("lot_overrides") or {}


def qtms_water():
    return load().get("qtms_water") or {}


def set_lot_override(lot_id, patch):
    state = load()
    ov = state.get("lot_overrides") or {}
    cur = ov.get(lot_id) or {}
    cur.update(patch)
    # 全 False/空 时清除该 Lot 的覆盖，避免残留
    if not any([cur.get("hold"), cur.get("apc_ood"), cur.get("apc_failed")]):
        ov.pop(lot_id, None)
    else:
        ov[lot_id] = cur
    state["lot_overrides"] = ov
    save(state)
    return cur


def set_qtms_water(loop, water):
    state = load()
    qw = state.get("qtms_water") or {}
    qw[loop] = int(water)
    state["qtms_water"] = qw
    save(state)
    return qw
