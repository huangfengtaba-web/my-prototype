# -*- coding: utf-8 -*-
"""Loop Engineering 评测入口。

用法：
    python -m harness.run_eval            # 跑全部
    python -m harness.run_eval -k urgent  # 只跑 id 含 urgent 的
    python -m harness.run_eval -v         # 打印每个用例的详细结果

特点：
    - 规则模式执行，**零 LLM 调用、零 token 消耗**
    - 断言的是「结果性质」（达成/停止/重规划次数/是否调某工具），不是具体数值
    - 退出码：全过 0，有失败 1（可直接接 CI）
"""
import argparse
import os
import sys
import traceback

import yaml

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.agent import loop                                    # noqa: E402

CASES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "cases", "loop-golden.yaml")


def load_cases() -> list[dict]:
    with open(CASES_FILE, encoding="utf-8") as f:
        return yaml.safe_load(f) or []


def _check(case: dict, result: dict) -> list[str]:
    """按 expect 断言，返回失败信息列表（空=通过）。"""
    exp = case.get("expect") or {}
    fails = []

    if "status" in exp and result.get("status") != exp["status"]:
        fails.append(f"status 期望 {exp['status']}，实际 {result.get('status')}")

    if "goal_met" in exp and bool(result.get("goal_met")) != bool(exp["goal_met"]):
        fails.append(f"goal_met 期望 {exp['goal_met']}，实际 {result.get('goal_met')}")

    if "max_rounds" in exp and result.get("rounds", 0) > exp["max_rounds"]:
        fails.append(f"轮次 {result.get('rounds')} 超过上限 {exp['max_rounds']}")

    if "min_replans" in exp and result.get("replans", 0) < exp["min_replans"]:
        fails.append(f"重规划 {result.get('replans')} 少于期望 {exp['min_replans']}")

    if "stopped_contains" in exp:
        if exp["stopped_contains"] not in (result.get("stopped_reason") or ""):
            fails.append(f"停止原因不含「{exp['stopped_contains']}」：{result.get('stopped_reason')}")

    if "min_observations" in exp and len(result.get("observations") or []) < exp["min_observations"]:
        fails.append(f"观测数 {len(result.get('observations') or [])} 少于 {exp['min_observations']}")

    if "must_call" in exp:
        called = {o.get("skill") for o in (result.get("observations") or [])}
        if exp["must_call"] not in called:
            fails.append(f"未调用 {exp['must_call']}，实际调用 {sorted(called)}")

    if "min_distinct_plans" in exp:
        tried = {tuple(sorted(s["args"].items()))
                 for p in (result.get("plan") or []) for s in p}
        if len(tried) < exp["min_distinct_plans"]:
            fails.append(f"不同方案数 {len(tried)} 少于 {exp['min_distinct_plans']}（重规划在打转）")

    return fails


def run_case(case: dict, verbose: bool = False) -> dict:
    cid = case.get("id", "?")
    cfg = dict(case.get("config") or {})
    cfg["enabled"] = True                       # 评测时强制开启

    original = loop.plan_rule
    if case.get("plan_override"):
        steps = [loop.Step(s["skill"], s.get("args") or {}, s.get("note", ""))
                 for s in case["plan_override"]]
        loop.plan_rule = lambda goal, state, _s=steps: list(_s)

    try:
        result = loop.run_loop(case["goal"], **cfg)
    except Exception as e:                      # noqa: BLE001
        loop.plan_rule = original
        return {"id": cid, "passed": False,
                "fails": [f"抛出异常: {type(e).__name__}: {e}"],
                "traceback": traceback.format_exc()[-600:]}
    finally:
        loop.plan_rule = original

    fails = _check(case, result)
    if verbose:
        print(f"    status={result.get('status')} met={result.get('goal_met')} "
              f"rounds={result.get('rounds')} replans={result.get('replans')} "
              f"elapsed={result.get('elapsed_s')}s trace={result.get('trace_id')}")
        for o in (result.get("observations") or []):
            print(f"      · {o}")
    return {"id": cid, "desc": case.get("desc", ""), "passed": not fails,
            "fails": fails, "trace_id": result.get("trace_id"),
            "status": result.get("status"), "goal_met": result.get("goal_met"),
            "rounds": result.get("rounds"), "replans": result.get("replans")}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="harness.run_eval")
    ap.add_argument("-k", "--filter", default="", help="只跑 id 含该子串的用例")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args(argv)

    cases = load_cases()
    if args.filter:
        cases = [c for c in cases if args.filter in c.get("id", "")]
    if not cases:
        print("没有匹配的用例")
        return 1

    print(f"=== Loop 评测：{len(cases)} 个用例 ===\n")
    results = []
    for i, c in enumerate(cases, 1):
        print(f"[{i}/{len(cases)}] {c['id']} — {c.get('desc', '')}")
        r = run_case(c, args.verbose)
        results.append(r)
        if r["passed"]:
            print(f"    PASS  ({r.get('status')}, rounds={r.get('rounds')}, "
                  f"replans={r.get('replans')}, trace={r.get('trace_id')})")
        else:
            print("    FAIL")
            for f in r["fails"]:
                print("      -", f)
            if r.get("traceback"):
                print(r["traceback"])
        print()

    passed = sum(1 for r in results if r["passed"])
    print(f"=== 结果：{passed}/{len(results)} 通过 ===")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
