"""The repo-only smoke-pack tool (D-16, A10): builds, validates and lists its edge values."""

import importlib.util
import re
import subprocess
import sys
from pathlib import Path

import openpyxl
import pytest
from epb.formats import probematrix_v2 as fmt
from epb.formats.validate import validate_workbook

REPO_ROOT = Path(__file__).resolve().parents[2]
TOOL = REPO_ROOT / "tools" / "make-smoke-pack.py"
EXPORT_DATE = "2026-10-17T00:00:00Z"

# (tag number, column, value exactly as written): the edge cells of the smoke table.
EDGE_CELLS = [
    (1, "Description", "=SUM(A1:A2) appears as plain text in the shift log heading."),
    (1, "Tags", "pump-trip, alarm-log, shift-handover"),
    (1, "Linked Equipment", "Pump P-101, Valve V-12, Meter M-3"),
    (1, "Collection Date", "2026-09"),
    (1, "Collection Conditions", "0"),
    (1, "Preservation Method", "40000000000000000001"),
    (2, "Description", "+44 is the dialling code written on the contractor badge."),
    (
        2,
        "Linked Individuals",
        "Shift Supervisor (Control Room), Contractor Technician A (Pump House)",
    ),
    (2, "Collection Date", "2026"),
    (3, "Description", "-5 °C was the reading on the cold-store display."),
    (3, "Collection Date", "2026-09-14"),
    (4, "Description", "@shift-lead was the channel name used in the radio log."),
    (5, "Description", "Recording of the pump-house alarm, 0 minutes 45 seconds long."),
    (
        6,
        "Description",
        "Gasket recovered from flange F-7; long ID 31000000000000000007 is stamped on it.",
    ),
    (7, "Description", "Lab sample report for oil sample OS-2."),
    (8, "Description", "Site map with zones A to D marked."),
]


@pytest.fixture(scope="module")
def tool():
    spec = importlib.util.spec_from_file_location("make_smoke_pack", TOOL)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
        yield module
    finally:
        sys.modules.pop(spec.name, None)


@pytest.fixture
def smoke(tool, tmp_path):
    path = tmp_path / "smoke.xlsx"
    items = tool.build(path, EXPORT_DATE)
    wb = openpyxl.load_workbook(path)
    try:
        rows = list(wb[fmt.SHEET_EVIDENCE].iter_rows(values_only=True))
    finally:
        wb.close()
    by_tag = {}
    tag_column = fmt.EVIDENCE_HEADERS.index("Evidence Tag")
    for row in rows[1:]:
        by_tag[row[tag_column]] = dict(zip(fmt.EVIDENCE_HEADERS, row, strict=True))
    return path, items, by_tag


def test_build_validates_and_checklist_covers_a10(smoke):
    path, items, by_tag = smoke
    assert validate_workbook(path) == []
    assert len(by_tag) == 8

    qa_values = {row["QA Status"] for row in by_tag.values()}
    assert qa_values == set(fmt.QA_STATUSES)

    for n, column, value in EDGE_CELLS:
        assert by_tag[f"TAG-ACM-{n:08d}"][column] == value, (n, column)

    def has(predicate):
        return any(predicate(item) for item in items)

    assert has(lambda i: i.column == "Description" and i.value.startswith("="))
    assert has(lambda i: i.value == "0")
    assert has(lambda i: re.fullmatch(r"\d{20}", i.value) is not None)
    assert has(lambda i: re.fullmatch(r"\d{4}-\d{2}", i.value) is not None)
    assert has(lambda i: i.column == "Tags" and "3 separate entries" in i.expected)
    assert has(lambda i: i.column == "Linked Equipment" and "3 separate entries" in i.expected)
    checklist_qa = {i.value for i in items if i.column == "QA Status"}
    assert checklist_qa == set(fmt.QA_STATUSES)

    for item in items:  # every checklist value is the exact value written
        assert by_tag[item.tag][item.column] == item.value


def test_rows_carry_the_common_fields(smoke):
    _path, _items, by_tag = smoke
    for n in range(1, 9):
        row = by_tag[f"TAG-ACM-{n:08d}"]
        assert row["Evidence ID"] == f"EVD-ACM-{n:03d}"
        assert row["Integrity Verified"] == "No"
        assert re.fullmatch(r"sha256:[0-9a-f]{64}", row["Hash/Checksum"])
        assert row["Created At"] == EXPORT_DATE == row["Updated At"]


def test_cli_writes_workbook_and_prints_checklist(tmp_path):
    out = tmp_path / "nested" / "smoke.xlsx"
    result = subprocess.run(
        [sys.executable, str(TOOL), "--out", str(out), "--export-date", EXPORT_DATE],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=120,
    )
    assert result.returncode == 0, result.stderr
    assert "Checklist" in result.stdout
    assert str(out.resolve()) in result.stdout
    assert out.is_file()
    assert validate_workbook(out) == []
