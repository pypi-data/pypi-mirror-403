"""Helpers for injecting learning objects into runtime prompts."""

from __future__ import annotations

import hashlib
import logging
from typing import Any, Dict, Tuple

from marlo.learning.management.usage import get_tracker
from marlo.trajectories.capture.context import ExecutionContext

logger = logging.getLogger(__name__)


def resolve_playbook(
    role: str,
    *,
    apply: bool,
    limit: int = 1000,
) -> Tuple[str | None, str | None, Dict[str, Any] | None]:
    """Return structured learning objects for prompt injection and usage tracking."""

    try:
        context = ExecutionContext.get()
    except Exception:  # pragma: no cover - defensive guard when unset
        return None, None, None

    state = context.metadata.get("learning_state")
    if not isinstance(state, dict):
        return None, None, None

    active_entries = state.get("active") if isinstance(state.get("active"), list) else []
    metadata = {"active_count": len(active_entries)}

    try:
        tracker = get_tracker()
        tracker.register_entries(role, active_entries)
    except Exception:  # pragma: no cover - instrumentation must not fail core flow
        logger.debug("Unable to register learning entries for role %s", role, exc_info=True)

    if not apply:
        return None, None, metadata

    cache = context.metadata.setdefault("_learning_playbooks", {})
    payload_entries = _extract_entries(active_entries)
    raw_payload = _serialise_entries(payload_entries)
    cached = cache.get(role)
    if cached and cached.get("raw") == raw_payload:
        _record_applied_learning_ids(
            context,
            cached.get("applied_ids") or [],
            cached.get("digest"),
            cached.get("text"),
        )
        return cached.get("text"), cached.get("digest"), metadata
    if not payload_entries:
        cache[role] = {"raw": raw_payload, "text": None, "digest": None, "applied_ids": []}
        _record_applied_learning_ids(context, [], None, None)
        return None, None, metadata

    trimmed, applied_ids = _trim_payload(payload_entries, limit)
    if not trimmed:
        cache[role] = {"raw": raw_payload, "text": None, "digest": None, "applied_ids": []}
        _record_applied_learning_ids(context, [], None, None)
        return None, None, metadata

    digest = hashlib.sha256(trimmed.encode("utf-8")).hexdigest()
    cache[role] = {"raw": raw_payload, "text": trimmed, "digest": digest, "applied_ids": applied_ids}

    _record_applied_learning_ids(context, applied_ids, digest, trimmed)

    return trimmed, digest, metadata


def _extract_entries(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    payload_entries = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        learning_id = entry.get("learning_id")
        learning = entry.get("learning")
        if not isinstance(learning_id, str) or not learning_id.strip():
            continue
        if not isinstance(learning, str) or not learning.strip():
            continue
        payload_entries.append(
            {
                "learning_id": learning_id.strip(),
                "learning": learning.strip(),
            }
        )
    return payload_entries


def _serialise_entries(entries: list[dict[str, Any]]) -> str:
    if not entries:
        return ""
    return "\n\n".join(entry["learning"] for entry in entries if isinstance(entry.get("learning"), str))


def _trim_payload(entries: list[dict[str, Any]], limit: int) -> tuple[str, list[str]]:
    if limit <= 0:
        return _serialise_entries(entries), [entry["learning_id"] for entry in entries]
    applied_ids: list[str] = []
    texts: list[str] = []
    running_length = 0
    for entry in entries:
        learning = entry.get("learning")
        learning_id = entry.get("learning_id")
        if not isinstance(learning, str) or not isinstance(learning_id, str):
            continue
        separator = "\n\n" if texts else ""
        candidate = f"{separator}{learning}"
        if running_length + len(candidate) > limit:
            break
        texts.append(learning)
        applied_ids.append(learning_id)
        running_length += len(candidate)
    return ("\n\n".join(texts) if texts else ""), applied_ids


def _record_applied_learning_ids(
    context: ExecutionContext,
    learning_ids: list[str],
    digest: str | None,
    text: str | None,
) -> None:
    task_meta = context.metadata.setdefault("task_metadata", {})
    task_meta["applied_learning_ids"] = list(learning_ids)
    definition_hash = context.metadata.get("definition_hash")
    if isinstance(definition_hash, str) and definition_hash:
        sorted_ids = sorted(
            entry.strip() for entry in learning_ids if isinstance(entry, str) and entry.strip()
        )
        prompt_variant_hash = hashlib.sha256((definition_hash + "".join(sorted_ids)).encode("utf-8")).hexdigest()
        task_meta["prompt_variant_hash"] = prompt_variant_hash
        session_meta = context.metadata.get("session_metadata")
        if isinstance(session_meta, dict):
            session_meta["prompt_variant_hash"] = prompt_variant_hash
    if digest is not None and text is not None:
        task_meta["applied_learning_digest"] = digest
        task_meta["applied_learning_chars"] = len(text)
