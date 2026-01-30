from fastapi import FastAPI
from pydantic import BaseModel
from typing import Any, Dict
from ..core import SensoryMemoryADI, SensoryConfig

app = FastAPI(title="sensory-memory-adi", version="0.1.2.1")
_sm = SensoryMemoryADI(cfg=SensoryConfig())

class AddVisualIn(BaseModel):
    frame: Dict[str, Any]
class AddAudioTextIn(BaseModel):
    text: str
    meta: Dict[str, Any] = {}
class AddHapticIn(BaseModel):
    event: Dict[str, Any]

@app.post("/visual")
def add_visual(payload: AddVisualIn):
    _sm.iconic.add_frame(payload.frame); return {"ok": True}

@app.post("/audio_text")
def add_audio_text(payload: AddAudioTextIn):
    _sm.echoic.add_audio_text(payload.text, meta=payload.meta); return {"ok": True}

@app.post("/haptic")
def add_haptic(payload: AddHapticIn):
    _sm.haptic.add_touch(payload.event); return {"ok": True}

@app.get("/attend")
def attend(top_k: int = 8, include_affect: bool = True):
    return _sm.attend(top_k=top_k, include_affect=include_affect).model_dump()
