"""``epb scan``: walk, fingerprint, register and report (WS-02, D-08, research Pattern 4).

Every fixture is synthetic. Each test checks that the scan left ``inputs/`` exactly as it was.
"""

import hashlib
import json

from epb import schema
from epb.state import STATE_FILE

INIT = [
    "init",
    "--title",
    "Synthetic Valve Trip",
    "--slug",
    "synthetic-valve-trip",
    "--prefix",
    "SVT",
    "--timezone",
    "UTC",
    "--json",
]
PDF_BYTES = b"%PDF-1.4\n% synthetic test report\n1 0 obj << >> endobj\n%%EOF\n"
NOTES_BYTES = b"Synthetic shift notes: valve V-1 closed at 10:05.\n"
PENDING = "waiting for conversion (coming in a later version)"


# --- helpers ----------------------------------------------------------------------------------


def _init(run_epb, case_dir):
    proc = run_epb(INIT, cwd=case_dir)
    assert proc.returncode == 0, proc.stdout + proc.stderr


def _put(case_dir, rel, data):
    path = case_dir / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def _snapshot(folder):
    """Every path under ``folder`` with the SHA-256 of each regular file."""
    if not folder.exists():
        return None
    found = {}
    for path in sorted(folder.rglob("*")):
        rel = path.relative_to(folder).as_posix()
        if path.is_symlink() or not path.is_file():
            found[rel] = "not a regular file" if not path.is_dir() else None
        else:
            found[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
    return found


def _scan(run_epb, case_dir):
    """Run ``scan --json``, check it left inputs/ untouched, and return the envelope."""
    before = _snapshot(case_dir / "inputs")
    proc = run_epb(["scan", "--json"], cwd=case_dir)
    assert _snapshot(case_dir / "inputs") == before, "scan changed inputs/"
    assert proc.stdout, proc.stderr
    envelope = json.loads(proc.stdout)
    envelope["_exit"] = proc.returncode
    envelope["_stderr"] = proc.stderr
    return envelope


def _record(case_dir, src_id):
    return json.loads((case_dir / ".epb" / "sources" / f"{src_id}.json").read_text("utf-8"))


def _state(case_dir):
    return json.loads((case_dir / STATE_FILE).read_text(encoding="utf-8"))


# --- tracer: two new inputs end to end --------------------------------------------------------


def test_scan_registers_two_new_inputs(run_epb, case_dir):
    _init(run_epb, case_dir)
    pdf = _put(case_dir, "inputs/a/report.pdf", PDF_BYTES)
    notes = _put(case_dir, "inputs/notes.txt", NOTES_BYTES)

    envelope = _scan(run_epb, case_dir)
    assert envelope["_exit"] == 0, envelope
    data = envelope["data"]
    assert data["changed"] is True
    assert data["run"] == "002"
    assert data["new"] == ["S001", "S002"]
    assert data["sources_total"] == 2

    # IDs follow sorted path order: inputs/a/report.pdf < inputs/notes.txt.
    expected = {"S001": (pdf, "inputs/a/report.pdf"), "S002": (notes, "inputs/notes.txt")}
    for src_id, (path, rel) in expected.items():
        record = _record(case_dir, src_id)
        assert schema.validate(record, "source") == []
        assert record["src_id"] == src_id
        assert record["paths"] == [rel]
        assert record["parents"] == []
        assert record["status"] == "pending"
        assert record["presence"] == "present"
        assert record["first_seen_run"] == "002"
        version = record["versions"][0]
        assert version["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
        assert version["size"] == path.stat().st_size
        assert version["mtime_ns"] == path.stat().st_mtime_ns
        assert version["paths"] == [rel]
        assert version["seen_run"] == "002"
    assert _record(case_dir, "S001")["versions"][0]["mime"] == "application/pdf"
    assert _record(case_dir, "S002")["versions"][0]["mime"] == "text/plain"


def test_scan_updates_state_and_writes_run_002(run_epb, case_dir):
    _init(run_epb, case_dir)
    _put(case_dir, "inputs/a/report.pdf", PDF_BYTES)
    _put(case_dir, "inputs/notes.txt", NOTES_BYTES)
    _scan(run_epb, case_dir)

    state = _state(case_dir)
    assert schema.validate(state, "state") == []
    assert state["counters"]["source"] == 2
    assert state["counters"]["run"] == 2
    assert sorted(state["fingerprints"]) == ["inputs/a/report.pdf", "inputs/notes.txt"]
    assert state["fingerprints"]["inputs/notes.txt"]["src_id"] == "S002"
    assert state["fingerprints"]["inputs/notes.txt"]["sha256"] == (
        hashlib.sha256(NOTES_BYTES).hexdigest()
    )
    run = json.loads((case_dir / ".epb" / "runs" / "002" / "run.json").read_text("utf-8"))
    assert schema.validate(run, "run") == []
    assert run["command"] == "scan"
    assert run["scan"]["new"] == ["S001", "S002"]
    assert list((case_dir / ".epb" / "tmp").iterdir()) == []


def test_every_source_record_validates_with_empty_parents(run_epb, case_dir):
    _init(run_epb, case_dir)
    _put(case_dir, "inputs/a/report.pdf", PDF_BYTES)
    _put(case_dir, "inputs/notes.txt", NOTES_BYTES)
    _scan(run_epb, case_dir)
    records = sorted((case_dir / ".epb" / "sources").glob("*.json"))
    assert [path.name for path in records] == ["S001.json", "S002.json"]
    for path in records:
        record = json.loads(path.read_text(encoding="utf-8"))
        assert schema.validate(record, "source") == []
        assert record["parents"] == []


def test_index_lists_both_inputs_as_waiting(run_epb, case_dir):
    _init(run_epb, case_dir)
    _put(case_dir, "inputs/a/report.pdf", PDF_BYTES)
    _put(case_dir, "inputs/notes.txt", NOTES_BYTES)
    _scan(run_epb, case_dir)
    text = (case_dir / "INDEX.md").read_text(encoding="utf-8")
    inputs = text.split("## 3. Inputs", 1)[1].split("## 4.", 1)[0]
    rows = [line for line in inputs.splitlines() if line.startswith("| S")]
    assert len(rows) == 2
    assert "inputs/a/report.pdf" in rows[0] and PENDING in rows[0]
    assert "inputs/notes.txt" in rows[1] and PENDING in rows[1]
    assert "Run 002" in text.split("## 6. Run history", 1)[1]
