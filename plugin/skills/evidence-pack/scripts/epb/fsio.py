"""Durable file primitives shared by the workspace store (WS-06).

Standard library only. Every write the store makes goes through ``write_durable`` (new file,
flushed and fsynced) and lands with ``replace_with_retry`` (an atomic rename that tolerates a
brief Windows sharing violation). JSON records are serialised by ``json_bytes`` so the same
object always yields the same bytes.
"""

import hashlib
import json
import os
import time
from datetime import UTC, datetime
from pathlib import Path


def write_durable(path, data: bytes) -> None:
    """Create ``path`` (it must not exist), write ``data``, flush and fsync it."""
    with open(path, "xb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())


def fsync_dir(path) -> None:
    """fsync a directory so a rename inside it survives a power cut. A no-op on Windows,
    which cannot open a directory for fsync."""
    if os.name == "nt":
        return
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def replace_with_retry(src, dst, *, attempts: int = 10, delay_s: float = 0.05) -> None:
    """``os.replace(src, dst)``, retried only on ``PermissionError``.

    On Windows a virus scanner or indexer can hold the target open for a moment, which
    shows up as a sharing violation. Every other error is raised at once.
    """
    for attempt in range(attempts):
        try:
            os.replace(src, dst)
            return
        except PermissionError:
            if attempt == attempts - 1:
                raise
            time.sleep(delay_s)


def sha256_bytes(data: bytes) -> str:
    """The lower-case hex SHA-256 of ``data``."""
    return hashlib.sha256(data).hexdigest()


def sha256_file(path) -> str:
    """The lower-case hex SHA-256 of the file at ``path``."""
    with open(path, "rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def json_bytes(obj) -> bytes:
    """Deterministic JSON: sorted keys, two-space indent, non-ASCII kept, trailing newline."""
    text = json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    return text.encode("utf-8")


def read_json(path):
    """Parse the UTF-8 JSON file at ``path``."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def utc_now_iso() -> str:
    """The current UTC time at second precision, for example ``2026-10-18T09:30:00Z``."""
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
