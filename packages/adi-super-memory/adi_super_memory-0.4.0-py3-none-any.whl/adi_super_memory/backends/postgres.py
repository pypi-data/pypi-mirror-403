import json
from datetime import datetime
from typing import List, Optional
from .base import Backend
from ..types import MemoryItem

class PostgresBackend(Backend):
    def __init__(self, dsn: str):
        try:
            import psycopg
        except Exception as e:
            raise RuntimeError("Install postgres extras: pip install 'adi-super-memory[postgres]'") from e
        self._conn = psycopg.connect(dsn)
        self._conn.execute("""
        CREATE TABLE IF NOT EXISTS memory(
            id TEXT PRIMARY KEY,
            tenant TEXT NOT NULL,
            kind TEXT NOT NULL,
            actor TEXT NOT NULL,
            title TEXT NOT NULL,
            text TEXT NOT NULL,
            tags JSONB NOT NULL,
            metadata JSONB NOT NULL,
            score DOUBLE PRECISION NOT NULL,
            namespace TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL,
            updated_at TIMESTAMPTZ NOT NULL,
            embedding JSONB NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_mem_tenant_kind ON memory(tenant, kind);
        """)
        self._conn.commit()

    def upsert(self, item: MemoryItem, embedding: List[float]) -> None:
        with self._conn.cursor() as cur:
            cur.execute("""
            INSERT INTO memory(id,tenant,kind,actor,title,text,tags,metadata,score,namespace,created_at,updated_at,embedding)
            VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT(id) DO UPDATE SET
              tenant=EXCLUDED.tenant, kind=EXCLUDED.kind, actor=EXCLUDED.actor, title=EXCLUDED.title, text=EXCLUDED.text,
              tags=EXCLUDED.tags, metadata=EXCLUDED.metadata, score=EXCLUDED.score, namespace=EXCLUDED.namespace,
              created_at=EXCLUDED.created_at, updated_at=EXCLUDED.updated_at, embedding=EXCLUDED.embedding
            """, (
                item.id, item.tenant, item.kind, item.actor, item.title, item.text,
                json.dumps(item.tags), json.dumps(item.metadata), float(item.score), item.namespace,
                item.created_at, item.updated_at, json.dumps(embedding)
            ))
        self._conn.commit()

    def get(self, item_id: str):
        with self._conn.cursor() as cur:
            cur.execute("SELECT * FROM memory WHERE id=%s", (item_id,))
            row=cur.fetchone()
        if not row: return None
        return self._row(row)

    def delete(self, item_id: str) -> None:
        with self._conn.cursor() as cur:
            cur.execute("DELETE FROM memory WHERE id=%s", (item_id,))
        self._conn.commit()

    def iter_items(self, tenant: str, kinds: Optional[List[str]] = None):
        with self._conn.cursor() as cur:
            if kinds:
                cur.execute("SELECT * FROM memory WHERE tenant=%s AND kind = ANY(%s)", (tenant, kinds))
            else:
                cur.execute("SELECT * FROM memory WHERE tenant=%s", (tenant,))
            rows=cur.fetchall()
        for r in rows:
            yield self._row(r)

    def _row(self, row):
        (id_, tenant, kind, actor, title, text, tags, metadata, score, namespace, created_at, updated_at, embedding)=row
        item=MemoryItem(
            id=id_, tenant=tenant, kind=kind, actor=actor, title=title, text=text,
            tags=list(tags), metadata=dict(metadata), score=float(score), namespace=namespace,
            created_at=created_at if isinstance(created_at, datetime) else datetime.fromisoformat(str(created_at)),
            updated_at=updated_at if isinstance(updated_at, datetime) else datetime.fromisoformat(str(updated_at)),
        )
        return item, list(embedding)
