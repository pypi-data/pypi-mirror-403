from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple
import math

@dataclass
class SalienceScorer:
    w_recency: float = 0.6
    w_signal: float = 0.4
    def score(self, kind: str, payload: Dict[str, Any], age_seconds: float) -> float:
        rec = math.exp(-max(age_seconds,0.0))
        signal = 0.2
        if kind == "haptic":
            signal = float(payload.get("pressure", 0.3))
        elif kind == "echoic":
            txt = str(payload.get("text",""))
            signal = min(1.0, len(txt)/180.0)
        elif kind == "iconic":
            objs = payload.get("objects") or payload.get("detections") or []
            try: signal = min(1.0, len(objs)/12.0)
            except Exception: signal = 0.3
        return max(0.0, min(1.0, self.w_recency*rec + self.w_signal*signal))

@dataclass
class AttentionRouter:
    scorer: SalienceScorer = field(default_factory=SalienceScorer)
    def route(self, items: List[Tuple[str, float, Dict[str, Any]]], top_k: int = 8) -> List[Dict[str, Any]]:
        scored=[]
        for kind, age, payload in items:
            s=self.scorer.score(kind,payload,age_seconds=age)
            scored.append({"kind":kind,"score":s,"age_seconds":age,"payload":payload})
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:max(1, top_k)]
