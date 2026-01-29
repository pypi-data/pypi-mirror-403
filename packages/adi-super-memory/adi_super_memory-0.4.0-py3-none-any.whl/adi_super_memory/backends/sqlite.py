from typing import Iterable, List, Optional, Tuple
import sqlite3, os, json, threading
from datetime import datetime
from .base import Backend
from ..types import MemoryItem

class SQLiteBackend(Backend):
    def __init__(self, path: str = "adi_super_memory.sqlite3"):
        self.path=path
        self._lock=threading.RLock()
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        self._conn=sqlite3.connect(path, check_same_thread=False)
        self._conn.execute("""CREATE TABLE IF NOT EXISTS memory(
            id TEXT PRIMARY KEY,
            tenant TEXT, kind TEXT, actor TEXT, title TEXT, text TEXT,
            tags_json TEXT, metadata_json TEXT, score REAL, namespace TEXT,
            created_at TEXT, updated_at TEXT, embedding_json TEXT
        )""")
        self._conn.execute("CREATE INDEX IF NOT EXISTS idx_mem_tenant_kind ON memory(tenant, kind)")
        self._conn.commit()
    def upsert(self, item: MemoryItem, embedding: List[float]) -> None:
        with self._lock:
            self._conn.execute("""
            INSERT INTO memory VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(id) DO UPDATE SET
              tenant=excluded.tenant, kind=excluded.kind, actor=excluded.actor, title=excluded.title, text=excluded.text,
              tags_json=excluded.tags_json, metadata_json=excluded.metadata_json, score=excluded.score, namespace=excluded.namespace,
              created_at=excluded.created_at, updated_at=excluded.updated_at, embedding_json=excluded.embedding_json
            """, (
                item.id, item.tenant, item.kind, item.actor, item.title, item.text,
                json.dumps(item.tags), json.dumps(item.metadata), float(item.score), item.namespace,
                item.created_at.isoformat(), item.updated_at.isoformat(), json.dumps(embedding)
            ))
            self._conn.commit()
    def get(self, item_id: str):
        with self._lock:
            cur=self._conn.execute("SELECT * FROM memory WHERE id=?", (item_id,))
            row=cur.fetchone()
        if not row: return None
        return self._row(row)
    def delete(self, item_id: str) -> None:
        with self._lock:
            self._conn.execute("DELETE FROM memory WHERE id=?", (item_id,))
            self._conn.commit()
    def iter_items(self, tenant: str, kinds: Optional[List[str]] = None):
        with self._lock:
            if kinds:
                q=",".join(["?"]*len(kinds))
                cur=self._conn.execute(f"SELECT * FROM memory WHERE tenant=? AND kind IN ({q})", (tenant, *kinds))
            else:
                cur=self._conn.execute("SELECT * FROM memory WHERE tenant=?", (tenant,))
            rows=cur.fetchall()
        for r in rows:
            yield self._row(r)
    def _row(self, row):
        (id_, tenant, kind, actor, title, text, tags_json, metadata_json, score, namespace, created_at, updated_at, embedding_json)=row
        item=MemoryItem(
            id=id_, tenant=tenant, kind=kind, actor=actor, title=title, text=text,
            tags=json.loads(tags_json), metadata=json.loads(metadata_json), score=float(score), namespace=namespace,
            created_at=datetime.fromisoformat(created_at), updated_at=datetime.fromisoformat(updated_at)
        )
        return item, json.loads(embedding_json)
