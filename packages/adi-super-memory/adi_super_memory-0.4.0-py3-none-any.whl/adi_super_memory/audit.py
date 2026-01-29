from dataclasses import dataclass
from typing import Dict, List
import hashlib, json
from datetime import datetime, timezone

@dataclass(frozen=True)
class AuditEvent:
    ts: str
    tenant: str
    action: str
    subject: str
    prev_hash: str
    hash: str
    payload: Dict[str, str]

class HashChainedAuditLog:
    def __init__(self):
        self._last="0"*64
        self._events: List[AuditEvent]=[]
    def append(self, tenant: str, action: str, subject: str, payload: Dict[str,str]) -> AuditEvent:
        ts=datetime.now(timezone.utc).isoformat()
        body={"ts":ts,"tenant":tenant,"action":action,"subject":subject,"prev":self._last,"payload":payload}
        raw=json.dumps(body, sort_keys=True).encode("utf-8")
        h=hashlib.sha256(raw).hexdigest()
        ev=AuditEvent(ts, tenant, action, subject, self._last, h, payload)
        self._events.append(ev)
        self._last=h
        return ev
    def last_hash(self)->str:
        return self._last
