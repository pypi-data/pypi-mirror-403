from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple, Union

@dataclass(frozen=True)
class FramePayload:
    data: memoryview
    shape: Optional[Tuple[int, ...]] = None
    dtype: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None

def as_frame_payload(frame: Any, meta: Optional[Dict[str, Any]] = None) -> Union[Dict[str, Any], FramePayload]:
    if isinstance(frame, dict):
        return frame
    if isinstance(frame, (bytes, bytearray, memoryview)):
        return FramePayload(data=memoryview(frame), meta=meta)
    try:
        import numpy as np  # optional
        if isinstance(frame, np.ndarray):
            return FramePayload(data=memoryview(frame), shape=tuple(frame.shape), dtype=str(frame.dtype), meta=meta)
    except Exception:
        pass
    try:
        return FramePayload(data=memoryview(frame), meta=meta)
    except Exception:
        return {"type":"frame_repr", "repr": repr(frame), "meta": meta or {}}
