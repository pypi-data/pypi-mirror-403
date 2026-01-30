from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from .core import SensoryMemoryADI, SensoryConfig
from .agi.attention import SalienceScorer

@dataclass
class SensoryBuffer:
    """Legacy-friendly wrapper API."""
    decay_ms: int = 500
    cfg: Optional[SensoryConfig] = None
    _sm: SensoryMemoryADI = field(init=False)

    def __post_init__(self):
        if self.cfg is None:
            self.cfg = SensoryConfig(
                iconic_seconds=max(0.05, float(self.decay_ms) / 1000.0),
                echoic_seconds=3.0,
                haptic_seconds=1.5,
            )
        self._sm = SensoryMemoryADI(cfg=self.cfg)

    @property
    def sm(self) -> SensoryMemoryADI:
        return self._sm

    def capture(self, payload: Dict[str, Any], ts: Optional[float] = None) -> None:
        t = str(payload.get("type","")).lower()
        if t in ("frame","image","vision","iconic"):
            self._sm.iconic.add_frame(payload, ts=ts)
        elif t in ("touch","haptic"):
            self._sm.haptic.add_touch(payload, ts=ts)
        else:
            if "content" in payload and "text" not in payload:
                self._sm.echoic.add_audio_text(str(payload["content"]), ts=ts, meta={"source_type": t or "payload"})
            elif "text" in payload:
                self._sm.echoic.add_audio_text(str(payload["text"]), ts=ts, meta={"source_type": t or "payload"})
            else:
                self._sm.echoic.add_audio({"type":"event", **payload}, ts=ts)

    def attend(self, top_k: int = 8, include_affect: bool = True):
        return self._sm.attend(top_k=top_k, include_affect=include_affect)

class SaliencyFilter:
    """Legacy-friendly saliency checks."""
    scorer = SalienceScorer()

    @staticmethod
    def is_high_impact(payload: Dict[str, Any], *, threshold: float = 0.7) -> bool:
        if "priority" in payload:
            try:
                return float(payload["priority"]) >= threshold
            except Exception:
                pass
        kind = "echoic"
        p = {"text": str(payload.get("content") or payload.get("text") or "")}
        score = SaliencyFilter.scorer.score(kind, p, age_seconds=0.0)
        return score >= threshold
