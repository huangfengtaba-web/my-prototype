# -*- coding: utf-8 -*-
"""Loop Engineering 回归：目标解析、确定性判定、状态机、缓存、硬闸。

不依赖 LLM：所有用例在规则模式（LLM 未配置）下跑。
涉及真实求解的用例控制在 1~2 轮，避免测试耗时过长。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.agent import goals, loop                            # noqa: E402


# ---------------------------------------------------------------- 目标解析
def test_parse_urgent_deadline():
    g = goals.parse_goal("让急货 10 点前上机")
    assert g.kind == "urgent_deadline"
    assert g.params["deadline_min"] == 600
    assert g.params["lot"] == "LOT-A01"


def test_parse_urgent_with_minutes():
    g = goals.parse_goal("LOT-A01 必须 09:30 开工")
    assert g.kind == "urgent_deadline"
    assert g.params["deadline_min"] == 570


def test_parse_makespan():
    g = goals.parse_goal("MakeSpan 不晚于 12:35")
    assert g.kind == "makespan_le"
    assert g.params["limit_min"] == 755


def test_parse_on_time_rate():
    g = goals.parse_goal("准时率要达到 95% 以上")
    assert g.kind == "on_time_ge"
    assert abs(g.params["rate"] - 0.95) < 1e-6


def test_parse_freeform():
    g = goals.parse_goal("帮我看看这个产线怎么样")
    assert g.kind == "freeform"


# ---------------------------------------------------------------- 判定
def test_evaluate_urgent_met():
    goal = goals.Goal("urgent_deadline", {"lot": "LOT-A01", "deadline_min": 600})
    met, ev = goals.evaluate(goal, {"solve": {"urgent_a01_start": "10:00"}})
    assert met is True and ev["slack_min"] == 0


def test_evaluate_urgent_not_met():
    goal = goals.Goal("urgent_deadline", {"lot": "LOT-A01", "deadline_min": 540})
    met, ev = goals.evaluate(goal, {"solve": {"urgent_a01_start": "10:00"}})
    assert met is False and ev["slack_min"] == -60


def test_evaluate_makespan():
    goal = goals.Goal("makespan_le", {"limit_min": 755})
    met, ev = goals.evaluate(goal, {"solve": {"makespan": "12:35"}})
    assert met is True and ev["actual_min"] == 755

    goal2 = goals.Goal("makespan_le", {"limit_min": 700})
    met2, ev2 = goals.evaluate(goal2, {"solve": {"makespan": "12:35"}})
    assert met2 is False and ev2["slack_min"] == -55


def test_evaluate_on_time_requires_sim():
    goal = goals.Goal("on_time_ge", {"rate": 0.95})
    met, ev = goals.evaluate(goal, {})
    assert met is False and "未找到仿真 KPI" in ev["reason"]

    met2, _ = goals.evaluate(goal, {"sim": {"kpis": {"on_time_rate": 0.97}}})
    assert met2 is True


# ---------------------------------------------------------------- 状态机
def test_loop_disabled_by_default():
    r = loop.run_loop("让急货 10 点前上机")
    assert r["status"] == "disabled"
    assert "AGENT_LOOP_ENABLED" in r["stopped_reason"]


def test_loop_reaches_goal_in_one_round():
    r = loop.run_loop("让急货 10 点前上机", enabled=True, max_rounds=3)
    assert r["goal_met"] is True and r["status"] == "done"
    assert r["rounds"] == 1
    # 轨迹文件必须存在且含五个阶段
    from backend.app.agent import trace
    phases = {e["phase"] for e in trace.read_trace(r["trace_id"])}
    assert {"start", "plan", "act", "observe", "reflect", "end"} <= phases


def test_loop_stops_when_unreachable():
    r = loop.run_loop("让急货 9 点前上机", enabled=True, max_rounds=4, max_replans=2)
    assert r["goal_met"] is False and r["status"] == "stopped"
    assert r["replans"] == 2
    assert "重规划" in r["stopped_reason"]
    # 至少尝试过两种不同方案（说明重规划不是原地打转）
    tried = {tuple(sorted(s["args"].items())) for p in r["plan"] for s in p}
    assert len(tried) >= 2


def test_solve_cache_avoids_duplicate_run():
    """同 (skill,args) 在一次 loop 内只跑一次。"""
    cfg = loop.load_config(enabled=True)
    usage = {"llm_calls": 0, "tokens": 0, "solve_calls": 0}
    cache: dict = {}
    step = loop.Step("run_solve", {"case": "urgent-A01"})
    r1, c1 = loop.act(step, cache, usage)
    r2, c2 = loop.act(step, cache, usage)
    assert c1 is False and c2 is True
    assert usage["solve_calls"] == 1
    assert r1["run_id"] == r2["run_id"]


def test_observe_extracts_key_numbers():
    obs = loop.observe("run_solve", {
        "run_id": "ab12", "status": "done", "milp": {"step2": "Optimal"},
        "lots": 9, "urgent_a01_start": "10:00", "urgent_a01_eqp": "IMM04",
        "makespan": "12:35"})
    assert obs["urgent_start"] == "10:00" and obs["makespan"] == "12:35" and obs["lots"] == 9


def test_plan_rule_varies_by_replan_count():
    goal = goals.Goal("urgent_deadline", {"lot": "LOT-A01", "deadline_min": 600})
    p0 = loop.plan_rule(goal, {"replans": 0})
    p1 = loop.plan_rule(goal, {"replans": 1})
    p3 = loop.plan_rule(goal, {"replans": 3})
    assert p0[0].args != p1[0].args != p3[0].args
