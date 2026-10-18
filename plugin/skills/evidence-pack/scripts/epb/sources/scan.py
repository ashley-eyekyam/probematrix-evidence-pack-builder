"""``epb scan``: take stock of ``inputs/`` (WS-02, WS-03, design §7.1, research Pattern 4).

Scan only reads ``inputs/``. It walks it without following links, fingerprints every regular
file (SHA-256, size, type and modification time), classifies the result against what the case
folder already knows (``epb.sources.classify``) and, when anything changed, writes the new and
changed source records, the fingerprints, a run record and a fresh ``INDEX.md`` in one
transaction.
"""

import os
import stat
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

from epb import fsio, mime

INPUTS_DIR = "inputs"
SOURCES_DIR = ".epb/sources"


@dataclass(frozen=True)
class FileFact:
    """One regular file found in ``inputs/``."""

    rel: str  # NFC, POSIX, relative to the case folder: "inputs/a/report.pdf"
    size: int
    mtime_ns: int
    sha256: str
    mime: str
    mime_mismatch: dict | None


@dataclass
class WalkResult:
    files: list = field(default_factory=list)  # FileFact, sorted by rel
    ignored: list = field(default_factory=list)  # Ignored, sorted by rel


def rel_key(case_root, path) -> str:
    """The path of ``path`` relative to the case folder, POSIX style and NFC-normalised."""
    rel = Path(path).relative_to(case_root).as_posix()
    return unicodedata.normalize("NFC", rel)


def walk_inputs(case_root) -> WalkResult:
    """Fingerprint every regular file under ``inputs/``, sorted by path."""
    case_root = Path(case_root)
    inputs = case_root / INPUTS_DIR
    result = WalkResult()
    if not inputs.is_dir():
        return result
    for folder, dirnames, filenames in os.walk(inputs, followlinks=False):
        dirnames.sort()
        for name in sorted(filenames):
            path = Path(folder) / name
            info = os.lstat(path)
            if not stat.S_ISREG(info.st_mode):
                continue
            detected, mismatch = mime.detect(path)
            result.files.append(
                FileFact(
                    rel=rel_key(case_root, path),
                    size=info.st_size,
                    mtime_ns=info.st_mtime_ns,
                    sha256=fsio.sha256_file(path),
                    mime=detected,
                    mime_mismatch=mismatch,
                )
            )
    result.files.sort(key=lambda fact: fact.rel)
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


def run_scan(session, ctx):
    """Scan the case folder opened as ``session`` and return the command's ``Result``."""
    import copy

    from epb import index, runs, txn
    from epb.cli import Result
    from epb.sources.classify import classify

    started_at = fsio.utc_now_iso()
    case_root = Path(session.case_root)
    walk = walk_inputs(case_root)
    state = copy.deepcopy(session.state)
    next_run = f"{state['counters']['run'] + 1:03d}"
    plan = classify(
        state["fingerprints"],
        session.sources,
        walk.files,
        run_id=next_run,
        source_counter=state["counters"]["source"],
    )

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
