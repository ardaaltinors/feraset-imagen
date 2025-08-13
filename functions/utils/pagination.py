"""Simple helpers for opaque pagination tokens.

Tokens encode the last item's cursor (e.g., timestamp + id) as base64 JSON.
"""
from __future__ import annotations

import base64
import json
from datetime import datetime
from typing import Tuple


def encode_page_token(timestamp: datetime, document_id: str) -> str:
    payload = {
        "ts": timestamp.isoformat(),
        "id": document_id,
    }
    raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("utf-8")


def decode_page_token(token: str) -> Tuple[datetime, str]:
    try:
        raw = base64.urlsafe_b64decode(token.encode("utf-8")).decode("utf-8")
        data = json.loads(raw)
        ts_str = data.get("ts")
        doc_id = data.get("id")
        if not ts_str or not doc_id:
            raise ValueError("Missing fields in page token")
        # datetime.fromisoformat handles timezone-aware strings
        ts = datetime.fromisoformat(ts_str)
        return ts, doc_id
    except Exception as exc:
        raise ValueError(f"Invalid page token: {exc}") from exc
