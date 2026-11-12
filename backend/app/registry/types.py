# -*- coding: utf-8 -*-
"""技能（Skill）类型定义。

一个 Skill = 能力声明 + 执行句柄，是 MCP / OpenAI function calling / 前端能力面板
三端的唯一真源。
"""
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass(frozen=True)
class Skill:
    """单个可被 Agent 调用的能力。

    字段约定（改名前先看 core.legacy_view 与 tests/test_agent.py）：
      - name 必须与旧 TOOLS 的 key 完全一致，否则 agent.py 的工具路由会失效
      - input_schema 是 JSON Schema draft-07 子集（见 validate.py 支持的子集）
    """

    name: str
    title: str
    category: str            # data | solve | sim | workflow | analytics | agent | knowledge
    description: str         # 给 LLM 看的能力说明（含调用时机）
    input_schema: dict
    handler: Callable[..., dict]
    output_schema: dict | None = None
    examples: tuple = ()     # ({"input": {...}, "note": "..."},)
    tags: tuple = ()
    risk: str = "compute"    # read | compute | write
    timeout_s: int = 120
    max_result_chars: int = 2000
    version: str = "1.0.0"
    args_doc: dict = field(default_factory=dict)   # 兼容旧 TOOLS 的 args 描述

    # ---- 派生视图 ----
    def to_openai_tool(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.input_schema,
            },
        }

    def to_mcp_tool(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema,
        }

    def to_panel(self) -> dict:
        return {
            "name": self.name,
            "title": self.title,
            "category": self.category,
            "description": self.description,
            "risk": self.risk,
            "input_schema": self.input_schema,
            "examples": list(self.examples),
            "tags": list(self.tags),
            "version": self.version,
        }


@dataclass(frozen=True)
class Goal:
    """Loop Engineering 的目标（阶段四使用，此处先定义避免后续改动面扩散）。"""

    kind: str                # urgent_deadline | makespan_le | on_time_ge | freeform
    params: dict
    text: str = ""

    def __repr__(self) -> str:
        return f"Goal({self.kind}, {self.params})"


__all__ = ["Skill", "Goal"]
