from datetime import datetime, timezone
from typing import List
import math

def cosine(a: List[float], b: List[float]) -> float:
    dot=na=nb=0.0
    for x,y in zip(a,b):
        dot += x*y; na += x*x; nb += y*y
    d = math.sqrt(na)*math.sqrt(nb)
    return (dot/d) if d else 0.0

def recency_weight(created_at: datetime, half_life_days: float) -> float:
    now = datetime.now(timezone.utc)
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    age_days = max((now-created_at).total_seconds(),0.0)/86400.0
    return math.pow(0.5, age_days/half_life_days) if half_life_days>0 else 1.0
