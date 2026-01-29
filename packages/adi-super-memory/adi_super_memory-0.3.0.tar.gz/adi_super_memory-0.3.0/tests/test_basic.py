from adi_super_memory import SuperMemory, MemoryPolicy
from adi_super_memory.backends import InMemoryBackend
from adi_super_memory.safety import EnterpriseSafetyMode

def test_smoke():
    mem = SuperMemory(backend=InMemoryBackend(), policy=MemoryPolicy.default(), safety=EnterpriseSafetyMode.default())
    mem.stm.add("user","hi")
    mem.add_knowledge("sap","Vendor","company code required",["sap"])
    assert len(mem.recall("company code", top_k=3)) >= 1
