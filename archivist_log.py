"""Artefact log as a JSON array — design doc ``archivist_log.json``."""

from __future__ import annotations

import json
import os
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, cast


def read_log(path: Path | str) -> list[dict[str, Any]]:
    """Load all records from a JSON array log file; returns newest last (append order)."""
    p = Path(path)
    if not p.is_file() or p.stat().st_size == 0:
        return []
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    if isinstance(raw, list):
        return [cast(dict[str, Any], x) for x in raw if isinstance(x, dict)]
    if isinstance(raw, dict):
        return [cast(dict[str, Any], raw)]
    return []


def append_artefact(path: Path | str, record: Mapping[str, Any]) -> None:
    """Append one record (single atomic rewrite). Prefer ``extend_log`` from scanners."""
    extend_log(path, [record])


def extend_log(path: Path | str, records: list[Mapping[str, Any]]) -> None:
    """
    Append many records in **one** read–merge–write cycle.

    Reduces Windows file-lock churn when many artefacts arrive quickly.
    """
    if not records:
        return
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)

    if p.exists() and p.stat().st_size > 0:
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            if not isinstance(data, list):
                data = [data]
        except json.JSONDecodeError:
            data = []
    else:
        data = []

    now = datetime.now(timezone.utc).isoformat()
    for rec in records:
        row = dict(rec)
        row.setdefault("discovered_at", now)
        data.append(row)

    payload = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    _atomic_write_text(p, payload)


def _atomic_write_text(p: Path, text: str) -> None:
    """Write ``text`` to ``p`` using a temp file in the same directory + replace."""
    fd, tmp = tempfile.mkstemp(
        prefix=".archivist_log_",
        suffix=".tmp",
        dir=str(p.parent),
        text=True,
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        _replace_with_retries(tmp, p)
    finally:
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except OSError:
                pass


def _replace_with_retries(tmp: str, dest: Path) -> None:
    last: OSError | None = None
    for _ in range(40):
        try:
            os.replace(tmp, dest)
            return
        except PermissionError as e:
            last = e
            time.sleep(0.05)
    if last:
        raise last

