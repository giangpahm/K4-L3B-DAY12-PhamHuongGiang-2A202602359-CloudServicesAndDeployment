import json
import sys
from datetime import datetime, timezone


def utc_now_iso() -> str:
    """Trả về thời gian UTC theo chuẩn ISO-8601 kết thúc bằng Z."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def log_event(event: str, level: str = "info", **fields) -> str:
    """Ghi một dòng log JSON ra stdout."""
    payload = {
        "event": event,
        "level": level.lower(),
        "timestamp": utc_now_iso(),
    }
    payload.update(fields)

    log_line = json.dumps(payload, ensure_ascii=False)
    print(log_line, file=sys.stdout, flush=True)
    return log_line