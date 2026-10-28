# -*- coding: utf-8 -*-
"""GTX FSO Litho · 排程 AI Agent。

双模式（自动选择，前端 /api/agent/status 可查）：
    - LLM 模式：配置 LLM_API_BASE/LLM_API_KEY 后走 OpenAI 兼容 function calling，
      模型自主决定调哪些工具，最多 MAX_ITER 轮；
    - 规则模式（回退，默认）：无 LLM 时按关键词路由到工具，保证演示永不冷场。

会话：SESSIONS 内存字典（服务重启清空），每会话保留最近 20 条消息。
"""
import re
import threading
import uuid

from backend.app.agent import llm, tools

MAX_ITER = 6
SESSIONS: dict = {}
_LOCK = threading.Lock()

SYSTEM_PROMPT = """你是光刻排程系统的 AI 助手（GTX FSO Litho）。你可以调用工具：
- list_cases / run_solve / run_sim / run_workflow / list_workflows / get_mock_data / get_result
回答要求：中文、简洁、给出关键数字（MILP 状态、MakeSpan、急货 LOT-A01 开工、准时率）；
用户让你"跑/算/试"时直接调工具执行，不要只给建议。"""


# ---------------------------------------------------------------------
# 规则模式：关键词 → 工具（无 LLM 时的兜底，也用于 LLM 故障降级）
# ---------------------------------------------------------------------
def _case_in(text):
    found = [c for c in tools.tool_list_cases()["cases"] if c in text]
    return found[0] if found else None


def _rule_route(message):
    """返回 (tool_name, args, 理由)。匹配不到返回 (None, None, None)。

    优先级：具体用例名的执行意图 > 对比/工作流/仿真 > 清单查询 > 数据概况 > 裸执行。
    """
    msg = message.lower()
    case = _case_in(message)
    run_verb = r"跑|求解|算|运行|执行|排程|solve|看看|试"
    if case and re.search(r"仿真|模拟|扰动|故障|simulate", msg):
        return "run_sim", {"case": case}, "指定用例的执行态仿真"
    if re.search(r"对比|比较|what.?if|多场景", msg):
        return "run_workflow", {"template_id": "scenario-compare"}, "用户要对比多个场景"
    if re.search(r"工作流|流程|链路|workflow", msg):
        return "run_workflow", {"template_id": "daily-scheduling", "case": case}, "用户要跑工作流"
    if case and re.search(run_verb, msg):
        return "run_solve", {"case": case}, "指定用例的求解"
    if re.search(r"有哪些|清单|列表|哪些用例|什么用例|什么场景", msg):
        return "list_cases", {}, "用户询问用例清单"
    if re.search(r"机台|lot|光罩|数据|reticle", msg):
        return "get_mock_data", {}, "用户询问数据概况"
    if re.search(run_verb, msg):
        return "run_solve", {"case": None}, "用户要跑求解（基线）"
    return None, None, None


def _fmt_tool_result(name, result):
    """把工具结果压缩成对话友好的中文摘要。"""
    if name == "list_cases":
        return f"可用用例：{'、'.join(result['cases']) or '无'}"
    if name == "run_solve":
        if result.get("status") in ("done", "suboptimal"):
            return (f"求解完成（run_id `{result['run_id']}`，case={result.get('case') or '基线'}），"
                    f"MILP {result['milp']}，急货 LOT-A01 开工 {result.get('urgent_a01_start') or '未排'}。"
                    f"完整结果可在「求解演示」页按 run_id 查看。")
        return f"求解失败：{result.get('status')} {result.get('error', '')[:150]}"
    if name == "run_sim":
        if "error" in result:
            return f"仿真失败：{result['error']}"
        k = result["kpis"]
        return (f"仿真完成：准时率 {k['on_time_rate']:.0%}，实际 MakeSpan {k['makespan_actual']}"
                f"（计划 {k['makespan_planned']}，偏差 {k['makespan_delta_min']}min），"
                f"故障 {k['breakdowns']} 次 / 返工 {k['rework_count']} 次 / QTime 违约 {k['qtime_violations']}。")
    if name == "run_workflow":
        steps = " → ".join(f"{s['name']}:{s['status']}" for s in result["steps"])
        if result["status"] == "done" and result.get("steps") and \
                result["steps"][-1]["name"] == "生成报告":
            return f"工作流执行完成（{result['status']}）。步骤：{steps}。报告见「AI 工作流」页运行记录。"
        return f"工作流状态 {result['status']}，步骤：{steps}" + (
            f"，错误：{result['error'][:150]}" if result.get("error") else "")
    if name == "list_workflows":
        t = "、".join(x["id"] for x in result["templates"])
        return f"可用工作流模板：{t}"
    if name == "get_mock_data":
        return (f"数据概况：机台 {result['machines_count']} 台，Lot {result['lots_count']} 个，"
                f"光罩 {len(result['reticles'])} 个。急货故事线：LOT-A01（PRI1+SHR）+ RT-0101 外部 IRIS。")
    if name == "get_result":
        if "error" in result:
            return result["error"]
        s = result.get("summary") or {}
        return f"run_id {result.get('run_id')}：MILP {s.get('milp_status')}，状态 {result.get('status')}。"
    return str(result)[:300]


def _call_tool(name, args):
    if name not in tools.TOOLS:
        return {"error": f"未知工具 {name}"}
    try:
        return tools.TOOLS[name]["fn"](**args)
    except Exception as e:                    # 工具异常不炸会话，转为错误结果
        return {"error": f"{type(e).__name__}: {e}"}


# ---------------------------------------------------------------------
# 对话入口
# ---------------------------------------------------------------------
def chat(message, session_id=None):
    sid = session_id or uuid.uuid4().hex[:8]
    with _LOCK:
        session = SESSIONS.setdefault(sid, {"messages": [], "mode": None})

    mode = "llm" if llm.llm_config()["enabled"] else "rule"
    session["mode"] = mode
    tool_trace = []

    if mode == "llm":
        reply, tool_trace = _chat_llm(session, message)
    else:
        reply, tool_trace = _chat_rule(message)

    session["messages"] = (session["messages"] + [
        {"role": "user", "content": message},
        {"role": "assistant", "content": reply}])[-20:]
    return {"session_id": sid, "mode": mode, "reply": reply, "tool_calls": tool_trace}


def _chat_rule(message):
    name, args, reason = _rule_route(message)
    if name is None:
        return ("我是排程 AI 助手（当前规则模式，未配置 LLM）。你可以让我：\n"
                "- 「跑一下 urgent-A01」——执行六步 MILP 求解\n"
                "- 「仿真 default」——求解后做执行态仿真\n"
                "- 「对比场景」——多场景 What-if 工作流\n"
                "- 「有哪些用例」「看机台数据」「跑日计划工作流」\n"
                "配置 LLM_API_BASE/LLM_API_KEY/LLM_MODEL 后可切换为 LLM 自主决策模式。"), []
    result = _call_tool(name, args)
    trace = [{"name": name, "args": args, "reason": reason,
              "ok": "error" not in result, "summary": _fmt_tool_result(name, result)}]
    reply = _fmt_tool_result(name, result)
    return reply, trace


def _chat_llm(session, message):
    msgs = [{"role": "system", "content": SYSTEM_PROMPT}] + session["messages"] + [
        {"role": "user", "content": message}]
    specs = tools.tool_specs_for_llm()
    trace = []
    for _ in range(MAX_ITER):
        msg = llm.chat(msgs, tools=specs)
        calls = msg.get("tool_calls") or []
        if not calls:
            return msg.get("content") or "（LLM 返回空回复）", trace
        msgs.append(msg)
        for c in calls:
            fn = c["function"]
            name = fn["name"]
            try:
                import json as _json
                args = _json.loads(fn.get("arguments") or "{}")
            except Exception:
                args = {}
            result = _call_tool(name, args)
            trace.append({"name": name, "args": args, "reason": "LLM 决策",
                          "ok": "error" not in result,
                          "summary": _fmt_tool_result(name, result)})
            msgs.append({"role": "tool", "tool_call_id": c.get("id", ""),
                         "content": str(result)[:2000]})
    return "（已达最大工具调用轮次，先汇报以上结果）", trace


def agent_status():
    cfg = llm.llm_config()
    return {"mode": "llm" if cfg["enabled"] else "rule",
            "model": cfg["model"] if cfg["enabled"] else None,
            "tools": sorted(tools.TOOLS)}
