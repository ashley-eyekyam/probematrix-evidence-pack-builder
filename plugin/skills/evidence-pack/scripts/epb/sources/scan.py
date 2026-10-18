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
import re
import stat
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

from epb import fsio, mime
from epb.errors import EpbError
from epb.sources.sidecars import orphan_target, pair_sidecars, sidecar_target

INPUTS_DIR = "inputs"
SOURCES_DIR = ".epb/sources"
MEDIA_DIR = ".epb/media"

# OS and editor leftovers: listed as ignored, never registered. The fixed names match in any
# letter case; the patterns match as written.
JUNK_PATTERNS = (".DS_Store", "Thumbs.db", "desktop.ini", "~$*", "._*", ".~lock.*#", "*.tmp")
_JUNK_NAMES = frozenset(p.lower() for p in JUNK_PATTERNS if not any(c in p for c in "*?["))
_JUNK_GLOBS = tuple(p for p in JUNK_PATTERNS if any(c in p for c in "*?["))

# The ignored reason for a file or folder whose name is not valid text (not valid UTF-8).
BAD_NAME = "bad-name"
_SURROGATES = re.compile("[\ud800-\udfff]")

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
    """Something in ``inputs/`` that scan skipped: ``junk``, ``link``, ``special`` or
    ``bad-name`` (a name that is not valid text; ``rel`` is then its ``display_path``)."""

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


def name_is_text(name: str) -> bool:
    """Whether ``name`` is valid text. On Linux a name whose bytes are not valid UTF-8 reaches
    Python holding lone surrogates (surrogateescape), which can never be written as UTF-8."""
    try:
        name.encode("utf-8")
    except UnicodeEncodeError:
        return False
    return True


def display_path(rel: str) -> str:
    """``rel`` with every part that is not valid text shown as U+FFFD. Never raises.

    Bytes smuggled in by surrogateescape are decoded back and replaced; any other lone
    surrogate (a Windows NTFS name can hold one) is replaced directly."""
    try:
        return rel.encode("utf-8", "surrogateescape").decode("utf-8", "replace")
    except UnicodeEncodeError:
        return _SURROGATES.sub("�", rel)


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


def _same_name(rel) -> EpbError:
    return EpbError(
        "BAD_ARGUMENT",
        f"Two files in the inputs folder have the same name written in two different ways "
        f"({rel}): the letters are the same but are stored as different characters. The "
        "plugin cannot tell them apart, so nothing was changed.",
        hint="Rename one of the two files, then scan again.",
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
    never opened; OS junk as ``junk``. A name that is not valid text is listed as ``bad-name``
    under its ``display_path`` and never registered, whatever kind of entry it names. Nothing
    under ``inputs/`` is ever written.

    Path keys are NFC, so a name stored in NFD form (as macOS writes it) is the same key as its
    NFC spelling. Two files whose names differ only in that way (possible on Linux) would share
    one key, so the scan stops with ``BAD_ARGUMENT`` rather than silently keep one of them."""
    case_root = Path(case_root)
    inputs = case_root / INPUTS_DIR
    result = WalkResult()
    if _is_link(inputs):
        result.ignored.append(Ignored(f"{INPUTS_DIR}/", "link"))
        return result
    if not inputs.is_dir():
        return result

    def fail(error):
        rel = display_path(rel_key(case_root, error.filename)) if error.filename else INPUTS_DIR
        raise _unreadable(rel, error)

    seen = set()  # NFC keys already used; two spellings of one name cannot both be kept
    for folder, dirnames, filenames in os.walk(inputs, onerror=fail, followlinks=False):
        kept = []
        for name in sorted(dirnames):
            path = Path(folder) / name
            if not name_is_text(name):
                # Pruned: nothing inside a folder named like this is opened or registered.
                skipped = Ignored(display_path(rel_key(case_root, path)) + "/", BAD_NAME)
                result.ignored.append(skipped)
            elif _is_link(path):
                result.ignored.append(Ignored(rel_key(case_root, path), "link"))
            else:
                kept.append(name)
        dirnames[:] = kept
        for name in sorted(filenames):
            path = Path(folder) / name
            rel = rel_key(case_root, path)
            if not name_is_text(name):
                result.ignored.append(Ignored(display_path(rel), BAD_NAME))
                continue
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
            if rel in seen:
                raise _same_name(rel)
            seen.add(rel)
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


def _paths_text(paths) -> str:
    return ", ".join(sorted(paths))


def _change_lines(plan, pairing) -> list:
    """One plain-language line per change, in a fixed order: new versions, new inputs,
    renames, copies, moves, restores, removals, then notes newly paired with their inputs.
    Each line starts with the source's ID as the user sees it (``S004`` or ``S004v2``) and one
    of its paths."""
    from epb.index import display_id

    by_id = {record["src_id"]: record for record in plan.sources}
    moved_to = {(entry["to_src"], entry["path"]): entry["from_src"] for entry in plan.moved}
    reported = set()  # (src_id, path) pairs already explained by a line
    lines = []

    def line(src_id, path, text):
        reported.add((src_id, path))
        lines.append(f"{display_id(by_id[src_id])} {path}: {text}")

    for entry in plan.new_versions:
        record = by_id[entry["src_id"]]
        previous = [v for v in record["versions"] if v["version"] < entry["version"]]
        since = f" since run {previous[-1]['seen_run']}" if previous else ""
        for path in record["paths"]:
            line(entry["src_id"], path, f"new version (the file changed{since})")
    for src_id in plan.new:
        for path in by_id[src_id]["paths"]:
            before = moved_to.get((src_id, path))
            if before is not None:
                line(
                    src_id,
                    path,
                    f"new input; it was a copy of {display_id(by_id[before])}, "
                    "and the copies now differ",
                )
            else:
                line(src_id, path, "new input")
    for entry in plan.renamed:
        line(entry["src_id"], entry["from"], f"renamed to {entry['to']}")
        reported.add((entry["src_id"], entry["to"]))
    for entry in plan.duplicates:
        src_id, path = entry["src_id"], entry["path"]
        before = moved_to.get((src_id, path))
        others = [rel for rel in by_id[src_id]["paths"] if rel != path]
        if before is not None:
            line(
                src_id,
                path,
                f"now holds the same content as {_paths_text(others) or display_id(by_id[src_id])}"
                f", so it moved from {display_id(by_id[before])} to {display_id(by_id[src_id])}",
            )
        else:
            line(src_id, path, f"another copy of {_paths_text(others)}")
    for entry in plan.moved:
        if (entry["to_src"], entry["path"]) not in reported:
            line(
                entry["to_src"],
                entry["path"],
                f"moved from {display_id(by_id[entry['from_src']])}",
            )
    for src_id in plan.restored:
        for path in by_id[src_id]["paths"]:
            line(src_id, path, "back in the folder")
    for src_id in plan.removed:
        last = _last_paths(by_id[src_id])
        holders = _now_held_by(plan, last)
        if holders:
            line(
                src_id,
                _paths_text(last),
                "its content is no longer in the folder (the path now holds "
                f"{', '.join(display_id(by_id[other]) for other in holders)}); "
                "its record is kept",
            )
        else:
            line(src_id, _paths_text(last), "removed from the folder; its record is kept")
    for pair in pairing.pairs:
        if pair["src_id"] not in pairing.changed:
            continue
        note, target = by_id[pair["src_id"]], by_id[pair["target"]]
        path = next(rel for rel in sorted(note["paths"]) if sidecar_target(rel) in target["paths"])
        lines.append(
            f"{display_id(note)} {path}: a note for {display_id(target)} ({sidecar_target(path)})"
        )
    return lines


def _now_held_by(plan, paths) -> list:
    """The sources that hold any of ``paths`` after this scan, sorted by number."""
    from epb.sources.classify import src_number

    owners = {plan.fingerprints[rel]["src_id"] for rel in paths if rel in plan.fingerprints}
    return sorted(owners, key=src_number)


def _last_paths(record) -> list:
    for version in record["versions"]:
        if version["version"] == record["current_version"]:
            return list(version["paths"])
    return list(record["versions"][-1]["paths"])


def _scan_record(plan, walk, pairing) -> dict:
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
        "sidecars": list(pairing.pairs),
        "orphan_sidecars": list(pairing.orphans),
    }


def _data(plan, walk, pairing, run_id, changed) -> dict:
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
        "sidecars": list(pairing.pairs),
        "orphan_sidecars": list(pairing.orphans),
        "sources_total": len(plan.sources),
    }


_BAD_NAME_ORIGIN = (
    "Names like this can come from a ZIP file made on an older Windows computer or from an old "
    "shared drive."
)


def _warn_ignored(walk, ctx) -> None:
    for item in walk.ignored:
        if item.reason == BAD_NAME and item.rel.endswith("/"):
            ctx.warn(
                "BAD_NAME_IGNORED",
                f"The folder {item.rel} and everything in it were skipped because the folder's "
                "name is not valid text.",
                f"Rename the folder to a plain name, then scan again. {_BAD_NAME_ORIGIN}",
            )
        elif item.reason == BAD_NAME:
            ctx.warn(
                "BAD_NAME_IGNORED",
                f"{item.rel} was skipped because its name is not valid text, so the plugin "
                "cannot record it.",
                f"Rename it to a plain name, then scan again. {_BAD_NAME_ORIGIN}",
            )
        elif item.reason == "link":
            ctx.warn(
                "LINK_IGNORED",
                f"{item.rel} is a link (a shortcut to somewhere else), so it was not followed.",
                "If it points to evidence, copy the file itself into the inputs folder.",
            )


def _warn_orphans(plan, pairing, ctx) -> None:
    by_id = {record["src_id"]: record for record in plan.sources}
    for src_id in pairing.orphans:
        record = by_id[src_id]
        target = orphan_target(record)
        note = next(rel for rel in sorted(record["paths"]) if sidecar_target(rel) == target)
        ctx.warn(
            "SIDECAR_ORPHAN",
            f"{note} is a note for {target}, but that file is not in inputs/.",
            "Put the file it describes next to it, or rename the note to match that file's "
            "name exactly.",
        )


def _label(kind: str) -> str:
    from epb.index import MIME_LABELS

    return MIME_LABELS.get(kind, kind)


def _warn_changes(plan, ctx) -> None:
    by_id = {record["src_id"]: record for record in plan.sources}
    for entry in plan.mime_mismatches:
        ctx.warn(
            "MIME_MISMATCH",
            f"{entry['path']} looks like {_label(entry['by_content'])} but its name says "
            f"{_label(entry['by_extension'])}. The plugin will treat it by its content.",
            "Nothing is needed if the content is right; rename the file if you prefer.",
        )
    for src_id in plan.removed:
        last = _last_paths(by_id[src_id])
        if _now_held_by(plan, last):
            text = (
                f"The content {src_id} had at {_paths_text(last)} is no longer anywhere in "
                "inputs/ (the file now holds different content)."
            )
        else:
            text = f"{_paths_text(last)} {'is' if len(last) == 1 else 'are'} no longer in inputs/."
        ctx.warn(
            "INPUT_REMOVED",
            f"{text} Its record is kept, and anything already built from it stays.",
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
    # Pairing works on the records classify returned (copies), before anything is staged, so
    # it commits in the same transaction as the records it links (WS-04).
    pairing = pair_sidecars(
        plan.sources, {rel: entry["src_id"] for rel, entry in plan.fingerprints.items()}
    )
    originals = {record["src_id"]: record for record in session.sources}
    plan.records = [record for record in plan.sources if record != originals.get(record["src_id"])]
    plan.changed = plan.changed or bool(plan.records)
    _warn_orphans(plan, pairing, ctx)
    if not plan.changed:
        message = NO_FILES if not session.sources and not walk.files else NO_CHANGES
        return Result(data=_data(plan, walk, pairing, None, False), message=message)

    _warn_changes(plan, ctx)
    _run_expanders(case_root, plan)
    summary = _summary(plan)
    run_id, run_record = runs.new_run(
        state,
        "scan",
        started_at=started_at,
        summary=summary,
        scan=_scan_record(plan, walk, pairing),
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
    message = "\n".join(
        [
            summary,
            *_change_lines(plan, pairing),
            f"Run {run_id}. See INDEX.md in the case folder for the full list.",
        ]
    )
    return Result(data=_data(plan, walk, pairing, run_id, True), message=message)
