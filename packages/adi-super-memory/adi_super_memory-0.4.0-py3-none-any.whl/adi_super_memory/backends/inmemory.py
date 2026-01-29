from typing import Dict, Iterable, List, Optional, Tuple
import threading
from .base import Backend
from ..types import MemoryItem

class InMemoryBackend(Backend):
    def __init__(self):
        self._lock=threading.RLock()
        self._store: Dict[str, Tuple[MemoryItem, List[float]]] = {}
    def upsert(self, item: MemoryItem, embedding: List[float]) -> None:
        with self._lock:
            self._store[item.id]=(item, embedding)
    def get(self, item_id: str):
        with self._lock:
            return self._store.get(item_id)
    def delete(self, item_id: str) -> None:
        with self._lock:
            self._store.pop(item_id, None)
    def iter_items(self, tenant: str, kinds: Optional[List[str]] = None):
        with self._lock:
            for item, emb in self._store.values():
                if item.tenant != tenant: continue
                if kinds and item.kind not in kinds: continue
                yield item, emb
