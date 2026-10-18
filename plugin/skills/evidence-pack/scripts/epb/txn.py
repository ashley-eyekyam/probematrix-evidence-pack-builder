"""Journalled workspace transactions with ``state.json`` last, and crash recovery (WS-06).

A transaction stages every file in memory, validating each record against its schema first
(WS-08). ``commit()`` then:

1. writes each blob durably to ``.epb/tmp/txn-<id>/NNNN``, ``state.json`` last;
2. writes ``manifest.json.tmp`` listing ``{tmp, final, sha256}`` in that order, fsyncs it and
   renames it to ``manifest.json``. **That rename is the commit point**;
3. renames each blob onto its final path in manifest order;
4. removes the journal folder.

A failure before the commit point removes the journal, so nothing changes. A failure after
it leaves the journal for ``recover()``, which rolls it forward. Recovery is idempotent.
"""

import copy
import os
import secrets
import shutil
from datetime import UTC, datetime
from pathlib import Path

from epb import fsio, schema
from epb.state import STATE_FILE

TMP_DIR = ".epb/tmp"
MANIFEST = "manifest.json"
MANIFEST_TMP = "manifest.json.tmp"
MANIFEST_SCHEMA_VERSION = 1


def _new_id() -> str:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return f"{stamp}-{os.getpid()}-{secrets.token_hex(3)}"


class Transaction:
    """One atomic change to a case folder."""

    def __init__(self, case_root, command: str):
        self.case_root = Path(case_root)
        self.command = command
        self.id = _new_id()
        self._staged: list[tuple[str, bytes]] = []
        self._state: bytes | None = None

    @property
    def staged_paths(self) -> list[str]:
        """The final paths in the order they will be applied, ``state.json`` last."""
        paths = [rel for rel, _ in self._staged]
        if self._state is not None:
            paths.append(STATE_FILE)
        return paths

    def stage_json(self, rel: str, obj, schema_name: str):
        """Validate ``obj`` against ``schema_name`` and stage it as deterministic JSON."""
        schema.check(obj, schema_name, label=rel)
        self._staged.append((rel, fsio.json_bytes(obj)))
        return self

    def stage_record(self, rel: str, obj, schema_name: str, encode):
        """Validate ``obj`` against ``schema_name`` and stage ``encode(obj)``."""
        schema.check(obj, schema_name, label=rel)
        data = encode(obj)
        if isinstance(data, str):
            data = data.encode("utf-8")
        self._staged.append((rel, data))
        return self

    def stage_text(self, rel: str, text: str):
        """Stage a plain-text file such as ``INDEX.md`` or ``.epb/.gitignore``."""
        self._staged.append((rel, text.encode("utf-8")))
        return self

    def set_state(self, state: dict):
        """Stage ``state.json``, stamped with this transaction, to be applied last."""
        state = copy.deepcopy(state)
        state["last_txn"] = {
            "id": self.id,
            "command": self.command,
            "committed_at": fsio.utc_now_iso(),
        }
        schema.check(state, "state", label=STATE_FILE)
        self._state = fsio.json_bytes(state)
        return self

    def _blobs(self) -> list[tuple[str, bytes]]:
        blobs = list(self._staged)
        if self._state is not None:
            blobs.append((STATE_FILE, self._state))
        return blobs

    def commit(self) -> str | None:
        """Write everything staged atomically and return the transaction id, or ``None``
        when nothing was staged."""
        blobs = self._blobs()
        if not blobs:
            return None
        tmp_root = self.case_root / TMP_DIR
        tmp_root.mkdir(parents=True, exist_ok=True)
        txn_dir = tmp_root / f"txn-{self.id}"
        txn_dir.mkdir()
        try:
            entries = []
            for index, (rel, data) in enumerate(blobs):
                name = f"{index:04d}"
                fsio.write_durable(txn_dir / name, data)
                entries.append({"tmp": name, "final": rel, "sha256": fsio.sha256_bytes(data)})
            manifest = {
                "schema_version": MANIFEST_SCHEMA_VERSION,
                "txn": self.id,
                "command": self.command,
                "entries": entries,
            }
            fsio.write_durable(txn_dir / MANIFEST_TMP, fsio.json_bytes(manifest))
            os.replace(txn_dir / MANIFEST_TMP, txn_dir / MANIFEST)  # COMMIT POINT
        except BaseException:
            shutil.rmtree(txn_dir, ignore_errors=True)
            raise
        # Past the commit point: no cleanup on failure, recover() rolls the journal forward.
        fsio.fsync_dir(txn_dir)
        _apply(self.case_root, txn_dir, entries)
        shutil.rmtree(txn_dir)
        fsio.fsync_dir(tmp_root)
        return self.id


def _apply(case_root: Path, txn_dir: Path, entries: list) -> None:
    """Move each journalled blob onto its final path, in manifest order."""
    for entry in entries:
        tmp = txn_dir / entry["tmp"]
        final = case_root / entry["final"]
        if not tmp.exists():
            continue  # already applied by an earlier, interrupted attempt
        final.parent.mkdir(parents=True, exist_ok=True)
        fsio.replace_with_retry(tmp, final)
        fsio.fsync_dir(final.parent)


def _journal_dirs(case_root) -> list[Path]:
    tmp_root = Path(case_root) / TMP_DIR
    if not tmp_root.is_dir():
        return []
    return sorted(path for path in tmp_root.glob("txn-*") if path.is_dir())


def pending_journals(case_root) -> list[str]:
    """Ids of committed journals that have not been fully applied yet."""
    return [
        path.name.removeprefix("txn-")
        for path in _journal_dirs(case_root)
        if (path / MANIFEST).is_file()
    ]


def recover(case_root) -> list[str]:
    """Finish every committed journal, discard every uncommitted one, and return the ids of
    the journals that were finished. Safe to call any number of times."""
    case_root = Path(case_root)
    finished = []
    for txn_dir in _journal_dirs(case_root):
        manifest_path = txn_dir / MANIFEST
        if manifest_path.is_file():
            manifest = fsio.read_json(manifest_path)
            _apply(case_root, txn_dir, manifest["entries"])
            finished.append(manifest["txn"])
        shutil.rmtree(txn_dir)
    return finished
