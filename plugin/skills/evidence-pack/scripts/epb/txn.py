"""Journalled workspace transactions with ``state.json`` last, and crash recovery (WS-06).

A transaction stages every file in memory, validating each record against its schema first
(WS-08). ``commit()`` then:

1. writes each blob durably to ``.epb/tmp/txn-<id>/NNNN``, ``state.json`` last;
2. writes ``manifest.json.tmp`` listing ``{tmp, final, sha256}`` in that order, fsyncs it and
   renames it to ``manifest.json``. **That rename is the commit point**;
3. renames each blob onto its final path in manifest order;
4. removes the journal folder.

Each step calls ``faults.checkpoint`` (``stage:<i>``, ``pre-manifest``, ``manifest``,
``apply:<i>``, ``cleanup``, and ``recover:<i>`` inside ``recover()``) so the test suite can
crash the process for real at every one of them. Outside the tests the checkpoints do nothing.

A failure before the commit point removes the journal, so nothing changes. A failure after
it leaves the journal for ``recover()``, which rolls it forward. Recovery is idempotent.

A transaction may write only ``INDEX.md`` and files under ``.epb/`` or ``outputs/``. It can
never write under ``inputs/`` or outside the case folder, and ``state.json`` is written only
through ``set_state``.
"""

import copy
import os
import re
import secrets
import shutil
from datetime import UTC, datetime
from pathlib import Path

from epb import faults, fsio, schema
from epb.errors import EpbError
from epb.state import STATE_FILE

TMP_DIR = ".epb/tmp"
MANIFEST = "manifest.json"
MANIFEST_TMP = "manifest.json.tmp"
MANIFEST_SCHEMA_VERSION = 1

_ALLOWED_PREFIXES = (".epb/", "outputs/")
_TMP_NAME = re.compile(r"^\d{4}$")
_BACKUP_PATH = re.compile(r"^\.epb/runs/\d{3,}/pre-upgrade/.+$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_REPORT_HINT = (
    "Report this error code to the plugin maintainer. Do not edit the evidence or the .epb folder."
)
_RESTORE_HINT = (
    "Restore the .epb folder from a backup or from version control if you keep one. "
    "Do not edit it by hand, and do not ask the agent to repair it."
)


def _path_problem(rel) -> str | None:
    """Why ``rel`` may not be written by a transaction, or ``None`` when it may."""
    if not isinstance(rel, str) or not rel:
        return "the path is empty"
    if "\\" in rel:
        return "the path contains a backslash"
    if rel.startswith("/") or re.match(r"^[A-Za-z]:", rel):
        return "the path is absolute"
    parts = rel.split("/")
    if any(part in ("", ".", "..") for part in parts):
        return "the path has an empty, '.' or '..' part"
    if rel != "INDEX.md" and not rel.startswith(_ALLOWED_PREFIXES):
        return "only INDEX.md and files under .epb/ or outputs/ may be written"
    if rel == TMP_DIR or rel.startswith(TMP_DIR + "/"):
        return "the transaction folder cannot be written into"
    return None


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

    def _check_path(self, rel) -> None:
        problem = _path_problem(rel)
        if problem is None and rel == STATE_FILE:
            problem = "state.json is written only through set_state"
        if problem is None and rel in self.staged_paths:
            problem = "the path is already staged in this transaction"
        if problem is not None:
            raise EpbError(
                "INTERNAL_ERROR",
                f"The plugin tried to write {rel!r} in the case folder and was stopped: "
                f"{problem}. Nothing was written.",
                hint=_REPORT_HINT,
            )

    def stage_json(self, rel: str, obj, schema_name: str):
        """Validate ``obj`` against ``schema_name`` and stage it as deterministic JSON."""
        self._check_path(rel)
        schema.check(obj, schema_name, label=rel)
        self._staged.append((rel, fsio.json_bytes(obj)))
        return self

    def stage_record(self, rel: str, obj, schema_name: str, encode):
        """Validate ``obj`` against ``schema_name`` and stage ``encode(obj)``."""
        self._check_path(rel)
        schema.check(obj, schema_name, label=rel)
        data = encode(obj)
        if isinstance(data, str):
            data = data.encode("utf-8")
        self._staged.append((rel, data))
        return self

    def stage_text(self, rel: str, text: str):
        """Stage a plain-text file such as ``INDEX.md`` or ``.epb/.gitignore``."""
        self._check_path(rel)
        self._staged.append((rel, text.encode("utf-8")))
        return self

    def stage_backup(self, rel: str, data: bytes):
        """Stage a raw byte copy of a file, unvalidated. Only for the D-09 pre-upgrade
        backup, so ``rel`` must lie under ``.epb/runs/<NNN>/pre-upgrade/``."""
        self._check_path(rel)
        if not _BACKUP_PATH.match(rel):
            raise EpbError(
                "INTERNAL_ERROR",
                f"The plugin tried to write a raw copy to {rel!r}, outside a pre-upgrade "
                "backup folder, and was stopped. Nothing was written.",
                hint=_REPORT_HINT,
            )
        self._staged.append((rel, bytes(data)))
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
                faults.checkpoint(f"stage:{index}")
            manifest = {
                "schema_version": MANIFEST_SCHEMA_VERSION,
                "txn": self.id,
                "command": self.command,
                "entries": entries,
            }
            fsio.write_durable(txn_dir / MANIFEST_TMP, fsio.json_bytes(manifest))
            faults.checkpoint("pre-manifest")
            os.replace(txn_dir / MANIFEST_TMP, txn_dir / MANIFEST)  # COMMIT POINT
        except BaseException:
            shutil.rmtree(txn_dir, ignore_errors=True)
            raise
        # Past the commit point: no cleanup on failure, recover() rolls the journal forward.
        faults.checkpoint("manifest")
        fsio.fsync_dir(txn_dir)
        _apply(self.case_root, txn_dir, entries, "apply")
        shutil.rmtree(txn_dir)
        faults.checkpoint("cleanup")
        fsio.fsync_dir(tmp_root)
        return self.id


def _journal_error(txn_dir: Path, problem: str) -> EpbError:
    return EpbError(
        "STATE_INVALID",
        f"An interrupted change in {TMP_DIR}/{txn_dir.name} cannot be finished safely: {problem}.",
        hint=_RESTORE_HINT,
        data={"journal": f"{TMP_DIR}/{txn_dir.name}"},
    )


def _apply(case_root: Path, txn_dir: Path, entries: list, point: str) -> None:
    """Move each journalled blob onto its final path, in manifest order. An entry whose blob
    is gone was applied by an earlier, interrupted attempt; its final file must match. The
    checkpoint ``<point>:<i>`` follows every entry, applied now or found applied."""
    for index, entry in enumerate(entries):
        tmp = txn_dir / entry["tmp"]
        final = case_root / entry["final"]
        if tmp.exists():
            final.parent.mkdir(parents=True, exist_ok=True)
            fsio.replace_with_retry(tmp, final)
            fsio.fsync_dir(final.parent)
        elif not final.is_file() or fsio.sha256_file(final) != entry["sha256"]:
            raise _journal_error(txn_dir, f"{entry['final']} does not match what the change wrote")
        faults.checkpoint(f"{point}:{index}")


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


def _read_manifest(txn_dir: Path) -> dict:
    """Read and check a journal manifest; anything unexpected is ``STATE_INVALID``."""
    try:
        manifest = fsio.read_json(txn_dir / MANIFEST)
    except (UnicodeDecodeError, ValueError):
        raise _journal_error(txn_dir, "its manifest cannot be read") from None
    if (
        not isinstance(manifest, dict)
        or not isinstance(manifest.get("txn"), str)
        or not isinstance(manifest.get("entries"), list)
    ):
        raise _journal_error(txn_dir, "its manifest is not in the expected form")
    for entry in manifest["entries"]:
        if (
            not isinstance(entry, dict)
            or not isinstance(entry.get("tmp"), str)
            or not _TMP_NAME.match(entry["tmp"])
            or not isinstance(entry.get("sha256"), str)
            or not _SHA256.match(entry["sha256"])
            or _path_problem(entry.get("final")) is not None
        ):
            raise _journal_error(txn_dir, "its manifest lists an entry the plugin cannot trust")
    return manifest


def recover(case_root) -> list[str]:
    """Finish every committed journal, discard every uncommitted one, and return the ids of
    the journals that were finished. Safe to call any number of times, including after a
    crash during recovery itself."""
    case_root = Path(case_root)
    finished = []
    for txn_dir in _journal_dirs(case_root):
        if (txn_dir / MANIFEST).is_file():
            manifest = _read_manifest(txn_dir)
            _apply(case_root, txn_dir, manifest["entries"], "recover")
            finished.append(manifest["txn"])
        # No manifest (a stray manifest.json.tmp included): the commit point was never
        # reached, so nothing was applied and the journal is simply discarded.
        shutil.rmtree(txn_dir)
    return finished
