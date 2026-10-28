# -*- coding: utf-8 -*-
"""仿真运行器：把六步 MILP 的计划排程喂给执行态仿真。

不进程隔离（fab_sim 无模块级可变状态，随机数由 seed 锚定，天然可复现）；
但求解仍走 solver_runner 的子进程隔离路径。
"""
from backend.app import solver_runner
from backend.sim import run_simulation


def run_sim(plan, seed=42, breakdown=True, params=None):
    """直接对给定计划排程仿真（工作流引擎用：求解步骤的输出直接喂进来）。"""
    return run_simulation(plan, seed=seed, breakdown=breakdown, params=params)


def run_sim_for_case(case=None, seed=42, breakdown=True, params=None):
    """端到端：先子进程求解（隔离），再对计划仿真。返回 {solve_run_id, solve_status, sim}。"""
    solve = solver_runner.run_solve(case)
    if solve["status"] not in ("done", "suboptimal") or not solve.get("summary"):
        return {"error": f"求解失败（{solve['status']}），无法仿真",
                "solve_status": solve["status"], "detail": solve.get("error")}
    sim = run_sim(solve["summary"]["schedule"], seed=seed, breakdown=breakdown, params=params)
    return {"solve_run_id": solve["run_id"], "solve_status": solve["status"],
            "case": case, "sim": sim}
