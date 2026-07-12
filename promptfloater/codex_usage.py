"""Read local Codex usage snapshots from Codex Desktop session logs.

The Codex app writes non-secret usage events to JSONL session logs.  PromptFloater
only reads those local event records and extracts the latest rate-limit snapshot.
It never reads auth files and never sends this data anywhere.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_MAX_FILES = 40
TAIL_BYTES = 256 * 1024


def default_codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex")


def _candidate_logs(codex_home: Path, max_files: int = DEFAULT_MAX_FILES) -> list[Path]:
    roots = [codex_home / "sessions", codex_home / "archived_sessions"]
    files: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        try:
            files.extend(path for path in root.rglob("*.jsonl") if path.is_file())
        except OSError:
            continue
    return sorted(files, key=lambda path: path.stat().st_mtime, reverse=True)[:max_files]


def _tail_lines(path: Path, max_bytes: int = TAIL_BYTES) -> list[str]:
    try:
        size = path.stat().st_size
        with path.open("rb") as handle:
            if size > max_bytes:
                handle.seek(-max_bytes, os.SEEK_END)
                handle.readline()  # discard a possibly partial first line
            raw = handle.read()
    except OSError:
        return []
    return raw.decode("utf-8", errors="ignore").splitlines()


def _event_timestamp(event: dict[str, Any]) -> datetime:
    raw = event.get("timestamp")
    if isinstance(raw, str):
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            pass
    return datetime.fromtimestamp(0, timezone.utc)


def _rate_limits_from_event(event: dict[str, Any]) -> dict[str, Any] | None:
    payload = event.get("payload")
    if not isinstance(payload, dict):
        return None
    if payload.get("type") != "token_count":
        return None
    rate_limits = payload.get("rate_limits") or event.get("rate_limits")
    if isinstance(rate_limits, dict) and rate_limits.get("primary"):
        return rate_limits
    return None


def _iter_rate_limit_events(codex_home: Path) -> list[tuple[dict[str, Any], datetime, Path]]:
    events: list[tuple[dict[str, Any], datetime, Path]] = []
    for path in _candidate_logs(codex_home):
        for line in reversed(_tail_lines(path)):
            if '"token_count"' not in line or '"rate_limits"' not in line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            rate_limits = _rate_limits_from_event(event)
            if not rate_limits:
                continue
            timestamp = _event_timestamp(event)
            events.append((rate_limits, timestamp, path))
            break
    return events


def _window_snapshot(raw: dict[str, Any]) -> dict[str, Any] | None:
    if not isinstance(raw, dict):
        return None
    used_percent = raw.get("used_percent")
    resets_at = raw.get("resets_at")
    window_minutes = raw.get("window_minutes")
    if not isinstance(used_percent, (int, float)) or not isinstance(resets_at, (int, float)):
        return None
    return {
        "used_percent": round(float(used_percent), 1),
        "window_minutes": int(window_minutes) if isinstance(window_minutes, (int, float)) else None,
        "resets_at": int(resets_at),
        "resets_at_iso": datetime.fromtimestamp(float(resets_at)).astimezone().isoformat(timespec="minutes"),
    }


def _aggregate_window(events: list[tuple[dict[str, Any], datetime, Path]], key: str) -> dict[str, Any] | None:
    windows: list[dict[str, Any]] = []
    for rate_limits, timestamp, _path in events:
        raw = rate_limits.get(key)
        if not isinstance(raw, dict):
            continue
        snapshot = _window_snapshot(raw)
        if not snapshot:
            continue
        snapshot["_timestamp"] = timestamp
        windows.append(snapshot)
    if not windows:
        return None

    latest_reset = max(window["resets_at"] for window in windows)
    current_windows = [window for window in windows if window["resets_at"] == latest_reset]
    highest = max(current_windows, key=lambda window: window["used_percent"])
    return {
        "used_percent": highest["used_percent"],
        "window_minutes": highest["window_minutes"],
        "resets_at": highest["resets_at"],
        "resets_at_iso": highest["resets_at_iso"],
    }


def get_codex_usage(codex_home: str | os.PathLike[str] | None = None) -> dict[str, Any]:
    """Return the latest local Codex usage snapshot.

    The return value is intentionally UI-ready and stable:
    ``{"available": False, "error": "..."}`` when no snapshot can be read, or
    ``{"available": True, "primary": {...}, "secondary": {...}}`` when found.
    """

    home = Path(codex_home) if codex_home is not None else default_codex_home()
    events = _iter_rate_limit_events(home)
    if not events:
        return {"available": False, "error": "未检测到 Codex 用量记录"}

    primary = _aggregate_window(events, "primary")
    if primary is None:
        return {"available": False, "error": "Codex 用量记录格式不完整"}

    latest_rate_limits, latest_timestamp, latest_path = max(events, key=lambda event: event[1])
    result: dict[str, Any] = {
        "available": True,
        "limit_id": latest_rate_limits.get("limit_id") or "codex",
        "limit_name": latest_rate_limits.get("limit_name"),
        "primary": primary,
        "secondary": _aggregate_window(events, "secondary"),
        "captured_at": latest_timestamp.astimezone().isoformat(timespec="seconds"),
        "source": str(latest_path),
        "source_count": len(events),
        "aggregation": "max_used_percent_for_current_reset_window",
    }
    return result
