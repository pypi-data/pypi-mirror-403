# sensory-memory-adi (v0.1.2)

A **production-ready sensory memory layer** for agentic AI systems:
- **Visual (Iconic) buffer**: ultra-short retention for frames/observations
- **Auditory (Echoic) buffer**: short retention for audio chunks/ASR snippets
- **Touch (Haptic) buffer**: short retention for touch events/pressure/vibration
- **Attention routing (AGI-ready hooks)**: salience scoring + event routing
- **Feeling-aware touch interpretation**: friendly labels (tap/press/hold/swipe) + arousal estimate
- **Privacy/Redaction hooks**: optional text redaction and safe snapshots
- Optional **FastAPI service** for deployment

## Memory Types & Typical Durations

| Type | Duration (typical) |
|---|---|
| Visual (Iconic) | ~0.2–0.5 seconds |
| Auditory (Echoic) | ~2–4 seconds |
| Touch (Haptic) | ~1–2 seconds |

## Install
```bash
pip install sensory-memory-adi
```

Optional server:
```bash
pip install "sensory-memory-adi[server]"
uvicorn sensory_memory_adi.server.app:app --host 0.0.0.0 --port 8081
```

## Quickstart
```python
from sensory_memory_adi import SensoryMemoryADI, SensoryConfig

sm = SensoryMemoryADI(cfg=SensoryConfig(iconic_seconds=0.5, echoic_seconds=3.0, haptic_seconds=1.5))
sm.iconic.add_frame({"camera":"front", "objects":["car","lane"]})
sm.echoic.add_audio_text("User said: turn left at next light")
sm.haptic.add_touch({"kind":"tap", "pressure":0.6, "duration_ms":120})

print(sm.attend(top_k=5).model_dump())
```


## Robotics & Cars (v0.1.2)
v0.1.2 adds **real timestamps** for all events and lightweight adapters:
- **ROS2 adapter (optional)**: convert ROS2 message dictionaries into iconic/echoic/haptic events
- **CAN bus adapter (optional)**: decode basic CAN frames (id, data) into haptic/echoic events (you can map signals)

> The ROS2 adapter is dependency-free by default. If you use rclpy, integrate by passing your decoded data into the adapter functions.

### Real timestamps
All `add_*` methods accept `ts` (Unix seconds). If omitted, current UTC time is used.
The `attend()` function now uses the true timestamps to compute recency.


## Zero-copy frames (v0.1.2)
`IconicBuffer.add_frame()` supports **zero-copy** payloads using `memoryview` or NumPy arrays (optional).
If you pass a NumPy array, we store a `memoryview` of the underlying buffer plus shape/dtype metadata (**no copy**).

Install NumPy support:
```bash
pip install "sensory-memory-adi[numpy]"
```

## High-concurrency ingestion (v0.1.2)
Includes:
- `ThreadSafeIngestor` (multi-producer via `queue.SimpleQueue`, centralized drain)
- `AsyncIngestor` (multi-producer via `asyncio.Queue`, centralized drain)

## Optional C/C++ hot path (v0.1.2)
A **pybind11** extension skeleton is included to accelerate the ring buffer.
It is **OFF by default**. Build it only when needed:

macOS/Linux:
```bash
export SENSORY_MEMORY_ADI_BUILD_EXT=1
pip install .
```

Windows PowerShell:
```powershell
$env:SENSORY_MEMORY_ADI_BUILD_EXT="1"
pip install .
```

## Benchmarks
Run:
```bash
python bench/benchmark.py
```

## ROS/ROS2 buffering patterns (optional utilities)
Includes a dependency-free `ApproxTimeSynchronizer` utility inspired by ROS message_filters.


## Legacy compatibility names (v0.1.2.1)
If you have example code using `SensoryBuffer` and `SaliencyFilter`, v0.1.2.1 provides them as wrappers:

```python
from sensory_memory_adi import SensoryBuffer, SaliencyFilter
sensory_layer = SensoryBuffer(decay_ms=500)
raw_input = {"type":"log_stream","content":"Critical Error: System Overheat","priority":0.9}
sensory_layer.capture(raw_input)

if SaliencyFilter.is_high_impact(raw_input):
    print("Promoting sensory data to Short-Term Memory...")
```
