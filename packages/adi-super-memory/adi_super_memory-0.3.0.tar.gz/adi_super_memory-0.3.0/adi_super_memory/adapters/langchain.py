class LangChainMemoryAdapter:
    def __init__(self, super_memory, key: str = "history"):
        self.mem=super_memory; self.key=key
    @property
    def memory_variables(self): return [self.key]
    def load_memory_variables(self, inputs): return {self.key: self.mem.stm.messages()}
    def save_context(self, inputs, outputs):
        self.mem.stm.add("user", str(inputs))
        self.mem.stm.add("assistant", str(outputs))
