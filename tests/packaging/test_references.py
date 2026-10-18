"""The router skill's references stay in step with the code (D-04, D-06, BLD-01).

``references/workspace-contract.md`` must describe every path in ``epb.workspace`` with its
sharing class, and ``references/evidence-pack-v2.md`` must carry every header, enum, metadata
string and validator finding code from the format module and the validator, plus the date
the format was last checked against the importer. A change to the code that is not written
into the reference fails here.
"""

import ast
import re
from pathlib import Path

import pytest
from epb import workspace
from epb.formats import probematrix_v2 as fmt
from epb.sources import scan, sidecars

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_DIR = REPO_ROOT / "plugin" / "skills" / "evidence-pack"
REFERENCES = SKILL_DIR / "references"
CONTRACT = REFERENCES / "workspace-contract.md"
FORMAT = REFERENCES / "evidence-pack-v2.md"
VALIDATOR = SKILL_DIR / "scripts" / "epb" / "formats" / "validate.py"
CODE_RE = re.compile(r"^[A-Z]+(?:_[A-Z]+)+$")

ENUMS = {
    "TYPES": fmt.TYPES,
    "PRIORITIES": fmt.PRIORITIES,
    "ANALYSIS_STATUSES": fmt.ANALYSIS_STATUSES,
    "QA_STATUSES": fmt.QA_STATUSES,
    "RETENTION_CATEGORIES": fmt.RETENTION_CATEGORIES,
    "CUSTODY_CONDITIONS": fmt.CUSTODY_CONDITIONS,
    "CUSTODY_ACTIONS": fmt.CUSTODY_ACTIONS,
    "INTEGRITY_VALUES": fmt.INTEGRITY_VALUES,
}


def read(path):
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def finding_codes():
    """Every finding code the validator can emit: the upper-case snake-case string literals
    in ``formats/validate.py``."""
    tree = ast.parse(VALIDATOR.read_text(encoding="utf-8"))
    return sorted(
        {
            node.value
            for node in ast.walk(tree)
            if isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and CODE_RE.match(node.value)
        }
    )


FINDING_CODES = finding_codes()


def test_both_references_exist():
    assert CONTRACT.is_file(), "references/workspace-contract.md is missing"
    assert FORMAT.is_file(), "references/evidence-pack-v2.md is missing"


# --- workspace-contract.md -------------------------------------------------------------------


@pytest.mark.parametrize(
    ("path", "classification"),
    [(path, classification) for path, classification, _ in workspace.CONTRACT_PATHS],
    ids=[path for path, _, _ in workspace.CONTRACT_PATHS],
)
def test_contract_path_listed_with_its_classification(path, classification):
    lines = read(CONTRACT).splitlines()
    assert any(f"`{path}`" in line and classification in line for line in lines), (
        f"no line in workspace-contract.md names `{path}` together with {classification!r}"
    )


@pytest.mark.parametrize("classification", workspace.CLASSIFICATIONS)
def test_contract_explains_every_classification(classification):
    assert f"**{classification}**" in read(CONTRACT)


@pytest.mark.parametrize("line", workspace.GITIGNORE_LINES)
def test_contract_lists_every_ignored_folder(line):
    assert f"`{line}`" in read(CONTRACT)


@pytest.mark.parametrize(
    "phrase",
    [
        workspace.GITATTRIBUTES_TEXT.strip(),
        "S004v2",
        "S1000",
        "parents",
        "schema_version",
        "pre-upgrade",
        "- [ ] Imported:",
        "content wins",
        "STATE_INVALID",
        "WORKSPACE_TOO_NEW",
        "LOCK_TIMEOUT",
    ],
)
def test_contract_phrases(phrase):
    assert phrase in read(CONTRACT)


@pytest.mark.parametrize("pattern", scan.JUNK_PATTERNS)
def test_contract_lists_every_junk_pattern(pattern):
    assert f"`{pattern}`" in read(CONTRACT)


@pytest.mark.parametrize("suffix", sidecars.SIDECAR_SUFFIXES)
def test_contract_names_sidecar_suffixes(suffix):
    assert f"<file>{suffix}" in read(CONTRACT)


def test_contract_says_reverted_content_is_new_content():
    text = re.sub(r"\s+", " ", read(CONTRACT)).lower()
    assert "older version" in text
    assert "counts as new content" in text


# --- evidence-pack-v2.md ---------------------------------------------------------------------


def test_format_records_the_importer_check_date():
    assert fmt.IMPORTER_CHECKED == "2026-10-17"
    assert f"Checked against the ProbeMatrix importer on {fmt.IMPORTER_CHECKED}" in read(FORMAT)


@pytest.mark.parametrize(
    ("header", "width"),
    list(zip(fmt.EVIDENCE_HEADERS, fmt.EVIDENCE_WIDTHS_WCH, strict=True)),
    ids=list(fmt.EVIDENCE_HEADERS),
)
def test_format_lists_every_evidence_header_with_its_width(header, width):
    lines = read(FORMAT).splitlines()
    assert any(f"`{header}`" in line and f"| {width} |" in line for line in lines), (
        f"no table row for `{header}` with width {width}"
    )


@pytest.mark.parametrize("header", fmt.ATTACHMENT_HEADERS)
def test_format_lists_every_attachment_header(header):
    assert f"`{header}`" in read(FORMAT)


@pytest.mark.parametrize(
    "value",
    [(name, value) for name, values in ENUMS.items() for value in values],
    ids=[f"{name}:{value}" for name, values in ENUMS.items() for value in values],
)
def test_format_lists_every_enum_value(value):
    assert f"`{value[1]}`" in read(FORMAT)


@pytest.mark.parametrize("text", fmt.METADATA_LABELS + fmt.METADATA_NOTES)
def test_format_quotes_every_metadata_string(text):
    assert text in read(FORMAT)


@pytest.mark.parametrize(
    "text",
    [
        fmt.FORMAT_MARKER,
        *fmt.SHEET_ORDER,
        str(fmt.MAX_CELL_CHARS),
        f"`{fmt.LIST_SEPARATOR}`",
        *fmt.CUSTODY_REQUIRED_KEYS,
        *fmt.CUSTODY_OPTIONAL_KEYS,
        "-IMP1",
    ],
)
def test_format_names_the_fixed_strings(text):
    assert text in read(FORMAT)


def test_validator_has_finding_codes():
    assert len(FINDING_CODES) >= 20, FINDING_CODES


@pytest.mark.parametrize("code", FINDING_CODES)
def test_format_explains_every_finding_code(code):
    assert f"`{code}`" in read(FORMAT)


# --- both ------------------------------------------------------------------------------------


@pytest.mark.parametrize("path", [CONTRACT, FORMAT], ids=lambda p: p.name)
def test_no_todo_and_no_parent_paths(path):
    text = read(path)
    assert text, f"{path.name} is empty or missing"
    assert "TODO" not in text
    assert "../" not in text and "..\\" not in text
