# -*- coding: utf-8 -*-
"""求解类技能：六步 MILP 求解、按 run_id 查结果。"""
from backend.app.registry.core import register
from backend.app.registry.types import Skill
from backend.app.solver_runner import get_result, run_solve
from backend.solver import cli


def _summarize_solve(r):
    s = r.get("summary") or {}
    sched = s.get("schedule") or []
    a01 = next((x for x in sched if x["lot"] == "LOT-A01"), {})
    return {
        "run_id": r["run_id"],
        "status": r["status"],
        "case": r.get("case"),
        "milp": s.get("milp_status"),
        "urgent_a01_start": a01.get("start"),
        "schedule_preview": sched[:4],
    }


def tool_run_solve(case=None, fix=False):
    return _summarize_solve(run_solve(case, fix=fix))


_CASES = None


def _case_enum():
    """启动时快照用例名，供 JSON Schema 的 enum 使用。取不到就退化为自由字符串。"""
    global _CASES
    if _CASES is None:
        try:
            _CASES = cli.list_cases()
        except Exception:                     # noqa: BLE001  用例目录缺失不应阻塞注册
            _CASES = []
    return _CASES


register(Skill(
    name="run_solve",
    title="六步 MILP 求解",
    category="solve",
    description="对指定 scenario 跑一次六步 MILP 排程求解，返回 run_id、MILP 状态、"
                "急货 LOT-A01 开工时间与首 4 行排程。用户说「跑/算/求解/排程」时调用。",
    input_schema={
        "type": "object",
        "properties": {
            "case": {"type": "string",
                     "description": "scenario 用例名；省略=基线",
                     **({"enum": _case_enum()} if _case_enum() else {})},
            "fix": {"type": "boolean", "default": False,
                    "description": "Fix Lot 模式：按上次运行冻结机台与顺序"},
        },
        "required": [],
        "additionalProperties": False,
    },
    handler=tool_run_solve,
    examples=({"input": {"case": "urgent-A01"}, "note": "急货场景求解"},),
    tags=("milp", "cbc", "core"),
    risk="compute",
    timeout_s=120,
    max_result_chars=800,
    args_doc={"case": "scenario 用例名，可选", "fix": "是否 Fix Lot，默认 false"},
))

register(Skill(
    name="get_result",
    title="查询历史结果",
    category="solve",
    description="按 run_id 查询一次历史求解的完整结果（含逐 Lot 排程与光罩状态）。"
                "用户给出具体 run_id 或要「看上次结果」时调用。",
    input_schema={
        "type": "object",
        "properties": {
            "run_id": {"type": "string", "minLength": 4, "maxLength": 32,
                       "description": "求解运行 ID（8 位短码）"},
        },
        "required": ["run_id"],
        "additionalProperties": False,
    },
    handler=lambda run_id: get_result(run_id) or {"error": f"run_id {run_id} 不存在"},
    examples=({"input": {"run_id": "a1b2c3d4"}, "note": "查某次求解详情"},),
    tags=("history", "readonly"),
    risk="read",
    timeout_s=15,
    max_result_chars=1200,
    args_doc={"run_id": "求解运行 ID"},
))
