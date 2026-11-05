# -*- coding: utf-8 -*-
"""GTX FSO Litho · FastAPI 后端。

接口分组：
    求解    POST /api/solve/run            六步 MILP（子进程隔离）
            GET  /api/solve/result/{run_id}
    仿真    POST /api/sim/run              求解 + 执行态仿真（扰动可复现）
    工作流  GET  /api/workflow/templates   模板清单
            POST /api/workflow/run         异步启动（线程执行，前端轮询）
            GET  /api/workflow/status/{wf_id}
            GET  /api/workflow/list        最近运行记录
    Agent   GET  /api/agent/status         LLM/规则模式 + 工具清单
            POST /api/agent/chat           对话（可触发任意工具）
    基础    GET  /api/health  /api/mock/data  /api/cases

启动：uvicorn backend.app.api:app --reload --port 8000（工作目录=仓库根）
"""
import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from backend.app import sim_runner, solver_runner, workflow
from backend.app.agent import agent
from backend.solver import cli
from backend.solver.mock_data import CONFIG, DATE, LOTS, MACHINES, RETICLES, RUN

app = FastAPI(title="GTX FSO Litho Scheduling API", version="0.2.0")

# CORS：本地放行 5173；生产用 LITHO_CORS_ORIGINS 覆盖（勿用 *，见 docs/04_DEPLOYMENT.md §4）
_origins = [o.strip() for o in os.getenv(
    "LITHO_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------- 基础
class SolveRequest(BaseModel):
    case: str | None = None      # scenario 名，缺省跑基线
    fix: bool | None = None      # R1: Fix Lot——按上次运行冻结机台与顺序


class SimRequest(BaseModel):
    case: str | None = None
    seed: int = 42
    breakdown: bool = True


@app.get("/api/health")
def health():
    return {"ok": True, "solver": os.getenv("LITHO_SOLVER", "CBC"),
            "agent_mode": agent.agent_status()["mode"],
            "docgen_enabled": os.getenv("DOCGEN_ENABLED", "1") == "1",
            "version": "0.2.0"}


@app.get("/api/mock/data")
def mock_data():
    # 只读导出，不在 API 进程内做任何覆盖（覆盖只发生在求解子进程里）
    return {"date": DATE, "run": RUN, "machines": MACHINES,
            "lots": LOTS, "reticles": RETICLES, "config": CONFIG}


@app.get("/api/cases")
def cases():
    return {"cases": cli.list_cases()}


# ---------------------------------------------------------------- 求解
@app.post("/api/solve/run")
def solve_run(req: SolveRequest):
    if req.case and req.case not in cli.list_cases():
        raise HTTPException(404, detail=f"未知用例 {req.case}，可用：{', '.join(cli.list_cases()) or '无'}")
    return solver_runner.run_solve(req.case, fix=bool(req.fix))


def _digest_of(record: dict) -> str:
    """把一次求解结果压成一段人类可读纯文本。

    为什么放在后端：Dify 工作流的 code 节点在「输入类型 / 输出 schema / 变量绑定」
    任何一环出问题都会静默失败，导致 LLM 收到空输入而自由发挥。
    改由后端直接产出文本，Dify 只需「HTTP 取文本 → LLM 解读」两个环节。
    """
    d = record or {}
    s = d.get("summary") or {}
    milp = s.get("milp_status") or {}
    sched = [r for r in (s.get("schedule") or []) if r.get("start")]
    a01 = next((r for r in sched if r.get("lot") == "LOT-A01"), {})
    ends = [r.get("end") for r in sched if r.get("end")]
    notes = [f"{r.get('lot')}：{r.get('post_note')}" for r in sched
             if r.get("post_note") and r.get("post_note") not in ("-", "")]
    loads = {}
    for r in sched:
        eqp = r.get("eqp") or "?"
        loads[eqp] = loads.get(eqp, 0) + 1
    top = sorted(loads.items(), key=lambda kv: (-kv[1], kv[0]))
    lines = [
        f"run_id: {d.get('run_id', '-')}",
        f"求解状态: {d.get('status', '-')}",
        f"场景: {d.get('case') or '基线'}",
        f"MILP: {milp.get('step2', '-')} / {milp.get('step3', '-')}",
        f"MakeSpan（最后完工）: {max(ends) if ends else '-'}",
        f"急货 LOT-A01 上机: {a01.get('start', '-')} @ {a01.get('eqp', '-')}",
        f"排产 Lot 数: {len(sched)}",
        "机台负载: " + ("；".join(f"{e} {n}批" for e, n in top) or "无"),
        "卡控与校准: " + ("｜".join(notes) if notes else "无"),
    ]
    return "\n".join(lines)


@app.get("/api/solve/digest", response_class=PlainTextResponse)
@app.post("/api/solve/digest", response_class=PlainTextResponse)
def solve_digest(case: str = ""):
    """跑一次求解，直接返回可读摘要纯文本（供 Dify LLM 节点消费）。

    同时注册 GET 与 POST：Dify 的 HTTP 请求节点默认 method=post，
    若只提供 GET 会返回 405 Method Not Allowed。
    """
    case = (case or "").strip() or None
    if case and case not in cli.list_cases():
        raise HTTPException(404, detail=f"未知用例 {case}，可用：{', '.join(cli.list_cases()) or '无'}")
    return _digest_of(solver_runner.run_solve(case))


@app.get("/api/solve/compare-digest", response_class=PlainTextResponse)
@app.post("/api/solve/compare-digest", response_class=PlainTextResponse)
def solve_compare_digest(case: str = "urgent-A01"):
    """跑基线 + 指定场景两次求解，返回对比摘要纯文本（供 Dify LLM 节点消费）。"""
    case = (case or "").strip() or "urgent-A01"
    if case not in cli.list_cases():
        raise HTTPException(404, detail=f"未知用例 {case}，可用：{', '.join(cli.list_cases()) or '无'}")
    b = solver_runner.run_solve(None)
    u = solver_runner.run_solve(case)

    def _start_map(rec):
        sched = (rec.get("summary") or {}).get("schedule") or []
        return {r.get("lot"): r.get("start") for r in sched if r.get("start")}

    bs, us = _start_map(b), _start_map(u)
    moves = [f"{lot} {bs[lot]}→{us[lot]}" for lot in sorted(bs)
             if lot in us and bs[lot] != us[lot]]
    moved = "；".join(moves) if moves else "无"
    return ("【基线】\n" + _digest_of(b) +
            "\n\n【场景 " + case + "】\n" + _digest_of(u) +
            "\n\n开工时间变化: " + moved)


# ---------------------------------------------------------------- 配置管理（R1）
from backend.solver.mock_data import CONFIG as _CONFIG_DEFAULTS  # noqa: E402
from backend.solver.cli import RUNTIME_CONFIG as _RT_CONFIG, load_runtime_config  # noqa: E402

_CONFIG_EDITABLE = ["temp_change_min", "release_gap_min", "iris_min", "transport_min",
                    "load_min", "w_changeover", "w_makespan", "time_limit_s",
                    "stocker_phys", "stocker_water", "iris_reset_wafers", "chunk_size"]


class ConfigRequest(BaseModel):
    patches: dict | None = None       # 键必须属于 CONFIG 白名单
    reset: bool | None = None         # True = 清除运行时覆盖，恢复默认


@app.get("/api/config")
def get_config():
    """当前生效配置（默认值 + 运行时覆盖合并）。下一次求解（子进程启动时）生效。"""
    merged = {**_CONFIG_DEFAULTS, **load_runtime_config()}
    return {"config": {k: merged[k] for k in _CONFIG_EDITABLE if k in merged},
            "overridden": sorted(load_runtime_config().keys()),
            "editable": _CONFIG_EDITABLE}


@app.put("/api/config")
def put_config(req: ConfigRequest):
    import json as _json
    overrides = {} if req.reset else load_runtime_config()
    if not req.reset:
        for k, v in (req.patches or {}).items():
            if k not in _CONFIG_EDITABLE:
                raise HTTPException(400, detail=f"配置项 {k} 不可编辑，允许：{_CONFIG_EDITABLE}")
            try:
                v = int(v) if isinstance(v, str) and v.isdigit() else v
            except Exception:
                pass
            overrides[k] = v
    os.makedirs(os.path.dirname(_RT_CONFIG), exist_ok=True)
    with open(_RT_CONFIG, "w", encoding="utf-8") as f:
        _json.dump(overrides, f, ensure_ascii=False, indent=1)
    return {"ok": True, "overridden": sorted(overrides.keys()),
            "note": "下一次求解生效（子进程启动时加载）"}


@app.get("/api/solve/result/{run_id}")
def solve_result(run_id: str):
    record = solver_runner.get_result(run_id)
    if record is None:
        raise HTTPException(404, detail=f"run_id {run_id} 不存在（服务重启后历史结果会清空）")
    return record


@app.get("/api/solve/list")
def solve_list(limit: int = 20):
    """最近求解批次摘要（运行批次选择器）。"""
    return {"runs": solver_runner.list_runs(limit)}


@app.get("/api/solve/lot/{run_id}/{lot_id}")
def solve_lot(run_id: str, lot_id: str):
    """单 Lot 全景：基础属性 → 排程 → BARC → 光罩 → 六步时间线。"""
    from backend.app.lot_panorama import lot_panorama
    return lot_panorama(run_id, lot_id)


@app.get("/api/logs")
def logs():
    """Scheduling Log + Error Management（真数据，派生自本服务全部求解运行）。

    错误分类口径（docs/specs 日志设计）：DATA_ERROR（数据校验类）/
    MODEL_ERROR（求解超时/非最优）/ UNKNOWN_ERROR（其余失败）。
    """
    schedulings, errors = [], []
    for r in solver_runner.list_runs(50):
        schedulings.append({
            "model": "Litho_Main", "version": "V1.3", "run_id": r["run_id"],
            "case": r.get("case"), "status": r["status"],
            "start": r.get("started_at"), "end": r.get("started_at"),
        })
        if r["status"] in ("failed", "timeout", "suboptimal"):
            error_type = {"timeout": "MODEL_ERROR", "suboptimal": "MODEL_ERROR",
                          "failed": "UNKNOWN_ERROR"}.get(r["status"], "UNKNOWN_ERROR")
            errors.append({
                "run_id": r["run_id"], "error_type": error_type,
                "error_info": f"求解状态 {r['status']}（case={r.get('case') or '基线'}）",
                "detail": (r.get("detail") or r.get("status"))[:300],
                "time": r.get("started_at"),
            })
    return {"schedulings": schedulings, "errors": errors}


# ---------------------------------------------------------------- 仿真
@app.post("/api/sim/run")
def sim_run(req: SimRequest):
    if req.case and req.case not in cli.list_cases():
        raise HTTPException(404, detail=f"未知用例 {req.case}，可用：{', '.join(cli.list_cases()) or '无'}")
    result = sim_runner.run_sim_for_case(case=req.case, seed=req.seed, breakdown=req.breakdown)
    if "error" in result:
        raise HTTPException(500, detail=result["error"])
    return result


# ---------------------------------------------------------------- 工作流
class WorkflowRunRequest(BaseModel):
    template: str | None = None       # 原契约字段（连字符 ID）
    template_id: str | None = None    # T2-4 兼容字段（下划线 ID），二选一
    params: dict | None = None


@app.get("/api/workflow/templates")
def workflow_templates():
    return workflow.list_templates()


@app.post("/api/workflow/run")
def workflow_run(req: WorkflowRunRequest):
    """优先线上 Dify，未配置/不可达自动 local_fallback（响应含 mode，HTTP 恒 200）。

    本地模式保留原 record 字段（wf_id/steps/...），可继续用 status 接口轮询。
    """
    tid = req.template or req.template_id
    if not tid:
        raise HTTPException(400, detail="template / template_id 二选一必填")
    try:
        return workflow.run_with_fallback(tid, req.params)
    except KeyError as e:
        raise HTTPException(404, detail=str(e))


@app.get("/api/workflow/status/{wf_id}")
def workflow_status(wf_id: str):
    record = workflow.WORKFLOWS.get(wf_id)
    if record is None:
        raise HTTPException(404, detail=f"工作流 {wf_id} 不存在（服务重启后历史会清空）")
    return record


@app.get("/api/workflow/list")
def workflow_list():
    return {"runs": sorted(workflow.WORKFLOWS.values(),
                           key=lambda r: r["created_at"], reverse=True)[:20]}


# ---------------------------------------------------------------- Agent
class AgentChatRequest(BaseModel):
    message: str
    session_id: str | None = None


@app.get("/api/agent/status")
def agent_status():
    return agent.agent_status()


@app.post("/api/agent/chat")
def agent_chat(req: AgentChatRequest):
    if not req.message.strip():
        raise HTTPException(400, detail="消息不能为空")
    return agent.chat(req.message, req.session_id)


# ---------------------------------------------------------------- 3D 孪生时间轴
from backend.app.twin_timeline import build_timeline  # noqa: E402


@app.get("/api/twin/timeline/{run_id}")
def twin_timeline(run_id: str):
    """把某次求解结果转成 3D 孪生时间轴事件流。"""
    rec = solver_runner.get_result(run_id)
    if not rec:
        raise HTTPException(404, detail=f"run_id 不存在或已过期: {run_id}")
    return build_timeline(rec.get("summary") or {}, run_id=run_id)


# ---------------------------------------------------------------- WPS 文档生成
from backend.app.docgen import api as docgen_api  # noqa: E402

app.include_router(docgen_api.router)


# ---------------------------------------------------------------- AI 解读（Dify 最佳接入点）
from backend.app import explain  # noqa: E402


class ExplainRequest(BaseModel):
    run_id: str


@app.post("/api/explain/run")
def explain_run(req: ExplainRequest):
    """排程结果 AI 解读：Dify 工作流优先（HTTP 节点回调取数 + LLM 生成中文解读），
    未配置/不可达自动本地规则解读（mode=local_fallback）。"""
    return explain.explain_run(req.run_id)


# ---------------------------------------------------------------- CIM 集成中心
from backend.app.cim import router as cim_router  # noqa: E402

app.include_router(cim_router)
