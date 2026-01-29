class LangChainMemoryAdapter:
    def __init__(self, super_memory, key: str='history', limit:int=50):
        self.mem=super_memory; self.key=key; self.limit=limit
    @property
    def memory_variables(self):
        return [self.key]
    def load_memory_variables(self, inputs):
        return {self.key: self.mem.stm.to_openai_messages(limit=self.limit)}
    def save_context(self, inputs, outputs):
        self.mem.stm.add('user', str(inputs)); self.mem.stm.add('assistant', str(outputs))
