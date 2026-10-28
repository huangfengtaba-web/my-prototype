# -*- coding: utf-8 -*-
"""LLM 客户端：OpenAI 兼容 /chat/completions（含 function calling）。

环境变量（不配置则 Agent 走规则模式，见 agent.py）：
    LLM_API_BASE   如 https://api.openai.com/v1 或任意兼容网关
    LLM_API_KEY    sk-...
    LLM_MODEL      模型名，如 gpt-4o-mini / glm-4-flash / qwen-plus
"""
import json
import os
import urllib.error
import urllib.request


class LLMError(RuntimeError):
    pass


def llm_config():
    base = os.getenv("LLM_API_BASE", "").rstrip("/")
    key = os.getenv("LLM_API_KEY", "")
    model = os.getenv("LLM_MODEL", "gpt-4o-mini")
    enabled = bool(base and key)
    return {"enabled": enabled, "base": base, "key": key, "model": model}


def chat(messages, tools=None, timeout=60):
    """调用 OpenAI 兼容接口，返回首个 choice 的 message dict（可能含 tool_calls）。"""
    cfg = llm_config()
    if not cfg["enabled"]:
        raise LLMError("LLM 未配置（缺 LLM_API_BASE / LLM_API_KEY）")
    payload = {"model": cfg["model"], "messages": messages, "temperature": 0.2}
    if tools:
        payload["tools"] = tools
    req = urllib.request.Request(
        f"{cfg['base']}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {cfg['key']}"},
        method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
        raise LLMError(f"LLM 调用失败: {e}") from e
    return data["choices"][0]["message"]
