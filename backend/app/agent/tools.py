# -*- coding: utf-8 -*-
"""Agent 工具注册表（兼容层）。

历史：本模块曾是工具的唯一真源（TOOLS = {name: {desc, args, fn}}）。
现在真源迁移到 backend/app/registry/，本模块只做两件事：
  1) 用 registry.legacy_view() 生成与旧结构完全一致的 TOOLS，
     保证 agent.py 的 _call_tool（TOOLS[name]["fn"]）与 agent_status（sorted(TOOLS)）不用改；
  2) tool_specs_for_llm() 委托 registry 输出**真正的 JSON Schema**
     （旧实现把所有参数都声明成 {"type": "string"}，导致 LLM 把 seed/breakdown 传成字符串）。

新增工具请去 backend/app/registry/skills/ 下定义，不要在这里加。
"""
from backend.app.registry import legacy_view, to_openai_tools
from backend.app.registry.skills.cases import tool_get_mock_data, tool_list_cases  # noqa: F401
from backend.app.registry.skills.sim import tool_run_sim  # noqa: F401
from backend.app.registry.skills.solving import tool_run_solve  # noqa: F401
from backend.app.registry.skills.workflow import (  # noqa: F401
    tool_list_workflows,
    tool_run_workflow,
)

# 兼容视图：结构与旧 TOOLS 完全一致
TOOLS = legacy_view()


def tool_specs_for_llm():
    """生成 OpenAI function-calling 的 tools 声明（来自注册表的真 JSON Schema）。"""
    return to_openai_tools()
