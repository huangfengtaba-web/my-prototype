# -*- coding: utf-8 -*-
"""技能注册表：全系统能力的唯一真源。

用法：
    from backend.app.registry import REGISTRY, get, to_openai_tools, to_mcp_tools

三端消费：
    OpenAI function calling → to_openai_tools()
    MCP server              → to_mcp_tools()
    前端能力面板             → to_panel()
"""
from backend.app.registry.types import Skill

REGISTRY: dict[str, Skill] = {}

# 分类展示顺序（前端面板按此排序）
CATEGORY_ORDER = ("data", "solve", "sim", "workflow", "analytics", "agent", "knowledge")
CATEGORY_TITLES = {
    "data": "数据查询",
    "solve": "求解",
    "sim": "仿真",
    "workflow": "工作流",
    "analytics": "分析",
    "agent": "Agent",
    "knowledge": "知识",
}


def register(skill: Skill) -> Skill:
    """注册一个技能。重名直接报错，避免静默覆盖。"""
    if skill.name in REGISTRY:
        raise ValueError(f"技能重名: {skill.name}")
    REGISTRY[skill.name] = skill
    return skill


def get(name: str) -> Skill | None:
    return REGISTRY.get(name)


def names() -> list[str]:
    return sorted(REGISTRY)


# ---------------------------------------------------------------- 三端视图
def to_openai_tools() -> list[dict]:
    """OpenAI function calling 声明。按名称排序保证输出稳定（便于测试与 diff）。"""
    return [REGISTRY[n].to_openai_tool() for n in names()]


def to_mcp_tools() -> list[dict]:
    """MCP tools/list 返回体。"""
    return [REGISTRY[n].to_mcp_tool() for n in names()]


def to_panel() -> list[dict]:
    """前端能力面板：按分类分组。"""
    grouped: dict[str, list[dict]] = {}
    for n in names():
        s = REGISTRY[n]
        grouped.setdefault(s.category, []).append(s.to_panel())
    ordered = [c for c in CATEGORY_ORDER if c in grouped]
    ordered += [c for c in grouped if c not in CATEGORY_ORDER]
    return [{
        "category": c,
        "title": CATEGORY_TITLES.get(c, c),
        "skills": grouped[c],
    } for c in ordered]


def system_prompt_fragment() -> str:
    """生成系统提示里的「可用能力」段落（替代原先手写的 7 个工具名列表）。"""
    lines = ["可用能力（只能调用下列名称，禁止编造）："]
    for n in names():
        s = REGISTRY[n]
        args = ", ".join(s.args_doc) if s.args_doc else "无参数"
        lines.append(f"- {s.name}（{s.title}｜{args}）：{s.description}")
    return "\n".join(lines)


# ---------------------------------------------------------------- 兼容层
def legacy_view() -> dict:
    """生成与旧 TOOLS 结构完全一致的 dict，供未迁移的调用方使用。

    旧结构：{"list_cases": {"desc": str, "args": {k: str}, "fn": callable}, ...}
    保留原因：agent.py 的 _call_tool 用 TOOLS[name]["fn"]，agent_status 用 sorted(TOOLS)。
    """
    return {
        n: {
            "desc": REGISTRY[n].description,
            "args": dict(REGISTRY[n].args_doc),
            "fn": REGISTRY[n].handler,
        }
        for n in names()
    }


__all__ = [
    "REGISTRY", "CATEGORY_ORDER", "CATEGORY_TITLES",
    "register", "get", "names",
    "to_openai_tools", "to_mcp_tools", "to_panel", "system_prompt_fragment",
    "legacy_view",
]
