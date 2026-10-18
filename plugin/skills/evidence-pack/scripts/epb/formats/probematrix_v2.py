"""The ProbeMatrix ``EVIDENCE_PACK_V2`` workbook format (data only, no logic).

Every string here is a file-format constant transcribed from the importer contract in
the Phase 1 research (design §8.4, §8.5). Headers, sheet names, metadata labels and notes
must stay byte-exact: ProbeMatrix matches headers by name and reads metadata by position.
Re-check this module against the importer whenever it changes, and update
``IMPORTER_CHECKED``.
"""

# Date this module was last checked against the ProbeMatrix importer.
IMPORTER_CHECKED = "2026-10-17"

FORMAT_MARKER = "EVIDENCE_PACK_V2"

SHEET_METADATA = "Pack Metadata"
SHEET_EVIDENCE = "Evidence Pack"
SHEET_ATTACHMENTS = "Attachments Manifest"
SHEET_ORDER = (SHEET_METADATA, SHEET_EVIDENCE, SHEET_ATTACHMENTS)

EVIDENCE_HEADERS = (
    "Evidence ID",
    "Type",
    "Description",
    "Priority",
    "Analysis Status",
    "Tags",
    "Linked Individuals",
    "Linked Equipment",
    "Source",
    "Collection Date",
    "Collection Method",
    "Collector",
    "Storage Location",
    "Evidence Tag",
    "Hash/Checksum",
    "Related Evidence",
    "Chain of Custody (JSON)",
    "Integrity Verified",
    "Collection Conditions",
    "Preservation Method",
    "Access Restrictions",
    "Regulatory Requirements",
    "Retention Category",
    "Retention Until",
    "QA Status",
    "QA Reviewed By",
    "QA Reviewed At",
    "Verification Notes",
    "Created At",
    "Updated At",
)

# Column widths in SheetJS "wch" units, one per Evidence Pack header, in header order.
EVIDENCE_WIDTHS_WCH = (
    12, 18, 60, 10, 15, 25, 25, 25, 20, 15,
    20, 15, 20, 15, 20, 25, 40, 15, 25, 20,
    25, 25, 15, 15, 15, 20, 22, 30, 22, 22,
)  # fmt: skip

ATTACHMENT_HEADERS = (
    "Evidence ID",
    "Attachment ID",
    "File Name",
    "File Type",
    "File Size (bytes)",
    "MIME Type",
    "File Hash (SHA-256)",
    "Uploaded By",
    "Uploaded At",
    "Integrity Status",
    "Last Verified At",
)

ATTACHMENT_WIDTHS_WCH = (12, 12, 40, 12, 15, 25, 70, 15, 22, 15, 22)

# A ProbeMatrix export stores each column width on disk as wch + this offset.
WIDTH_OFFSET = 0.83203125

# Pack Metadata rows 1-6: column A label, column B value.
METADATA_LABELS = (
    "Evidence Pack Format",
    "Incident Number",
    "Incident Title",
    "Export Date",
    "Total Evidence Items",
    "Total Attachments",
)

# Pack Metadata rows 8-10, column A. Row 7 is blank.
METADATA_NOTES = (
    "IMPORTANT: Do not modify the structure of this file.",
    "Modifying column headers or the metadata sheet may cause import errors.",
    "Note: Attachments are listed in the Attachments Manifest sheet for reference only.",
)

METADATA_ROW_COUNT = 10
METADATA_BLANK_ROW = 7
METADATA_NOTES_FIRST_ROW = 8

REQUIRED_HEADERS = ("Evidence ID", "Type", "Description", "Priority", "Analysis Status")

TYPES = (
    "witness_statement",
    "photograph",
    "document",
    "log_record",
    "recording",
    "physical_item",
    "lab_report",
    "other",
)

PRIORITIES = ("critical", "high", "medium", "low")

ANALYSIS_STATUSES = ("analyzed", "pending", "requires_followup")

# ProbeMatrix evidence lifecycle status, imported from the QA Status column.
QA_STATUSES = (
    "collected",
    "preserved",
    "under_review",
    "verified",
    "disputed",
    "released",
    "destroyed",
    "sealed",
)

RETENTION_CATEGORIES = ("regulatory", "legal", "internal", "permanent")

CUSTODY_CONDITIONS = ("intact", "sealed", "damaged", "opened", "unknown")

CUSTODY_ACTIONS = ("transfer", "inspection", "duplication", "return", "sealed", "unsealed")

# ChainOfCustodyEntry: required keys (non-empty strings) and optional keys with their types.
CUSTODY_REQUIRED_KEYS = ("timestamp", "transferred_from", "transferred_to", "received_by")
CUSTODY_OPTIONAL_KEYS = {
    "reason": str,
    "condition_on_receipt": str,
    "verification_confirmed": bool,
    "action_type": str,
    "location": str,
    "notes": str,
}

INTEGRITY_VALUES = ("Yes", "No")

# Columns the importer splits on commas into separate entries.
LIST_COLUMNS = (
    "Tags",
    "Linked Individuals",
    "Linked Equipment",
    "Related Evidence",
    "Regulatory Requirements",
)
LIST_SEPARATOR = ", "

# Excel's per-cell character limit. openpyxl truncates longer strings silently.
MAX_CELL_CHARS = 32767
