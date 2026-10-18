"""Sync-folder detection (stub; filled in by the GREEN commit)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class SyncHit:
    provider: str
    root: str | None
    reason: str


PROVIDERS = ()


def check(path, *, home=None, environ=None, platform=None):
    return []


def warning_for(hit):
    raise NotImplementedError
