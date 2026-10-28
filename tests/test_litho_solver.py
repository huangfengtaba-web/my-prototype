# -*- coding: utf-8 -*-
"""litho_solver 回归测试（E1）。

设计：全部通过子进程 `python -m backend.solver run --json` 跑，
     与 API 生产路径完全一致，天然规避 mock_data 同进程状态污染。

验收口径（docs/03_ALGORITHM_DEMO.md §6.2）：
  - step2 / step3 状态 = Optimal
  - 急货 LOT-A01 最早开工
  - RT-0101 就绪链路 = IRIS 20 + 搬送 10 + 装载 5 = 35min

运行：在仓库根执行 pytest tests/ -v
"""
import json
import os
import subprocess
import sys

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TIMEOUT_S = 180


def run_cli(case=None):
    """子进程跑一次 CLI，返回解析出的 SUMMARY JSON。"""
    cmd = [sys.executable, "-m", "backend.solver", "run", "--json"]
    if case:
        cmd += ["--case", case]
    proc = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=TIMEOUT_S)
    assert proc.returncode == 0, f"CLI 失败：\n{proc.stderr[-2000:]}"
    idx = proc.stdout.rfind("\n{")
    assert idx != -1, "stdout 里没找到 JSON 结果"
    return json.loads(proc.stdout[idx + 1:])


def to_min(hm):
    h, m = hm.split(":")
    return int(h) * 60 + int(m)


def test_default_optimal():
    """基线：step2 / step3 必须都是 Optimal。"""
    summary = run_cli()
    milp = summary["milp_status"]
    assert milp["step2"] == "Optimal", f"step2 = {milp['step2']}"
    assert milp["step3"] == "Optimal", f"step3 = {milp['step3']}"
    assert len(summary["schedule"]) == 10          # 10 个 Lot 全部排产


def test_urgent_a01_starts_first():
    """急货故事线：LOT-A01（PRI1+SHR）到站即开工，零无谓延迟。

    注：LOT-A01 的到站时间是 10:00（600min），晚于其他 Lot 的 09:00，
    所以「最早开工」的正确口径是开工 = 到站（不被优先级低的 Lot 挤占），而非全厂最小值。
    """
    from backend.solver.mock_data import LOTS
    a01_ready = next(l["ready"] for l in LOTS if l["lot"] == "LOT-A01")
    summary = run_cli("urgent-A01")
    starts = {r["lot"]: to_min(r["start"]) for r in summary["schedule"] if r["start"]}
    assert starts["LOT-A01"] == a01_ready, \
        f"急货 LOT-A01 开工 {starts['LOT-A01']} ≠ 到站 {a01_ready}，存在无谓延迟"


def test_rt0101_ready_chain_35min():
    """RT-0101 就绪链路：IRIS 20min + 搬送 10min + 装载 5min = 35min。"""
    from backend.solver.mock_data import CONFIG, RETICLES
    summary = run_cli()
    ready = to_min(summary["reticles"]["RT-0101"]["ready"])
    iris_at = RETICLES["RT-0101"]["iris_at"]        # 基线 = 550（09:10）
    chain = ready - iris_at
    expected = CONFIG["iris_min"] + CONFIG["transport_min"] + CONFIG["load_min"]
    assert chain == expected, f"就绪链路 {chain}min ≠ IRIS{CONFIG['iris_min']}+搬送{CONFIG['transport_min']}+装载{CONFIG['load_min']}"


def test_reticle_delay_couples_to_lots():
    """光罩延迟场景：RT-0101 IRIS 推迟到 11:00 后，就绪链路 35min 守恒，
    且依赖它的 Lot 开工必须顺延（step3 光罩就绪耦合约束）。"""
    from backend.solver.cli import load_case
    from backend.solver.mock_data import RETICLES
    base = run_cli()
    delayed = run_cli("reticle-delay")
    iris_delayed = load_case("reticle-delay")["reticles"]["RT-0101"]["iris_at"]
    assert iris_delayed != RETICLES["RT-0101"]["iris_at"], "用例未生效：iris_at 与基线相同"
    # 35min 链路守恒
    assert to_min(base["reticles"]["RT-0101"]["ready"]) - RETICLES["RT-0101"]["iris_at"] == 35
    assert to_min(delayed["reticles"]["RT-0101"]["ready"]) - iris_delayed == 35
    # Lot 开工顺延：急货 LOT-A01 开工 ≥ 光罩就绪时间（基线 585，延迟后 695）
    base_a01 = next(r for r in base["schedule"] if r["lot"] == "LOT-A01")
    del_a01 = next(r for r in delayed["schedule"] if r["lot"] == "LOT-A01")
    assert to_min(del_a01["start"]) >= iris_delayed + 35, \
        f"光罩推迟后 LOT-A01 未顺延：{del_a01['start']}"
    assert to_min(del_a01["start"]) > to_min(base_a01["start"]), "延迟场景下 LOT-A01 开工未晚于基线"


def test_story_check_consistent():
    """story_check 自检块存在且急货字段非空。"""
    summary = run_cli()
    sc = summary["story_check"]
    assert sc["LOT-A01 上机时间"], "LOT-A01 上机时间为空"
    assert sc["RT-0101 就绪时间"], "RT-0101 就绪时间为空"


@pytest.mark.parametrize("case", ["default", "urgent-A01", "reticle-delay", "temp-conflict"])
def test_all_cases_run(case):
    """4 个 scenario 全部可跑通且 Optimal（E4/E5 的回归网）。"""
    summary = run_cli(case)
    assert summary["milp_status"]["step2"] == "Optimal", case
    assert summary["milp_status"]["step3"] == "Optimal", case
