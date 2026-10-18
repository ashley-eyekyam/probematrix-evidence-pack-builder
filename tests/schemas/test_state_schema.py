"""The WS-13 state contract and the D-07 chunk-plan contract are complete from Phase 1.

``state.json`` already declares the workbook registry, the evidence and tag counters, the item
map, per-chunk status and import records, so later phases never migrate it. Per-chunk status
holds no raw text; the chunk plan with section headings is ``ledger/chunks.json``.
"""

import copy
import json
from importlib import resources

import pytest
from epb import __version__
from epb.schema import validate
from epb.state import new_state

SHA = "a" * 64
TIMESTAMP = "2026-10-18T09:30:00Z"


def _state(**overrides):
    state = new_state(__version__)
    state.update(overrides)
    return state


def _draft_master():
    return {
        "file": "evidence-pack-synthetic-case-master.xlsx",
        "kind": "master",
        "number": 1,
        "status": "draft",
        "imported_at": None,
        "writes": [
            {
                "run": "001",
                "sha256": SHA,
                "item_count": 12,
                "tag_first": "TAG-SYN-00000001",
                "tag_last": "TAG-SYN-00000012",
                "written_at": TIMESTAMP,
            }
        ],
    }


def _imported_delta():
    return {
        "file": "evidence-pack-synthetic-case-delta-002.xlsx",
        "kind": "delta",
        "number": 2,
        "status": "imported",
        "imported_at": TIMESTAMP,
        "writes": [
            {
                "run": "004",
                "sha256": SHA,
                "item_count": 0,
                "tag_first": None,
                "tag_last": None,
                "written_at": TIMESTAMP,
            }
        ],
    }


def _chunk_status():
    return {
        "src_id": "S001",
        "version": 1,
        "seg_from": "S001-p001",
        "seg_to": "S001v2-p004",
        "status": "in_progress",
        "claim_count": 3,
    }


def _chunk_plan():
    return {
        "schema_version": 1,
        "chunks": [
            {
                "chunk_id": "S001.c001",
                "src_id": "S001",
                "version": 1,
                "section_path": ["Synthetic report", "Sequence of events"],
                "seg_ids": ["S001-p001", "S001-p002"],
                "est_tokens": 6400,
                "overlap_from": None,
            },
            {
                "chunk_id": "S001.c002",
                "src_id": "S001",
                "version": 1,
                "section_path": [],
                "seg_ids": ["S001-p002"],
                "est_tokens": 900,
                "overlap_from": "S001-p002",
            },
        ],
    }


def _schema_doc(name):
    text = resources.files("epb").joinpath("schemas", f"{name}.schema.json").read_text("utf-8")
    return json.loads(text)


# --- the state contract -----------------------------------------------------------------


def test_new_state_validates():
    assert validate(new_state(__version__), "state") == []


@pytest.mark.parametrize(
    "path",
    [("workbooks",), ("counters", "evidence"), ("counters", "tag"), ("chunks",)],
    ids=lambda path: "/".join(path),
)
def test_required_fields_are_required(path):
    state = new_state(__version__)
    target = state
    for key in path[:-1]:
        target = target[key]
    del target[path[-1]]
    assert validate(state, "state") != []


def test_draft_master_and_imported_delta_validate():
    state = _state(workbooks=[_draft_master(), _imported_delta()])
    assert validate(state, "state") == []


def test_consolidated_workbook_validates():
    record = _draft_master()
    record.update(file="evidence-pack-synthetic-case-consolidated-2026-10-18.xlsx")
    record.update(kind="consolidated")
    assert validate(_state(workbooks=[record]), "state") == []


def test_locked_workbook_status_is_invalid():
    record = _draft_master()
    record["status"] = "locked"
    issues = validate(_state(workbooks=[record]), "state")
    assert [issue.pointer for issue in issues] == ["/workbooks/0/status"]


@pytest.mark.parametrize(
    "name",
    [
        "evidence-pack-Synthetic-master.xlsx",
        "evidence-pack-synthetic-delta-2.xlsx",
        "evidence-pack-synthetic-master.xls",
        "pack-synthetic-master.xlsx",
    ],
)
def test_bad_workbook_file_name_is_invalid(name):
    record = _draft_master()
    record["file"] = name
    assert validate(_state(workbooks=[record]), "state") != []


def test_bad_tag_in_write_record_is_invalid():
    record = _draft_master()
    record["writes"][0]["tag_first"] = "TAG-syn-1"
    assert validate(_state(workbooks=[record]), "state") != []


def test_unknown_workbook_key_is_invalid():
    record = _draft_master()
    record["locked"] = True
    assert validate(_state(workbooks=[record]), "state") != []


def test_item_ref_validates():
    items = {"EVD-SYN-001": {"version_added": 1, "workbook": "evidence-pack-x-master.xlsx"}}
    assert validate(_state(items=items), "state") == []


def test_item_key_must_be_an_evidence_id():
    items = {"item-1": {"version_added": 1, "workbook": "evidence-pack-x-master.xlsx"}}
    assert validate(_state(items=items), "state") != []


def test_item_ref_rejects_unknown_key():
    items = {
        "EVD-SYN-001": {
            "version_added": 1,
            "workbook": "evidence-pack-x-master.xlsx",
            "description": "raw text",
        }
    }
    assert validate(_state(items=items), "state") != []


def test_chunk_status_validates():
    assert validate(_state(chunks={"S001.c001": _chunk_status()}), "state") == []


@pytest.mark.parametrize("key", ["section_path", "heading"])
def test_chunk_status_holds_no_raw_text(key):
    entry = _chunk_status()
    entry[key] = ["Sequence of events"] if key == "section_path" else "Sequence of events"
    issues = validate(_state(chunks={"S001.c001": entry}), "state")
    assert issues != []
    assert all(issue.pointer.startswith("/chunks/S001.c001") for issue in issues)


def test_chunk_status_rejects_unknown_status():
    entry = _chunk_status()
    entry["status"] = "skipped"
    assert validate(_state(chunks={"S001.c001": entry}), "state") != []


def test_chunk_status_rejects_bad_segment_id():
    entry = _chunk_status()
    entry["seg_from"] = "page 1"
    assert validate(_state(chunks={"S001.c001": entry}), "state") != []


def test_import_record_validates():
    record = {
        "file": "evidence-pack-synthetic-case-master.xlsx",
        "run": "003",
        "method": "mark-imported",
        "recorded_at": TIMESTAMP,
        "item_count": 12,
        "tag_first": "TAG-SYN-00000001",
        "tag_last": "TAG-SYN-00000012",
    }
    assert validate(_state(imports=[record]), "state") == []
    record["method"] = "guess"
    assert validate(_state(imports=[record]), "state") != []


def test_fingerprint_key_must_be_under_inputs():
    fingerprint = {"src_id": "S001", "version": 1, "sha256": SHA, "size": 10, "mtime_ns": 0}
    assert validate(_state(fingerprints={"inputs/a/report.pdf": fingerprint}), "state") == []
    assert validate(_state(fingerprints={"outputs/report.pdf": fingerprint}), "state") != []


def test_newer_schema_version_is_left_to_code():
    """The version check lives in load_state, so a D-09 upgrade can validate any version."""
    assert validate(_state(schema_version=2), "state") == []


# --- the chunk plan contract (ledger/chunks.json) ----------------------------------------


def test_chunk_plan_with_headings_validates():
    assert validate(_chunk_plan(), "chunks") == []


@pytest.mark.parametrize(
    "mutate",
    [
        lambda chunk: chunk.update(seg_ids=[]),
        lambda chunk: chunk.pop("seg_ids"),
        lambda chunk: chunk.update(est_tokens=-1),
        lambda chunk: chunk.update(section_path="Sequence of events"),
        lambda chunk: chunk.update(status="done"),
    ],
    ids=["empty-seg-ids", "missing-seg-ids", "negative-tokens", "heading-not-list", "extra-key"],
)
def test_bad_chunk_plan_entry_is_invalid(mutate):
    plan = _chunk_plan()
    mutate(plan["chunks"][0])
    assert validate(plan, "chunks") != []


def test_chunk_plan_needs_schema_version():
    plan = _chunk_plan()
    del plan["schema_version"]
    assert validate(plan, "chunks") != []


# --- schema hygiene ----------------------------------------------------------------------


def _object_nodes(node, where="#"):
    if isinstance(node, dict):
        if node.get("type") == "object":
            yield where, node
        for key, value in node.items():
            yield from _object_nodes(value, f"{where}/{key}")
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from _object_nodes(value, f"{where}/{index}")


@pytest.mark.parametrize("name", ["state", "chunks"])
def test_every_object_is_closed(name):
    doc = _schema_doc(name)
    nodes = list(_object_nodes(doc))
    assert nodes
    for where, node in nodes:
        closed = node.get("additionalProperties")
        if "properties" in node:
            assert closed is False, f"{name}: {where} is not closed"
        else:  # a map: every value must match a schema
            assert isinstance(closed, dict), f"{name}: {where} accepts any value"


@pytest.mark.parametrize("name", ["state", "chunks"])
def test_no_format_keywords(name):
    """jsonschema ignores format by default (research Pitfall 6); use pattern."""
    assert '"format"' not in json.dumps(_schema_doc(name))


def test_schema_ids():
    assert _schema_doc("state")["$id"] == "epb:state"
    assert _schema_doc("chunks")["$id"] == "epb:chunks"


def test_validate_does_not_mutate():
    state = _state(workbooks=[_draft_master()])
    before = copy.deepcopy(state)
    validate(state, "state")
    assert state == before
