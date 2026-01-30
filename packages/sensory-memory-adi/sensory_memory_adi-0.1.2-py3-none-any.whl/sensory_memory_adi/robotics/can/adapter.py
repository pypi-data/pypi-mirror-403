from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, Optional

@dataclass
class CanBusAdapter:
    """Minimal CAN bus adapter for cars/robots.

    This adapter does not assume a specific DBC. It provides:
      - Raw frame capture
      - Convenience mapping: certain IDs -> haptic or echoic-text events (customizable)

    CAN frame dict expected:
      {"arbitration_id": int, "data": bytes|list[int], "timestamp": float|None}
    """
    # user can map ids to labels/types
    id_map: Dict[int, Dict[str, Any]] = None

    def __post_init__(self):
        if self.id_map is None:
            # defaults are placeholders; customize for your platform
            self.id_map = {
                0x100: {"type":"haptic", "kind":"vibration", "pressure":0.4},
                0x200: {"type":"echoic_text", "prefix":"CAN status:"},
            }

    def decode(self, frame: Dict[str, Any]) -> Dict[str, Any]:
        arb = int(frame.get("arbitration_id", 0))
        data = frame.get("data", b"")
        if isinstance(data, list):
            data = bytes(int(x) & 0xFF for x in data)
        mapping = self.id_map.get(arb)

        if not mapping:
            # raw fallback
            return {"type":"raw", "source":"can", "arbitration_id": arb, "data_hex": data.hex()}

        t = mapping.get("type")
        if t == "haptic":
            out = {"source":"can","arbitration_id":arb,"kind":mapping.get("kind","unknown"),
                   "pressure": float(mapping.get("pressure",0.3)),
                   "duration_ms": int(mapping.get("duration_ms",120))}
            return out

        if t == "echoic_text":
            prefix = str(mapping.get("prefix","CAN:"))
            return {"type":"asr_text","source":"can","arbitration_id":arb,
                    "text": f"{prefix} id=0x{arb:X} data={data.hex()}",
                    "meta": {"len": len(data)}}

        return {"type":"raw","source":"can","arbitration_id":arb,"data_hex":data.hex()}
