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


class SimRequest(BaseModel):
    case: str | None = None
    seed: int = 42
    breakdown: bool = True


@app.get("/api/health")
def health():
    return {"ok": True, "solver": os.getenv("LITHO_SOLVER", "CBC"),
            "agent_mode": agent.agent_status()["mode"], "version": "0.2.0"}


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
    return solver_runner.run_solve(req.case)


@app.get("/api/solve/result/{run_id}")
def solve_result(run_id: str):
    record = solver_runner.get_result(run_id)
    if record is None:
        raise HTTPException(404, detail=f"run_id {run_id} 不存在（服务重启后历史结果会清空）")
    return record


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
    template: str                # TEMPLATES 键
    params: dict | None = None


@app.get("/api/workflow/templates")
def workflow_templates():
    return {"templates": workflow.list_templates()}


@app.post("/api/workflow/run")
def workflow_run(req: WorkflowRunRequest):
    try:
        return workflow.run_workflow(req.template, req.params)
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
