#!/usr/bin/env python3
"""Build the Phase 1 synthetic smoke workbook for the owner's ProbeMatrix import (D-16, A10).

Repo-only tool: it is never shipped in plugin/. It writes eight synthetic items (prefix
ACM) that exercise every edge case the importer must keep as text: a Description that
starts with =, + , - or @, a 0 value, 20-digit IDs, YYYY and YYYY-MM dates, multi-entry
list columns and every QA Status value. The workbook is written with the real format
module and validator, to a git-ignored scratch path. Nothing it writes is committed.

The tool prints a checklist of every edge value as written. The owner imports the
workbook and compares; only the owner reports the import result.

Usage:
    .venv/bin/python tools/make-smoke-pack.py [--out PATH] [--export-date ISO]
"""

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = REPO_ROOT / "plugin" / "skills" / "evidence-pack" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from epb.formats.writer import PackInvalid, PackMetadata, write_pack  # noqa: E402

DEFAULT_OUT = REPO_ROOT / "scratch" / "smoke" / "evidence-pack-smoke.xlsx"

INCIDENT_NUMBER = "INC-ACM-2026"
INCIDENT_TITLE = "Smoke test: synthetic edge cases (ACM)"

CUSTODY = json.dumps(
    [
        {
            "timestamp": "2026-10-17T00:00:00Z",
            "transferred_from": "synthetic smoke test",
            "transferred_to": "evidence-pack-builder workspace",
            "received_by": "Investigating team",
            "action_type": "duplication",
            "condition_on_receipt": "intact",
        }
    ]
)

# One entry per smoke row: Type, Priority, Analysis Status, QA Status, Description, and
# the other edge cells of that row.
ROWS = (
    (
        "document",
        "critical",
        "pending",
        "collected",
        "=SUM(A1:A2) appears as plain text in the shift log heading.",
        {
            "Tags": "pump-trip, alarm-log, shift-handover",
            "Linked Equipment": "Pump P-101, Valve V-12, Meter M-3",
            "Collection Date": "2026-09",
            "Collection Conditions": "0",
            "Preservation Method": "40000000000000000001",
        },
    ),
    (
        "witness_statement",
        "high",
        "analyzed",
        "preserved",
        "+44 is the dialling code written on the contractor badge.",
        {
            "Linked Individuals": (
                "Shift Supervisor (Control Room), Contractor Technician A (Pump House)"
            ),
            "Collection Date": "2026",
        },
    ),
    (
        "photograph",
        "medium",
        "requires_followup",
        "under_review",
        "-5 °C was the reading on the cold-store display.",
        {"Collection Date": "2026-09-14"},
    ),
    (
        "log_record",
        "low",
        "pending",
        "verified",
        "@shift-lead was the channel name used in the radio log.",
        {},
    ),
    (
        "recording",
        "medium",
        "pending",
        "disputed",
        "Recording of the pump-house alarm, 0 minutes 45 seconds long.",
        {},
    ),
    (
        "physical_item",
        "high",
        "analyzed",
        "released",
        "Gasket recovered from flange F-7; long ID 31000000000000000007 is stamped on it.",
        {},
    ),
    (
        "lab_report",
        "critical",
        "requires_followup",
        "destroyed",
        "Lab sample report for oil sample OS-2.",
        {},
    ),
    (
        "other",
        "low",
        "pending",
        "sealed",
        "Site map with zones A to D marked.",
        {},
    ),
)


@dataclass(frozen=True)
class ChecklistItem:
    """One value the owner compares after the import."""

    tag: str
    column: str
    value: str
    expected: str


def _tag(n: int) -> str:
    return f"TAG-ACM-{n:08d}"


def smoke_rows(export_date: str) -> list[dict]:
    """The eight synthetic Evidence Pack rows, keyed by header."""
    rows = []
    for n, (kind, priority, status, qa, description, extra) in enumerate(ROWS, start=1):
        digest = hashlib.sha256(f"smoke-row-{n}".encode("ascii")).hexdigest()
        row = {
            "Evidence ID": f"EVD-ACM-{n:03d}",
            "Type": kind,
            "Description": description,
            "Priority": priority,
            "Analysis Status": status,
            "Source": "Synthetic smoke test, p.1",
            "Evidence Tag": _tag(n),
            "Hash/Checksum": f"sha256:{digest}",
            "Chain of Custody (JSON)": CUSTODY,
            "Integrity Verified": "No",
            "QA Status": qa,
            "Created At": export_date,
            "Updated At": export_date,
        }
        row.update(extra)
        rows.append(row)
    return rows


def _entries(value: str) -> str:
    parts = value.split(", ")
    return f"shows as {len(parts)} separate entries: " + " | ".join(parts)


def checklist(rows: list[dict]) -> list[ChecklistItem]:
    """Every edge value as written, with what ProbeMatrix should display."""
    items: list[ChecklistItem] = []

    def add(n: int, column: str, expected: str) -> None:
        items.append(ChecklistItem(_tag(n), column, rows[n - 1][column], expected))

    exact = "shows exactly as written, as text"
    add(1, "Description", exact + ", starting with =SUM(A1:A2); no computed number")
    add(1, "Tags", _entries(rows[0]["Tags"]))
    add(1, "Linked Equipment", _entries(rows[0]["Linked Equipment"]))
    add(1, "Collection Date", "shows exactly 2026-09; not a full date or a date serial number")
    add(1, "Collection Conditions", "shows exactly 0; not blank")
    add(1, "Preservation Method", "shows all 20 digits; not scientific notation or rounded")
    add(2, "Description", exact + ", starting with +44")
    add(2, "Linked Individuals", _entries(rows[1]["Linked Individuals"]))
    add(2, "Collection Date", "shows exactly 2026; not a number or a full date")
    add(3, "Description", exact + ", starting with -5 °C")
    add(3, "Collection Date", "shows exactly 2026-09-14; not a date serial number")
    add(4, "Description", exact + ", starting with @shift-lead")
    add(6, "Description", exact + ", with all 20 digits of the stamped ID")
    for n in range(1, len(rows) + 1):
        add(n, "QA Status", f"lifecycle status shows {rows[n - 1]['QA Status']}")
    return items


def _created(export_date: str) -> datetime:
    moment = datetime.fromisoformat(export_date.replace("Z", "+00:00"))
    if moment.tzinfo is not None:
        moment = moment.astimezone(timezone.utc).replace(tzinfo=None)
    return moment


def build(out_path, export_date: str) -> list[ChecklistItem]:
    """Write the smoke workbook to ``out_path`` and return its checklist.

    Raises ``PackInvalid`` when the pack does not validate; nothing is left at
    ``out_path`` in that case.
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    rows = smoke_rows(export_date)
    metadata = PackMetadata(
        incident_number=INCIDENT_NUMBER,
        incident_title=INCIDENT_TITLE,
        export_date=export_date,
    )
    write_pack(out_path, metadata=metadata, rows=rows, created=_created(export_date))
    return checklist(rows)


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")


def _iso(text: str) -> str:
    try:
        _created(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"not an ISO 8601 date-time: {text!r}") from None
    return text


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="make-smoke-pack.py",
        description="Build the synthetic smoke workbook for the ProbeMatrix import check.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUT,
        help="where to write the workbook (default: scratch/smoke/evidence-pack-smoke.xlsx)",
    )
    parser.add_argument(
        "--export-date",
        type=_iso,
        default=None,
        help="Export Date and Created/Updated At values (default: now, UTC)",
    )
    args = parser.parse_args(argv)
    out_path = args.out.resolve()
    try:
        items = build(out_path, args.export_date or _now())
    except PackInvalid as exc:
        print("The smoke workbook did not validate:", file=sys.stderr)
        for finding in exc.findings:
            print(f"  {finding.code}: {finding.message}", file=sys.stderr)
        return 1

    print("Checklist")
    print(f"Workbook: {out_path}")
    print("Import it into a new test incident in ProbeMatrix, then compare each value:")
    for number, item in enumerate(items, start=1):
        print(f'{number:2d}. {item.tag} | {item.column} | "{item.value}" | {item.expected}')
    return 0


if __name__ == "__main__":
    sys.exit(main())
