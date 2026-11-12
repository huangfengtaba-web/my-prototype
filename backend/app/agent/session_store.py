# -*- coding: utf-8 -*-
"""会话持久化：三级存储，写穿缓存。

背景：agent.SESSIONS 是纯内存 dict，服务一重启会话全丢（Render 免费层还会休眠）。
本模块提供三级实现，按环境自动选择：

    PgStore     有 SUPABASE_DB_URL          → 跨重启、跨实例
    JsonlStore  本地开发、无 DB              → 单机持久化
    MemoryStore RENDER 环境 / 显式指定       → 退化为纯内存（与旧行为一致）

强制指定：AGENT_SESSION_STORE=pg|jsonl|memory
"""
import json
import os
import threading
import time

_LOCK = threading.Lock()


class MemoryStore:
    """纯内存。等价于改造前的行为，作为 Render 与兜底实现。"""

    name = "memory"

    def __init__(self):
        self._data: dict[str, dict] = {}

    def load(self, sid: str):
        return self._data.get(sid)

    def save(self, sid: str, session: dict) -> None:
        with _LOCK:
            self._data[sid] = json.loads(json.dumps(session, ensure_ascii=False, default=str))

    def list(self, limit: int = 20):
        return list(self._data)[-limit:]


class JsonlStore:
    """一行一次全量快照，追加写。简单、可 tail、可人工排查。"""

    name = "jsonl"

    def __init__(self, root: str | None = None):
        self.root = root or os.getenv("AGENT_SESSION_DIR", ".runtime/agent_sessions")
        os.makedirs(self.root, exist_ok=True)

    def _path(self, sid: str) -> str:
        safe = "".join(c for c in sid if c.isalnum() or c in "-_")[:64] or "default"
        return os.path.join(self.root, f"{safe}.jsonl")

    def load(self, sid: str):
        path = self._path(sid)
        if not os.path.exists(path):
            return None
        last = None
        try:
            with open(path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        last = line
        except OSError:
            return None
        if not last:
            return None
        try:
            return json.loads(last).get("session")
        except (json.JSONDecodeError, AttributeError):
            return None

    def save(self, sid: str, session: dict) -> None:
        rec = {"sid": sid, "ts": int(time.time()),
               "session": json.loads(json.dumps(session, ensure_ascii=False, default=str))}
        try:
            with open(self._path(sid), "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        except OSError:
            pass                      # 持久化失败不能影响对话主链路

    def list(self, limit: int = 20):
        try:
            files = sorted(os.listdir(self.root),
                           key=lambda f: os.path.getmtime(os.path.join(self.root, f)),
                           reverse=True)
        except OSError:
            return []
        return [f[:-6] for f in files if f.endswith(".jsonl")][:limit]


class PgStore:
    """Supabase Postgres。表结构见 docs/11（已追加 DDL）。"""

    name = "pg"

    def __init__(self, dsn: str):
        self.dsn = dsn

    def _conn(self):
        import psycopg2
        return psycopg2.connect(self.dsn, connect_timeout=8)

    def load(self, sid: str):
        try:
            with self._conn() as conn, conn.cursor() as cur:
                cur.execute(
                    "select messages, summary, mode from agent_sessions where session_id=%s", (sid,))
                row = cur.fetchone()
            if not row:
                return None
            msgs, summary, mode = row
            if isinstance(msgs, str):
                msgs = json.loads(msgs)
            return {"messages": msgs or [], "summary": summary or "", "mode": mode}
        except Exception:             # noqa: BLE001  表不存在/网络问题都退化为无历史
            return None

    def save(self, sid: str, session: dict) -> None:
        try:
            with self._conn() as conn, conn.cursor() as cur:
                cur.execute(
                    """
                    insert into agent_sessions (session_id, messages, summary, mode, updated_at)
                    values (%s, %s, %s, %s, now())
                    on conflict (session_id) do update
                       set messages = excluded.messages,
                           summary  = excluded.summary,
                           mode     = excluded.mode,
                           updated_at = now()
                    """,
                    (sid,
                     json.dumps(session.get("messages") or [], ensure_ascii=False),
                     session.get("summary") or "",
                     session.get("mode")),
                )
        except Exception:             # noqa: BLE001
            pass

    def list(self, limit: int = 20):
        try:
            with self._conn() as conn, conn.cursor() as cur:
                cur.execute("select session_id from agent_sessions "
                            "order by updated_at desc limit %s", (limit,))
                return [r[0] for r in cur.fetchall()]
        except Exception:             # noqa: BLE001
            return []


_STORE = None


def get_store():
    """按环境选择存储实现（单例）。"""
    global _STORE
    if _STORE is not None:
        return _STORE

    forced = (os.getenv("AGENT_SESSION_STORE") or "auto").strip().lower()
    dsn = (os.getenv("SUPABASE_DB_URL") or "").strip()

    if forced == "memory" or (forced == "auto" and os.getenv("RENDER")):
        _STORE = MemoryStore()
    elif forced == "jsonl":
        _STORE = JsonlStore()
    elif forced == "pg":
        _STORE = PgStore(dsn) if dsn else MemoryStore()
    elif dsn:
        _STORE = PgStore(dsn)
    else:
        _STORE = JsonlStore()
    return _STORE


def reset_store(store=None) -> None:
    """测试用：替换/清空单例。"""
    global _STORE
    _STORE = store


__all__ = ["MemoryStore", "JsonlStore", "PgStore", "get_store", "reset_store"]
