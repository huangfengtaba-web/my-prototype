# -*- coding: utf-8 -*-
"""Agent 工具注册表：把系统能力暴露给 LLM（function calling）或规则路由。

新增工具：在 TOOLS 里加条目（name → desc/args/fn），LLM 的 tools spec 会自动生成。
"""
from backend.app import workflow
from backend.app.sim_runner import run_sim_for_case
from backend.app.solver_runner import get_result, run_solve
from backend.solver import cli
from backend.solver.mock_data import LOTS, MACHINES, RETICLES


def _summarize_solve(r):
    s = r.get("summary") or {}
    sched = s.get("schedule") or []
    a01 = next((x for x in sched if x["lot"] == "LOT-A01"), {})
    return {"run_id": r["run_id"], "status": r["status"], "case": r.get("case"),
            "milp": s.get("milp_status"),
            "urgent_a01_start": a01.get("start"),
            "schedule_preview": sched[:4]}


def _summarize_sim(r):
    if "error" in r:
        return r
    k = r["sim"]["kpis"]
    return {"solve_run_id": r["solve_run_id"], "kpis": k}


def _summarize_workflow(r):
    return {"wf_id": r["wf_id"], "status": r["status"],
            "steps": [{"name": s["name"], "status": s["status"]} for s in r["steps"]],
            "error": r.get("error")}


def tool_list_cases():
    return {"cases": cli.list_cases()}


def tool_run_solve(case=None):
    return _summarize_solve(run_solve(case))


def tool_get_mock_data():
    return {"machines": MACHINES, "lots": LOTS, "reticles": RETICLES,
            "lots_count": len(LOTS), "machines_count": len(MACHINES)}


def tool_run_sim(case=None, seed=42, breakdown=True):
    return _summarize_sim(run_sim_for_case(case=case, seed=seed, breakdown=breakdown))


def tool_run_workflow(template_id="daily-scheduling", case=None):
    params = dict(case=case) if case else {}
    return _summarize_workflow(workflow.run_workflow_sync(template_id, params or None))


def tool_list_workflows():
    return {"templates": workflow.list_templates(),
            "recent_runs": [{k: r[k] for k in ("wf_id", "template", "status")}
                            for r in list(workflow.WORKFLOWS.values())[-5:]]}


TOOLS = {
    "list_cases": {
        "desc": "列出所有可用的 scenario 用例名",
        "args": {},
        "fn": tool_list_cases,
    },
    "run_solve": {
        "desc": "跑一次六步 MILP 排程求解（case 可选，缺省跑基线）",
        "args": {"case": "scenario 用例名，可选"},
        "fn": tool_run_solve,
    },
    "get_result": {
        "desc": "按 run_id 查询历史求解结果",
        "args": {"run_id": "求解运行 ID"},
        "fn": lambda run_id: get_result(run_id) or {"error": f"run_id {run_id} 不存在"},
    },
    "get_mock_data": {
        "desc": "获取机台/Lot/光罩 mock 数据概览",
        "args": {},
        "fn": tool_get_mock_data,
    },
    "run_sim": {
        "desc": "对指定 scenario 求解后做执行态仿真（故障/返工/光罩接力扰动）",
        "args": {"case": "scenario 用例名，可选", "seed": "随机种子，默认 42",
                 "breakdown": "是否启用机台故障，默认 true"},
        "fn": tool_run_sim,
    },
    "run_workflow": {
        "desc": "执行一条工作流（daily-scheduling 日计划链路 / scenario-compare 多场景对比）",
        "args": {"template_id": "模板 ID", "case": "scenario 用例名，可选"},
        "fn": tool_run_workflow,
    },
    "list_workflows": {
        "desc": "列出可用工作流模板与最近运行记录",
        "args": {},
        "fn": tool_list_workflows,
    },
}


def tool_specs_for_llm():
    """生成 OpenAI function-calling 的 tools 声明。"""
    return [{
        "type": "function",
        "function": {
            "name": name,
            "description": t["desc"],
            "parameters": {
                "type": "object",
                "properties": {k: {"type": "string", "description": v}
                               for k, v in t["args"].items()},
            },
        },
    } for name, t in TOOLS.items()]
