# -*- coding: utf-8 -*-
"""求解器运行器：子进程隔离调用 `python -m backend.solver`。

为什么必须子进程隔离
--------------------
mock_data 的 LOTS / CONFIG / RETICLES 是模块级可变对象，scenario 覆盖会直接改它们。
若在 API 进程内反复调用 litho_solver.main()，第二次调用拿到的已是上一次被改过的数据。
每次求解新起子进程（约 2s 冷启动，求解本身 <1s，演示可接受），天然防污染。

结果不落库：RUNS 是内存字典，进程重启即清空（演示口径，见 docs/05_AGENT_HANDOFF_TEMPLATE.md）。
"""
import os
import subprocess
import sys
import threading
import time
import uuid

# 仓库根 = backend/app/ 的上上级；子进程必须以它为 cwd 才能导入 backend.solver 包
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SOLVER_TIMEOUT_S = int(os.getenv("LITHO_TIME_LIMIT_S", "120"))

RUNS: dict = {}          # run_id -> result dict
_RUNS_LOCK = threading.Lock()   # FastAPI 线程池并发写保护


def _new_run_id():
    return uuid.uuid4().hex[:8]


def _out_dir(run_id):
    d = os.path.join(REPO_ROOT, "backend", "solver", "output", run_id)
    os.makedirs(d, exist_ok=True)
    return d


def _parse_summary(stdout):
    """从 CLI stdout 提取最后的 JSON 结果（cmd_run --json 打印在末尾）。"""
    idx = stdout.rfind("\n{")
    if idx == -1:
        return None
    import json
    try:
        return json.loads(stdout[idx + 1:])
    except json.JSONDecodeError:
        return None


def run_solve(case=None):
    """同步执行一次求解，返回 {run_id, status, summary|error, started_at, finished_at}。

    case: scenario 名（tests/cases/*.yaml），None 用基线数据。
    """
    run_id = _new_run_id()
    record = {
        "run_id": run_id,
        "case": case,
        "status": "running",
        "summary": None,
        "error": None,
        "solver": os.getenv("LITHO_SOLVER", "CBC"),
        "started_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "finished_at": None,
    }
    with _RUNS_LOCK:
        RUNS[run_id] = record

    cmd = [sys.executable, "-m", "backend.solver", "run", "--out", _out_dir(run_id), "--json"]
    if case:
        cmd += ["--case", case]

    try:
        proc = subprocess.run(
            cmd, cwd=REPO_ROOT, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=SOLVER_TIMEOUT_S,
        )
    except subprocess.TimeoutExpired:
        record.update(status="timeout",
                      error=f"求解超过 {SOLVER_TIMEOUT_S}s 被终止，可调大 LITHO_TIME_LIMIT_S",
                      finished_at=time.strftime("%Y-%m-%d %H:%M:%S"))
        return record

    if proc.returncode != 0:
        record.update(status="failed",
                      error=(proc.stderr or proc.stdout or "").strip()[-2000:],
                      finished_at=time.strftime("%Y-%m-%d %H:%M:%S"))
        return record

    summary = _parse_summary(proc.stdout)
    if summary is None:
        record.update(status="failed",
                      error="子进程成功但未能解析出 JSON 结果（stdout 结构变化？）",
                      stdout_tail=proc.stdout[-2000:],
                      finished_at=time.strftime("%Y-%m-%d %H:%M:%S"))
        return record

    milp = summary.get("milp_status") or {}
    ok = (milp.get("step2") == "Optimal" and milp.get("step3") == "Optimal")
    record.update(
        status="done" if ok else "suboptimal",
        summary=summary,
        finished_at=time.strftime("%Y-%m-%d %H:%M:%S"),
    )
    return record


def get_result(run_id):
    return RUNS.get(run_id)


def list_runs(limit=20):
    """最近求解批次摘要（新结果页的运行批次选择器用，最新在前）。"""
    out = []
    for r in sorted(RUNS.values(), key=lambda x: x.get("started_at", ""), reverse=True)[:limit]:
        s = r.get("summary") or {}
        out.append({
            "run_id": r["run_id"],
            "case": r.get("case"),
            "status": r.get("status"),
            "started_at": r.get("started_at"),
            "milp": s.get("milp_status"),
            "batch": (s.get("run") or {}).get("batch"),
            "lots": len(s.get("schedule") or []),
        })
    return out
