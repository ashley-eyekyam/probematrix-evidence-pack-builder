"""The doctor registry (stub; filled in by the GREEN commit)."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ToolSpec:
    id: str
    label: str
    names: tuple
    version_args: tuple
    version_regex: str
    enables: str
    in_use: bool
    install: dict
    extra_paths: dict = field(default_factory=dict)


@dataclass(frozen=True)
class ExtraSpec:
    id: str
    file: str
    packages: tuple
    licence: str
    enables: str


REGISTRY = ()
EXTRAS = ()
