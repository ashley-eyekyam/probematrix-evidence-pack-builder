"""Two-week dependency-age check (PKG-09, D-18). Interface skeleton; logic lands in GREEN."""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_EXCEPTIONS = REPO_ROOT / "plugin" / "security-exceptions.json"

EXEMPT: dict[str, str] = {}


class PyPIUnavailable(Exception):
    """PyPI could not be asked about a release."""


@dataclass(frozen=True)
class Finding:
    name: str
    version: str
    uploaded: object = None
    age_days: int | None = None

    def line(self, prefix: str) -> str:
        return ""


@dataclass
class Report:
    violations: list = field(default_factory=list)
    stale: list = field(default_factory=list)
    exempt: list = field(default_factory=list)
    excepted: list = field(default_factory=list)


def normalise(name: str) -> str:
    return name


def load_exceptions(path) -> list[dict]:
    return []


def evaluate(installed, upload_times, exceptions, now, min_age_days=14) -> Report:
    return Report()


def parse_upload_time(payload: dict):
    return None


def fetch_upload_time(name: str, version: str, timeout: float = 20.0):
    raise PyPIUnavailable("not implemented")


def installed_distributions() -> list[tuple[str, str]]:
    return []


def main(argv: list[str] | None = None) -> int:
    return 0


if __name__ == "__main__":
    sys.exit(main())
