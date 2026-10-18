"""The format module equals an independent transcription of the importer contract (BLD-01).

The literals below are re-typed from the importer contract in the Phase 1 research
(01-RESEARCH.md, "Importer contract"), not copied from ``probematrix_v2.py``, so a typo in
either place fails this test.
"""

import openpyxl
import pytest
from epb.formats import FORMATS, get_format
from epb.formats import probematrix_v2 as fmt
from epb.formats.validate import validate_workbook
from epb.formats.writer import write_pack
from epbtest.packkit import CREATED, metadata, valid_row

CONTRACT = {
    "FORMAT_MARKER": "EVIDENCE_PACK_V2",
    "SHEET_METADATA": "Pack Metadata",
    "SHEET_EVIDENCE": "Evidence Pack",
    "SHEET_ATTACHMENTS": "Attachments Manifest",
    "SHEET_ORDER": ("Pack Metadata", "Evidence Pack", "Attachments Manifest"),
    "EVIDENCE_HEADERS": (
        "Evidence ID", "Type", "Description", "Priority", "Analysis Status", "Tags",
        "Linked Individuals", "Linked Equipment", "Source", "Collection Date",
        "Collection Method", "Collector", "Storage Location", "Evidence Tag", "Hash/Checksum",
        "Related Evidence", "Chain of Custody (JSON)", "Integrity Verified",
        "Collection Conditions", "Preservation Method", "Access Restrictions",
        "Regulatory Requirements", "Retention Category", "Retention Until", "QA Status",
        "QA Reviewed By", "QA Reviewed At", "Verification Notes", "Created At", "Updated At",
    ),
    "EVIDENCE_WIDTHS_WCH": (
        12, 18, 60, 10, 15, 25, 25, 25, 20, 15, 20, 15, 20, 15, 20,
        25, 40, 15, 25, 20, 25, 25, 15, 15, 15, 20, 22, 30, 22, 22,
    ),
    "ATTACHMENT_HEADERS": (
        "Evidence ID", "Attachment ID", "File Name", "File Type", "File Size (bytes)",
        "MIME Type", "File Hash (SHA-256)", "Uploaded By", "Uploaded At", "Integrity Status",
        "Last Verified At",
    ),
    "ATTACHMENT_WIDTHS_WCH": (12, 12, 40, 12, 15, 25, 70, 15, 22, 15, 22),
    "WIDTH_OFFSET": 0.83203125,
    "METADATA_LABELS": (
        "Evidence Pack Format", "Incident Number", "Incident Title", "Export Date",
        "Total Evidence Items", "Total Attachments",
    ),
    "METADATA_NOTES": (
        "IMPORTANT: Do not modify the structure of this file.",
        "Modifying column headers or the metadata sheet may cause import errors.",
        "Note: Attachments are listed in the Attachments Manifest sheet for reference only.",
    ),
    "METADATA_ROW_COUNT": 10,
    "REQUIRED_HEADERS": ("Evidence ID", "Type", "Description", "Priority", "Analysis Status"),
    "TYPES": (
        "witness_statement", "photograph", "document", "log_record", "recording",
        "physical_item", "lab_report", "other",
    ),
    "PRIORITIES": ("critical", "high", "medium", "low"),
    "ANALYSIS_STATUSES": ("analyzed", "pending", "requires_followup"),
    "QA_STATUSES": (
        "collected", "preserved", "under_review", "verified", "disputed", "released",
        "destroyed", "sealed",
    ),
    "RETENTION_CATEGORIES": ("regulatory", "legal", "internal", "permanent"),
    "CUSTODY_CONDITIONS": ("intact", "sealed", "damaged", "opened", "unknown"),
    "CUSTODY_ACTIONS": ("transfer", "inspection", "duplication", "return", "sealed", "unsealed"),
    "CUSTODY_REQUIRED_KEYS": ("timestamp", "transferred_from", "transferred_to", "received_by"),
    "CUSTODY_OPTIONAL_KEYS": {
        "reason": str, "condition_on_receipt": str, "verification_confirmed": bool,
        "action_type": str, "location": str, "notes": str,
    },
    "INTEGRITY_VALUES": ("Yes", "No"),
    "LIST_COLUMNS": (
        "Tags", "Linked Individuals", "Linked Equipment", "Related Evidence",
        "Regulatory Requirements",
    ),
    "LIST_SEPARATOR": ", ",
    "MAX_CELL_CHARS": 32767,
    "IMPORTER_CHECKED": "2026-10-17",
}  # fmt: skip


@pytest.mark.parametrize("name", sorted(CONTRACT))
def test_constant_matches_contract(name):
    assert getattr(fmt, name) == CONTRACT[name]


def test_counts_and_alignment():
    assert len(fmt.EVIDENCE_HEADERS) == 30 == len(fmt.EVIDENCE_WIDTHS_WCH)
    assert len(fmt.ATTACHMENT_HEADERS) == 11 == len(fmt.ATTACHMENT_WIDTHS_WCH)
    assert len(set(fmt.EVIDENCE_HEADERS)) == 30
    assert set(fmt.REQUIRED_HEADERS) <= set(fmt.EVIDENCE_HEADERS)
    assert set(fmt.LIST_COLUMNS) <= set(fmt.EVIDENCE_HEADERS)


def test_format_seam():
    assert FORMATS == {"probematrix_v2": "epb.formats.probematrix_v2"}
    assert get_format("probematrix_v2") is fmt
    with pytest.raises(KeyError):
        get_format("probematrix_v3")


@pytest.mark.parametrize("count", [0, 1, 8])
def test_totals_render_as_plain_decimal(tmp_path, count):
    path = tmp_path / "pack.xlsx"
    rows = [valid_row(n + 1) for n in range(count)]
    write_pack(path, metadata=metadata(), rows=rows, created=CREATED)
    assert validate_workbook(path) == []
    wb = openpyxl.load_workbook(path)
    try:
        assert wb[fmt.SHEET_METADATA]["B5"].value == str(count)
        assert wb[fmt.SHEET_METADATA]["B6"].value == "0"
    finally:
        wb.close()
