"""Content-centred classification of a scan (WS-02, WS-03, research Pattern 4 and Q4).

``classify`` is a pure function: it reads the previous fingerprints, the source records and
the files found now, and returns a ``ScanPlan`` saying what to write. It never touches the
disk. The rules, in order:

1. The files found now are grouped by SHA-256; each group's paths are sorted.
2. Every known source, in numeric ID order, whose *current* content is still present keeps
   it: its paths become that group's paths. It is reported as renamed (some old paths gone,
   new ones appeared), a duplicate (paths added, none gone), restored (it had been removed
   from the folder), or not at all (unchanged). A path that belonged to another source before
   is also reported as moved.
3. Every remaining group, in order of its first path, is new content. If a source whose
   current content is gone had one of these paths, the lowest such source gets a new version
   (back to ``pending``). Otherwise the content becomes a new source with the next ID.
4. Every known source that was neither kept nor given a new version is ``removed from
   folder`` with no paths; its last known paths stay in its latest ``versions`` entry.
   Records are never deleted.
5. Only a source's current version is matched: content equal to a superseded version is new
   content (a reverted file is a new version or a new source, never a step back).

Content wins (research Q4): when a known path now holds another source's content, the path
joins that source and the old source keeps whatever paths still hold its own content.
"""

import copy
from dataclasses import dataclass, field

SOURCE_SCHEMA_VERSION = 1
PRESENT = "present"
REMOVED = "removed from folder"
PENDING = "pending"


@dataclass
class ScanPlan:
    """What a scan would change. ``changed`` is false when nothing needs writing."""

    records: list  # new and changed source records, sorted by source number
    sources: list  # every source record after the scan, sorted by source number
    fingerprints: dict  # the new state["fingerprints"]
    source_counter: int  # the new state["counters"]["source"]
    new: list = field(default_factory=list)
    new_versions: list = field(default_factory=list)
    renamed: list = field(default_factory=list)
    duplicates: list = field(default_factory=list)
    moved: list = field(default_factory=list)
    removed: list = field(default_factory=list)
    restored: list = field(default_factory=list)
    mime_mismatches: list = field(default_factory=list)
    changed: bool = False


def src_number(src_id: str) -> int:
    """``S012`` → 12."""
    return int(src_id[1:])


def format_src_id(number: int) -> str:
    """12 → ``S012``; three digits at least, growing to ``S1000`` and beyond."""
    return f"S{number:03d}"


def _current(record: dict) -> dict:
    for version in record["versions"]:
        if version["version"] == record["current_version"]:
            return version
    return record["versions"][-1]


def _known_paths(record: dict) -> list:
    """The paths a source holds now, or its last known paths when it was removed."""
    return list(record["paths"]) or list(_current(record)["paths"])


def _fingerprint(src_id, version, fact) -> dict:
    return {
        "src_id": src_id,
        "version": version,
        "sha256": fact.sha256,
        "size": fact.size,
        "mtime_ns": fact.mtime_ns,
    }


def _version_entry(number, fact, paths, run_id) -> dict:
    return {
        "version": number,
        "sha256": fact.sha256,
        "size": fact.size,
        "mime": fact.mime,
        "mtime_ns": fact.mtime_ns,
        "seen_run": run_id,
        "paths": list(paths),
    }


def _new_record(src_id, fact, paths, run_id) -> dict:
    return {
        "schema_version": SOURCE_SCHEMA_VERSION,
        "src_id": src_id,
        "current_version": 1,
        "paths": list(paths),
        "presence": PRESENT,
        "status": PENDING,
        "parents": [],
        "source_kind": None,
        "sidecar_of": None,
        "sidecars": [],
        "first_seen_run": run_id,
        "last_processed_run": None,
        "mime_mismatch": fact.mime_mismatch,
        "versions": [_version_entry(1, fact, paths, run_id)],
    }


def classify(previous, sources, files, *, run_id, source_counter) -> ScanPlan:
    """Decide what a scan changes.

    ``previous`` is ``state["fingerprints"]``, ``sources`` the source records, ``files`` the
    ``FileFact`` list found now, ``run_id`` the number the scan's run would get, and
    ``source_counter`` ``state["counters"]["source"]``. Nothing passed in is modified.
    """
    originals = {record["src_id"]: record for record in sources}
    records = {src_id: copy.deepcopy(record) for src_id, record in originals.items()}
    order = sorted(records, key=src_number)
    facts = {fact.rel: fact for fact in files}

    groups: dict[str, list] = {}
    for rel in sorted(facts):
        groups.setdefault(facts[rel].sha256, []).append(rel)

    previous_owner = {rel: entry["src_id"] for rel, entry in previous.items()}
    plan = ScanPlan(records=[], sources=[], fingerprints={}, source_counter=source_counter)
    owner: dict[str, tuple[str, int]] = {}  # path -> (src_id, version) after this scan

    def note_moves(src_id, paths):
        for rel in paths:
            before = previous_owner.get(rel)
            if before is not None and before != src_id:
                plan.moved.append({"path": rel, "from_src": before, "to_src": src_id})

    # 2. Known sources whose current content is still present keep it.
    claimed = set()
    taken = set()
    for src_id in order:
        record = records[src_id]
        sha = _current(record)["sha256"]
        if sha not in groups:
            continue
        new_paths = groups[sha]
        old_paths = sorted(record["paths"])
        claimed.add(src_id)
        taken.add(sha)
        if record["presence"] == REMOVED:
            plan.restored.append(src_id)
        else:
            gone = [rel for rel in old_paths if rel not in new_paths]
            added = [rel for rel in new_paths if rel not in old_paths]
            if gone and added:
                for index, rel in enumerate(added):
                    if index < len(gone):
                        plan.renamed.append({"src_id": src_id, "from": gone[index], "to": rel})
                    else:
                        plan.duplicates.append({"src_id": src_id, "path": rel})
            else:
                plan.duplicates.extend({"src_id": src_id, "path": rel} for rel in added)
        note_moves(src_id, [rel for rel in new_paths if rel not in old_paths])
        record["paths"] = list(new_paths)
        record["presence"] = PRESENT
        _current(record)["paths"] = list(new_paths)
        for rel in new_paths:
            owner[rel] = (src_id, record["current_version"])

    # 3. New content: a new version of a source whose content is gone, or a new source.
    versioned = set()
    remaining = sorted((paths for sha, paths in groups.items() if sha not in taken))
    for paths in remaining:
        fact = facts[paths[0]]
        candidates = [
            src_id
            for src_id in order
            if src_id not in claimed
            and src_id not in versioned
            and set(_known_paths(records[src_id])) & set(paths)
        ]
        if candidates:
            src_id = candidates[0]
            record = records[src_id]
            number = max(version["version"] for version in record["versions"]) + 1
            record["versions"].append(_version_entry(number, fact, paths, run_id))
            record["current_version"] = number
            record["paths"] = list(paths)
            record["presence"] = PRESENT
            record["status"] = PENDING
            record["mime_mismatch"] = fact.mime_mismatch
            versioned.add(src_id)
            plan.new_versions.append({"src_id": src_id, "version": number})
        else:
            plan.source_counter += 1
            src_id = format_src_id(plan.source_counter)
            record = _new_record(src_id, fact, paths, run_id)
            records[src_id] = record
            order.append(src_id)
            plan.new.append(src_id)
        note_moves(src_id, paths)
        if fact.mime_mismatch is not None:
            plan.mime_mismatches.append({"src_id": src_id, "path": paths[0], **fact.mime_mismatch})
        for rel in paths:
            owner[rel] = (src_id, record["current_version"])

    # 4. Everything else is no longer in the folder.
    for src_id in order:
        if src_id in claimed or src_id in versioned or src_id in plan.new:
            continue
        record = records[src_id]
        if record["presence"] != REMOVED:
            record["presence"] = REMOVED
            record["paths"] = []
            plan.removed.append(src_id)

    # Fingerprints: an unchanged file keeps the fingerprint it had, so touching a file without
    # changing its content is not a change.
    for rel in sorted(facts):
        src_id, version = owner[rel]
        before = previous.get(rel)
        if (
            before is not None
            and before["src_id"] == src_id
            and before["version"] == version
            and before["sha256"] == facts[rel].sha256
        ):
            plan.fingerprints[rel] = dict(before)
        else:
            plan.fingerprints[rel] = _fingerprint(src_id, version, facts[rel])

    order.sort(key=src_number)
    plan.sources = [records[src_id] for src_id in order]
    plan.records = [records[src_id] for src_id in order if records[src_id] != originals.get(src_id)]
    plan.changed = bool(plan.records) or plan.fingerprints != previous
    return plan
