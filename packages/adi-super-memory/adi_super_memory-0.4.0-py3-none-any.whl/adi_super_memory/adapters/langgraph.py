class LangGraphMemoryStore:
    def __init__(self, super_memory):
        self.mem=super_memory
    def put(self, namespace: str, key: str, value):
        self.mem.stm.set(f"{namespace}:{key}", value)
    def get(self, namespace: str, key: str, default=None):
        return self.mem.stm.get(f"{namespace}:{key}", default)
    def append_message(self, role: str, content: str):
        self.mem.stm.add(role, content)
    def recall(self, query: str, top_k: int=8, kinds=None):
        return self.mem.recall(query=query, top_k=top_k, kinds=kinds)

class LangGraphStateAdapter:
    def __init__(self, super_memory, messages_key: str="messages"):
        self.mem=super_memory; self.messages_key=messages_key
    def load_messages(self, state: dict, limit:int=50):
        state[self.messages_key]=self.mem.stm.to_openai_messages(limit=limit); return state
    def add_user(self, text: str): self.mem.stm.add("user", text)
    def add_assistant(self, text: str): self.mem.stm.add("assistant", text)
    def attach_memory_context(self, state: dict, query: str, top_k:int=8):
        items=self.mem.recall(query=query, top_k=top_k)
        state["memory_context"]=[{"kind":i.kind,"text":i.text,"tags":i.tags,"score":i.score} for i in items]
        return state
