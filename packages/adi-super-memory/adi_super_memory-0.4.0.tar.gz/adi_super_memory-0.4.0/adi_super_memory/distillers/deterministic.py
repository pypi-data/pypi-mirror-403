from typing import Dict, List
from ..types import MemoryItem
class DeterministicDistiller:
    def distill(self, events: List[MemoryItem]) -> List[Dict[str,str]]:
        by_tag={}
        for e in events:
            for t in (e.tags or ["untagged"]):
                by_tag.setdefault(t, []).append(e)
        out=[]
        for tag, items in by_tag.items():
            avg=sum(float(x.score) for x in items)/max(len(items),1)
            out.append({"title":f"Wisdom: {tag}","text":f"avg_score={avg:.2f} over {len(items)} events","tag":tag,"avg_score":f"{avg:.3f}","examples":""})
        return out
