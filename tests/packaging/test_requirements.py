"""PKG-08 manifest assertions for the requirement files.

Standard library only, so this module also runs under a system pytest before the dev
environment exists.
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CORE = REPO_ROOT / "plugin" / "requirements.txt"
DEV = REPO_ROOT / "requirements-dev.txt"

TZDATA_LINE = 'tzdata; sys_platform == "win32"'

# Exact floors for the permissive core (PKG-08, D-11). tzdata has no floor (D-20).
CORE_FLOORS = {
    "jsonschema": "4.25",
    "PyYAML": "6.0.3",
    "openpyxl": "3.1.5",
    "defusedxml": "0.7.1",
    "lxml": "6.1.0",
    "charset-normalizer": "3.4.3",
    "pdfplumber": "0.11.9",
    "pypdf": "6.19.0",
    "Pillow": "12.3.0",
    "rapidfuzz": "3.14.1",
    "python-docx": "1.2.0",
    "python-pptx": "1.0.2",
    "beautifulsoup4": "4.13",
    "markdownify": "1.2.0",
}

_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*")


def requirement_lines(path: Path) -> list[str]:
    """Return the non-blank lines of a requirements file with comments removed."""
    lines = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if line:
            lines.append(line)
    return lines


def dist_name(line: str) -> str:
    match = _NAME_RE.match(line)
    assert match, f"cannot read a distribution name from {line!r}"
    return match.group(0)


def canonical(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def test_core_requirements_exact_set():
    names = {canonical(dist_name(line)) for line in requirement_lines(CORE)}
    expected = {canonical(name) for name in CORE_FLOORS} | {"tzdata"}
    assert len(expected) == 15
    assert names == expected


def test_core_floors():
    floors = {}
    for line in requirement_lines(CORE):
        if line == TZDATA_LINE:
            continue
        name, sep, version = line.partition(">=")
        assert sep, f"core line without a minimum pin: {line!r}"
        floors[name.strip()] = version.strip()
    assert floors == CORE_FLOORS
    # The PKG-08 security floors, spelled out so a change to them is deliberate.
    assert floors["lxml"] == "6.1.0"
    assert floors["pdfplumber"] == "0.11.9"
    assert floors["Pillow"] == "12.3.0"
    assert floors["pypdf"] == "6.19.0"


def test_core_uses_minimum_pins_only():
    for line in requirement_lines(CORE):
        if line == TZDATA_LINE:
            continue
        assert ">=" in line, line
        for forbidden in ("==", "~=", "<", "@ ", "://", "--hash"):
            assert forbidden not in line, f"{forbidden!r} in core line {line!r}"


def test_tzdata_windows_marker():
    tz_lines = [line for line in requirement_lines(CORE) if dist_name(line) == "tzdata"]
    assert tz_lines == [TZDATA_LINE]


def test_dev_requirements():
    assert requirement_lines(DEV) == [
        "-r plugin/requirements.txt",
        "pytest>=9.0",
        "ruff==0.16.10",
    ]
