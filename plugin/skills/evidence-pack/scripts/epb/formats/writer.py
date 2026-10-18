"""Text-only writer for ``EVIDENCE_PACK_V2`` workbooks (BLD-01, BLD-02, BLD-08).

Every cell is written as text, so a value such as ``=SUM(1,2)``, ``0`` or ``2026-09``
reaches ProbeMatrix exactly as written: never a formula, a number or a date. The writer
never changes cell text to make a pack pass. The only change it makes is removing C0
control characters, which a workbook cannot hold. Anything else that would not survive
is rejected with ``PackInvalid``.

The workbook is saved to a temporary sibling, re-read and validated from disk, and only
then moved onto the target path, so a failed write never leaves a partial or invalid file.
"""

import os
import zipfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path

from openpyxl import Workbook
from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE
from openpyxl.utils import get_column_letter
from openpyxl.writer.excel import ExcelWriter

from epb.formats import probematrix_v2 as fmt
from epb.formats.validate import Finding, validate_rows, validate_workbook


@dataclass(frozen=True)
class PackMetadata:
    """The variable values of the Pack Metadata sheet (rows 2, 3, 4 and 6, column B)."""

    incident_number: str
    incident_title: str
    export_date: str
    total_attachments: str = "0"


class PackInvalid(Exception):
    """The pack failed validation; ``findings`` lists every error found."""

    def __init__(self, findings: Sequence[Finding]):
        self.findings = list(findings)
        lines = [f"{f.code}: {f.message}" for f in self.findings]
        super().__init__("The evidence pack is not valid:\n" + "\n".join(lines))


def _strip_controls(value):
    if isinstance(value, str):
        return ILLEGAL_CHARACTERS_RE.sub("", value)
    return value


def _errors(findings: Sequence[Finding]) -> list[Finding]:
    return [f for f in findings if f.severity == "error"]


def _put_text(ws, row: int, column: int, value) -> None:
    """Write one value as a text cell. ``None`` and ``""`` write no cell at all."""
    if value is None or value == "":
        return
    if not isinstance(value, str):
        raise TypeError(f"every pack cell is text, got {type(value).__name__}")
    clean = ILLEGAL_CHARACTERS_RE.sub("", value)
    if len(clean) > fmt.MAX_CELL_CHARS:
        raise ValueError("cell text is longer than a workbook cell can hold")
    cell = ws.cell(row=row, column=column)
    cell.value = clean  # a leading '=' makes openpyxl mark this a formula...
    cell.data_type = "s"  # ...so force text: written as an inline string, never <f>
    cell.number_format = "@"


def _set_widths(ws, widths: Sequence[int]) -> None:
    for index, wch in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(index)].width = wch + fmt.WIDTH_OFFSET


def _build(metadata: PackMetadata, rows: Sequence[Mapping], created: datetime) -> Workbook:
    wb = Workbook()
    meta_ws = wb.active
    meta_ws.title = fmt.SHEET_METADATA
    evidence_ws = wb.create_sheet(fmt.SHEET_EVIDENCE)
    attachments_ws = wb.create_sheet(fmt.SHEET_ATTACHMENTS)

    values = (
        fmt.FORMAT_MARKER,
        metadata.incident_number,
        metadata.incident_title,
        metadata.export_date,
        str(len(rows)),
        metadata.total_attachments,
    )
    for row_number, (label, value) in enumerate(
        zip(fmt.METADATA_LABELS, values, strict=True), start=1
    ):
        _put_text(meta_ws, row_number, 1, label)
        _put_text(meta_ws, row_number, 2, value)
    for offset, note in enumerate(fmt.METADATA_NOTES):
        _put_text(meta_ws, fmt.METADATA_NOTES_FIRST_ROW + offset, 1, note)

    for column, header in enumerate(fmt.EVIDENCE_HEADERS, start=1):
        _put_text(evidence_ws, 1, column, header)
    for row_number, row in enumerate(rows, start=2):
        for column, header in enumerate(fmt.EVIDENCE_HEADERS, start=1):
            _put_text(evidence_ws, row_number, column, row.get(header))
    _set_widths(evidence_ws, fmt.EVIDENCE_WIDTHS_WCH)

    for column, header in enumerate(fmt.ATTACHMENT_HEADERS, start=1):
        _put_text(attachments_ws, 1, column, header)
    _set_widths(attachments_ws, fmt.ATTACHMENT_WIDTHS_WCH)

    wb.properties.created = created
    wb.properties.modified = created
    return wb


def _save(wb: Workbook, path: Path) -> None:
    # openpyxl's Workbook.save stamps the modified time with the wall clock; writing
    # through ExcelWriter keeps the injected time, so the properties are reproducible.
    archive = zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED, allowZip64=True)
    try:
        ExcelWriter(wb, archive).save()
    finally:
        archive.close()


def write_pack(path, *, metadata: PackMetadata, rows: Sequence[Mapping], created: datetime) -> Path:
    """Validate, write and re-validate an evidence pack at ``path``.

    ``rows`` are mappings from Evidence Pack header to a ``str`` value or ``None``.
    ``created`` sets the workbook's created and modified properties. Raises
    ``PackInvalid`` before writing when a value would not survive, and after writing
    when the saved file does not validate; the target path is untouched in both cases.
    """
    path = Path(path)
    metadata = replace(
        metadata,
        incident_number=_strip_controls(metadata.incident_number),
        incident_title=_strip_controls(metadata.incident_title),
        export_date=_strip_controls(metadata.export_date),
        total_attachments=_strip_controls(metadata.total_attachments),
    )
    rows = [{key: _strip_controls(value) for key, value in row.items()} for row in rows]

    errors = _errors(validate_rows(metadata, rows))
    if errors:
        raise PackInvalid(errors)

    wb = _build(metadata, rows, created)
    tmp = path.with_name(path.name + ".tmp")
    try:
        _save(wb, tmp)
        errors = _errors(validate_workbook(tmp))
        if errors:
            raise PackInvalid(errors)
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink()
    return path
