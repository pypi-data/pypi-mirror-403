"""Deterministic JSON digest helper."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def json_digest(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


__all__ = ["json_digest"]
