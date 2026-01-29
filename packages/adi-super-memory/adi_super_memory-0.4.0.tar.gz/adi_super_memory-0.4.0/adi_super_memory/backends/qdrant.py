from datetime import datetime
from typing import List, Optional
from .base import Backend
from ..types import MemoryItem

class QdrantBackend(Backend):
    def __init__(self, url: str="http://localhost:6333", collection: str="adi_super_memory", dim: int=256, api_key: Optional[str]=None):
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.http.models import Distance, VectorParams
        except Exception as e:
            raise RuntimeError("Install qdrant extras: pip install 'adi-super-memory[qdrant]'") from e
        self.client = QdrantClient(url=url, api_key=api_key)
        self.collection=collection
        self.dim=dim
        cols=self.client.get_collections().collections
        if not any(c.name==collection for c in cols):
            self.client.create_collection(collection_name=collection, vectors_config=VectorParams(size=dim, distance=Distance.COSINE))

    def upsert(self, item: MemoryItem, embedding: List[float]) -> None:
        payload={
            "tenant":item.tenant,"kind":item.kind,"actor":item.actor,"title":item.title,"text":item.text,
            "tags":item.tags,"metadata":item.metadata,"score":float(item.score),"namespace":item.namespace,
            "created_at":item.created_at.isoformat(),"updated_at":item.updated_at.isoformat()
        }
        self.client.upsert(collection_name=self.collection, points=[{"id": item.id, "vector": embedding, "payload": payload}])

    def get(self, item_id: str):
        pts=self.client.retrieve(collection_name=self.collection, ids=[item_id], with_payload=True, with_vectors=True)
        if not pts: return None
        p=pts[0]
        return self._payload_to_item(p.payload, item_id), list(p.vector)

    def delete(self, item_id: str) -> None:
        self.client.delete(collection_name=self.collection, points_selector={"points":[item_id]})

    def iter_items(self, tenant: str, kinds: Optional[List[str]] = None):
        flt={"must":[{"key":"tenant","match":{"value":tenant}}]}
        if kinds:
            flt["must"].append({"key":"kind","match":{"any":kinds}})
        offset=None
        while True:
            pts, offset = self.client.scroll(collection_name=self.collection, scroll_filter=flt, limit=128, offset=offset, with_payload=True, with_vectors=True)
            for p in pts:
                yield self._payload_to_item(p.payload, str(p.id)), list(p.vector)
            if offset is None or len(pts)==0:
                break

    def search(self, tenant: str, query_vector: List[float], top_k: int = 8, kinds: Optional[List[str]] = None):
        flt={"must":[{"key":"tenant","match":{"value":tenant}}]}
        if kinds:
            flt["must"].append({"key":"kind","match":{"any":kinds}})
        res=self.client.search(collection_name=self.collection, query_vector=query_vector, limit=top_k, query_filter=flt, with_payload=True)
        out=[]
        for r in res:
            out.append((self._payload_to_item(r.payload, str(r.id)), float(r.score)))
        return out

    def _payload_to_item(self, payload, item_id: str):
        return MemoryItem(
            id=item_id,
            tenant=payload["tenant"],
            kind=payload["kind"],
            actor=payload["actor"],
            title=payload["title"],
            text=payload["text"],
            tags=list(payload.get("tags") or []),
            metadata=dict(payload.get("metadata") or {}),
            score=float(payload.get("score") or 0.0),
            namespace=payload.get("namespace") or "default",
            created_at=datetime.fromisoformat(payload["created_at"]),
            updated_at=datetime.fromisoformat(payload["updated_at"]),
        )
