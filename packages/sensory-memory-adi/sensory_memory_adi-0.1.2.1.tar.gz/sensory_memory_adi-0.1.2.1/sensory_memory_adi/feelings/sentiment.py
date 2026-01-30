from dataclasses import dataclass
from typing import Dict

@dataclass(frozen=True)
class SentimentHeuristics:
    def score(self, text: str) -> Dict[str, float]:
        t = (text or "").lower()
        pos = sum(w in t for w in ["thanks","great","good","love","awesome","perfect","nice"])
        neg = sum(w in t for w in ["hate","bad","angry","upset","terrible","worst","annoyed"])
        urgent = sum(w in t for w in ["now","urgent","asap","immediately","quick","fast"])
        valence = (pos - neg) / 5.0
        arousal = min(1.0, (urgent + neg) / 4.0)
        return {"valence": max(-1.0, min(1.0, valence)), "arousal": arousal}
