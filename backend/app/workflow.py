# -*- coding: utf-8 -*-
"""GTX FSO Litho · 工作流引擎（本地 fallback 底座，Dify 线上编排见 ai/dify_client）。

注意：本模块**不是 Dify**——它是 Dify 不可用/未配置时的本地降级执行器。
统一入口 run_with_fallback：优先线上 Dify，失败/未配置自动落回本地步骤执行。

    - 模板（TEMPLATES）：模板元数据 + 本地步骤序列 + 对应 Dify App（dify_key）
    - 运行记录（WORKFLOWS）：内存字典，每步有状态/耗时/输出摘要（服务重启清空）
    - 执行：后台线程异步跑（前端轮询状态）；run_workflow_sync 供测试与 Agent 直接调用

扩展新工作流：在 TEMPLATES 里加条目即可，步骤函数签名统一为 step(ctx, params) -> dict。
"""
import threading
import time
import traceback
import uuid

from backend.app import sim_runner, solver_runner
from backend.solver import cli
from backend.solver.mock_data import LOTS, MACHINES, RETICLES

WORKFLOWS: dict = {}          # wf_id -> record
_LOCK = threading.Lock()


def _norm_tid(template_id: str) -> str:
    """模板 ID 归一化：'daily_scheduling' 与 'daily-scheduling' 等价。"""
    return (template_id or "").strip().replace("_", "-").lower()


# ---------------------------------------------------------------------
# 步骤实现（统一签名：step(ctx, params) -> dict 输出；抛异常即该步失败）
# ---------------------------------------------------------------------
def step_validate_data(ctx, params):
    """① 数据校验：光罩引用完整、机台 Capability 可覆盖、到站时间合法。"""
    issues = []
    for l in LOTS:
        if l["reticle"] not in RETICLES:
            issues.append(f"{l['lot']} 引用了不存在的光罩 {l['reticle']}")
        if not [e for e, m in MACHINES.items() if l["product"] in m["products"]]:
            issues.append(f"{l['lot']} 的产品 {l['product']} 无任何机台可加工")
        if not (0 <= l["ready"] <= 24 * 60):
            issues.append(f"{l['lot']} 到站时间 {l['ready']} 超出当日范围")
    return {"ok": not issues, "issues": issues,
            "checked": {"lots": len(LOTS), "machines": len(MACHINES), "reticles": len(RETICLES)}}


def step_solve(ctx, params):
    """② 求解：子进程跑六步 MILP（params.case 指定 scenario）。"""
    r = solver_runner.run_solve(params.get("case"))
    if r["status"] not in ("done", "suboptimal"):
        raise RuntimeError(f"求解失败 {r['status']}: {r.get('error', '')[:300]}")
    ctx["solve"] = r
    return {"run_id": r["run_id"], "status": r["status"],
            "case": r.get("case"), "milp": r["summary"].get("milp_status")}


def step_simulate(ctx, params):
    """③ 仿真：对上一步计划做执行态仿真（seed 参数化）。"""
    if "solve" not in ctx:
        raise RuntimeError("仿真依赖求解步骤的输出（ctx.solve 缺失）")
    sim = sim_runner.run_sim(ctx["solve"]["summary"]["schedule"],
                             seed=params.get("seed", 42),
                             breakdown=params.get("breakdown", True))
    ctx["sim"] = sim
    k = sim["kpis"]
    return {"on_time_rate": k["on_time_rate"], "makespan_actual": k["makespan_actual"],
            "makespan_delta_min": k["makespan_delta_min"], "breakdowns": k["breakdowns"]}


def step_compare(ctx, params):
    """④ 对比：汇总 ctx["solves"] 里多个场景的 MakeSpan / 急货开工。"""
    solves = ctx.get("solves") or {}
    if not solves:
        raise RuntimeError("没有可对比的求解结果（ctx.solves 缺失）")
    table = []
    for case, r in solves.items():
        sched = r["summary"]["schedule"]
        a01 = next((x for x in sched if x["lot"] == "LOT-A01"), {})
        ends = [x["end"] for x in sched if x.get("end")]
        table.append({"case": case, "milp": r["summary"]["milp_status"],
                      "makespan": max(ends) if ends else None,
                      "urgent_a01_start": a01.get("start")})
    return {"table": table}


def step_report(ctx, params):
    """⑤ 报告：把链路结果汇总成 Markdown 摘要（前端直接渲染）。"""
    lines = [f"# 工作流执行报告 · {time.strftime('%Y-%m-%d %H:%M:%S')}", ""]
    if "solve" in ctx:
        s = ctx["solve"]["summary"]
        lines += [f"## 求解（case={ctx['solve'].get('case') or '基线'}）",
                  f"- run_id: `{ctx['solve']['run_id']}`",
                  f"- MILP: {s['milp_status']}",
                  f"- 急货故事线: {jsonable(s.get('story_check'))}", ""]
    if "sim" in ctx:
        k = ctx["sim"]["kpis"]
        lines += ["## 执行仿真", f"- 准时率: {k['on_time_rate']:.0%}",
                  f"- 实际 MakeSpan: {k['makespan_actual']}（计划 {k['makespan_planned']}，"
                  f"偏差 {k['makespan_delta_min']}min）",
                  f"- 扰动: 故障 {k['breakdowns']} 次 / 返工 {k['rework_count']} 次 / "
                  f"QTime 违约 {k['qtime_violations']}", ""]
    if "compare" in ctx:
        lines += ["## 场景对比", "| Case | MILP | MakeSpan | 急货 LOT-A01 开工 |",
                  "|---|---|---|---|"]
        for row in ctx["compare"]["table"]:
            lines.append(f"| {row['case']} | {row['milp']} | {row['makespan']} | "
                         f"{row['urgent_a01_start']} |")
        lines.append("")
    text = "\n".join(lines)
    ctx["report"] = text
    return {"markdown": text}


def jsonable(obj):
    return {k: (v if isinstance(v, (str, int, float)) else str(v)) for k, v in obj.items()} \
        if isinstance(obj, dict) else obj


def _step_solve_all(ctx, params):
    """多场景求解：逐个跑 params.cases，结果挂到 ctx.solves 供对比步骤用。"""
    ctx["solves"] = {}
    last = None
    for case in params.get("cases") or ["default"]:
        r = solver_runner.run_solve(case)
        if r["status"] not in ("done", "suboptimal"):
            raise RuntimeError(f"场景 {case} 求解失败: {r.get('error', '')[:200]}")
        ctx["solves"][case] = r
        last = r
    ctx["solve"] = last          # 兼容 report 步骤
    return {c: r["summary"]["milp_status"] for c, r in ctx["solves"].items()}


# ---------------------------------------------------------------------
# 模板：步骤序列声明（solve_case 为 None 表示跑基线）
# ---------------------------------------------------------------------
TEMPLATES = {
    "daily-scheduling": {
        "name": "日计划链路（校验→求解→仿真→报告）",
        "desc": "生产日常排程主链路：先校验数据一致性，跑六步 MILP 得到计划，"
                "再做执行态仿真验证计划稳健性，最后出 Markdown 报告。",
        "params": {"case": None, "seed": 42, "breakdown": True},
        "dify_key": "daily_scheduling",
        "steps": [("validate", "数据校验", step_validate_data),
                  ("solve", "六步 MILP 求解", step_solve),
                  ("simulate", "执行态仿真", step_simulate),
                  ("report", "生成报告", step_report)],
    },
    "scenario-compare": {
        "name": "多场景对比（基线/急货/光罩延迟）",
        "desc": "并行视角下的 What-if 分析：对 3 个 scenario 各跑一次求解，"
                "对比 MakeSpan 与急货开工时间，输出对比表。",
        "params": {"cases": ["default", "urgent-A01", "reticle-delay"]},
        "dify_key": "scenario_compare",
        "steps": [("solve_all", "多场景求解", _step_solve_all),
                  ("compare", "结果对比", step_compare),
                  ("report", "生成报告", step_report)],
    },
}


# ---------------------------------------------------------------------
# 引擎：同步执行 + 线程异步执行
# ---------------------------------------------------------------------
def _execute(wf_id, template_id, params):
    tpl = TEMPLATES[template_id]
    record = WORKFLOWS[wf_id]
    record["status"] = "running"
    ctx = {}
    merged = dict(tpl["params"])
    merged.update(params or {})
    record["params"] = merged
    for step_id, step_name, fn in tpl["steps"]:
        step_rec = {"id": step_id, "name": step_name, "status": "running",
                    "started_at": time.strftime("%H:%M:%S"), "seconds": None,
                    "output": None, "error": None}
        record["steps"].append(step_rec)
        t0 = time.time()
        try:
            out = fn(ctx, merged)
            step_rec.update(status="done", seconds=round(time.time() - t0, 2),
                            output=_brief(out))
        except Exception as e:                        # 单步失败：整条工作流标 failed，保留现场
            step_rec.update(status="failed", seconds=round(time.time() - t0, 2),
                            error=f"{type(e).__name__}: {e}")
            record.update(status="failed", error=f"步骤 {step_name} 失败: {e}",
                          traceback=traceback.format_exc()[-1500:],
                          finished_at=time.strftime("%Y-%m-%d %H:%M:%S"))
            return
    record.update(status="done", finished_at=time.strftime("%Y-%m-%d %H:%M:%S"))


def _brief(out, _depth=0):
    """步骤输出整理（前端时间线展示用）：保留 JSON 结构，只截断超长字符串/列表。"""
    if _depth > 4:
        return "…"
    if isinstance(out, dict):
        return {k: _brief(v, _depth + 1) for k, v in list(out.items())[:10]}
    if isinstance(out, list):
        return [_brief(v, _depth + 1) for v in out[:12]]
    if isinstance(out, str):
        return out if len(out) <= 4000 else out[:4000] + f"…（共 {len(out)} 字符）"
    if isinstance(out, (int, float, bool)) or out is None:
        return out
    return str(out)[:200]


def run_workflow(template_id, params=None):
    """异步启动工作流（后台线程），返回运行记录。未知模板抛 KeyError。"""
    tid = _norm_tid(template_id)
    if tid not in TEMPLATES:
        raise KeyError(f"未知模板 {template_id}，可用：{', '.join(TEMPLATES)}")
    wf_id = uuid.uuid4().hex[:8]
    with _LOCK:
        WORKFLOWS[wf_id] = {"wf_id": wf_id, "template": tid,
                            "template_name": TEMPLATES[tid]["name"],
                            "status": "pending", "params": params or {},
                            "steps": [], "error": None,
                            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                            "finished_at": None}
    threading.Thread(target=_execute, args=(wf_id, tid, params),
                     daemon=True, name=f"wf-{wf_id}").start()
    return WORKFLOWS[wf_id]


def run_workflow_sync(template_id, params=None):
    """同步执行（测试与 Agent 用）：直接复用 _execute，返回完成后的记录。"""
    tid = _norm_tid(template_id)
    if tid not in TEMPLATES:
        raise KeyError(f"未知模板 {template_id}，可用：{', '.join(TEMPLATES)}")
    wf_id = uuid.uuid4().hex[:8]
    with _LOCK:
        WORKFLOWS[wf_id] = {"wf_id": wf_id, "template": tid,
                            "template_name": TEMPLATES[tid]["name"],
                            "status": "pending", "params": params or {},
                            "steps": [], "error": None,
                            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                            "finished_at": None}
    _execute(wf_id, tid, params)
    return WORKFLOWS[wf_id]


def run_with_fallback(template_id: str, params: dict | None = None) -> dict:
    """统一入口：优先走线上 Dify；不可用/失败则降级本地执行（HTTP 仍 200）。"""
    from backend.app.ai import dify_client

    tid = _norm_tid(template_id)
    tpl = TEMPLATES.get(tid) or {}
    wf_key = tpl.get("dify_key")

    if wf_key and dify_client.configured(wf_key):
        try:
            res = dify_client.run_workflow(wf_key, params or {})
            res["template_id"] = tid
            return res
        except dify_client.DifyUnavailable as e:
            local = run_workflow_sync(tid, params)
            local["mode"] = "local_fallback"
            local["fallback_reason"] = str(e)
            return local

    local = run_workflow_sync(tid, params)
    local["mode"] = "local_fallback"
    local["fallback_reason"] = "Dify 未配置"
    return local


def list_templates():
    from backend.app.ai import dify_client

    return {"templates": [
        {"id": k, "name": v["name"], "desc": v["desc"], "params": v["params"],
         "dify_key": v.get("dify_key"),
         "dify_configured": dify_client.configured(v.get("dify_key", ""))}
        for k, v in TEMPLATES.items()
    ]}


def cases():
    return cli.list_cases()
