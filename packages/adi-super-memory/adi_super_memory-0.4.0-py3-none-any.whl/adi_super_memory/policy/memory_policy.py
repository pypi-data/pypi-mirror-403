from __future__ import annotations
from dataclasses import dataclass
from datetime import timedelta
from typing import Callable, Optional
RedactionFn = Callable[[str], str]

@dataclass(frozen=True)
class MemoryPolicy:
    episodic_ttl: Optional[timedelta] = timedelta(days=30)
    knowledge_ttl: Optional[timedelta] = None
    super_ttl: Optional[timedelta] = None
    recency_half_life_days: float = 14.0
    distill_min_score: float = 0.6
    redaction: Optional[RedactionFn] = None
    @staticmethod
    def default() -> "MemoryPolicy":
        return MemoryPolicy()
