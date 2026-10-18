"""Validator for ``EVIDENCE_PACK_V2`` workbooks, stricter than the ProbeMatrix importer.

Two entry points return findings with stable codes:

- ``validate_rows(metadata, rows)`` checks the values before anything is written.
- ``validate_workbook(path)`` re-reads a saved workbook from disk, because formulas and
  truncation happen at write time and only the file shows them.

Every finding is collected; validation never stops at the first problem. Findings are
sorted by sheet order, row, column and code, so two runs over the same input list them
identically.
"""

import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path

import openpyxl
from openpyxl.utils import get_column_letter

from epb.formats import probematrix_v2 as fmt


@dataclass(frozen=True)
class Finding:
    """One validation problem. ``cell`` is an A1 reference, or None for a sheet-level finding."""

    code: str
    sheet: str | None
    cell: str | None
    column: str | None
    message: str
    severity: str = "error"


_CELL_REF = re.compile(r"^([A-Z]+)(\d+)$")


def _column_index(letters: str) -> int:
    index = 0
    for ch in letters:
        index = index * 26 + (ord(ch) - ord("A") + 1)
    return index


def _sort_key(finding: Finding) -> tuple:
    if finding.sheet is None:
        sheet_index = -1
    elif finding.sheet in fmt.SHEET_ORDER:
        sheet_index = fmt.SHEET_ORDER.index(finding.sheet)
    else:
        sheet_index = len(fmt.SHEET_ORDER)
    row = col = 0
    match = _CELL_REF.match(finding.cell or "")
    if match:
        col = _column_index(match.group(1))
        row = int(match.group(2))
    return (sheet_index, row, col, finding.code, finding.column or "", finding.message)


def _finish(findings: Iterable[Finding]) -> list[Finding]:
    """Drop repeats of the same code on the same cell, then sort deterministically."""
    seen: set[tuple] = set()
    unique: list[Finding] = []
    for finding in findings:
        if finding.cell is not None:
            key = (finding.code, finding.sheet, finding.cell)
        else:
            key = (finding.code, finding.sheet, finding.column, finding.message)
        if key in seen:
            continue
        seen.add(key)
        unique.append(finding)
    return sorted(unique, key=_sort_key)


def _ref(column_number: int, row_number: int) -> str:
    return f"{get_column_letter(column_number)}{row_number}"


def _is_blank(value) -> bool:
    return value is None or (isinstance(value, str) and value.strip() == "")


# ---------------------------------------------------------------------------
# Value rules shared by validate_rows and validate_workbook
# ---------------------------------------------------------------------------


def _cell_findings(value, sheet: str, cell: str, column: str | None) -> list[Finding]:
    """Rules that apply to every cell on every sheet."""
    if value is None:
        return []
    where = f"{column} ({cell})" if column else cell
    if not isinstance(value, str):
        return [
            Finding(
                "CELL_NOT_TEXT",
                sheet,
                cell,
                column,
                f"{where} holds a {type(value).__name__} value; every cell must be text.",
            )
        ]
    return []


def _exact_enum(value, allowed: tuple, code: str, sheet, cell, column, *, blank_ok: bool):
    if value is None or value == "":
        if blank_ok:
            return []
        return [
            Finding(code, sheet, cell, column, f"{column} ({cell}) is blank; use one of {allowed}.")
        ]
    if not isinstance(value, str) or value in allowed:
        return []
    return [
        Finding(
            code,
            sheet,
            cell,
            column,
            f"{column} ({cell}) is {value!r}; it must be exactly one of {', '.join(allowed)}.",
        )
    ]


def _row_findings(row: Mapping, row_number: int, columns: Mapping[str, int]) -> list[Finding]:
    """Rules for one Evidence Pack data row. ``columns`` maps header name to column number."""
    sheet = fmt.SHEET_EVIDENCE
    out: list[Finding] = []

    def ref(header: str) -> str:
        return _ref(columns.get(header, fmt.EVIDENCE_HEADERS.index(header) + 1), row_number)

    for header in ("Evidence ID", "Type", "Description"):
        value = row.get(header)
        if _is_blank(value):
            out.append(
                Finding(
                    "REQUIRED_BLANK",
                    sheet,
                    ref(header),
                    header,
                    f"{header} ({ref(header)}) is blank; every item needs one.",
                )
            )

    if not _is_blank(row.get("Type")):
        out += _exact_enum(
            row.get("Type"), fmt.TYPES, "ENUM_INVALID", sheet, ref("Type"), "Type", blank_ok=False
        )
    for header, allowed in (
        ("Priority", fmt.PRIORITIES),
        ("Analysis Status", fmt.ANALYSIS_STATUSES),
    ):
        out += _exact_enum(
            row.get(header), allowed, "ENUM_INVALID", sheet, ref(header), header, blank_ok=False
        )
    return out


# ---------------------------------------------------------------------------
# validate_rows: before writing
# ---------------------------------------------------------------------------


def validate_rows(metadata, rows) -> list[Finding]:
    """Check pack metadata and item rows before they are written.

    ``metadata`` is a ``PackMetadata``; ``rows`` is a sequence of mappings from Evidence Pack
    header to a ``str`` value or ``None``.
    """
    findings: list[Finding] = []
    meta_values = (
        (2, metadata.incident_number),
        (3, metadata.incident_title),
        (4, metadata.export_date),
        (6, metadata.total_attachments),
    )
    for row_number, value in meta_values:
        label = fmt.METADATA_LABELS[row_number - 1]
        findings += _cell_findings(value, fmt.SHEET_METADATA, f"B{row_number}", label)

    columns = {header: index + 1 for index, header in enumerate(fmt.EVIDENCE_HEADERS)}
    for index, row in enumerate(rows):
        row_number = index + 2
        for key in row:
            if key not in columns:
                findings.append(
                    Finding(
                        "HEADERS_INVALID",
                        fmt.SHEET_EVIDENCE,
                        None,
                        str(key),
                        f"Row {row_number} has a value for {key!r}, which is not an "
                        "Evidence Pack column.",
                    )
                )
        for header, column_number in columns.items():
            findings += _cell_findings(
                row.get(header), fmt.SHEET_EVIDENCE, _ref(column_number, row_number), header
            )
        findings += _row_findings(row, row_number, columns)
    return _finish(findings)


# ---------------------------------------------------------------------------
# validate_workbook: the saved file
# ---------------------------------------------------------------------------


def _sheet_grid(ws) -> list[tuple]:
    max_column = ws.max_column or 0
    max_row = ws.max_row or 0
    if max_column == 0 or max_row == 0:
        return []
    return [
        tuple(row)
        for row in ws.iter_rows(
            min_row=1, max_row=max_row, min_col=1, max_col=max_column, values_only=True
        )
    ]


def _empty(value) -> bool:
    return value is None or value == ""


def _check_metadata(grid: list[tuple], data_rows: int) -> list[Finding]:
    sheet = fmt.SHEET_METADATA
    out: list[Finding] = []
    expected: dict[tuple[int, int], str | None] = {}
    for index, label in enumerate(fmt.METADATA_LABELS):
        expected[(index + 1, 1)] = label
        expected[(index + 1, 2)] = None  # a value cell: checked below
    for index, note in enumerate(fmt.METADATA_NOTES):
        expected[(fmt.METADATA_NOTES_FIRST_ROW + index, 1)] = note

    def value_at(row_number: int, column_number: int):
        if row_number > len(grid):
            return None
        row = grid[row_number - 1]
        return row[column_number - 1] if column_number <= len(row) else None

    for row_index, row in enumerate(grid, start=1):
        for column_index, value in enumerate(row, start=1):
            out += _cell_findings(value, sheet, _ref(column_index, row_index), None)
            if _empty(value) or (row_index, column_index) in expected:
                continue
            out.append(
                Finding(
                    "METADATA_LAYOUT",
                    sheet,
                    _ref(column_index, row_index),
                    None,
                    f"Pack Metadata cell {_ref(column_index, row_index)} must be empty; the "
                    f"sheet has exactly {fmt.METADATA_ROW_COUNT} rows in a fixed layout.",
                )
            )

    for (row_number, column_number), text in expected.items():
        if text is None:
            continue
        actual = value_at(row_number, column_number)
        if actual != text:
            out.append(
                Finding(
                    "METADATA_LAYOUT",
                    sheet,
                    _ref(column_number, row_number),
                    None,
                    f"Pack Metadata {_ref(column_number, row_number)} is {actual!r}; "
                    f"it must be exactly {text!r}.",
                )
            )

    marker = value_at(1, 2)
    if marker != fmt.FORMAT_MARKER:
        out.append(
            Finding(
                "FORMAT_MARKER",
                sheet,
                "B1",
                fmt.METADATA_LABELS[0],
                f"Pack Metadata B1 is {marker!r}; it must be exactly {fmt.FORMAT_MARKER!r}.",
            )
        )
    total = value_at(5, 2)
    if total != str(data_rows):
        out.append(
            Finding(
                "METADATA_TOTAL_MISMATCH",
                sheet,
                "B5",
                fmt.METADATA_LABELS[4],
                f"Total Evidence Items (B5) is {total!r} but the Evidence Pack sheet has "
                f"{data_rows} item rows; it must be {str(data_rows)!r}.",
            )
        )
    attachments = value_at(6, 2)
    if attachments != "0":
        out.append(
            Finding(
                "METADATA_ATTACHMENTS",
                sheet,
                "B6",
                fmt.METADATA_LABELS[5],
                f"Total Attachments (B6) is {attachments!r}; packs carry no attachments, "
                "so it must be '0'.",
            )
        )
    return out


def _check_header_row(grid, expected: tuple, sheet: str, code: str) -> list[Finding]:
    header_row = grid[0] if grid else ()
    actual = tuple(header_row[: len(expected)])
    extra = [value for value in header_row[len(expected) :] if not _empty(value)]
    if actual == expected and not extra:
        return []
    return [
        Finding(
            code,
            sheet,
            "A1",
            None,
            f"The {sheet} header row must be exactly the {len(expected)} headers in order.",
        )
    ]


def _data_rows(grid: list[tuple]) -> list[tuple[int, tuple]]:
    return [
        (row_number, row)
        for row_number, row in enumerate(grid[1:], start=2)
        if any(not _empty(value) for value in row)
    ]


def _check_evidence(grid: list[tuple]) -> list[Finding]:
    sheet = fmt.SHEET_EVIDENCE
    out = _check_header_row(grid, fmt.EVIDENCE_HEADERS, sheet, "HEADERS_INVALID")
    header_row = grid[0] if grid else ()
    columns: dict[str, int] = {}
    for column_number, header in enumerate(header_row, start=1):
        if header in fmt.EVIDENCE_HEADERS and header not in columns:
            columns[header] = column_number
    names = {number: name for name, number in columns.items()}

    for column_number, header in enumerate(header_row, start=1):
        out += _cell_findings(header, sheet, _ref(column_number, 1), None)

    for row_number, row in _data_rows(grid):
        mapping: dict[str, object] = {}
        for column_number, value in enumerate(row, start=1):
            name = names.get(column_number)
            out += _cell_findings(value, sheet, _ref(column_number, row_number), name)
            if name is not None:
                mapping[name] = value
            elif not _empty(value):
                out.append(
                    Finding(
                        "HEADERS_INVALID",
                        sheet,
                        _ref(column_number, row_number),
                        None,
                        f"{_ref(column_number, row_number)} holds a value in a column with no "
                        "Evidence Pack header.",
                    )
                )
        out += _row_findings(mapping, row_number, columns)
    return out


def _check_attachments(grid: list[tuple]) -> list[Finding]:
    sheet = fmt.SHEET_ATTACHMENTS
    out = _check_header_row(grid, fmt.ATTACHMENT_HEADERS, sheet, "ATTACHMENTS_INVALID")
    for row_index, row in enumerate(grid, start=1):
        for column_index, value in enumerate(row, start=1):
            out += _cell_findings(value, sheet, _ref(column_index, row_index), None)
    for row_number, _row in _data_rows(grid):
        out.append(
            Finding(
                "ATTACHMENTS_INVALID",
                sheet,
                f"A{row_number}",
                None,
                f"Attachments Manifest row {row_number} has content; the sheet holds headers only.",
            )
        )
    return out


def validate_workbook(path) -> list[Finding]:
    """Re-read a saved workbook from disk and return every finding."""
    path = Path(path)
    findings: list[Finding] = []
    with open(path, "rb") as handle:
        try:
            wb = openpyxl.load_workbook(handle, read_only=True, data_only=False)
        except Exception as exc:  # any unreadable workbook is a structural failure
            return [
                Finding(
                    "SHEETS_INVALID",
                    None,
                    None,
                    None,
                    f"The file could not be read as a workbook: {type(exc).__name__}.",
                )
            ]
        try:
            names = list(wb.sheetnames)
            if names != list(fmt.SHEET_ORDER):
                findings.append(
                    Finding(
                        "SHEETS_INVALID",
                        None,
                        None,
                        None,
                        f"The sheets are {names}; they must be exactly "
                        f"{list(fmt.SHEET_ORDER)} in that order.",
                    )
                )
            grids = {name: _sheet_grid(wb[name]) for name in names if name in fmt.SHEET_ORDER}
        finally:
            wb.close()

    evidence = grids.get(fmt.SHEET_EVIDENCE)
    data_rows = len(_data_rows(evidence)) if evidence is not None else 0
    if fmt.SHEET_METADATA in grids:
        findings += _check_metadata(grids[fmt.SHEET_METADATA], data_rows)
    if evidence is not None:
        findings += _check_evidence(evidence)
    if fmt.SHEET_ATTACHMENTS in grids:
        findings += _check_attachments(grids[fmt.SHEET_ATTACHMENTS])
    return _finish(findings)
