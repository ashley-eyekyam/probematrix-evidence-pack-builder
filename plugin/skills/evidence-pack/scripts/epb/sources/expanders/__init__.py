"""The expander seam (PF-11, D-14).

An expander unpacks a carrier input (an archive or an email) into child inputs, each of which
becomes a source of its own with the carrier in its ``parents`` (D-08). ``scan`` asks
``expanders_for(mime)`` for every new source and every new version, and runs what it gets.

The registry is empty in Phase 1, so a ``.7z``, ``.zip`` or ``.eml`` is registered as an
ordinary source and nothing is expanded. Phase 2 registers the zip and email expanders here,
and a ``.7z`` expander that runs an external ``7z``, ``7za`` or ``7zz`` program (D-14; no
py7zr). Without that program a ``.7z`` input is marked ``unprocessed: 7z tool not installed``.
"""

from pathlib import Path
from typing import Protocol


class Expander(Protocol):
    """What an expander provides."""

    name: str
    mime_types: tuple[str, ...]

    def expand(self, path: Path, src_id: str, workdir: Path) -> list:
        """Unpack ``path`` (the file of source ``src_id``) under ``workdir`` and return the
        child inputs found (Phase 2 defines their shape)."""
        ...


REGISTRY: list = []


def register(expander) -> None:
    """Add ``expander`` to the registry."""
    REGISTRY.append(expander)


def expanders_for(mime) -> list:
    """The registered expanders that handle ``mime``, in registration order."""
    return [expander for expander in REGISTRY if mime in expander.mime_types]
