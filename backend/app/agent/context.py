# -*- coding: utf-8 -*-
"""上下文工程：token 估算 + 预算压缩 + 滚动摘要。

解决 agent.py 里的两处硬截断：
    messages[-20:]   —— 按条数截，一条长工具结果就能撑爆上下文
    str(result)[:2000] —— 按字符截，中文下不足 2000 token 却切掉了关键数字

零依赖实现，不引入 tiktoken（要下模型文件、体积大、Render 免费层放不下）。
"""
import os

DEFAULT_BUDGET = int(os.getenv("AGENT_CONTEXT_BUDGET", "6000"))
DEFAULT_KEEP_TURNS = int(os.getenv("AGENT_KEEP_TURNS", "4"))
DEFAULT_SUMMARY_MAX = int(os.getenv("AGENT_SUMMARY_MAX", "200"))

# 每条消息的协议开销（role / 分隔符等），经验值
_PER_MESSAGE_OVERHEAD = 4

_CJK_MIN, _CJK_MAX = "\u4e00", "\u9fff"


def estimate_tokens(text) -> int:
    """估算 token 数。

    规则：CJK 与其全角标点按 1 token/字，其余按 3.5 字符/token。
    误差约 ±30%，对「预算闸门」这种用途完全够用，且零依赖、零 IO。
    """
    s = str(text or "")
    if not s:
        return 0
    cjk = sum(1 for c in s if _CJK_MIN <= c <= _CJK_MAX)
    return int(cjk + (len(s) - cjk) / 3.5)


def count_tokens(messages) -> int:
    return sum(estimate_tokens(m.get("content")) + _PER_MESSAGE_OVERHEAD
               for m in (messages or []))


def _clip(text, limit: int) -> str:
    s = str(text or "")
    return s if len(s) <= limit else s[:limit] + "…"


def merge_summary(summary: str, dropped, summary_max: int = DEFAULT_SUMMARY_MAX) -> str:
    """把被丢弃的对话压进摘要。

    不做 LLM 摘要（会产生额外调用与不确定行为），改为「取每条前 30 字拼接 + 硬截断」。
    信息量有限但确定、可测、零成本；后续可替换为 LLM 摘要。
    """
    parts = []
    if summary:
        parts.append(summary)
    for m in dropped:
        role = m.get("role")
        if role == "tool":
            continue                       # 工具结果不进摘要，噪音太大
        content = str(m.get("content") or "").strip().replace("\n", " ")
        if content:
            parts.append(f"{'用户' if role == 'user' else '助手'}: {_clip(content, 30)}")
    merged = "；".join(parts)
    if len(merged) <= summary_max:
        return merged
    # 超长时保留尾部（越新的信息越重要）
    return "…" + merged[-summary_max:] if summary_max > 1 else ""


def _shrink_tool(msg, limit: int = 400) -> dict:
    """把过长的 tool 消息压成「摘要标记 + 前 N 字」。"""
    content = str(msg.get("content") or "")
    if estimate_tokens(content) <= limit:
        return msg
    return {**msg, "content": _clip(content, limit * 2) + " …[已压缩]"}


def compress(messages, budget=None, keep_turns=None, summary=None,
             summary_max=None) -> tuple[list, str]:
    """按 token 预算压缩消息序列。

    六步（顺序执行，命中即停）：
      1. system 消息常驻
      2. 摘要作为一条 system 消息附加
      3. 只保留最近 keep_turns 轮（user+assistant 成对）
      4. 超预算 → 从最旧对话对丢弃，每丢一段写回摘要
      5. 仍超 → tool 消息压成前 800 字
      6. 仍超 → 逐条截断 content 直到进预算

    Returns: (压缩后的消息列表, 最新摘要)
    """
    budget = budget or DEFAULT_BUDGET
    keep_turns = keep_turns or DEFAULT_KEEP_TURNS
    summary_max = summary_max or DEFAULT_SUMMARY_MAX

    messages = list(messages or [])
    systems = [m for m in messages if m.get("role") == "system"]
    dialog = [m for m in messages if m.get("role") != "system"]

    # 第 3 步：按轮次保留
    keep_n = max(keep_turns * 2, 2)
    if len(dialog) > keep_n:
        dropped, dialog = dialog[:-keep_n], dialog[-keep_n:]
        summary = merge_summary(summary or "", dropped, summary_max)

    def _build():
        out = list(systems)
        if summary:
            out.append({"role": "system", "content": f"[历史摘要] {summary}"})
        out.extend(dialog)
        return out

    result = _build()
    if count_tokens(result) <= budget:
        return result, summary or ""

    # 第 5 步：压缩 tool 消息
    dialog = [_shrink_tool(m) for m in dialog]
    result = _build()
    if count_tokens(result) <= budget:
        return result, summary or ""

    # 第 6 步：逐条等比截断 content
    total = count_tokens(result) or 1
    ratio = max(budget / total, 0.15)
    dialog = [{**m, "content": _clip(m.get("content"), max(int(len(str(m.get("content") or "")) * ratio), 80))}
              for m in dialog]
    result = _build()

    # 极端情况：仍超预算 → 继续丢最旧的 user 消息（tool 结果属于当前轮，必须保留）
    while count_tokens(result) > budget and len(dialog) > 2:
        idx = next((i for i, m in enumerate(dialog[:-1]) if m.get("role") == "user"), None)
        if idx is None:
            idx = 0
        dropped = [dialog[idx]]
        dialog = dialog[:idx] + dialog[idx + 1:]
        summary = merge_summary(summary or "", dropped, summary_max)
        result = _build()
    return result, summary or ""


__all__ = [
    "estimate_tokens", "count_tokens", "compress", "merge_summary", "_shrink_tool",
    "DEFAULT_BUDGET", "DEFAULT_KEEP_TURNS", "DEFAULT_SUMMARY_MAX",
]
