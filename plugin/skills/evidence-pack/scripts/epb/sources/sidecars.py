"""Sidecar notes: ``<file>.note.md`` and ``<file>.note.yaml`` (WS-04, design §7.2, PF-01).

A sidecar is an input like any other: hashed, versioned and given its own source ID. Pairing
links it to the input it describes by exact file name. Interface only in this commit.
"""

from dataclasses import dataclass, field

SIDECAR_SUFFIXES = (".note.md", ".note.yaml")


@dataclass
class PairingResult:
    pairs: list = field(default_factory=list)
    orphans: list = field(default_factory=list)
    changed: list = field(default_factory=list)


def sidecar_target(rel: str) -> str | None:
    raise NotImplementedError


def pair_sidecars(records, current_paths) -> PairingResult:
    raise NotImplementedError
