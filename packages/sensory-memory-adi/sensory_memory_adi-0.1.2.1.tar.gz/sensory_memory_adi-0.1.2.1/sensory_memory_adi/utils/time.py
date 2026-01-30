from datetime import datetime, timezone
def now_ts() -> float:
    return datetime.now(timezone.utc).timestamp()
