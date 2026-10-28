# -*- coding: utf-8 -*-
"""GTX FSO Litho · FastAPI 后端。

5 个接口（对应 docs/specs/05_API接口设计.md 的演示子集）：
    GET  /api/health                 健康检查 + 求解器型号
    POST /api/solve/run              跑一次六步求解（body 可选 {"case": "..."}）
    GET  /api/solve/result/{run_id}  按 run_id 查历史结果
    GET  /api/mock/data              机台/Lot/光罩/配置 mock 数据
    GET  /api/cases                  列出 tests/cases/*.yaml 用例

启动：uvicorn backend.app.api:app --reload --port 8000（工作目录=仓库根）
"""
import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.app import solver_runner
from backend.solver import cli
from backend.solver.mock_data import CONFIG, DATE, LOTS, MACHINES, RETICLES, RUN

app = FastAPI(title="GTX FSO Litho Scheduling API", version="0.1.0")

# CORS：本地放行 5173；生产用 LITHO_CORS_ORIGINS 覆盖（勿用 *，见 docs/04_DEPLOYMENT.md §4）
_origins = [o.strip() for o in os.getenv(
    "LITHO_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


class SolveRequest(BaseModel):
    case: str | None = None      # scenario 名，缺省跑基线


@app.get("/api/health")
def health():
    return {"ok": True, "solver": os.getenv("LITHO_SOLVER", "CBC")}


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


@app.get("/api/mock/data")
def mock_data():
    # 只读导出，不在 API 进程内做任何覆盖（覆盖只发生在求解子进程里）
    return {"date": DATE, "run": RUN, "machines": MACHINES,
            "lots": LOTS, "reticles": RETICLES, "config": CONFIG}


@app.get("/api/cases")
def cases():
    return {"cases": cli.list_cases()}
