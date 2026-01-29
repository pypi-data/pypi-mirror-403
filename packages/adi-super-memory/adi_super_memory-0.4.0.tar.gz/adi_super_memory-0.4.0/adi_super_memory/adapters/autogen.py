from dataclasses import dataclass
from typing import List, Optional

@dataclass
class AutoGenConversationMemory:
    super_memory: any
    limit: int = 50
    def on_user_message(self, text: str): self.super_memory.stm.add("user", text)
    def on_assistant_message(self, text: str): self.super_memory.stm.add("assistant", text)
    def messages(self): return self.super_memory.stm.to_openai_messages(limit=self.limit)
    def retrieve_context(self, query: str, top_k:int=8): return self.super_memory.recall(query=query, top_k=top_k)

@dataclass
class AutoGenTeamMemory:
    super_memory: any
    def log(self, agent_name: str, kind: str, text: str, tags: Optional[List[str]]=None, score: float=0.0):
        self.super_memory.add_event(actor=agent_name, subkind=kind, text=text, tags=tags or [], score=score)
    def recall(self, query: str, top_k:int=8): return self.super_memory.recall(query=query, top_k=top_k)
