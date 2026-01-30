from dataclasses import dataclass, field
from typing import Deque, Generic, List, Tuple, TypeVar
from collections import deque

T = TypeVar("T")

@dataclass
class TimeRing(Generic[T]):
    ttl_seconds: float
    max_items: int = 512
    _dq: Deque[Tuple[float, T]] = field(default_factory=deque)

    def push(self, ts: float, item: T) -> None:
        self._dq.append((ts, item))
        while len(self._dq) > self.max_items:
            self._dq.popleft()

    def evict_older_than(self, cutoff_ts: float) -> int:
        removed = 0
        while self._dq and self._dq[0][0] < cutoff_ts:
            self._dq.popleft()
            removed += 1
        return removed

    def items(self) -> List[Tuple[float, T]]:
        return list(self._dq)

    def latest(self, k: int = 10) -> List[Tuple[float, T]]:
        return list(self._dq)[-max(0,k):]
