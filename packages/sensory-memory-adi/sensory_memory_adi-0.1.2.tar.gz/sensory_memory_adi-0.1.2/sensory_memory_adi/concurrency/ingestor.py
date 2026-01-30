from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable, Optional, Tuple
import queue
import asyncio

Event = Tuple[str, Any, Optional[float]]  # (channel, payload, ts)

@dataclass
class ThreadSafeIngestor:
    max_batch: int = 8192
    _q: "queue.SimpleQueue[Event]" = field(default_factory=queue.SimpleQueue)

    def push(self, channel: str, payload: Any, ts: Optional[float] = None) -> None:
        self._q.put((channel, payload, ts))

    def drain(self, handle: Callable[[str, Any, Optional[float]], None], limit: Optional[int] = None) -> int:
        n = 0
        lim = self.max_batch if limit is None else int(limit)
        while n < lim:
            try:
                ch, payload, ts = self._q.get_nowait()
            except Exception:
                break
            handle(ch, payload, ts)
            n += 1
        return n

@dataclass
class AsyncIngestor:
    max_batch: int = 8192
    _q: "asyncio.Queue[Event]" = field(default_factory=asyncio.Queue)

    async def push(self, channel: str, payload: Any, ts: Optional[float] = None) -> None:
        await self._q.put((channel, payload, ts))

    async def drain(self, handle, limit: Optional[int] = None) -> int:
        n = 0
        lim = self.max_batch if limit is None else int(limit)
        while n < lim:
            try:
                ch, payload, ts = self._q.get_nowait()
            except Exception:
                break
            res = handle(ch, payload, ts)
            if asyncio.iscoroutine(res):
                await res
            n += 1
        return n
