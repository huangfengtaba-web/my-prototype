# -*- coding: utf-8 -*-
"""运行记录持久化（可选）：SUPABASE_DB_URL 设置时写 Postgres（Supabase），否则内存模式。

设计：persist 永不抛出（失败仅打日志），保证 API 主链路不受数据库影响。
写入三张表：solve_runs（运行头）/ solve_lots（逐 Lot 明细）/ solve_errors（错误）。
建表 SQL 见 docs/11_VSCODE_DEPLOY_SUPABASE.md §5。
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
                # 1) 运行头
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
                # 2) 逐 Lot 明细（重跑同 run_id 先清再插）
                cur.execute("delete from solve_lots where run_id = %s", (record["run_id"],))
                for r in summary.get("schedule") or []:
                    cur.execute(
                        """insert into solve_lots
                           (run_id, lot_id, eqp, eqp_group, reticle, priority, temp,
                            start_time, end_time, barc_er, barc_lr, post_note)
                           values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                        (record["run_id"], r.get("lot"), r.get("eqp"), r.get("eqp_group"),
                         r.get("reticle"), r.get("priority"), r.get("temp"),
                         r.get("start"), r.get("end"), r.get("barc_er"),
                         r.get("barc_lr"), r.get("post_note")),
                    )
                # 3) 错误记录
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
