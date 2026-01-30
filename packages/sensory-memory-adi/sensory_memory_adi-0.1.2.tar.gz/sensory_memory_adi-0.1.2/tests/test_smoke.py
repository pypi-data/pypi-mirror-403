from sensory_memory_adi import SensoryMemoryADI, SensoryConfig
from sensory_memory_adi.robotics import Ros2Adapter, CanBusAdapter


def test_smoke():
    sm = SensoryMemoryADI(cfg=SensoryConfig())
    sm.iconic.add_frame({"objects":["lane","car"]})
    sm.echoic.add_audio_text("Thanks, this is great!")
    sm.haptic.add_touch({"kind":"tap","pressure":0.7,"duration_ms":80})
    snap = sm.attend(top_k=5)
    assert len(snap.attended) >= 1
    assert len(snap.haptic_feelings) >= 1


def test_adapters():
    sm = SensoryMemoryADI(cfg=SensoryConfig())
    ros = Ros2Adapter()
    sm.iconic.add_frame(ros.to_iconic({"topic":"/cam","frame":{"objects":["cone"]}}))
    sm.echoic.add_audio_text("hello")
    can = CanBusAdapter()
    ev = can.decode({"arbitration_id":0x100,"data":[1,2,3]})
    sm.haptic.add_touch(ev)
    snap = sm.attend(top_k=5)
    assert snap.attended


def test_threadsafe_ingestor():
    from sensory_memory_adi.concurrency import ThreadSafeIngestor
    sm = SensoryMemoryADI(cfg=SensoryConfig())
    ing = ThreadSafeIngestor()
    for i in range(2000):
        ing.push("iconic", {"objects":[i]})
        ing.push("echoic_text", f"t{i}")
        ing.push("haptic", {"kind":"tap","pressure":0.4,"duration_ms":120})
    def handle(ch, payload, ts):
        if ch == "iconic":
            sm.iconic.add_frame(payload, ts=ts)
        elif ch == "echoic_text":
            sm.echoic.add_audio_text(payload, ts=ts)
        elif ch == "haptic":
            sm.haptic.add_touch(payload, ts=ts)
    ing.drain(handle, limit=10000)
    snap = sm.attend(top_k=10)
    assert snap.attended
