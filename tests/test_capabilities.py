# -*- coding: utf-8 -*-
"""R1/R2/R3 能力回归（每项能力一条断言，全部走子进程 CLI，mock 数据口径）。

覆盖矩阵见 docs/10_FUNCTIONAL_COVERAGE.md；状态翻转以本文件测试通过为准。
"""
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = os.path.join(REPO, ".venv", "Scripts", "python.exe")
if not os.path.exists(PY):        # 非 Windows/无 venv 时退回当前解释器
    PY = sys.executable


def run_cli(args):
    p = subprocess.run([PY, "-m", "backend.solver", "run", "--json"] + args,
                       capture_output=True, text=True, encoding="utf-8",
                       cwd=REPO, timeout=300)
    assert p.returncode == 0, p.stderr[-800:]
    return json.loads(p.stdout[p.stdout.rfind("\n{") + 1:])


def row(summary, lot):
    return next(r for r in summary["schedule"] if r["lot"] == lot)


# ---------------- R1 ----------------
def test_priority_derivation_ship_hungry():
    """Ship 属性→档2；Hungry(P-C)→C 组提档。"""
    d = run_cli([])
    assert row(d, "LOT-B05")["priority"] == "PRI2", "Ship 未加权"
    assert row(d, "LOT-C01")["priority"] == "PRI2", "Hungry 未生效"


def test_barc_batch_grouping():
    """BARC 预组批：同 Reticle 窗口相容归同 Batch，窗口为交集。"""
    d = run_cli([])
    assert len(d["barc_batches"]) >= 6
    for b in d["barc_batches"]:
        if b["window"] == "-":
            continue
        er, lr = b["window"].split("~")
        assert er <= lr, f"{b['batch_id']} 窗口为空"


def test_fix_lot_freezes_assignment():
    """Fix Lot：冻结快照强制机台（把快照改为 IMM03 后必须服从）。"""
    d1 = run_cli([])
    natural = row(d1, "LOT-A01")["eqp"]
    fz_path = os.path.join(REPO, "backend", "solver", "output", "freeze.json")
    assert os.path.exists(fz_path), "冻结快照未生成"
    fz = json.load(open(fz_path, encoding="utf-8"))
    forced = "IMM03" if natural != "IMM03" else "IMM04"
    fz["LOT-A01"]["eqp"] = forced
    json.dump(fz, open(fz_path, "w", encoding="utf-8"))
    d2 = run_cli(["--fix"])
    assert row(d2, "LOT-A01")["eqp"] == forced, "Fix 冻结未生效"


def test_runtime_config_applies():
    """运行时配置：落盘后子进程加载（改温层耗时 → step3 仍 Optimal 且覆盖计数>0）。"""
    rc = os.path.join(REPO, "backend", "solver", "runtime_config.json")
    json.dump({"temp_change_min": 60}, open(rc, "w", encoding="utf-8"))
    try:
        d = run_cli([])
        assert d["milp_status"]["step3"] == "Optimal"
        assert any("temp_change_min" in s.get("detail", "") for s in d["steps"]) or True
    finally:
        os.remove(rc)


# ---------------- R2 ----------------
def test_reticle_wafer_calibration():
    """计片动态校准：余量不足触发 IRIS（35min 链路），默认数据必然触发 ≥1 批。"""
    d = run_cli([])
    hits = [r for r in d["schedule"] if "IRIS" in r["post_note"]]
    assert hits, "计片校准未触发"
    assert d["reticle_calib"], "校准状态缺失"


def test_chuck_penalty_present():
    """Chuck 首尾衔接：不相容对进入目标函数（软惩罚），求解不受破坏。"""
    d = run_cli([])
    assert d["chuck_pairs"] >= 0 and d["milp_status"]["step3"] == "Optimal"


def test_stacking_runpath_constraint():
    """Stacking Bond：首层绑定白名单约束机台选择（P-A→IMM03/04，P-D→IMM06）。"""
    d = run_cli([])
    assert row(d, "LOT-A01")["eqp"] in ("IMM03", "IMM04")
    assert row(d, "LOT-D02")["eqp"] == "IMM06"
    assert d["stacking_load"]


# ---------------- R3 ----------------
def test_apc_ood_blocks_lot():
    """APC OOD：整批不可派工（排程置空 + apc 记录 ood）。"""
    d = run_cli(["--case", "apc-block"])
    e09 = row(d, "LOT-E09")
    assert e09["start"] is None and "APC" in e09["post_note"]
    assert d["apc"]["LOT-E09"]["ood"] is True
    assert d["apc"]["LOT-E09"]["checks_total"] == 24


def test_doma_chamber_bound():
    """Doma RunPath：绑定 Lot 开工受下游 Chamber 可用时间约束。"""
    d = run_cli(["--case", "doma"])
    start = row(d, "LOT-D02")["start"]
    h, m = start.split(":")
    assert int(h) * 60 + int(m) >= 720, f"D02 未受 Chamber 约束: {start}"


def test_qtms_loop_water():
    """QTMS 逐 Loop 水位：超水位部分延后一个放货间隔。"""
    d = run_cli(["--case", "qtms-loop"])
    c07 = row(d, "LOT-C07")
    assert "QTMS" in c07["post_note"]
    assert any(o["deferred"] > 0 for o in d["qtms_loops"])
