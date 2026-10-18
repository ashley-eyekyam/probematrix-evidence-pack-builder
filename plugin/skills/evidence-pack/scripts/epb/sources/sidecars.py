"""Sidecar notes: ``<file>.note.md`` and ``<file>.note.yaml`` (WS-04, design §7.2, PF-01).

A sidecar is an input like any other: hashed, versioned and given its own source ID by
``classify``. Pairing then links it to the input it describes, by exact file name only
(``inputs/cam3.mp4.note.md`` describes ``inputs/cam3.mp4``). A misnamed note is an orphan and
is reported, which is the honest outcome (T-01-39). A sidecar's custody content is read only in
Phase 5; here it is hashed and paired.

Pairing is recomputed from the paths present now on every scan, and ``scan`` stages it in the
same transaction as the source records, so a sidecar never points at an unregistered source:

- a present source with a sidecar-named path gets ``source_kind: sidecar`` and ``sidecar_of``
  the source at the target path (``null`` when the target is not in ``inputs/``, an orphan);
- every source's ``sidecars`` lists the present sidecars that describe it, by number;
- a source removed from the folder describes nothing and is described by nothing now, but a
  removed sidecar keeps ``source_kind: sidecar``;
- a ``source_kind`` other than ``sidecar`` or ``null`` (set by a later phase) is never changed.

When a note's content sits at several sidecar paths (copies next to several files), every
target lists it, and ``sidecar_of`` is the target of its first path in sorted order.
"""

from dataclasses import dataclass, field

SIDECAR_SUFFIXES = (".note.md", ".note.yaml")
SIDECAR = "sidecar"
REMOVED = "removed from folder"


@dataclass
class PairingResult:
    """What ``pair_sidecars`` found and changed. ``pairs`` holds ``{src_id, target}`` entries
    (one per sidecar and target), ``orphans`` the IDs of present sidecars with no target, and
    ``changed`` the IDs whose pairing fields changed. All are sorted by source number."""

    pairs: list = field(default_factory=list)
    orphans: list = field(default_factory=list)
    changed: list = field(default_factory=list)


def _number(src_id) -> int:
    return int(src_id[1:])


def sidecar_target(rel: str) -> str | None:
    """The path a sidecar describes: ``rel`` without its suffix, when the remaining file name
    is not empty. ``None`` when ``rel`` is not a sidecar name (suffixes match exactly)."""
    folder, _, name = rel.rpartition("/")
    for suffix in SIDECAR_SUFFIXES:
        if name.endswith(suffix) and len(name) > len(suffix):
            target = name[: -len(suffix)]
            return f"{folder}/{target}" if folder else target
    return None


def _fields(record) -> tuple:
    return record.get("source_kind"), record.get("sidecar_of"), list(record.get("sidecars", []))


def pair_sidecars(records, current_paths) -> PairingResult:
    """Set ``source_kind``, ``sidecar_of`` and ``sidecars`` on ``records`` (changed in place)
    from ``current_paths`` (each path in ``inputs/`` now mapped to its source ID)."""
    by_id = {record["src_id"]: record for record in records}
    before = {src_id: _fields(record) for src_id, record in by_id.items()}
    order = sorted(by_id, key=_number)
    result = PairingResult()
    described: dict[str, list] = {src_id: [] for src_id in order}

    for src_id in order:
        record = by_id[src_id]
        record["sidecar_of"] = None
        if record.get("presence") == REMOVED:
            continue
        named = sorted(rel for rel in record["paths"] if sidecar_target(rel) is not None)
        if not named:
            if record.get("source_kind") == SIDECAR:
                record["source_kind"] = None  # renamed to an ordinary name
            continue
        if record.get("source_kind") not in (None, SIDECAR):
            continue  # a later phase decided what this is
        record["source_kind"] = SIDECAR
        targets = []
        for rel in named:
            target = current_paths.get(sidecar_target(rel))
            if target is not None and target != src_id and target not in targets:
                targets.append(target)
        if targets:
            record["sidecar_of"] = targets[0]
            for target in targets:
                described[target].append(src_id)
                result.pairs.append({"src_id": src_id, "target": target})
        else:
            result.orphans.append(src_id)

    for src_id in order:
        by_id[src_id]["sidecars"] = sorted(described[src_id], key=_number)
    result.changed = [src_id for src_id in order if _fields(by_id[src_id]) != before[src_id]]
    return result


def orphan_target(record) -> str | None:
    """The missing target path an orphan sidecar names (its first sidecar path in order)."""
    paths = record.get("paths") or []
    for rel in sorted(paths):
        target = sidecar_target(rel)
        if target is not None:
            return target
    return None
