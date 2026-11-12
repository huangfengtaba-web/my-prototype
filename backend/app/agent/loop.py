# -*- coding: utf-8 -*-
"""Loop Engineering：Plan → Act → Observe → Reflect → (Replan | Done | Stopped)。

与现有 agent.chat 的关系：
    chat()      —— 单层 ReAct，LLM 选一个工具、执行、回灌、再选，最多 6 轮，无目标概念
    run_loop()  —— 显式规划循环，有目标、有判定、有反思、有重规划、有预算与轨迹

两者共用同一套技能注册表（backend/app/registry），互不干扰。

安全设计（防止演示时烧钱 / 卡死）：
    AGENT_LOOP_ENABLED      默认 0，需显式开启
    AGENT_LOOP_MAX_ROUNDS   默认 8
    AGENT_LOOP_MAX_REPLANS  默认 3
    AGENT_LOOP_BUDGET_TOKENS 默认 20000
    AGENT_LOOP_MAX_WALL_S   默认 180
    同 (skill,args) 在**一次 loop 内**缓存，避免重复求解（求解是重操作）
"""
import json
import os
import time
from dataclasses import dataclass, field

from backend.app.agent import goals, prompts
from backend.app.agent import llm as llm_mod
from backend.app.agent import trace as trace_mod
from backend.app.registry import get as get_skill


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


def _env_bool(name: str, default: bool) -> bool:
    v = (os.getenv(name) or "").strip().lower()
    if not v:
        return default
    return v in ("1", "true", "yes", "on")


@dataclass
class Step:
    skill: str
    args: dict = field(default_factory=dict)
    note: str = ""

    def as_dict(self) -> dict:
        return {"skill": self.skill, "args": self.args, "note": self.note}


@dataclass
class LoopConfig:
    enabled: bool = False
    max_rounds: int = 8
    max_replans: int = 3
    budget_tokens: int = 20000
    max_wall_s: int = 180
    explain_with_llm: bool = True


def load_config(**overrides) -> LoopConfig:
    cfg = LoopConfig(
        enabled=_env_bool("AGENT_LOOP_ENABLED", False),
        max_rounds=_env_int("AGENT_LOOP_MAX_ROUNDS", 8),
        max_replans=_env_int("AGENT_LOOP_MAX_REPLANS", 3),
        budget_tokens=_env_int("AGENT_LOOP_BUDGET_TOKENS", 20000),
        max_wall_s=_env_int("AGENT_LOOP_MAX_WALL_S", 180),
        explain_with_llm=_env_bool("AGENT_LOOP_EXPLAIN", True),
    )
    for k, v in overrides.items():
        if v is not None and hasattr(cfg, k):
            setattr(cfg, k, v)
    return cfg


# ---------------------------------------------------------------- PLAN
def plan_rule(goal, state: dict) -> list[Step]:
    """无 LLM 时的确定性计划。replans 次数决定策略，保证「重规划」真的有变化。"""
    n = state.get("replans", 0)

    if goal.kind == "urgent_deadline":
        if n == 0:
            return [Step("run_solve", {"case": "urgent-A01"}, "先跑急货场景，看 LOT-A01 实际上机时间")]
        if n == 1:
            return [Step("run_solve", {"case": "default"}, "换基线场景，确认急货场景是否反而更慢")]
        if n == 2:
            return [Step("run_solve", {"case": "urgent-A01", "fix": True},
                         "用 Fix Lot 锁定机台与顺序再试一次")]
        return [Step("run_sim", {"case": "urgent-A01", "seed": 42, "breakdown": True},
                     "求解已无法改善，跑仿真确认扰动下急货是否进一步推迟")]

    if goal.kind == "makespan_le":
        if n == 0:
            return [Step("run_solve", {}, "跑基线求解，看整体完工时间")]
        if n == 1:
            return [Step("run_solve", {"case": "urgent-A01"}, "急货优先排序往往能压缩尾部拖期")]
        return [Step("run_sim", {"case": "default", "seed": 42, "breakdown": True},
                     "跑仿真确认故障扰动下的实际完工")]

    if goal.kind == "on_time_ge":
        if n == 0:
            return [Step("run_sim", {"case": "default", "seed": 42, "breakdown": True},
                         "跑带故障的仿真，拿准时率")]
        if n == 1:
            return [Step("run_sim", {"case": "default", "seed": 42, "breakdown": False},
                         "关掉故障扰动，看准时率是否由故障拉低")]
        return [Step("run_sim", {"case": "urgent-A01", "seed": 7, "breakdown": True},
                     "换场景与随机种子，验证是否场景本身导致延迟")]

    return [Step("list_cases", {}, "自由目标：先列出可用场景，避免瞎猜")]


def plan_llm(goal, state: dict, budget_left: int) -> tuple[list[Step], dict]:
    """LLM 规划。返回 (steps, usage)。失败时回落 plan_rule。"""
    usage = {"llm_calls": 0, "tokens": 0}
    sys_prompt = prompts.PLAN_SYSTEM.format(
        skills=prompts.skills_block(), goal=goals.describe(goal))
    msg = [{"role": "system", "content": sys_prompt},
           {"role": "user", "content": f"目标：{goal.text}\n已重规划 {state.get('replans', 0)} 次"}]
    try:
        resp = llm_mod.chat(msg, timeout=60)
        content = (resp.get("content") or "").strip()
        usage["llm_calls"] = 1
        usage["tokens"] = sum(_estimate(m["content"]) for m in msg) + _estimate(content)
        data = _extract_json(content)
        steps = []
        for s in (data.get("steps") or [])[:4]:
            name = (s.get("skill") or "").strip()
            if get_skill(name) is None:
                continue                       # 丢弃幻觉出来的工具名
            steps.append(Step(name, s.get("args") or {}, s.get("note") or ""))
        if steps:
            return steps, usage
    except Exception:                          # noqa: BLE001  LLM 不可用即回落
        pass
    if usage["tokens"] > budget_left:
        return [], usage
    return plan_rule(goal, state), usage


def _extract_json(text: str) -> dict:
    """容错解析：模型常把 JSON 包在 ```json 里，或前后带说明文字。"""
    if not text:
        return {}
    s = text.strip()
    if "```" in s:
        parts = s.split("```")
        for p in parts:
            p = p.strip()
            if p.startswith("json"):
                p = p[4:].strip()
            if p.startswith("{"):
                s = p
                break
    i, j = s.find("{"), s.rfind("}")
    if i >= 0 and j > i:
        try:
            return json.loads(s[i:j + 1])
        except json.JSONDecodeError:
            return {}
    return {}


def _estimate(text) -> int:
    from backend.app.agent.context import estimate_tokens
    return estimate_tokens(text)


# ---------------------------------------------------------------- OBSERVE
def observe(skill_name: str, result: dict) -> dict:
    """把工具结果压成关键数字（写进 trace 与下一步 prompt，不保留全量）。"""
    r = result or {}
    if "error" in r:
        return {"ok": False, "error": str(r["error"])[:200]}

    if skill_name == "run_solve":
        # run_solve 工具返回的是压缩摘要（无 summary 字段），直接用其扁平字段
        return {"ok": True, "run_id": r.get("run_id"), "status": r.get("status"),
                "milp": r.get("milp"), "lots": r.get("lots"),
                "urgent_start": r.get("urgent_a01_start"),
                "urgent_eqp": r.get("urgent_a01_eqp"),
                "makespan": r.get("makespan")}

    if skill_name == "run_sim":
        k = (r.get("sim") or {}).get("kpis") or r.get("kpis") or {}
        return {"ok": True, "solve_run_id": r.get("solve_run_id"),
                "on_time_rate": k.get("on_time_rate"),
                "makespan_actual": k.get("makespan_actual"),
                "makespan_delta_min": k.get("makespan_delta_min"),
                "breakdowns": k.get("breakdowns"),
                "qtime_violations": k.get("qtime_violations")}

    if skill_name == "list_cases":
        return {"ok": True, "cases": r.get("cases") or []}

    return {"ok": True, "keys": sorted(r)[:8]}


def _ctx_update(ctx: dict, skill_name: str, result: dict) -> None:
    """把原始结果塞进判定上下文（evaluate 需要完整 schedule，不能只看 digest）。"""
    if skill_name == "run_solve" and "error" not in (result or {}):
        ctx["solve"] = result
    elif skill_name == "run_sim" and "error" not in (result or {}):
        ctx["sim"] = result


# ---------------------------------------------------------------- ACT
def act(step: Step, cache: dict, usage: dict) -> tuple[dict, bool]:
    """执行一步。返回 (result, from_cache)。"""
    key = json.dumps([step.skill, step.args], sort_keys=True, ensure_ascii=False)
    if key in cache:
        return cache[key], True

    skill = get_skill(step.skill)
    if skill is None:
        return {"error": f"未知工具 {step.skill}"}, False
    try:
        result = skill.handler(**(step.args or {}))
    except TypeError as e:
        result = {"error": f"参数错误: {e}"}
    except Exception as e:                     # noqa: BLE001
        result = {"error": f"{type(e).__name__}: {e}"}

    if step.skill in ("run_solve", "run_sim"):
        cache[key] = result
        usage["solve_calls"] = usage.get("solve_calls", 0) + 1
    return result, False


# ---------------------------------------------------------------- REFLECT
def reflect(goal, ctx: dict, cfg: LoopConfig, usage: dict) -> tuple[bool, dict, str]:
    """确定性判定 + （可选）LLM 解释。返回 (met, evidence, explanation)。"""
    met, evidence = goals.evaluate(goal, ctx)
    if not cfg.explain_with_llm or not llm_mod.llm_config()["enabled"]:
        return met, evidence, ""

    prompt = prompts.REFLECT_SYSTEM.format(
        goal=goals.describe(goal), met="达成" if met else "未达成",
        evidence=json.dumps(evidence, ensure_ascii=False))
    try:
        resp = llm_mod.chat([{"role": "system", "content": prompt},
                             {"role": "user", "content": "请给出解释与建议"}], timeout=45)
        text = (resp.get("content") or "").strip()
        usage["llm_calls"] = usage.get("llm_calls", 0) + 1
        usage["tokens"] = usage.get("tokens", 0) + _estimate(prompt) + _estimate(text)
        return met, evidence, text[:300]
    except Exception:                          # noqa: BLE001
        return met, evidence, ""


# ---------------------------------------------------------------- 主循环
def run_loop(goal_text: str, **overrides) -> dict:
    cfg = load_config(**overrides)
    goal = goals.parse_goal(goal_text)
    tr = trace_mod.Trace()

    if not cfg.enabled:
        return {
            "trace_id": tr.trace_id, "status": "disabled", "goal": goals.describe(goal),
            "goal_met": False,
            "stopped_reason": "AGENT_LOOP_ENABLED=0（默认关闭，防止误触发烧 token）",
            "hint": "设置 AGENT_LOOP_ENABLED=1 后重启后端，或调用时传 enabled=true",
            "rounds": 0, "plan": [], "observations": [], "reflections": [],
        }

    tr.phase("start", goal=goals.describe(goal), kind=goal.kind,
             raw=goal_text, config={"max_rounds": cfg.max_rounds,
                                    "budget_tokens": cfg.budget_tokens})

    state = {"round": 0, "replans": 0}
    usage = {"llm_calls": 0, "tokens": 0, "solve_calls": 0}
    cache: dict = {}
    ctx: dict = {}
    observations: list = []
    reflections: list = []
    all_steps: list = []
    pending: list[Step] = []

    status, stopped_reason = "stopped", ""
    met, evidence, explanation = False, {}, ""
    t0 = time.time()

    while state["round"] < cfg.max_rounds:
        # ---- 硬闸
        if time.time() - t0 > cfg.max_wall_s:
            stopped_reason = f"超过墙钟上限 {cfg.max_wall_s}s"
            break
        if usage["tokens"] > cfg.budget_tokens:
            stopped_reason = f"超过 token 预算 {cfg.budget_tokens}"
            break
        # 重规划次数用尽且无待执行步骤 → 直接收尾，不再白跑一轮
        if not pending and state["replans"] >= cfg.max_replans and state["round"] > 0:
            stopped_reason = f"已达最大重规划次数 {cfg.max_replans}"
            break

        state["round"] += 1
        rnd = state["round"]

        # ---- PLAN（待执行队列空时才规划）
        if not pending:
            if llm_mod.llm_config()["enabled"]:
                pending, u = plan_llm(goal, state, cfg.budget_tokens - usage["tokens"])
                usage["llm_calls"] += u["llm_calls"]
                usage["tokens"] += u["tokens"]
            else:
                pending = plan_rule(goal, state)
            if not pending:
                stopped_reason = "规划失败（LLM 未产出有效步骤，规则计划也为空）"
                break
            all_steps.append([s.as_dict() for s in pending])
            tr.phase("plan", round=rnd, replans=state["replans"],
                     steps=[s.as_dict() for s in pending])

        # ---- ACT
        step = pending.pop(0)
        ts = time.time()
        result, from_cache = act(step, cache, usage)
        ok = "error" not in (result or {})
        tr.phase("act", round=rnd, step=step.skill, args=step.args, ok=ok,
                 cached=from_cache, ms=int((time.time() - ts) * 1000))

        # ---- OBSERVE
        obs = observe(step.skill, result)
        observations.append({"round": rnd, "skill": step.skill, **obs})
        _ctx_update(ctx, step.skill, result)
        tr.phase("observe", round=rnd, digest=obs)

        if not ok:
            # 工具失败也要进入反思：让重规划换个策略
            pass

        # 计划还没走完 → 继续执行下一步
        if pending:
            continue

        # ---- REFLECT（计划走完后判定）
        met, evidence, explanation = reflect(goal, ctx, cfg, usage)
        reflections.append({"round": rnd, "met": met, "evidence": evidence,
                            "explanation": explanation})
        tr.phase("reflect", round=rnd, met=met, evidence=evidence,
                 explanation=explanation)

        if met:
            status = "done"
            break

        # ---- REPLAN
        if state["replans"] >= cfg.max_replans:
            stopped_reason = f"已达最大重规划次数 {cfg.max_replans}"
            break
        state["replans"] += 1
        tr.phase("replan", round=rnd, replans=state["replans"])

    if status != "done" and not stopped_reason:
        stopped_reason = f"已达最大轮次 {cfg.max_rounds}"

    tr.phase("end", status=status, met=met, stopped_reason=stopped_reason,
             usage=usage, elapsed=int(time.time() - t0))

    return {
        "trace_id": tr.trace_id,
        "status": status,
        "goal": goals.describe(goal),
        "goal_kind": goal.kind,
        "goal_met": met,
        "evidence": evidence,
        "explanation": explanation,
        "stopped_reason": stopped_reason,
        "rounds": state["round"],
        "replans": state["replans"],
        "plan": all_steps,
        "observations": observations,
        "reflections": reflections,
        "usage": usage,
        "elapsed_s": int(time.time() - t0),
    }


def loop_status(trace_id: str) -> dict:
    """从轨迹文件重建一次循环的状态（跨进程可查）。"""
    events = trace_mod.read_trace(trace_id)
    if not events:
        return {"trace_id": trace_id, "found": False, "events": []}

    def last(phase):
        for e in reversed(events):
            if e.get("phase") == phase:
                return e.get("payload") or {}
        return {}

    start = next((e.get("payload") or {} for e in events if e.get("phase") == "start"), {})
    end = last("end")
    return {
        "trace_id": trace_id,
        "found": True,
        "goal": start.get("goal"),
        "status": end.get("status") or "running",
        "goal_met": end.get("met"),
        "stopped_reason": end.get("stopped_reason"),
        "usage": end.get("usage"),
        "summary": trace_mod.summarize(events),
    }


__all__ = ["Step", "LoopConfig", "load_config", "plan_rule", "plan_llm",
           "observe", "act", "reflect", "run_loop", "loop_status"]
