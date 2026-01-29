# adi-super-memory v0.4 (Upgraded ZIP)

Includes:
- Full adapters: LangGraph + AutoGen + Semantic Kernel (+ LangChain)
- Backends: InMemory, SQLite, Postgres (optional), Qdrant vector backend (optional)
- Hosted service: FastAPI + RBAC tenant API keys
- Policy enforcement hooks for tool execution (action gating)

Run server:
```bash
pip install "adi-super-memory[server]"
uvicorn adi_super_memory.server.app:app --host 0.0.0.0 --port 8080
```
