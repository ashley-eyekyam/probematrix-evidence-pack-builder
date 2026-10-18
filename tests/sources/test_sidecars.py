"""Sidecar notes travel with their inputs (WS-04, design §7.2, PF-01).

Every fixture is synthetic. Scans run in-process through the ``cli`` fixture.
"""

import hashlib
import json

import pytest
from epb import schema

INIT = [
    "init",
    "--title",
    "Synthetic Camera Review",
    "--slug",
    "synthetic-camera-review",
    "--prefix",
    "SCR",
    "--timezone",
    "UTC",
    "--json",
]
VIDEO = b"\x00\x00\x00\x18ftypisom\x00\x00\x02\x00isomiso2synthetic video bytes"
NOTE = b"# Camera 3\n\nSynthetic note: recorded by the shift supervisor role.\n"
NOTE_YAML = b"camera: 3\nrecorded_by: shift supervisor (synthetic)\n"


# --- helpers ----------------------------------------------------------------------------------


def _init(cli, case):
    result = cli([*INIT, "--case", str(case)])
    assert result.exit_code == 0, result.stdout + result.stderr


def _put(case, rel, data):
    path = case / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def _scan(cli, case):
    result = cli(["scan", "--json", "--case", str(case)])
    assert result.exit_code == 0, result.stdout + result.stderr
    envelope = result.envelope
    for path in sorted((case / ".epb" / "sources").glob("*.json")):
        record = json.loads(path.read_text("utf-8"))
        assert schema.validate(record, "source") == [], path.name
    if envelope["data"]["run"] is not None:
        assert schema.validate(_run(case, envelope["data"]["run"]), "run") == []
    return envelope


def _record(case, src_id):
    return json.loads((case / ".epb" / "sources" / f"{src_id}.json").read_text("utf-8"))


def _run(case, run_id):
    return json.loads((case / ".epb" / "runs" / run_id / "run.json").read_text("utf-8"))


def _issues(case):
    text = (case / "INDEX.md").read_text(encoding="utf-8")
    return text.split("## 5. Open issues", 1)[1].split("\n## ", 1)[0]


def _warnings(envelope, code):
    return [item for item in envelope["warnings"] if item["code"] == code]


def _pairing(case, src_id):
    record = _record(case, src_id)
    return record["source_kind"], record["sidecar_of"], record["sidecars"]


# --- naming -----------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("rel", "target"),
    [
        ("inputs/cam3.mp4.note.md", "inputs/cam3.mp4"),
        ("inputs/a/cam3.mp4.note.yaml", "inputs/a/cam3.mp4"),
        ("inputs/log.note.md", "inputs/log"),
        ("inputs/.note.md", None),
        ("inputs/sub/.note.yaml", None),
        ("inputs/cam3.mp4", None),
        ("inputs/cam3.note.txt", None),
        ("inputs/cam3.mp4.NOTE.md", None),
    ],
)
def test_sidecar_target(rel, target):
    from epb.sources.sidecars import SIDECAR_SUFFIXES, sidecar_target

    assert SIDECAR_SUFFIXES == (".note.md", ".note.yaml")
    assert sidecar_target(rel) == target


# --- pairing through scan ---------------------------------------------------------------------


def test_note_md_is_paired_with_its_input(cli, case_dir):
    _init(cli, case_dir)
    video = _put(case_dir, "inputs/cam3.mp4", VIDEO)
    note = _put(case_dir, "inputs/cam3.mp4.note.md", NOTE)
    envelope = _scan(cli, case_dir)
    assert envelope["data"]["new"] == ["S001", "S002"]
    assert _pairing(case_dir, "S001") == (None, None, ["S002"])
    assert _pairing(case_dir, "S002") == ("sidecar", "S001", [])
    assert _record(case_dir, "S001")["versions"][0]["sha256"] == (
        hashlib.sha256(video.read_bytes()).hexdigest()
    )
    assert _record(case_dir, "S002")["versions"][0]["sha256"] == (
        hashlib.sha256(note.read_bytes()).hexdigest()
    )
    assert envelope["data"]["sidecars"] == [{"src_id": "S002", "target": "S001"}]
    assert envelope["data"]["orphan_sidecars"] == []
    run = _run(case_dir, "002")
    assert run["scan"]["sidecars"] == [{"src_id": "S002", "target": "S001"}]
    assert run["scan"]["orphan_sidecars"] == []
    assert _warnings(envelope, "SIDECAR_ORPHAN") == []


def test_note_md_pairing_is_shown_in_the_human_report(cli, case_dir):
    _init(cli, case_dir)
    _put(case_dir, "inputs/cam3.mp4", VIDEO)
    _put(case_dir, "inputs/cam3.mp4.note.md", NOTE)
    result = cli(["scan", "--case", str(case_dir)])
    assert result.exit_code == 0, result.stderr
    assert "S002 inputs/cam3.mp4.note.md: a note for S001 (inputs/cam3.mp4)" in result.stdout


def test_note_yaml_is_paired_the_same_way(cli, case_dir):
    _init(cli, case_dir)
    _put(case_dir, "inputs/cam3.mp4", VIDEO)
    _put(case_dir, "inputs/cam3.mp4.note.yaml", NOTE_YAML)
    envelope = _scan(cli, case_dir)
    assert _pairing(case_dir, "S001") == (None, None, ["S002"])
    assert _pairing(case_dir, "S002") == ("sidecar", "S001", [])
    assert envelope["data"]["sidecars"] == [{"src_id": "S002", "target": "S001"}]


def test_a_bare_note_name_is_an_ordinary_input(cli, case_dir):
    _init(cli, case_dir)
    _put(case_dir, "inputs/.note.md", b"synthetic notes with no target name")
    _put(case_dir, "inputs/sub/.note.yaml", b"synthetic: yaml with no target name\n")
    envelope = _scan(cli, case_dir)
    assert envelope["data"]["new"] == ["S001", "S002"]
    for src_id in ("S001", "S002"):
        assert _pairing(case_dir, src_id) == (None, None, [])
    assert envelope["data"]["sidecars"] == []
    assert envelope["data"]["orphan_sidecars"] == []
    assert _warnings(envelope, "SIDECAR_ORPHAN") == []


def test_orphan_sidecar_is_reported(cli, case_dir):
    _init(cli, case_dir)
    _put(case_dir, "inputs/cam9.mp4.note.md", NOTE)
    envelope = _scan(cli, case_dir)
    assert _pairing(case_dir, "S001") == ("sidecar", None, [])
    orphans = _warnings(envelope, "SIDECAR_ORPHAN")
    assert [item["message"] for item in orphans] == [
        "inputs/cam9.mp4.note.md is a note for inputs/cam9.mp4, but that file is not in inputs/."
    ]
    assert envelope["data"]["orphan_sidecars"] == ["S001"]
    assert _run(case_dir, "002")["scan"]["orphan_sidecars"] == ["S001"]
    assert "S001 (inputs/cam9.mp4.note.md) is a note for inputs/cam9.mp4" in _issues(case_dir)


def test_renaming_target_and_sidecar_together_keeps_the_pairing(cli, case_dir):
    _init(cli, case_dir)
    _put(case_dir, "inputs/cam3.mp4", VIDEO)
    _put(case_dir, "inputs/cam3.mp4.note.md", NOTE)
    _scan(cli, case_dir)
    (case_dir / "inputs/site").mkdir()
    for name in ("cam3.mp4", "cam3.mp4.note.md"):
        (case_dir / "inputs" / name).rename(case_dir / "inputs/site" / name)
    envelope = _scan(cli, case_dir)
    assert envelope["data"]["new"] == []
    assert [entry["src_id"] for entry in envelope["data"]["renamed"]] == ["S001", "S002"]
    assert _pairing(case_dir, "S001") == (None, None, ["S002"])
    assert _pairing(case_dir, "S002") == ("sidecar", "S001", [])
    assert envelope["data"]["sidecars"] == [{"src_id": "S002", "target": "S001"}]


def test_deleting_the_target_orphans_the_sidecar_until_it_returns(cli, case_dir):
    _init(cli, case_dir)
    _put(case_dir, "inputs/cam3.mp4", VIDEO)
    _put(case_dir, "inputs/cam3.mp4.note.md", NOTE)
    _scan(cli, case_dir)
    (case_dir / "inputs/cam3.mp4").unlink()
    gone = _scan(cli, case_dir)
    assert gone["data"]["removed"] == ["S001"]
    assert gone["data"]["orphan_sidecars"] == ["S002"]
    assert _pairing(case_dir, "S002") == ("sidecar", None, [])
    assert _pairing(case_dir, "S001") == (None, None, [])
    assert len(_warnings(gone, "SIDECAR_ORPHAN")) == 1
    assert "is a note for inputs/cam3.mp4" in _issues(case_dir)

    _put(case_dir, "inputs/cam3.mp4", VIDEO)
    back = _scan(cli, case_dir)
    assert back["data"]["restored"] == ["S001"]
    assert back["data"]["sidecars"] == [{"src_id": "S002", "target": "S001"}]
    assert back["data"]["orphan_sidecars"] == []
    assert _pairing(case_dir, "S001") == (None, None, ["S002"])
    assert _pairing(case_dir, "S002") == ("sidecar", "S001", [])
    assert "is a note for" not in _issues(case_dir)


def test_a_target_added_later_is_paired(cli, case_dir):
    _init(cli, case_dir)
    _put(case_dir, "inputs/cam3.mp4.note.md", NOTE)
    _scan(cli, case_dir)
    assert _pairing(case_dir, "S001") == ("sidecar", None, [])
    _put(case_dir, "inputs/cam3.mp4", VIDEO)
    envelope = _scan(cli, case_dir)
    assert envelope["data"]["new"] == ["S002"]
    assert _pairing(case_dir, "S001") == ("sidecar", "S002", [])
    assert _pairing(case_dir, "S002") == (None, None, ["S001"])
    assert _warnings(envelope, "SIDECAR_ORPHAN") == []


def test_editing_a_sidecar_makes_a_new_version(cli, case_dir):
    _init(cli, case_dir)
    _put(case_dir, "inputs/cam3.mp4", VIDEO)
    _put(case_dir, "inputs/cam3.mp4.note.md", NOTE)
    _scan(cli, case_dir)
    _put(case_dir, "inputs/cam3.mp4.note.md", NOTE + b"\nSynthetic addendum.\n")
    envelope = _scan(cli, case_dir)
    assert envelope["data"]["new_versions"] == [{"src_id": "S002", "version": 2}]
    assert envelope["data"]["new"] == []
    assert _record(case_dir, "S002")["current_version"] == 2
    assert _pairing(case_dir, "S002") == ("sidecar", "S001", [])
    assert _pairing(case_dir, "S001") == (None, None, ["S002"])


def test_a_removed_sidecar_is_not_an_orphan(cli, case_dir):
    _init(cli, case_dir)
    _put(case_dir, "inputs/cam3.mp4", VIDEO)
    _put(case_dir, "inputs/cam3.mp4.note.md", NOTE)
    _scan(cli, case_dir)
    (case_dir / "inputs/cam3.mp4.note.md").unlink()
    envelope = _scan(cli, case_dir)
    assert envelope["data"]["removed"] == ["S002"]
    assert envelope["data"]["orphan_sidecars"] == []
    assert _warnings(envelope, "SIDECAR_ORPHAN") == []
    assert _pairing(case_dir, "S001") == (None, None, [])
    assert _record(case_dir, "S002")["source_kind"] == "sidecar"
    issues = _issues(case_dir)
    assert "S002 (inputs/cam3.mp4.note.md) was removed from the folder" in issues
    assert "is a note for" not in issues


# --- pair_sidecars on its own -----------------------------------------------------------------


def _bare(src_id, paths, presence="present"):
    return {
        "src_id": src_id,
        "paths": list(paths) if presence == "present" else [],
        "presence": presence,
        "source_kind": None,
        "sidecar_of": None,
        "sidecars": [],
        "current_version": 1,
        "versions": [{"version": 1, "paths": list(paths)}],
    }


def test_pair_sidecars_sets_both_sides_and_reports_changes():
    from epb.sources.sidecars import pair_sidecars

    records = [
        _bare("S001", ["inputs/cam3.mp4"]),
        _bare("S002", ["inputs/cam3.mp4.note.md"]),
        _bare("S003", ["inputs/cam4.mp4.note.yaml"]),
    ]
    current = {rel: record["src_id"] for record in records for rel in record["paths"]}
    result = pair_sidecars(records, current)
    assert result.pairs == [{"src_id": "S002", "target": "S001"}]
    assert result.orphans == ["S003"]
    assert result.changed == ["S001", "S002", "S003"]
    assert records[0]["sidecars"] == ["S002"]
    assert records[1]["sidecar_of"] == "S001"
    assert records[2]["source_kind"] == "sidecar" and records[2]["sidecar_of"] is None

    again = pair_sidecars(records, current)
    assert again.changed == []
    assert again.pairs == result.pairs and again.orphans == result.orphans


def test_pair_sidecars_never_overwrites_another_kind():
    from epb.sources.sidecars import pair_sidecars

    records = [_bare("S001", ["inputs/cam3.mp4"])]
    records[0]["source_kind"] = "cctv"
    result = pair_sidecars(records, {"inputs/cam3.mp4": "S001"})
    assert records[0]["source_kind"] == "cctv"
    assert result.changed == []
