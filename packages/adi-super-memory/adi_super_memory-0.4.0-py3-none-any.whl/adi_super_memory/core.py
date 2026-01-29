from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
import uuid

from .types import MemoryItem
from .stm import MessageSTM
from .policy.memory_policy import MemoryPolicy
from .embeddings import HashEmbeddingProvider
from .retrieval import cosine, recency_weight
from .audit import HashChainedAuditLog
from .safety.modes import EnterpriseSafetyMode
from .policy.tool_policy import ToolPolicy, ToolCall
from .distillers.deterministic import DeterministicDistiller
from .backends.inmemory import InMemoryBackend

@dataclass
class SuperMemory:
    backend: object = InMemoryBackend()
    policy: MemoryPolicy = MemoryPolicy.default()
    embedder: object = HashEmbeddingProvider()
    tenant: str = "default"
    safety: object = EnterpriseSafetyMode.default()
    tool_policy: ToolPolicy = ToolPolicy()

    def __post_init__(self):
        self.stm = MessageSTM()
        self._distiller = DeterministicDistiller()
        self._audit = HashChainedAuditLog()

    def set_distiller(self, distiller):
        self._distiller = distiller

    def _redact(self, s: str) -> str:
        if getattr(self.policy, "redaction", None): s = self.policy.redaction(s)
        if getattr(self.safety, "redaction", None): s = self.safety.redaction(s)
        return s

    def _embed_text(self, item: MemoryItem) -> str:
        return f"{item.title}\n{item.text}\nTAGS:{' '.join(item.tags)}\nNS:{item.namespace}\nKIND:{item.kind}"

    def _upsert(self, item: MemoryItem, emb: List[float]):
        self.backend.upsert(item, emb)
        if getattr(self.safety, "require_signed_audit", False):
            self._audit.append(self.tenant, f"upsert:{item.kind}", item.id, {"actor": item.actor, "namespace": item.namespace})

    def add_event(self, actor: str, subkind: str, text: str, title: Optional[str]=None, tags: Optional[List[str]]=None, score: float=0.0, metadata: Optional[Dict[str,str]]=None, namespace: str="events"):
        now=datetime.now(timezone.utc)
        item=MemoryItem(
            id=str(uuid.uuid4()), tenant=self.tenant, kind="event", actor=actor,
            title=self._redact(title or subkind.capitalize()), text=self._redact(text),
            tags=tags or [], metadata={**(metadata or {}), "subkind": subkind},
            score=float(score), namespace=namespace, created_at=now, updated_at=now
        )
        emb=self.embedder.embed([self._embed_text(item)])[0]
        self._upsert(item, emb)
        return item

    def add_knowledge(self, namespace: str, title: str, content: str, tags: Optional[List[str]]=None, metadata: Optional[Dict[str,str]]=None):
        now=datetime.now(timezone.utc)
        item=MemoryItem(
            id=str(uuid.uuid4()), tenant=self.tenant, kind="knowledge", actor="system",
            title=self._redact(title), text=self._redact(content),
            tags=tags or [], metadata=metadata or {},
            score=0.0, namespace=namespace, created_at=now, updated_at=now
        )
        emb=self.embedder.embed([self._embed_text(item)])[0]
        self._upsert(item, emb)
        return item

    def add_super(self, title: str, text: str, tags: Optional[List[str]]=None, score: float=0.0, metadata: Optional[Dict[str,str]]=None, namespace: str="super"):
        now=datetime.now(timezone.utc)
        item=MemoryItem(
            id=str(uuid.uuid4()), tenant=self.tenant, kind="super", actor="system",
            title=self._redact(title), text=self._redact(text),
            tags=tags or [], metadata=metadata or {},
            score=float(score), namespace=namespace, created_at=now, updated_at=now
        )
        emb=self.embedder.embed([self._embed_text(item)])[0]
        self._upsert(item, emb)
        return item

    def recall(self, query: str, top_k: int=8, kinds: Optional[List[str]]=None):
        kinds=kinds or ["event","knowledge","super"]
        # Use server-side search if available (QdrantBackend)
        if hasattr(self.backend, "search"):
            try:
                qemb=self.embedder.embed([query])[0]
                hits=self.backend.search(self.tenant, qemb, top_k=top_k, kinds=kinds)
                return [i for (i, _s) in hits]
            except Exception:
                pass
        qemb=self.embedder.embed([query])[0]
        scored=[]
        for item, emb in self.backend.iter_items(self.tenant, kinds=kinds):
            sim=cosine(qemb, emb)
            rec=recency_weight(item.created_at, self.policy.recency_half_life_days)
            scored.append((0.7*sim+0.2*rec+0.1*float(item.score), item))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [i for _, i in scored[:top_k]]

    def distill(self, window_days: int=30, max_events: int=500):
        cutoff=datetime.now(timezone.utc)-timedelta(days=window_days)
        events=[]
        for item, _ in self.backend.iter_items(self.tenant, kinds=["event"]):
            if item.created_at >= cutoff and (item.score >= self.policy.distill_min_score or item.metadata.get("subkind")=="outcome"):
                events.append(item)
        events=sorted(events, key=lambda x: (x.created_at, x.score), reverse=True)[:max_events]
        distilled=self._distiller.distill(events)
        created=[]
        for d in distilled:
            created.append(self.add_super(d.get("title","Wisdom"), d.get("text",""), [d.get("tag","wisdom")], float(d.get("avg_score",0) or 0.0)).id)
        return {"source_events": len(events), "created_super_memories": len(created), "super_memory_ids": created}

    def gate_tool_call(self, scopes: List[str], tool_name: str, action: str, args: Dict[str,str], risk: str="low"):
        call=ToolCall(tool_name=tool_name, action=action, args=args, risk=risk)
        if not self.tool_policy.is_allowed(scopes, call):
            return False, "Denied by policy"
        if self.tool_policy.needs_human_approval(call):
            return False, "Requires human approval"
        return True, "Allowed"

    def record_tool_execution(self, tool_name: str, action: str, args: Dict[str,str], result: str, ok: bool):
        self.add_event(actor="executor", subkind="tool_exec",
                       text=f"tool={tool_name} action={action} ok={ok} result={result[:500]}",
                       tags=[f"tool:{tool_name}", f"ok:{ok}"], score=0.5 if ok else 0.0,
                       metadata={"action": action, **{f"arg_{k}": str(v) for k,v in args.items()}})

    def audit_last_hash(self)->str:
        return self._audit.last_hash()
