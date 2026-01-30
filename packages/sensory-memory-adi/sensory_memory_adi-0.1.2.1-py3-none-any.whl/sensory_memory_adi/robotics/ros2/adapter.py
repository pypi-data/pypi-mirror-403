from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, Optional

@dataclass
class Ros2Adapter:
    """Lightweight adapter for ROS2 pipelines.

    This module is dependency-free by default. In your ROS2 node, decode messages and pass
    dictionaries here.

    Expected dict shapes (examples):
      - Camera: {"topic":"/camera/front", "frame": {...}}
      - Audio/ASR: {"topic":"/asr", "text":"...", "meta": {...}}
      - Touch/Force: {"topic":"/touch", "kind":"press", "pressure":0.7, "duration_ms":200}
    """

    def to_iconic(self, msg: Dict[str, Any]) -> Dict[str, Any]:
        frame = msg.get("frame") or msg
        return {"source":"ros2","topic": msg.get("topic",""), **frame}

    def to_echoic_text(self, msg: Dict[str, Any]) -> Dict[str, Any]:
        return {"source":"ros2","topic": msg.get("topic",""), "type":"asr_text", "text": str(msg.get("text","")), "meta": msg.get("meta") or {}}

    def to_haptic(self, msg: Dict[str, Any]) -> Dict[str, Any]:
        out = {"source":"ros2","topic": msg.get("topic","")}
        for k in ["kind","pressure","duration_ms","x","y","device"]:
            if k in msg:
                out[k] = msg[k]
        if "kind" not in out:
            out["kind"]="unknown"
        return out
