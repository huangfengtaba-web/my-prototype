# -*- coding: utf-8 -*-
"""运行记录持久化（可选）：SUPABASE_DB_URL 设置时写 Postgres（Supabase），否则内存模式。

设计：persist 永不抛出（失败仅打日志），保证 API 主链路不受数据库影响。
建表 SQL 见 docs/11_VSCODE_DEPLOY_SUPABASE.md §4.1。
"""
import json
import os

_URL = os.getenv("SUPABASE_DB_URL", "")


def enabled() -> bool:
    return bool(_URL)


def persist_run(record: dict):
    if not _URL:
        return
    try:
        import psycopg2

        summary = record.get("summary") or {}
        conn = psycopg2.connect(_URL, connect_timeout=8)
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """insert into solve_runs
                       (run_id, case_name, status, started_at, finished_at, milp, summary)
                       values (%s,%s,%s,%s,%s,%s,%s)
                       on conflict (run_id) do update set status=excluded.status,
                         finished_at=excluded.finished_at, summary=excluded.summary""",
                    (record["run_id"], record.get("case"), record.get("status"),
                     record.get("started_at"), record.get("finished_at"),
                     json.dumps(summary.get("milp_status") or {}),
                     json.dumps(summary, ensure_ascii=False, default=str)),
                )
                if record.get("status") in ("failed", "timeout", "suboptimal"):
                    cur.execute(
                        """insert into solve_errors
                           (run_id, error_type, error_info, detail)
                           values (%s,%s,%s,%s)""",
                        (record["run_id"], "MODEL_ERROR",
                         f"求解状态 {record.get('status')}", str(record.get("error"))[:500]),
                    )
            conn.commit()
        finally:
            conn.close()
    except Exception as e:                        # noqa: BLE001
        print(f"[store] Supabase 持久化失败（不影响 API）: {e!r}")
