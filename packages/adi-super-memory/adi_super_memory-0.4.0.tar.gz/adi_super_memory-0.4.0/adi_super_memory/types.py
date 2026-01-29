from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List

@dataclass(frozen=True)
class MemoryItem:
    id: str
    created_at: datetime
    updated_at: datetime
    kind: str
    actor: str
    title: str
    text: str
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, str] = field(default_factory=dict)
    score: float = 0.0
    tenant: str = "default"
    namespace: str = "default"

@dataclass(frozen=True)
class RecallHit:
    item: MemoryItem
    similarity: float
