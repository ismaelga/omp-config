"""Decision logging: append-only JSONL of every jev verdict.

~/.omp/logs/jev.jsonl — the tuning corpus. Thresholds and criteria get
adjusted against this data; it is also the "wire it when proven" gate's
evidence. Content fields are truncated (they may contain secrets) but
metadata is logged whole.
"""

import json
import time
from pathlib import Path

LOG_PATH = Path.home() / ".omp" / "logs" / "jev.jsonl"
MAX_FIELD = 500  # chars per content-ish field


def log_decision(cmd: str, record: dict) -> None:
    entry = {"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "cmd": cmd}
    entry.update(record)
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with LOG_PATH.open("a") as f:
            f.write(json.dumps(_truncated(entry)) + "\n")
    except OSError:
        pass  # logging must never break the decision itself


def _truncated(obj):
    if isinstance(obj, dict):
        return {k: _truncated(v) for k, v in obj.items()}
    if isinstance(obj, str) and len(obj) > MAX_FIELD:
        return obj[:MAX_FIELD] + "…"
    return obj