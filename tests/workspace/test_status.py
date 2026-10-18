"""Run records, the run history in INDEX.md, and the read-only ``epb status`` (WS-01, WS-09,
research Pattern 2 and Q11)."""

import hashlib
import json

import pytest
from epb import __version__, fsio, runs, schema, workspace
from epb.errors import EpbError
from epb.state import STATE_FILE, new_state

INIT = [
    "init",
    "--title",
    "Acme Pump Trip",
    "--slug",
    "acme-pump-trip",
    "--prefix",
    "APT",
    "--timezone",
    "UTC",
    "--json",
]

EMPTY_SCAN = {
    "new": [],
    "new_versions": [],
    "renamed": [],
    "duplicates": [],
    "moved": [],
    "removed": [],
    "restored": [],
    "ignored": [],
    "mime_mismatches": [],
    "sidecars": [],
    "orphan_sidecars": [],
}


def _init(run_epb, case_dir):
    proc = run_epb(INIT, cwd=case_dir)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    return json.loads(proc.stdout)


def _status(run_epb, cwd):
    proc = run_epb(["status", "--json"], cwd=cwd)
    return proc, json.loads(proc.stdout)


def _snapshot(folder):
    """Every path under ``folder`` with the SHA-256 of each file (None for folders)."""
    found = {}
    for path in sorted(folder.rglob("*")):
        rel = path.relative_to(folder).as_posix()
        found[rel] = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
    return found


# --- run 001 from init ------------------------------------------------------------------------


def test_init_writes_run_001(run_epb, case_dir):
    envelope = _init(run_epb, case_dir)
    run_file = case_dir / ".epb" / "runs" / "001" / "run.json"
    assert run_file.is_file()
    record = json.loads(run_file.read_text(encoding="utf-8"))
    assert schema.validate(record, "run") == []
    assert record["run"] == "001"
    assert record["command"] == "init"
    assert record["summary"] == "Case folder created."
    assert record["scan"] is None and record["upgrade"] is None
    state = json.loads((case_dir / STATE_FILE).read_text(encoding="utf-8"))
    assert state["counters"]["run"] == 1
    assert ".epb/runs/001/run.json" in envelope["data"]["created"]


def test_index_run_history_shows_run_001(run_epb, case_dir):
    _init(run_epb, case_dir)
    text = (case_dir / "INDEX.md").read_text(encoding="utf-8")
    history = text.split("## 6. Run history\n\n", 1)[1].strip("\n").splitlines()
    assert len(history) == 1
    assert history[0].startswith("- Run 001 · ")
    assert history[0].endswith(" UTC · init · Case folder created.")
    assert "- Last run: Run 001 · " in text


# --- runs.py ----------------------------------------------------------------------------------


def test_run_json_path():
    assert runs.RUNS_DIR == ".epb/runs"
    assert runs.run_json_path("001") == ".epb/runs/001/run.json"


def test_new_run_allocates_and_validates():
    state = new_state(__version__)
    run_id, record = runs.new_run(
        state, "init", started_at="2026-10-17T10:00:00Z", summary="Case folder created."
    )
    assert run_id == "001"
    assert state["counters"]["run"] == 1
    assert record["run"] == "001"
    assert record["command"] == "init"
    assert record["started_at"] == "2026-10-17T10:00:00Z"
    assert record["plugin_version"] == __version__
    assert record["schema_version"] == 1
    assert schema.validate(record, "run") == []


@pytest.mark.parametrize(("before", "expected"), [(1, "002"), (998, "999"), (999, "1000")])
def test_run_ids_have_at_least_three_digits(before, expected):
    state = new_state(__version__)
    state["counters"]["run"] = before
    run_id, _ = runs.new_run(state, "scan", started_at=fsio.utc_now_iso(), summary="x")
    assert run_id == expected
    assert state["counters"]["run"] == before + 1


def test_scan_summary_validates_with_every_list():
    state = new_state(__version__)
    scan = dict(EMPTY_SCAN)
    scan["new"] = ["S001", "S002"]
    scan["new_versions"] = [{"src_id": "S004", "version": 2}]
    scan["ignored"] = [{"path": "inputs/.DS_Store", "reason": "junk"}]
    scan["mime_mismatches"] = [
        {
            "src_id": "S002",
            "path": "inputs/a.txt",
            "by_extension": "text/plain",
            "by_content": "application/pdf",
        }
    ]
    _, record = runs.new_run(
        state, "scan", started_at=fsio.utc_now_iso(), summary="Took stock.", scan=scan
    )
    assert schema.validate(record, "run") == []


def test_scan_summary_missing_a_list_is_invalid():
    state = new_state(__version__)
    scan = dict(EMPTY_SCAN)
    del scan["orphan_sidecars"]
    _, record = runs.new_run(state, "scan", started_at=fsio.utc_now_iso(), summary="x", scan=scan)
    assert schema.validate(record, "run") != []


@pytest.mark.parametrize(
    ("key", "value"),
    [("command", "Scan"), ("run", "01"), ("extra", 1), ("summary", 3)],
)
def test_run_record_is_closed_and_typed(key, value):
    _, record = runs.new_run(
        new_state(__version__), "init", started_at=fsio.utc_now_iso(), summary="x"
    )
    record[key] = value
    assert schema.validate(record, "run") != []


def test_upgrade_summary_validates():
    _, record = runs.new_run(
        new_state(__version__),
        "upgrade",
        started_at=fsio.utc_now_iso(),
        summary="Upgraded.",
        upgrade={
            "from": 1,
            "to": 2,
            "steps": ["1 → 2"],
            "backup_dir": ".epb/runs/002/pre-upgrade/",
        },
    )
    assert schema.validate(record, "run") == []


def _write_run(case_dir, run_id, record):
    folder = case_dir / ".epb" / "runs" / run_id
    folder.mkdir(parents=True)
    (folder / "run.json").write_bytes(fsio.json_bytes(record))


def test_load_runs_skips_missing_and_invalid_and_sorts(case_dir):
    state = new_state(__version__)
    records = {}
    for _ in range(3):
        run_id, record = runs.new_run(state, "scan", started_at=fsio.utc_now_iso(), summary="x")
        records[run_id] = record
    _write_run(case_dir, "002", records["002"])
    _write_run(case_dir, "001", records["001"])
    bad = dict(records["003"], command=7)
    _write_run(case_dir, "003", bad)
    (case_dir / ".epb" / "runs" / "004").mkdir()
    (case_dir / ".epb" / "runs" / "005").mkdir()
    (case_dir / ".epb" / "runs" / "005" / "run.json").write_text("{not json", encoding="utf-8")
    loaded = runs.load_runs(case_dir)
    assert [record["run"] for record in loaded] == ["001", "002"]


def test_load_runs_without_a_runs_folder(case_dir):
    assert runs.load_runs(case_dir) == []


# --- workspace sessions -----------------------------------------------------------------------


def test_find_workspace(case_dir, run_epb):
    with pytest.raises(EpbError) as caught:
        workspace.find_workspace(case_dir)
    assert caught.value.code == "NOT_A_WORKSPACE"
    _init(run_epb, case_dir)
    assert workspace.find_workspace(case_dir) == case_dir
    nested = case_dir / "inputs"
    with pytest.raises(EpbError):
        workspace.find_workspace(nested)  # no search of parent folders


def test_load_sources_without_a_sources_folder(case_dir):
    assert workspace.load_sources(case_dir) == []


def test_load_sources_sorted_by_number(case_dir, monkeypatch):
    checked = []
    monkeypatch.setattr(schema, "check", lambda obj, name, *, label: checked.append(name))
    folder = case_dir / ".epb" / "sources"
    folder.mkdir(parents=True)
    for src_id in ("S1000", "S999", "S002"):
        (folder / f"{src_id}.json").write_bytes(fsio.json_bytes({"src_id": src_id}))
    (folder / "notes.json").write_text("{}", encoding="utf-8")
    loaded = workspace.load_sources(case_dir)
    assert [record["src_id"] for record in loaded] == ["S002", "S999", "S1000"]
    assert checked == ["source", "source", "source"]


def test_load_sources_damaged_record_is_state_invalid(case_dir):
    folder = case_dir / ".epb" / "sources"
    folder.mkdir(parents=True)
    (folder / "S001.json").write_text("{not json", encoding="utf-8")
    with pytest.raises(EpbError) as caught:
        workspace.load_sources(case_dir)
    assert caught.value.code == "STATE_INVALID"


def test_open_for_mutation_yields_the_loaded_case(run_epb, case_dir, cli):
    _init(run_epb, case_dir)
    from epb.cli import Context

    ctx = Context(case=case_dir, json=True, verbose=False, wait=1.0)
    with workspace.open_for_mutation(case_dir, ctx, "scan") as session:
        assert session.case_root == case_dir
        assert session.case["slug"] == "acme-pump-trip"
        assert session.state["counters"]["run"] == 1
        assert session.sources == []
        assert [record["run"] for record in session.runs] == ["001"]


# --- epb status -------------------------------------------------------------------------------


def test_status_outside_a_case_folder(run_epb, case_dir):
    proc, envelope = _status(run_epb, case_dir)
    assert proc.returncode == 2, proc.stdout + proc.stderr
    assert envelope["errors"][0]["code"] == "NOT_A_WORKSPACE"
    assert list(case_dir.iterdir()) == []


def test_status_after_init(run_epb, case_dir):
    _init(run_epb, case_dir)
    proc, envelope = _status(run_epb, case_dir)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    data = envelope["data"]
    assert data["case"] == {
        "title": "Acme Pump Trip",
        "slug": "acme-pump-trip",
        "id_prefix": "APT",
        "timezone": "UTC",
    }
    assert data["inputs"] == {"total": 0, "present": 0, "removed": 0, "pending": 0}
    assert data["runs"] == 1
    assert data["last_run"]["run"] == "001"
    assert data["last_run"]["command"] == "init"
    assert data["last_run"]["finished_at"].endswith("Z")
    assert data["workbooks"] == 0
    assert envelope["warnings"] == []


def test_status_human_output(run_epb, case_dir):
    _init(run_epb, case_dir)
    proc = run_epb(["status"], cwd=case_dir)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "Acme Pump Trip" in proc.stdout


def test_status_changes_nothing(run_epb, case_dir):
    _init(run_epb, case_dir)
    before = _snapshot(case_dir)
    proc, _ = _status(run_epb, case_dir)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert _snapshot(case_dir) == before


def test_status_reports_but_never_finishes_an_interrupted_change(run_epb, case_dir):
    _init(run_epb, case_dir)
    journal = case_dir / ".epb" / "tmp" / "txn-20261018T000000Z-1-abcdef"
    journal.mkdir()
    blob = b"roles: []\n"
    (journal / "0000").write_bytes(blob)
    manifest = {
        "schema_version": 1,
        "txn": "20261018T000000Z-1-abcdef",
        "command": "scan",
        "entries": [
            {"tmp": "0000", "final": ".epb/rosters/roles.yaml", "sha256": fsio.sha256_bytes(blob)}
        ],
    }
    (journal / "manifest.json").write_bytes(fsio.json_bytes(manifest))
    before = _snapshot(case_dir)
    proc, envelope = _status(run_epb, case_dir)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert [item["code"] for item in envelope["warnings"]] == ["RECOVERY_PENDING"]
    assert "interrupted" in envelope["warnings"][0]["message"]
    assert (journal / "manifest.json").is_file()
    assert not (case_dir / ".epb" / "rosters" / "roles.yaml").exists()
    assert _snapshot(case_dir) == before
