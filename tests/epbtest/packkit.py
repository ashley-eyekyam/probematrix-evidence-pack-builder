"""Synthetic evidence-pack rows and helpers for the format tests.

Every value here is invented (prefix ACM). Nothing is copied from a real incident or from
the prototype pack.
"""

import json
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from epb.formats.writer import PackMetadata

CREATED = datetime(2026, 10, 17, 0, 0, 0)

CUSTODY_ENTRY = {
    "timestamp": "2026-10-17T00:00:00Z",
    "transferred_from": "synthetic test source",
    "transferred_to": "evidence-pack-builder workspace",
    "received_by": "Investigating team",
    "action_type": "duplication",
    "condition_on_receipt": "intact",
}


def metadata(**overrides) -> PackMetadata:
    values = {
        "incident_number": "INC-ACM-2026",
        "incident_title": "Synthetic test incident (ACM)",
        "export_date": datetime(2026, 10, 17, tzinfo=timezone.utc).isoformat(),
    }
    values.update(overrides)
    return PackMetadata(**values)


def valid_row(n: int = 1, **overrides) -> dict:
    """A complete, valid Evidence Pack row; keyword overrides use header names via a dict."""
    row = {
        "Evidence ID": f"EVD-ACM-{n:03d}",
        "Type": "document",
        "Description": f"Synthetic description for test item {n}.",
        "Priority": "medium",
        "Analysis Status": "pending",
        "Tags": "pump-trip, alarm-log",
        "Linked Individuals": "Shift Supervisor",
        "Linked Equipment": "Pump P-101",
        "Source": "Synthetic test source, p.1",
        "Evidence Tag": f"TAG-ACM-{n:08d}",
        "Hash/Checksum": "sha256:" + "0" * 64,
        "Chain of Custody (JSON)": json.dumps([CUSTODY_ENTRY]),
        "Integrity Verified": "No",
        "Created At": "2026-10-17T00:00:00Z",
        "Updated At": "2026-10-17T00:00:00Z",
    }
    row.update(overrides)
    return row


def with_values(row: dict, values: dict) -> dict:
    """Return a copy of ``row`` with header-keyed ``values`` applied."""
    out = dict(row)
    out.update(values)
    return out


def sheet_xml(path: Path) -> dict[str, str]:
    """Raw XML text of every worksheet part in the workbook at ``path``."""
    with zipfile.ZipFile(path) as archive:
        return {
            name: archive.read(name).decode("utf-8")
            for name in archive.namelist()
            if re.match(r"xl/worksheets/sheet\d+\.xml$", name)
        }


def codes(findings) -> list[str]:
    return [f.code for f in findings]
