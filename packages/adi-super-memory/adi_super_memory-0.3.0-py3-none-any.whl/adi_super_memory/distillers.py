from abc import ABC, abstractmethod
from typing import Dict, List
from .types import MemoryItem

class Distiller(ABC):
    @abstractmethod
    def distill(self, events: List[MemoryItem]) -> List[Dict[str,str]]: ...

class DeterministicDistiller(Distiller):
    def distill(self, events: List[MemoryItem]) -> List[Dict[str,str]]:
        by_tag = {}
        for e in events:
            for t in (e.tags or ["untagged"]):
                by_tag.setdefault(t, []).append(e)
        out=[]
        for tag, items in by_tag.items():
            avg = sum(float(x.score) for x in items)/max(len(items),1)
            out.append({"title": f"Wisdom: {tag}", "text": f"avg_score={avg:.2f} over {len(items)} events", "tag": tag, "avg_score": f"{avg:.3f}", "examples": ""})
        return out

class OpenAIChatDistiller(Distiller):
    def __init__(self, model: str = "gpt-4.1-mini", api_key=None):
        self.model=model; self.api_key=api_key
    def distill(self, events: List[MemoryItem]) -> List[Dict[str,str]]:
        try:
            from openai import OpenAI
        except Exception as e:
            raise RuntimeError("Install OpenAI extras: pip install 'adi-super-memory[llm]'") from e
        client = OpenAI(api_key=self.api_key)
        lines=[f"- score={e.score:.2f} tags={','.join(e.tags)}: {e.text[:200]}" for e in events[:80]]
        prompt="Return JSON array of heuristics (title,text,tag,avg_score,examples).\nEVENTS:\n" + "\n".join(lines)
        resp = client.chat.completions.create(model=self.model, messages=[{"role":"user","content":prompt}], temperature=0.2)
        import json as _json
        content = resp.choices[0].message.content or "[]"
        try:
            data = _json.loads(content)
            return data if isinstance(data, list) else []
        except Exception:
            return [{"title":"Wisdom: distilled","text":content[:1500],"tag":"distilled","avg_score":"0.0","examples":""}]
