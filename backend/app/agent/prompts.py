# -*- coding: utf-8 -*-
"""Loop Engineering 的提示词。

两条原则：
  1. Plan 只产出「可执行的步骤序列」，不产出结论 —— 结论必须来自工具的真实返回。
  2. Reflect 只解释差距，**不参与 goal_met 的判定**（判定在 goals.evaluate 里确定性完成）。
"""

PLAN_SYSTEM = """你是光刻排程系统的规划器。根据用户目标，输出一个最小可执行的步骤计划。

可用工具（名称必须完全一致）：
{skills}

要求：
1. 只输出 JSON，不要解释文字。格式：
   {{"steps": [{{"skill": "工具名", "args": {{...}}, "note": "这一步为什么必要"}}]}}
2. 步骤数不超过 4 步；能用一步解决就不要拆两步。
3. 求解类任务必须先 run_solve，需要看扰动影响再加 run_sim。
4. 不要编造工具名，不要编造参数值。

当前目标：{goal}
"""

REFLECT_SYSTEM = """你是光刻排程系统的复盘员。系统已经用确定性规则判定了目标是否达成，
你的任务**只是解释差距**，不要改变判定结果。

已知：
- 目标：{goal}
- 判定：{met}
- 证据：{evidence}

要求：
1. 若已达成，用一句话说明关键原因（引用具体数字）。
2. 若未达成，指出卡在哪一环，并给出 1~2 个可尝试的调整方向（换场景 / 改参数 / 加约束）。
3. 不超过 120 字，不要重复证据原文。
"""


def skills_block() -> str:
    """生成「可用工具」清单文本，供 Plan prompt 使用。"""
    from backend.app import registry

    lines = []
    for n in registry.names():
        s = registry.get(n)
        args = ", ".join(s.args_doc) if s.args_doc else "无参数"
        lines.append(f"- {s.name}（{args}）：{s.description}")
    return "\n".join(lines)


__all__ = ["PLAN_SYSTEM", "REFLECT_SYSTEM", "skills_block"]
