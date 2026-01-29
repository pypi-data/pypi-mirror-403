from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
import uuid, hashlib, json

from .stm import MessageSTM
from .policy import MemoryPolicy
from .embeddings import HashEmbeddingProvider, EmbeddingProvider
from .backends import Backend, InMemoryBackend
from .types import MemoryItem
from .retrieval import cosine, recency_weight
from .distillers import Distiller, DeterministicDistiller
from .safety.modes import EnterpriseSafetyMode, SafetyMode

@dataclass
class SuperMemory:
    backend: Backend = InMemoryBackend()
    policy: MemoryPolicy = MemoryPolicy.default()
    embedder: EmbeddingProvider = HashEmbeddingProvider()
    tenant: str = "default"
    safety: SafetyMode = EnterpriseSafetyMode.default()

    def __post_init__(self):
        self.stm = MessageSTM()
        self._distiller: Distiller = DeterministicDistiller()
        self._audit_last = "0"*64
        self._items: Dict[str, MemoryItem] = {}
        self._emb: Dict[str, List[float]] = {}

    def set_distiller(self, distiller: Distiller):
        self._distiller = distiller

    def _audit(self, action: str, item_id: str):
        body = json.dumps({"t": self.tenant, "a": action, "id": item_id, "prev": self._audit_last}, sort_keys=True).encode("utf-8")
        self._audit_last = hashlib.sha256(body).hexdigest()

    def audit_last_hash(self) -> str:
        return self._audit_last

    def add_event(self, actor: str, subkind: str, text: str, tags: Optional[List[str]] = None, score: float = 0.0):
        return self._add("event", actor, subkind.capitalize(), text, tags or [], score, {"subkind": subkind})

    def add_knowledge(self, namespace: str, title: str, content: str, tags: Optional[List[str]] = None):
        return self._add("knowledge", "system", title, content, tags or [], 0.0, {"namespace": namespace})

    def add_super(self, title: str, text: str, tags: Optional[List[str]] = None, score: float = 0.0):
        return self._add("super", "system", title, text, tags or [], score, {})

    def _add(self, kind: str, actor: str, title: str, text: str, tags: List[str], score: float, md: Dict[str,str]):
        now = datetime.now(timezone.utc)
        title = self.safety.redaction(title)
        text = self.safety.redaction(text)
        item = MemoryItem(id=str(uuid.uuid4()), created_at=now, kind=kind, actor=actor, title=title, text=text, tags=tags, metadata=md, score=float(score), tenant=self.tenant)
        emb = self.embedder.embed([title + "\n" + text + "\n" + " ".join(tags)])[0]
        self.backend.upsert(item, emb)
        self._audit(f"upsert:{kind}", item.id)
        return item

    def recall(self, query: str, top_k: int = 8, kinds: Optional[List[str]] = None):
        kinds = kinds or ["event","knowledge","super"]
        qemb = self.embedder.embed([query])[0]
        scored=[]
        for item, emb in self.backend.iter_items(self.tenant, kinds=kinds):
            sim = cosine(qemb, emb)
            rec = recency_weight(item.created_at, self.policy.recency_half_life_days)
            scored.append((0.7*sim+0.2*rec+0.1*float(item.score), item))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [i for _, i in scored[:top_k]]

    def distill(self, window_days: int = 30):
        cutoff = datetime.now(timezone.utc) - timedelta(days=window_days)
        events=[]
        for item, _ in self.backend.iter_items(self.tenant, kinds=["event"]):
            if item.created_at >= cutoff and (item.score >= self.policy.distill_min_score or item.metadata.get("subkind") == "outcome"):
                events.append(item)
        distilled = self._distiller.distill(events)
        created=[]
        for d in distilled:
            created.append(self.add_super(d.get("title","Wisdom"), d.get("text",""), [d.get("tag","wisdom")], float(d.get("avg_score",0) or 0.0)).id)
        return {"source_events": len(events), "created_super_memories": len(created), "super_memory_ids": created}
