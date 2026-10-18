"""``epb scan``: take stock of ``inputs/`` (WS-02, WS-03, design §7.1, research Pattern 4).

Scan only reads ``inputs/``. It walks it without following links, fingerprints every regular
file (SHA-256, size, type and modification time), classifies the result against what the case
folder already knows (``epb.sources.classify``) and, when anything changed, writes the new and
changed source records, the fingerprints, a run record and a fresh ``INDEX.md`` in one
transaction.
"""

import fnmatch
import hashlib
import os
import stat
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

from epb import fsio, mime
from epb.errors import EpbError

INPUTS_DIR = "inputs"
SOURCES_DIR = ".epb/sources"
MEDIA_DIR = ".epb/media"

# OS and editor leftovers: listed as ignored, never registered. The fixed names match in any
# letter case; the patterns match as written.
JUNK_PATTERNS = (".DS_Store", "Thumbs.db", "desktop.ini", "~$*", "._*", ".~lock.*#", "*.tmp")
_JUNK_NAMES = frozenset(p.lower() for p in JUNK_PATTERNS if not any(c in p for c in "*?["))
_JUNK_GLOBS = tuple(p for p in JUNK_PATTERNS if any(c in p for c in "*?["))

NO_FILES = "No files found in inputs/. Put evidence files there, then scan again."
NO_CHANGES = "No changes since the last scan."

# Open without following a link and without blocking on a pipe; O_BINARY matters on Windows.
_OPEN_FLAGS = (
    os.O_RDONLY
    | getattr(os, "O_NOFOLLOW", 0)
    | getattr(os, "O_NONBLOCK", 0)
    | getattr(os, "O_BINARY", 0)
)


@dataclass(frozen=True)
class FileFact:
    """One regular file found in ``inputs/``."""

    rel: str  # NFC, POSIX, relative to the case folder: "inputs/a/report.pdf"
    size: int
    mtime_ns: int
    sha256: str
    mime: str
    mime_mismatch: dict | None


@dataclass(frozen=True)
class Ignored:
    """Something in ``inputs/`` that scan skipped: ``junk``, ``link`` or ``special``."""

    rel: str
    reason: str


@dataclass
class WalkResult:
    files: list = field(default_factory=list)  # FileFact, sorted by rel
    ignored: list = field(default_factory=list)  # Ignored, sorted by rel


def rel_key(case_root, path) -> str:
    """The path of ``path`` relative to the case folder, POSIX style and NFC-normalised."""
    rel = Path(path).relative_to(case_root).as_posix()
    return unicodedata.normalize("NFC", rel)


def is_junk(name: str) -> bool:
    """Whether a file name is an OS or editor leftover (``JUNK_PATTERNS``)."""
    if name.lower() in _JUNK_NAMES:
        return True
    return any(fnmatch.fnmatchcase(name, pattern) for pattern in _JUNK_GLOBS)


def _is_link(path) -> bool:
    if os.path.islink(path):
        return True
    isjunction = getattr(os.path, "isjunction", None)  # Python 3.12+
    return bool(isjunction and isjunction(path))


def _unreadable(rel, error) -> EpbError:
    reason = getattr(error, "strerror", None) or type(error).__name__
    return EpbError(
        "BAD_ARGUMENT",
        f"{rel} in the inputs folder could not be read ({reason}). Nothing was changed.",
        hint="Close the file in any program that has it open, check that you can open it "
        "yourself, then scan again.",
    )


def _fingerprint(path):
    """``(sha256, size, mtime_ns)`` of a regular file, or ``None`` when ``path`` is not a
    regular file (any more). A link is never followed and a pipe is never waited on."""
    try:
        fd = os.open(path, _OPEN_FLAGS)
    except FileNotFoundError:
        return None
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode):
            return None
        with os.fdopen(fd, "rb", closefd=False) as handle:
            digest = hashlib.file_digest(handle, "sha256").hexdigest()
        return digest, info.st_size, info.st_mtime_ns
    finally:
        os.close(fd)


def walk_inputs(case_root) -> WalkResult:
    """Fingerprint every regular file under ``inputs/``, sorted by path. Links (and junctions)
    are listed as ``link`` and never followed; pipes, sockets and devices as ``special`` and
    never opened; OS junk as ``junk``. Nothing under ``inputs/`` is ever written."""
    case_root = Path(case_root)
    inputs = case_root / INPUTS_DIR
    result = WalkResult()
    if _is_link(inputs):
        result.ignored.append(Ignored(f"{INPUTS_DIR}/", "link"))
        return result
    if not inputs.is_dir():
        return result

    def fail(error):
        rel = rel_key(case_root, error.filename) if error.filename else INPUTS_DIR
        raise _unreadable(rel, error)

    for folder, dirnames, filenames in os.walk(inputs, onerror=fail, followlinks=False):
        kept = []
        for name in sorted(dirnames):
            path = Path(folder) / name
            if _is_link(path):
                result.ignored.append(Ignored(rel_key(case_root, path), "link"))
            else:
                kept.append(name)
        dirnames[:] = kept
        for name in sorted(filenames):
            path = Path(folder) / name
            rel = rel_key(case_root, path)
            try:
                info = os.lstat(path)
            except FileNotFoundError:
                continue  # gone since the folder was listed
            if stat.S_ISLNK(info.st_mode) or _is_link(path):
                result.ignored.append(Ignored(rel, "link"))
                continue
            if not stat.S_ISREG(info.st_mode):
                result.ignored.append(Ignored(rel, "special"))
                continue
            if is_junk(name):
                result.ignored.append(Ignored(rel, "junk"))
                continue
            try:
                found = _fingerprint(path)
            except OSError as error:
                raise _unreadable(rel, error) from None
            if found is None:
                continue
            sha256, size, mtime_ns = found
            detected, mismatch = mime.detect(path)
            result.files.append(
                FileFact(
                    rel=rel,
                    size=size,
                    mtime_ns=mtime_ns,
                    sha256=sha256,
                    mime=detected,
                    mime_mismatch=mismatch,
                )
            )
    result.files.sort(key=lambda fact: fact.rel)
    result.ignored.sort(key=lambda item: item.rel)
    return result


def _summary(plan) -> str:
    parts = []
    for count, one, many in (
        (len(plan.new), "new input", "new inputs"),
        (len(plan.new_versions), "new version", "new versions"),
        (len(plan.renamed), "renamed", "renamed"),
        (len(plan.duplicates), "duplicate copy", "duplicate copies"),
        (len(plan.moved), "moved path", "moved paths"),
        (len(plan.restored), "restored", "restored"),
        (len(plan.removed), "removed from folder", "removed from folder"),
    ):
        if count:
            parts.append(f"{count} {one if count == 1 else many}")
    return "Scanned inputs/: " + (", ".join(parts) if parts else "no changes") + "."


def _scan_record(plan, walk) -> dict:
    return {
        "new": list(plan.new),
        "new_versions": list(plan.new_versions),
        "renamed": list(plan.renamed),
        "duplicates": list(plan.duplicates),
        "moved": list(plan.moved),
        "removed": list(plan.removed),
        "restored": list(plan.restored),
        "ignored": [{"path": item.rel, "reason": item.reason} for item in walk.ignored],
        "mime_mismatches": list(plan.mime_mismatches),
        "sidecars": [],
        "orphan_sidecars": [],
    }


def _data(plan, walk, run_id, changed) -> dict:
    return {
        "changed": changed,
        "run": run_id,
        "new": list(plan.new),
        "new_versions": list(plan.new_versions),
        "renamed": list(plan.renamed),
        "duplicates": list(plan.duplicates),
        "moved": list(plan.moved),
        "removed": list(plan.removed),
        "restored": list(plan.restored),
        "ignored": [{"path": item.rel, "reason": item.reason} for item in walk.ignored],
        "sources_total": len(plan.sources),
    }


def _warn_ignored(walk, ctx) -> None:
    for item in walk.ignored:
        if item.reason == "link":
            ctx.warn(
                "LINK_IGNORED",
                f"{item.rel} is a link (a shortcut to somewhere else), so it was not followed.",
                "If it points to evidence, copy the file itself into the inputs folder.",
            )


def _warn_changes(plan, ctx) -> None:
    by_id = {record["src_id"]: record for record in plan.sources}
    for src_id in plan.removed:
        last = by_id[src_id]["versions"][-1]["paths"]
        ctx.warn(
            "INPUT_REMOVED",
            f"{src_id} ({', '.join(last)}) is no longer in the inputs folder. Its record is kept.",
            "Put the file back if it was removed by mistake; otherwise nothing is needed.",
        )


def _run_expanders(case_root, plan) -> None:
    """Hand every new source and new version to the expanders for its type (PF-11). The
    registry is empty in Phase 1, so nothing runs yet."""
    from epb.sources import expanders

    by_id = {record["src_id"]: record for record in plan.sources}
    for src_id in [*plan.new, *(entry["src_id"] for entry in plan.new_versions)]:
        record = by_id[src_id]
        version = record["versions"][-1]
        for expander in expanders.expanders_for(version["mime"]):
            expander.expand(
                case_root / record["paths"][0],
                src_id,
                case_root / MEDIA_DIR / src_id / "unpacked",
            )


def run_scan(session, ctx):
    """Scan the case folder opened as ``session`` and return the command's ``Result``.

    When nothing changed (no record and no fingerprint would differ) it writes nothing and
    allocates no run; that includes an empty or missing ``inputs/`` in a case with no sources.
    """
    import copy

    from epb import index, runs, txn
    from epb.cli import Result
    from epb.sources.classify import classify

    started_at = fsio.utc_now_iso()
    case_root = Path(session.case_root)
    walk = walk_inputs(case_root)
    _warn_ignored(walk, ctx)
    state = copy.deepcopy(session.state)
    next_run = f"{state['counters']['run'] + 1:03d}"
    plan = classify(
        state["fingerprints"],
        session.sources,
        walk.files,
        run_id=next_run,
        source_counter=state["counters"]["source"],
    )
    if not plan.changed:
        message = NO_FILES if not session.sources and not walk.files else NO_CHANGES
        return Result(data=_data(plan, walk, None, False), message=message)

    _warn_changes(plan, ctx)
    _run_expanders(case_root, plan)
    summary = _summary(plan)
    run_id, run_record = runs.new_run(
        state, "scan", started_at=started_at, summary=summary, scan=_scan_record(plan, walk)
    )
    state["fingerprints"] = plan.fingerprints
    state["counters"]["source"] = plan.source_counter
    transaction = txn.Transaction(case_root, "scan")
    for record in plan.records:
        transaction.stage_json(f"{SOURCES_DIR}/{record['src_id']}.json", record, "source")
    transaction.stage_json(runs.run_json_path(run_id), run_record, "run")
    transaction.stage_text(
        index.INDEX_FILE,
        index.render_index(
            index.IndexInputs(session.case, state, plan.sources, [*session.runs, run_record])
        ),
    )
    transaction.set_state(state)
    transaction.commit()
    return Result(
        data=_data(plan, walk, run_id, True),
        message=f"{summary}\nRun {run_id}. See INDEX.md in the case folder for the full list.",
    )
