from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from ..utils.ring import TimeRing
from ..utils.time import now_ts

@dataclass
class EchoicBuffer:
    ttl_seconds: float = 3.0
    max_items: int = 512
    _ring: TimeRing[Dict[str, Any]] = field(init=False)

    def __post_init__(self):
        self._ring = TimeRing(ttl_seconds=self.ttl_seconds, max_items=self.max_items)

    def add_audio(self, payload: Dict[str, Any], ts: Optional[float] = None) -> None:
        ts = now_ts() if ts is None else ts
        self._ring.push(ts, payload)
        self._ring.evict_older_than(ts - self.ttl_seconds)

    def add_audio_text(self, text: str, ts: Optional[float] = None, meta: Optional[Dict[str, Any]] = None) -> None:
        self.add_audio({"type":"asr_text","text":text,"meta":meta or {}}, ts=ts)

    def latest_text(self, k: int = 10) -> List[str]:
        ts = now_ts()
        self._ring.evict_older_than(ts - self.ttl_seconds)
        out=[]
        for _, p in self._ring.latest(k):
            if p.get("type") == "asr_text":
                out.append(str(p.get("text","")))
        return out

    def snapshot(self):
        ts = now_ts()
        self._ring.evict_older_than(ts - self.ttl_seconds)
        return self._ring.items()
