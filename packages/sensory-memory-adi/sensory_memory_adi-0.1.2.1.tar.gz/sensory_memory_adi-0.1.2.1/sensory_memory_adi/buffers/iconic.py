from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from ..utils.ring import TimeRing
from ..utils.time import now_ts
from ..zerocopy.frames import as_frame_payload

@dataclass
class IconicBuffer:
    ttl_seconds: float = 0.5
    max_items: int = 256
    _ring: TimeRing[Dict[str, Any]] = field(init=False)

    def __post_init__(self):
        self._ring = TimeRing(ttl_seconds=self.ttl_seconds, max_items=self.max_items)

    def add_frame(self, frame, ts: Optional[float] = None, meta: Optional[Dict[str, Any]] = None) -> None:
        ts = now_ts() if ts is None else ts
        payload = as_frame_payload(frame, meta=meta)
        self._ring.push(ts, payload)
        self._ring.evict_older_than(ts - self.ttl_seconds)

    def latest(self, k: int = 5) -> List[Dict[str, Any]]:
        ts = now_ts()
        self._ring.evict_older_than(ts - self.ttl_seconds)
        return [x for _, x in self._ring.latest(k)]

    def snapshot(self):
        ts = now_ts()
        self._ring.evict_older_than(ts - self.ttl_seconds)
        return self._ring.items()
