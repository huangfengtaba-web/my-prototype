# -*- coding: utf-8 -*-
"""排程结果 AI 解读（Dify 工作流最佳接入点）。

链路：POST /api/explain/run {run_id}
  ① Dify 已配置（DIFY_KEY_RESULT_EXPLAIN）→ 线上工作流：HTTP 节点回调
     /api/solve/result/{run_id} 取数 → LLM 生成中文解读 → mode=dify
  ② 未配置/不可达 → 本地规则解读（确定性拼装，无 LLM 也可用）→ mode=local_fallback

为什么这条线适合工作流：取数是确定性的 HTTP 回调，解释是 LLM 擅长的自然语言生成；
求解本体（MILP）、WPS COM、3D 高频推送不适合进工作流（见 docs/09 §P2-2）。
"""
import json

from backend.app.ai import dify_client
from backend.app import solver_runner


def _loads(summary):
    """机台累计加工时长（分钟）。"""
    out = {}
    for r in summary.get("schedule") or []:
        e = r.get("eqp")
        if not e or not r.get("start") or not r.get("end"):
            continue
        try:
            h, m = str(r["start"]).split(":")
            s = int(h) * 60 + int(m)
            h2, m2 = str(r["end"]).split(":")
            t = int(h2) * 60 + int(m2)
            out[e] = out.get(e, 0) + (t - s)
        except Exception:
            pass
    return out


def _local_report(summary: dict, record: dict) -> str:
    """本地规则解读（无 LLM 时的降级产物，确定性输出）。"""
    lines = [f"# 排程解读 · run {record.get('run_id')}（{record.get('case') or '基线'}）", ""]
    milp = summary.get("milp_status") or {}
    lines += ["## 求解状态",
              f"- MILP：②预组批 {milp.get('step2', '-')} / ③细排程 {milp.get('step3', '-')}", ""]

    story = summary.get("story_check") or {}
    if story:
        lines += ["## 急货故事线"]
        lines += [f"- {k}：{v}" for k, v in story.items()]
        lines.append("")

    loads = sorted(_loads(summary).items(), key=lambda kv: -kv[1])[:3]
    if loads:
        lines += ["## 机台累计加工（Top3）"]
        lines += [f"- {e}：{m} min" for e, m in loads]
        lines.append("")

    notes = [r for r in summary.get("schedule") or [] if r.get("post_note", "-") != "-"]
    if notes:
        lines += ["## 卡控与校准（需关注）"]
        lines += [f"- {r['lot']}：{r['post_note']}" for r in notes]
        lines.append("")

    warns = summary.get("reticle_temp_warn") or []
    if warns:
        lines += ["## 光罩温层跳变（RFP 2.1.7 风险）"]
        lines += [f"- {w['eqp']}：{w['detail']}" for w in warns]
        lines.append("")

    monitor = summary.get("monitor") or []
    if monitor:
        lines += ["## Monitor Lot（已隔离）"]
        lines += [f"- {m['lot']}：时效 {m['due']}" + ("（已过期，需先处理）" if m["overdue"] else "")
                  for m in monitor]
        lines.append("")

    lines += ["## 建议",
              "- 到「仿真验证」页跑执行态仿真（故障/返工/光罩接力），确认计划抗扰动能力；",
              "- 到「数字孪生回放」页按时间轴观看机台占用与光罩搬送；",
              "- 若急货未准时或卡控过多，用 Scenario（urgent-A01 / reticle-delay）做 What-if 对比。"]
    return "\n".join(lines)


def explain_run(run_id: str) -> dict:
    rec = solver_runner.get_result(run_id)
    if rec is None:
        return {"error": f"run_id 不存在或已过期: {run_id}"}
    summary = rec.get("summary") or {}
    report = _local_report(summary, rec)
    result = {"run_id": run_id, "mode": "local_fallback",
              "fallback_reason": "Dify 未配置", "report": report}

    if dify_client.configured("result_explain"):
        try:
            res = dify_client.run_workflow("result_explain", {"run_id": run_id})
            outputs = res.get("outputs") or {}
            result["mode"] = "dify"
            result["fallback_reason"] = None
            result["workflow_run_id"] = res.get("workflow_run_id")
            result["elapsed"] = res.get("elapsed")
            result["report"] = outputs.get("explanation") or outputs.get("text") or \
                json.dumps(outputs, ensure_ascii=False, indent=1)
        except dify_client.DifyUnavailable as e:
            result["fallback_reason"] = str(e)
    return result
