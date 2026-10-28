# -*- coding: utf-8 -*-
"""执行态仿真回归（确定性 / KPI 合理性 / 场景可跑）。"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.sim_runner import run_sim, run_sim_for_case          # noqa: E402
from backend.app.solver_runner import run_solve                       # noqa: E402
from backend.solver import cli                                        # noqa: E402
from backend.solver.mock_data import LOTS                             # noqa: E402


@pytest.fixture(scope="module")
def default_plan():
    """基线计划（module 级跑一次子进程求解，供本文件复用）。"""
    solve = run_solve("default")
    assert solve["status"] in ("done", "suboptimal"), solve.get("error")
    plan = solve["summary"]["schedule"]
    return {"plan": plan, "sim": run_sim(plan, seed=42)}


def test_same_seed_is_deterministic(default_plan):
    """同种子两次仿真 KPI 完全一致（可复现是仿真可信的前提）。"""
    plan = default_plan["plan"]
    a = run_sim(plan, seed=7)["kpis"]
    b = run_sim(plan, seed=7)["kpis"]
    assert a == b


def test_kpis_sane(default_plan):
    k = default_plan["sim"]["kpis"]
    assert 0.0 <= k["on_time_rate"] <= 1.0
    assert k["lots_simulated"] == len([l for l in LOTS if not l["qtms_over"]])
    # 加工时长的正态波动允许小幅提前完工；大幅提前说明仿真错位
    assert -60 <= k["makespan_delta_min"]
    assert k["avg_delay_min"] <= k["max_delay_min"]


def test_no_breakdown_is_punctual(default_plan):
    """关掉故障与返工后，仿真应基本贴合计划（延误只来自时长波动与光罩接力）。"""
    plan = default_plan["plan"]
    k = run_sim(plan, seed=1, breakdown=False, params={"rework_rate": 0})["kpis"]
    assert k["on_time_rate"] >= 0.8, f"无扰动场景准时率过低: {k}"


def test_sim_runs_for_all_cases():
    """4 个 scenario 全部可端到端仿真。"""
    for case in cli.list_cases():
        r = run_sim_for_case(case, seed=42)
        assert "error" not in r, f"{case}: {r.get('error')}"
        assert r["sim"]["kpis"]["lots_simulated"] > 0
