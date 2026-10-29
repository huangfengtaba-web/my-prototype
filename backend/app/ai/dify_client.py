# -*- coding: utf-8 -*-
"""Dify 线上工作流客户端。配置缺失/不可达抛 DifyUnavailable，由上层降级。

铁律（docs/09_FUSION_PLAN.md §P2）：
- 不做本地 Dify 部署（无 docker/、无镜像）；Dify 由用户线上搭建
- App Key 只能后端读环境变量，禁止出现在任何前端代码
- blocking 模式 timeout=90s（Cloudflare 100s 上限留余量）
"""
import os
import time

import httpx

DIFY_BASE = os.getenv("DIFY_BASE", "").rstrip("/")
_KEYS = {
    "daily_scheduling": os.getenv("DIFY_KEY_DAILY_SCHEDULING", ""),
    "scenario_compare": os.getenv("DIFY_KEY_SCENARIO_COMPARE", ""),
    "qa_chatflow":      os.getenv("DIFY_KEY_QA_CHATFLOW", ""),
}


class DifyUnavailable(RuntimeError):
    pass


def configured(wf_key: str) -> bool:
    return bool(DIFY_BASE) and bool(_KEYS.get(wf_key))


def is_available(wf_key: str, timeout: float = 3.0) -> bool:
    if not configured(wf_key):
        return False
    try:
        r = httpx.get(f"{DIFY_BASE}/parameters",
                      headers={"Authorization": f"Bearer {_KEYS[wf_key]}"},
                      timeout=timeout)
        return r.status_code == 200
    except Exception:
        return False


def run_workflow(wf_key: str, inputs: dict, user: str = "gtx-demo-001", timeout: int = 90) -> dict:
    if not configured(wf_key):
        raise DifyUnavailable(f"{wf_key} 未配置")
    t0 = time.time()
    try:
        r = httpx.post(f"{DIFY_BASE}/workflows/run",
                       headers={"Authorization": f"Bearer {_KEYS[wf_key]}",
                                "Content-Type": "application/json"},
                       json={"inputs": inputs, "response_mode": "blocking", "user": user},
                       timeout=timeout)
    except Exception as e:
        raise DifyUnavailable(f"Dify 请求失败: {e!r}") from e
    if r.status_code != 200:
        raise DifyUnavailable(f"Dify HTTP {r.status_code}: {r.text[:200]}")
    body = r.json()
    data = body.get("data") or {}
    return {"mode": "dify",
            "workflow_run_id": body.get("workflow_run_id") or data.get("id"),
            "status": data.get("status"),
            "outputs": data.get("outputs") or {},
            "elapsed": round(time.time() - t0, 2),
            "total_steps": data.get("total_steps")}
