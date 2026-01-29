class SemanticKernelMemoryStore:
    def __init__(self, super_memory):
        self.mem=super_memory
    def save_information(self, collection: str, text: str, id: str=""):
        self.mem.add_knowledge(namespace=collection, title=id or "note", content=text, tags=[collection])
    def search(self, collection: str, query: str, limit:int=5):
        items=self.mem.recall(query=query, top_k=limit, kinds=["knowledge","super","event"])
        out=[]
        for i in items:
            if i.namespace==collection or collection in i.tags:
                out.append(i.text)
        return out
    def get(self, collection: str, key: str):
        hits=self.mem.recall(query=key, top_k=10, kinds=["knowledge"])
        for h in hits:
            if h.namespace==collection and (h.title==key or key in h.title):
                return h.text
        return None
