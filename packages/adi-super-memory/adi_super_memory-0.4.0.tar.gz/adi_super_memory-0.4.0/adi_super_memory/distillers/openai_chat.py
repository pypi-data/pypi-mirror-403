import json
from typing import Dict, List, Optional
from ..types import MemoryItem
class OpenAIChatDistiller:
    def __init__(self, model: str="gpt-4.1-mini", api_key: Optional[str]=None):
        self.model=model; self.api_key=api_key
    def distill(self, events: List[MemoryItem]) -> List[Dict[str,str]]:
        try:
            from openai import OpenAI
        except Exception as e:
            raise RuntimeError("Install llm extras: pip install 'adi-super-memory[llm]'") from e
        client=OpenAI(api_key=self.api_key)
        lines=[f"- score={e.score:.2f} tags={','.join(e.tags)}: {e.text[:240]}" for e in events[:120]]
        prompt="Return JSON array of heuristics (title,text,tag,avg_score,examples).\nEVENTS:\n" + "\n".join(lines)
        resp=client.chat.completions.create(model=self.model, messages=[{"role":"user","content":prompt}], temperature=0.2)
        content=resp.choices[0].message.content or "[]"
        try:
            data=json.loads(content)
            return data if isinstance(data, list) else []
        except Exception:
            return [{"title":"Wisdom: distilled","text":content[:1600],"tag":"distilled","avg_score":"0.0","examples":""}]
