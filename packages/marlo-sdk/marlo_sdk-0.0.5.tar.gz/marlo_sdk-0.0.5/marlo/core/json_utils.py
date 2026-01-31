"""JSON coercion helpers."""

from __future__ import annotations

import json
from typing import Any


def coerce_json(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except (TypeError, ValueError):
            return value
    return value


def coerce_dict(value: Any) -> dict[str, Any]:
    payload = coerce_json(value)
    if isinstance(payload, dict):
        return dict(payload)
    return {}


def coerce_list(value: Any) -> list[Any]:
    payload = coerce_json(value)
    if isinstance(payload, list):
        return list(payload)
    return []


__all__ = ["coerce_dict", "coerce_json", "coerce_list"]
