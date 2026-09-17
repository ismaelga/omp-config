"""System One API client: evaluate() plus retry policy."""

import json
import os
import time
import urllib.error
import urllib.request

API_URL = "https://api.typesafe.ai/v1/systemone"
MODEL = "jev-latest"


def evaluate(state, questions: dict, retries: int = 1) -> dict:
    """POST state+questions to System One; return answers map.

    Retries once on network errors (URLError/timeout), never on HTTP
    status errors — a 401 won't fix itself in a second. Raises the last
    exception on final failure.
    """
    payload = json.dumps({"state": state, "model": MODEL, "questions": questions}).encode()
    last_err = None
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(
                API_URL,
                data=payload,
                headers={
                    "Authorization": f"Bearer {os.environ['TYPESAFE_API_KEY']}",
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.load(resp)["answers"]
        except urllib.error.HTTPError as e:
            # auth/quota/validation: retrying is pointless. Surface the body —
            # FastAPI 422s carry per-field detail that names the exact bad key.
            try:
                detail = e.read().decode()[:300]
            except Exception:
                detail = ""
            raise RuntimeError(f"HTTP {e.code}: {detail or e.reason}") from e
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError) as e:
            last_err = e
            if attempt < retries:
                time.sleep(1)
    raise last_err