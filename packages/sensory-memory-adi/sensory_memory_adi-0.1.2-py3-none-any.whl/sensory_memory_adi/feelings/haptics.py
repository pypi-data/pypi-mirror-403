from dataclasses import dataclass
from typing import Any, Dict

@dataclass(frozen=True)
class HapticFeeling:
    label: str
    arousal: float
    valence: float
    confidence: float
    note: str = ""

class HapticInterpreter:
    def interpret(self, event: Dict[str, Any]) -> HapticFeeling:
        kind = str(event.get("kind","unknown")).lower()
        pressure = _clamp(float(event.get("pressure", 0.3)), 0.0, 1.0)
        dur = float(event.get("duration_ms", 120))
        arousal = _clamp(0.6*pressure + 0.4*_inv_duration(dur), 0.0, 1.0)
        valence = _clamp(0.4*(0.6-pressure) - 0.3*_inv_duration(dur), -1.0, 1.0)
        label = kind
        note = ""
        conf = 0.7
        if kind in ("tap","double_tap"):
            if pressure < 0.35 and dur < 200: label = "gentle_tap"
            elif pressure > 0.75: label = "firm_tap"; valence -= 0.1
            if dur < 90 and pressure > 0.6: label="urgent_tap"; note="Fast + firm taps can indicate urgency."; conf=0.8
        elif kind in ("press","hold"):
            if dur > 600: label="steady_hold"; valence += 0.05
            if pressure > 0.8 and dur > 600: label="firm_hold"; valence -= 0.05
        elif kind in ("swipe","scroll"):
            label = "smooth_swipe" if pressure < 0.4 else "forceful_swipe"
            if pressure > 0.7: valence -= 0.05
        elif kind in ("vibration","shake"):
            label="vibration_signal"; valence -= 0.05; conf=0.6
        return HapticFeeling(label=label, arousal=_clamp(arousal,0,1), valence=_clamp(valence,-1,1), confidence=_clamp(conf,0,1), note=note)

def _clamp(x: float, a: float, b: float) -> float:
    return a if x < a else b if x > b else x
def _inv_duration(ms: float) -> float:
    ms = max(ms, 1.0)
    return _clamp(180.0/ms, 0.0, 1.0)
