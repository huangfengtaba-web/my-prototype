# -*- coding: utf-8 -*-
"""数据类技能：用例清单、mock 数据概览。"""
from backend.app.registry.core import register
from backend.app.registry.types import Skill
from backend.solver import cli
from backend.solver.mock_data import LOTS, MACHINES, RETICLES


def tool_list_cases():
    """列出全部 scenario 用例名（agent.py 的规则路由也直接调用本函数）。"""
    return {"cases": cli.list_cases()}


def tool_get_mock_data():
    return {
        "machines": MACHINES,
        "lots": LOTS,
        "reticles": RETICLES,
        "lots_count": len(LOTS),
        "machines_count": len(MACHINES),
    }


register(Skill(
    name="list_cases",
    title="用例清单",
    category="data",
    description="列出所有可用的 scenario 用例名（如 default / urgent-A01 / reticle-delay）。"
                "用户问「有哪些场景/用例」或需要确认可用参数时调用。",
    input_schema={"type": "object", "properties": {}, "required": [],
                  "additionalProperties": False},
    handler=tool_list_cases,
    examples=({"input": {}, "note": "列出全部用例"},),
    tags=("scenario", "readonly"),
    risk="read",
    timeout_s=10,
    max_result_chars=400,
    args_doc={},
))

register(Skill(
    name="get_mock_data",
    title="机台与批次数据",
    category="data",
    description="获取机台、Lot、光罩三类基础数据概览（含数量与光罩五态）。"
                "用户问「有哪些机台/多少 Lot/光罩状态」时调用。",
    input_schema={"type": "object", "properties": {}, "required": [],
                  "additionalProperties": False},
    handler=tool_get_mock_data,
    examples=({"input": {}, "note": "查看基础数据"},),
    tags=("equipment", "lot", "reticle", "readonly"),
    risk="read",
    timeout_s=10,
    max_result_chars=600,
    args_doc={},
))
