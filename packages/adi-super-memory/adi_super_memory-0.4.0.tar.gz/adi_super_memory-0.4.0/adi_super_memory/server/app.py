import os
from fastapi import FastAPI, Header, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, List, Optional

from ..core import SuperMemory
from ..backends.sqlite import SQLiteBackend
from ..policy.memory_policy import MemoryPolicy
from ..safety.modes import EnterpriseSafetyMode, GovernmentSafetyMode
from ..auth.keys import ApiKeyManager
from ..policy.tool_policy import ToolPolicy

app = FastAPI(title="adi-super-memory", version="0.4.0")

API_SECRET = os.environ.get("ADI_SUPER_MEMORY_API_SECRET", "dev-secret-change-me")
MODE = os.environ.get("ADI_SUPER_MEMORY_MODE", "enterprise")

akm = ApiKeyManager(API_SECRET)

mem = SuperMemory(
    backend=SQLiteBackend(os.environ.get("ADI_SUPER_MEMORY_SQLITE_PATH", "data/adi_super_memory.sqlite3")),
    policy=MemoryPolicy.default(),
    safety=GovernmentSafetyMode.default() if MODE=="government" else EnterpriseSafetyMode.default(),
)

mem.tool_policy = ToolPolicy(
    allowed_tools_by_scope={
        "read": {"*"},
        "write": {"*"},
        "tool_exec": {"sap","db","http"},
    }
)

def require_api_key(x_api_key: str = Header(..., alias="X-API-Key")):
    try:
        return akm.verify(x_api_key)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid API key")

class IssueKeyIn(BaseModel):
    tenant: str
    scopes: List[str]

@app.post("/auth/issue")
def issue_key(payload: IssueKeyIn):
    return {"api_key": akm.create(payload.tenant, payload.scopes)}

class EventIn(BaseModel):
    actor: str
    subkind: str
    text: str
    title: Optional[str] = None
    tags: List[str] = []
    score: float = 0.0
    metadata: Dict[str, str] = {}
    namespace: str = "events"

class KnowledgeIn(BaseModel):
    namespace: str
    title: str
    content: str
    tags: List[str] = []
    metadata: Dict[str, str] = {}

class RecallIn(BaseModel):
    query: str
    top_k: int = 8
    kinds: Optional[List[str]] = None

class ToolCallIn(BaseModel):
    tool_name: str
    action: str
    args: Dict[str, str] = {}
    risk: str = "low"

@app.post("/event")
def add_event(payload: EventIn, key=Depends(require_api_key)):
    mem.tenant = key.tenant
    item = mem.add_event(payload.actor, payload.subkind, payload.text, payload.title, payload.tags, payload.score, payload.metadata, payload.namespace)
    return {"id": item.id, "audit_hash": mem.audit_last_hash()}

@app.post("/knowledge")
def add_knowledge(payload: KnowledgeIn, key=Depends(require_api_key)):
    mem.tenant = key.tenant
    item = mem.add_knowledge(payload.namespace, payload.title, payload.content, payload.tags, payload.metadata)
    return {"id": item.id, "audit_hash": mem.audit_last_hash()}

@app.post("/recall")
def recall(payload: RecallIn, key=Depends(require_api_key)):
    mem.tenant = key.tenant
    items = mem.recall(payload.query, payload.top_k, payload.kinds)
    return {"items": [{"id": i.id, "kind": i.kind, "title": i.title, "text": i.text, "tags": i.tags, "score": i.score} for i in items]}

@app.post("/distill")
def distill(window_days: int = 30, key=Depends(require_api_key)):
    mem.tenant = key.tenant
    return mem.distill(window_days=window_days)

@app.post("/tool/gate")
def gate_tool(payload: ToolCallIn, key=Depends(require_api_key)):
    mem.tenant = key.tenant
    allowed, reason = mem.gate_tool_call(key.scopes, payload.tool_name, payload.action, payload.args, payload.risk)
    return {"allowed": allowed, "reason": reason}

@app.post("/tool/record")
def record_tool(payload: ToolCallIn, result: str = "", ok: bool = True, key=Depends(require_api_key)):
    mem.tenant = key.tenant
    mem.record_tool_execution(payload.tool_name, payload.action, payload.args, result, ok)
    return {"ok": True, "audit_hash": mem.audit_last_hash()}
