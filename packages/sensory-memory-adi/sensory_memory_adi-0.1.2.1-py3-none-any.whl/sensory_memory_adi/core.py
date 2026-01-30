from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from .buffers.iconic import IconicBuffer
from .buffers.echoic import EchoicBuffer
from .buffers.haptic import HapticBuffer
from .agi.attention import AttentionRouter, SalienceScorer
from .feelings.haptics import HapticInterpreter
from .feelings.sentiment import SentimentHeuristics
from .privacy.redaction import default_redactor
from .utils.time import now_ts

class SensoryConfig(BaseModel):
    iconic_seconds: float = 0.5
    echoic_seconds: float = 3.0
    haptic_seconds: float = 1.5
    max_iconic_items: int = 256
    max_echoic_items: int = 512
    max_haptic_items: int = 512

class AttentionSnapshot(BaseModel):
    attended: List[Dict[str, Any]]
    haptic_feelings: List[Dict[str, Any]]
    text_affect: Optional[Dict[str, float]] = None

@dataclass
class SensoryMemoryADI:
    cfg: SensoryConfig = field(default_factory=SensoryConfig)
    redactor: Optional[Any] = default_redactor

    def __post_init__(self):
        self.iconic = IconicBuffer(ttl_seconds=float(self.cfg.iconic_seconds), max_items=int(self.cfg.max_iconic_items))
        self.echoic = EchoicBuffer(ttl_seconds=float(self.cfg.echoic_seconds), max_items=int(self.cfg.max_echoic_items))
        self.haptic = HapticBuffer(ttl_seconds=float(self.cfg.haptic_seconds), max_items=int(self.cfg.max_haptic_items))
        self._router = AttentionRouter(scorer=SalienceScorer())
        self._haptic_interpreter = HapticInterpreter()
        self._sentiment = SentimentHeuristics()

    def attend(self, top_k: int = 8, include_affect: bool = True) -> AttentionSnapshot:
        now = now_ts()
        items=[]

        # Use true timestamps from buffers
        for ts, payload in self.iconic.snapshot():
            items.append(("iconic", now-ts, payload))
        for ts, payload in self.echoic.snapshot():
            items.append(("echoic", now-ts, payload))
        for ts, payload in self.haptic.snapshot():
            items.append(("haptic", now-ts, payload))

        attended = self._router.route(items, top_k=top_k)

        feelings=[]
        for ev in self.haptic.latest(k=10):
            hf = self._haptic_interpreter.interpret(ev)
            feelings.append(hf.__dict__)

        text_affect = None
        if include_affect:
            joined = " ".join(self.echoic.latest_text(k=10))
            if self.redactor:
                joined = self.redactor(joined)
            if joined.strip():
                text_affect = self._sentiment.score(joined)

        if self.redactor:
            for a in attended:
                p = a.get("payload") or {}
                if isinstance(p, dict) and p.get("type") == "asr_text" and "text" in p:
                    p["text"] = self.redactor(str(p["text"]))
                    a["payload"] = p

        return AttentionSnapshot(attended=attended, haptic_feelings=feelings, text_affect=text_affect)

