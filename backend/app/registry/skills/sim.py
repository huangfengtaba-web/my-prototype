# -*- coding: utf-8 -*-
"""仿真类技能：求解 + 执行态仿真（故障/返工/光罩接力扰动，seed 可复现）。"""
from backend.app.registry.core import register
from backend.app.registry.types import Skill
from backend.app.sim_runner import run_sim_for_case


def _summarize_sim(r):
    if "error" in r:
        return r
    return {"solve_run_id": r["solve_run_id"], "kpis": r["sim"]["kpis"]}


def _coerce(seed, breakdown):
    """LLM 可能把数字/布尔传成字符串，这里统一转换（旧实现全部声明为 string）。"""
    try:
        seed = int(seed)
    except (TypeError, ValueError):
        seed = 42
    if isinstance(breakdown, str):
        breakdown = breakdown.strip().lower() not in ("false", "0", "no", "off", "")
    return seed, bool(breakdown)


def tool_run_sim(case=None, seed=42, breakdown=True):
    seed, breakdown = _coerce(seed, breakdown)
    return _summarize_sim(run_sim_for_case(case=case, seed=seed, breakdown=breakdown))


register(Skill(
    name="run_sim",
    title="执行态仿真",
    category="sim",
    description="对指定 scenario 先求解再做执行态仿真（注:含设备故障、返工、光罩接力扰动），"
                "返回准时率、实际 MakeSpan、偏差分钟、故障数与 QTime 违约数。"
                "用户问「仿真/模拟/扰动下会怎样」时调用。",
    input_schema={
        "type": "object",
        "properties": {
            "case": {"type": "string", "description": "scenario 用例名；省略=基线"},
            "seed": {"type": "integer", "default": 42, "minimum": 0, "maximum": 999999,
                     "description": "随机种子，同种子结果可复现"},
            "breakdown": {"type": "boolean", "default": True,
                          "description": "是否启用设备故障扰动"},
        },
        "required": [],
        "additionalProperties": False,
    },
    handler=tool_run_sim,
    examples=({"input": {"case": "urgent-A01", "seed": 42, "breakdown": True},
               "note": "急货场景带故障仿真"},),
    tags=("des", "simulation", "core"),
    risk="compute",
    timeout_s=180,
    max_result_chars=500,
    args_doc={"case": "scenario 用例名，可选", "seed": "随机种子，默认 42",
              "breakdown": "是否启用机台故障，默认 true"},
))
