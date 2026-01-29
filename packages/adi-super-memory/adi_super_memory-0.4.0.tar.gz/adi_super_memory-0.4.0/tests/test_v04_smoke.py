from adi_super_memory.core import SuperMemory
from adi_super_memory.backends.inmemory import InMemoryBackend
from adi_super_memory.policy.memory_policy import MemoryPolicy
from adi_super_memory.auth.keys import ApiKeyManager
from adi_super_memory.policy.tool_policy import ToolPolicy

def test_memory_smoke():
    mem = SuperMemory(backend=InMemoryBackend(), policy=MemoryPolicy.default(), tenant="t1")
    mem.stm.add("user", "hello")
    mem.add_knowledge(namespace="sap", title="Vendor", content="company code required", tags=["sap"])
    assert len(mem.recall("company code", top_k=3)) >= 1

def test_api_key_roundtrip():
    akm = ApiKeyManager("secret")
    tok = akm.create("acme", scopes=["read","write"])
    key = akm.verify(tok)
    assert key.tenant == "acme"
    assert "read" in key.scopes

def test_tool_policy_gate():
    mem = SuperMemory(backend=InMemoryBackend(), policy=MemoryPolicy.default(), tenant="t1")
    mem.tool_policy = ToolPolicy(allowed_tools_by_scope={"read":{"sap"}}, denied_tools=set())
    allowed, _ = mem.gate_tool_call(scopes=["read"], tool_name="sap", action="get_vendor", args={}, risk="low")
    assert allowed
    denied, _ = mem.gate_tool_call(scopes=["read"], tool_name="http", action="get", args={}, risk="low")
    assert not denied
