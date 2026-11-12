# -*- coding: utf-8 -*-
"""工作流类技能：模板执行与模板清单。"""
from backend.app import workflow as workflow_mod
from backend.app.registry.core import register
from backend.app.registry.types import Skill


def _summarize_workflow(r):
    """兼容两种返回结构：

    - 本地执行：{wf_id, status, steps[], error}
    - Dify 执行：{mode:'dify', workflow_run_id, status, outputs, elapsed}
      （旧实现直接取 r["wf_id"] 会 KeyError，这里已修）
    """
    if "wf_id" not in r:
        return {
            "mode": r.get("mode"),
            "status": r.get("status"),
            "outputs": r.get("outputs"),
            "fallback_reason": r.get("fallback_reason"),
        }
    return {
        "wf_id": r["wf_id"],
        "status": r["status"],
        "steps": [{"name": s["name"], "status": s["status"]} for s in r["steps"]],
        "error": r.get("error"),
    }


def tool_run_workflow(template_id="daily-scheduling", case=None):
    params = dict(case=case) if case else {}
    return _summarize_workflow(workflow_mod.run_with_fallback(template_id, params or None))


def tool_list_workflows():
    return {
        "templates": workflow_mod.list_templates()["templates"],
        "recent_runs": [
            {k: r[k] for k in ("wf_id", "template", "status", "mode")} if "mode" in r
            else {k: r[k] for k in ("wf_id", "template", "status")}
            for r in list(workflow_mod.WORKFLOWS.values())[-5:]
        ],
    }


register(Skill(
    name="run_workflow",
    title="执行工作流",
    category="workflow",
    description="执行一条完整工作流：daily-scheduling（校验→求解→仿真→报告）或 "
                "scenario-compare（多场景对比）。用户要「跑日计划/对比场景/走完整流程」时调用。",
    input_schema={
        "type": "object",
        "properties": {
            "template_id": {"type": "string", "default": "daily-scheduling",
                            "description": "模板 ID：daily-scheduling 或 scenario-compare"},
            "case": {"type": "string", "description": "scenario 用例名，可选"},
        },
        "required": [],
        "additionalProperties": False,
    },
    handler=tool_run_workflow,
    examples=({"input": {"template_id": "scenario-compare"}, "note": "多场景对比"},),
    tags=("pipeline", "core"),
    risk="compute",
    timeout_s=180,
    max_result_chars=800,
    args_doc={"template_id": "模板 ID", "case": "scenario 用例名，可选"},
))

register(Skill(
    name="list_workflows",
    title="工作流清单",
    category="workflow",
    description="列出可用的工作流模板与最近 5 次运行记录（含 Dify/本地模式）。"
                "用户问「有哪些工作流/最近跑了什么」时调用。",
    input_schema={"type": "object", "properties": {}, "required": [],
                  "additionalProperties": False},
    handler=tool_list_workflows,
    examples=({"input": {}, "note": "查看模板与历史"},),
    tags=("pipeline", "readonly"),
    risk="read",
    timeout_s=10,
    max_result_chars=600,
    args_doc={},
))
