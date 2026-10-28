# -*- coding: utf-8 -*-
"""工作流引擎回归（模板执行 / 步骤状态 / 报告产出）。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app import workflow                                     # noqa: E402


def test_daily_scheduling_end_to_end():
    r = workflow.run_workflow_sync("daily-scheduling", {"case": "default"})
    assert r["status"] == "done", r.get("error")
    assert [s["status"] for s in r["steps"]] == ["done"] * 4
    validate = next(s for s in r["steps"] if s["id"] == "validate")
    assert validate["output"]["ok"] is True
    report = next(s for s in r["steps"] if s["id"] == "report")
    assert "## 求解" in report["output"]["markdown"]
    assert "## 执行仿真" in report["output"]["markdown"]


def test_scenario_compare_end_to_end():
    r = workflow.run_workflow_sync("scenario-compare")
    assert r["status"] == "done", r.get("error")
    compare = next(s for s in r["steps"] if s["id"] == "compare")
    table = compare["output"]["table"]
    assert {row["case"] for row in table} == {"default", "urgent-A01", "reticle-delay"}
    # 基线与光罩延迟场景的急货开工应不同（耦合约束生效）
    starts = {row["case"]: row["urgent_a01_start"] for row in table}
    assert starts["reticle-delay"] != starts["default"]


def test_unknown_template_rejected():
    try:
        workflow.run_workflow_sync("no-such-template")
        assert False, "应抛 KeyError"
    except KeyError:
        pass
