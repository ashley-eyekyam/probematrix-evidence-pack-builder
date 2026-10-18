"""Fail any installed distribution uploaded to PyPI less than two weeks ago (PKG-09, D-18).

Repo-only CI tool, standard library only. CI installs the dev set with
``--uploaded-prior-to P14D``, then installs the reviewed security-exception pins from
``plugin/security-exceptions.json``, the same file ``epb doctor --setup`` installs from.
This check runs after the tests and confirms that every installed release is at least
14 days old, unless that exact package and version is a reviewed exception.

An exception whose release has since passed the two-week mark is reported as ``STALE`` so it
can be removed; that does not fail the run.

Exit codes: 0 clean, 1 violations, 2 when the exceptions file is unusable or PyPI could not
be asked about every release. ``--pins`` prints one ``package==version`` line per exception
and makes no network call.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_EXCEPTIONS = REPO_ROOT / "plugin" / "security-exceptions.json"
PYPI_RELEASE_URL = "https://pypi.org/pypi/{name}/{version}/json"

EXCEPTION_FIELDS = ("package", "version", "advisory", "reason", "reviewed_by", "reviewed_on")

EXEMPT = {
    "pip": (
        "pip is upgraded to 26.1 or later before the cutoff flag exists, "
        "so it cannot be installed under the cutoff"
    ),
}


class PyPIUnavailable(Exception):
    """PyPI could not be asked about a release (network or server failure)."""


def normalise(name: str) -> str:
    """Return the PEP 503 normalised form of a distribution name."""
    return re.sub(r"[-_.]+", "-", name).lower()


@dataclass(frozen=True)
class Finding:
    name: str
    version: str
    uploaded: datetime | None = None
    age_days: int | None = None

    def line(self, prefix: str) -> str:
        if self.uploaded is None:
            detail = "no upload time on PyPI (is it published there?)"
        else:
            detail = f"uploaded {self.uploaded.date().isoformat()}, {self.age_days} days ago"
        if prefix == "STALE":
            detail += "; the reviewed exception is now old enough and can be removed"
        return f"{prefix} {self.name} {self.version}: {detail}"


@dataclass
class Report:
    violations: list[Finding] = field(default_factory=list)
    stale: list[Finding] = field(default_factory=list)
    exempt: list[tuple[str, str]] = field(default_factory=list)
    excepted: list[Finding] = field(default_factory=list)


def _sort_key(finding: Finding) -> tuple[str, str]:
    return normalise(finding.name), finding.version


def load_exceptions(path) -> list[dict]:
    """Load and validate the reviewed exceptions file, raising ``ValueError`` on any problem."""
    path = Path(path)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ValueError(f"security exceptions file not found: {path}") from None
    except json.JSONDecodeError as exc:
        raise ValueError(f"security exceptions file is not valid JSON: {path}: {exc}") from None
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise ValueError(f"security exceptions file needs schema_version 1: {path}")
    entries = data.get("exceptions")
    if not isinstance(entries, list):
        raise ValueError(f"security exceptions file needs an 'exceptions' list: {path}")
    for number, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict):
            raise ValueError(f"security exception {number} is not an object")
        label = entry.get("package") if isinstance(entry.get("package"), str) else "?"
        for name in EXCEPTION_FIELDS:
            value = entry.get(name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    f"security exception {number} ({label}) needs a non-empty {name!r}"
                )
        try:
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", entry["reviewed_on"]):
                raise ValueError
            date.fromisoformat(entry["reviewed_on"])
        except ValueError:
            raise ValueError(
                f"security exception {number} ({label}) needs 'reviewed_on' as YYYY-MM-DD"
            ) from None
    return entries


def evaluate(installed, upload_times, exceptions, now, min_age_days=14) -> Report:
    """Apply the two-week rule.

    ``installed`` is a list of ``(name, version)``; ``upload_times`` maps
    ``(normalised name, version)`` to an aware datetime, or None when PyPI has no file for
    that release; ``exceptions`` are entries from :func:`load_exceptions`.
    """
    minimum = timedelta(days=min_age_days)
    excepted_keys = {(normalise(e["package"]), e["version"]) for e in exceptions}
    report = Report()

    def finding(name, version, uploaded):
        days = None if uploaded is None else (now - uploaded).days
        return Finding(name, version, uploaded, days)

    for name, version in installed:
        key = (normalise(name), version)
        if key[0] in EXEMPT:
            report.exempt.append((name, EXEMPT[key[0]]))
            continue
        uploaded = upload_times.get(key)
        if uploaded is not None and now - uploaded >= minimum:
            continue
        if uploaded is not None and key in excepted_keys:
            report.excepted.append(finding(name, version, uploaded))
            continue
        report.violations.append(finding(name, version, uploaded))

    for entry in exceptions:
        uploaded = upload_times.get((normalise(entry["package"]), entry["version"]))
        if uploaded is not None and now - uploaded >= minimum:
            report.stale.append(finding(entry["package"], entry["version"], uploaded))

    report.violations.sort(key=_sort_key)
    report.stale.sort(key=_sort_key)
    report.excepted.sort(key=_sort_key)
    report.exempt.sort(key=lambda item: normalise(item[0]))
    return report


def parse_upload_time(payload: dict) -> datetime | None:
    """Return the earliest file upload time in a PyPI release JSON payload, or None."""
    times = [
        datetime.fromisoformat(item["upload_time_iso_8601"])
        for item in payload.get("urls", [])
        if item.get("upload_time_iso_8601")
    ]
    return min(times) if times else None


def fetch_upload_time(name: str, version: str, timeout: float = 20.0) -> datetime | None:
    """Ask PyPI when a release was uploaded; None when PyPI does not have that release."""
    url = PYPI_RELEASE_URL.format(
        name=urllib.parse.quote(normalise(name)), version=urllib.parse.quote(version)
    )
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        raise PyPIUnavailable(f"{name} {version}: HTTP {exc.code} from PyPI") from None
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise PyPIUnavailable(f"{name} {version}: {exc}") from None
    return parse_upload_time(payload)


def installed_distributions() -> list[tuple[str, str]]:
    """Return the ``(name, version)`` of every installed distribution, without duplicates."""
    seen = {}
    for dist in importlib.metadata.distributions():
        name = dist.metadata["Name"]
        if name:
            seen.setdefault((normalise(name), dist.version), (name, dist.version))
    return sorted(seen.values(), key=lambda item: (normalise(item[0]), item[1]))


def _lookup_all(keys: list[tuple[str, str]]) -> tuple[dict, list[str]]:
    """Fetch upload times for every key, retrying a failed lookup once."""

    def lookup(key):
        last_error = None
        for _attempt in range(2):
            try:
                return key, fetch_upload_time(*key), None
            except PyPIUnavailable as exc:
                last_error = str(exc)
        return key, None, last_error

    times, errors = {}, []
    with ThreadPoolExecutor(max_workers=8) as pool:
        for key, uploaded, error in pool.map(lookup, keys):
            if error is None:
                times[(normalise(key[0]), key[1])] = uploaded
            else:
                errors.append(error)
    return times, sorted(errors)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--exceptions", type=Path, default=DEFAULT_EXCEPTIONS)
    parser.add_argument("--min-age-days", type=int, default=14)
    parser.add_argument(
        "--pins", action="store_true", help="print package==version per exception and exit"
    )
    args = parser.parse_args(argv)
    if args.min_age_days < 0:
        parser.error("--min-age-days must be 0 or more")

    try:
        exceptions = load_exceptions(args.exceptions)
    except ValueError as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 2

    if args.pins:
        for entry in sorted(exceptions, key=lambda e: normalise(e["package"])):
            print(f"{entry['package']}=={entry['version']}")
        return 0

    installed = installed_distributions()
    keys = [(name, version) for name, version in installed if normalise(name) not in EXEMPT]
    # Also look up exceptions that are not installed, so stale entries are still reported.
    seen = {(normalise(name), version) for name, version in keys}
    keys += [
        (e["package"], e["version"])
        for e in exceptions
        if (normalise(e["package"]), e["version"]) not in seen
    ]
    upload_times, errors = _lookup_all(keys)
    if errors:
        for error in errors:
            print(f"ERROR could not ask PyPI about {error}", file=sys.stderr)
        print(
            f"ERROR PyPI could not be reached for {len(errors)} of {len(keys)} releases; "
            "the dependency age is unknown.",
            file=sys.stderr,
        )
        return 2

    report = evaluate(
        installed, upload_times, exceptions, datetime.now(UTC), min_age_days=args.min_age_days
    )
    for name, reason in report.exempt:
        print(f"EXEMPT {name}: {reason}")
    for item in report.excepted:
        print(item.line("EXCEPTION"))
    for item in report.stale:
        print(item.line("STALE"))
    for item in report.violations:
        print(item.line("VIOLATION"))
    if report.violations:
        print(
            f"{len(report.violations)} installed releases are newer than "
            f"{args.min_age_days} days and are not reviewed exceptions."
        )
        return 1
    print(
        f"Dependency age check passed: {len(installed)} installed distributions, "
        f"all at least {args.min_age_days} days old or reviewed exceptions."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
