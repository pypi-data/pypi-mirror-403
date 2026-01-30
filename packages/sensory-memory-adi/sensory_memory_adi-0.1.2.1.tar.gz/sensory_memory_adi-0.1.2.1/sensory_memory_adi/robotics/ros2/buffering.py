from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from ...utils.ring import TimeRing
from ...utils.time import now_ts

@dataclass
class ApproxTimeSynchronizer:
    topics: List[str]
    queue_size: int = 50
    slop_seconds: float = 0.05
    _rings: Dict[str, TimeRing[Any]] = field(default_factory=dict)

    def __post_init__(self):
        for t in self.topics:
            self._rings[t] = TimeRing(ttl_seconds=60.0, max_items=self.queue_size)

    def add(self, topic: str, msg: Any, ts: Optional[float] = None) -> None:
        ts = now_ts() if ts is None else float(ts)
        if topic not in self._rings:
            self._rings[topic] = TimeRing(ttl_seconds=60.0, max_items=self.queue_size)
        self._rings[topic].push(ts, msg)

    def get_latest(self) -> Optional[Dict[str, Any]]:
        latest_ts = None
        for ring in self._rings.values():
            last = ring.latest(1)
            if not last:
                continue
            ts, _ = last[-1]
            latest_ts = ts if latest_ts is None else max(latest_ts, ts)
        if latest_ts is None:
            return None

        out = {}
        for t, ring in self._rings.items():
            best = _closest_within(ring.items(), latest_ts, self.slop_seconds)
            if best is None:
                return None
            out[t] = best
        return out

def _closest_within(items: List[Tuple[float, Any]], target_ts: float, slop: float) -> Optional[Any]:
    best = None
    best_dt = None
    for ts, msg in items:
        dt = abs(ts - target_ts)
        if dt <= slop and (best_dt is None or dt < best_dt):
            best = msg
            best_dt = dt
    return best
