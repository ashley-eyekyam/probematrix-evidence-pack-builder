"""``epb scan``: walk, fingerprint, register and report (WS-02, D-08, research Pattern 4).

Every fixture is synthetic. Each test checks that the scan left ``inputs/`` exactly as it was.
"""

import hashlib
import json
import os
import unicodedata

import pytest
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


# --- junk, links and special files ------------------------------------------------------------

JUNK = (
    ".DS_Store",
    "Thumbs.db",
    "THUMBS.DB",
    "desktop.ini",
    "~$draft.docx",
    "._photo.jpg",
    ".~lock.report.odt#",
    "cache.tmp",
)
POSIX_ONLY = pytest.mark.skipif(os.name == "nt", reason="links and FIFOs are POSIX-only here")


def test_junk_is_listed_and_never_registered(run_epb, case_dir):
    _init(run_epb, case_dir)
    _put(case_dir, "inputs/notes.txt", NOTES_BYTES)
    for name in JUNK:
        _put(case_dir, f"inputs/sub/{name}", b"synthetic junk " + name.encode())
    envelope = _scan(run_epb, case_dir)
    assert envelope["_exit"] == 0, envelope
    ignored = {item["path"]: item["reason"] for item in envelope["data"]["ignored"]}
    assert ignored == {f"inputs/sub/{name}": "junk" for name in JUNK}
    assert envelope["data"]["new"] == ["S001"]
    assert sorted(_state(case_dir)["fingerprints"]) == ["inputs/notes.txt"]
    assert sorted(path.name for path in (case_dir / ".epb" / "sources").iterdir()) == ["S001.json"]


@POSIX_ONLY
def test_links_and_fifos_are_ignored_and_never_opened(run_epb, case_dir, tmp_path):
    _init(run_epb, case_dir)
    outside = tmp_path / "outside"
    (outside / "folder").mkdir(parents=True)
    (outside / "secret.txt").write_bytes(b"synthetic file outside the case folder")
    (outside / "folder" / "inner.txt").write_bytes(b"synthetic file in a linked folder")
    _put(case_dir, "inputs/notes.txt", NOTES_BYTES)
    os.symlink(outside / "secret.txt", case_dir / "inputs" / "file-link.txt")
    os.symlink(outside / "folder", case_dir / "inputs" / "folder-link")
    os.mkfifo(case_dir / "inputs" / "pipe")

    proc = run_epb(["scan", "--json"], cwd=case_dir, timeout=60)  # opening the FIFO would hang
    assert proc.returncode == 0, proc.stdout + proc.stderr
    envelope = json.loads(proc.stdout)
    ignored = {item["path"]: item["reason"] for item in envelope["data"]["ignored"]}
    assert ignored == {
        "inputs/file-link.txt": "link",
        "inputs/folder-link": "link",
        "inputs/pipe": "special",
    }
    codes = [item["code"] for item in envelope["warnings"]]
    assert codes.count("LINK_IGNORED") == 2
    assert envelope["data"]["new"] == ["S001"]
    assert sorted(_state(case_dir)["fingerprints"]) == ["inputs/notes.txt"]
    secret = hashlib.sha256(b"synthetic file outside the case folder").hexdigest()
    assert secret not in (case_dir / STATE_FILE).read_text(encoding="utf-8")


# --- empty inputs, empty files, identical files, unchanged rescans ----------------------------

NO_FILES = "No files found in inputs/. Put evidence files there, then scan again."
NO_CHANGES = "No changes since the last scan."


def _case_snapshot(case_dir):
    return _snapshot(case_dir)


@pytest.mark.parametrize("missing", [False, True], ids=["empty-inputs", "no-inputs-folder"])
def test_empty_inputs_writes_nothing(run_epb, case_dir, missing):
    _init(run_epb, case_dir)
    if missing:
        (case_dir / "inputs").rmdir()
    before = _case_snapshot(case_dir)
    envelope = _scan(run_epb, case_dir)
    assert envelope["_exit"] == 0, envelope
    assert envelope["data"]["changed"] is False
    assert envelope["data"]["run"] is None
    assert _case_snapshot(case_dir) == before
    human = run_epb(["scan"], cwd=case_dir)
    assert human.returncode == 0, human.stderr
    assert NO_FILES in human.stdout
    assert _case_snapshot(case_dir) == before


def test_zero_byte_file_gets_the_empty_hash(run_epb, case_dir):
    _init(run_epb, case_dir)
    _put(case_dir, "inputs/empty.txt", b"")
    envelope = _scan(run_epb, case_dir)
    assert envelope["_exit"] == 0, envelope
    version = _record(case_dir, "S001")["versions"][0]
    assert version["sha256"] == ("e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")
    assert version["size"] == 0


def test_identical_new_files_are_one_source_with_two_paths(run_epb, case_dir):
    _init(run_epb, case_dir)
    _put(case_dir, "inputs/z-copy.txt", NOTES_BYTES)
    _put(case_dir, "inputs/a/original.txt", NOTES_BYTES)
    envelope = _scan(run_epb, case_dir)
    assert envelope["data"]["new"] == ["S001"]
    record = _record(case_dir, "S001")
    assert record["paths"] == ["inputs/a/original.txt", "inputs/z-copy.txt"]
    assert record["versions"][0]["paths"] == record["paths"]
    assert _state(case_dir)["counters"]["source"] == 1


def test_new_ids_follow_nfc_code_point_order(run_epb, case_dir):
    _init(run_epb, case_dir)
    nfd = unicodedata.normalize("NFD", "inputs/été.txt")
    _put(case_dir, nfd, b"synthetic summer notes")
    _put(case_dir, "inputs/a.txt", b"synthetic lower a")
    _put(case_dir, "inputs/B.txt", b"synthetic upper B")
    envelope = _scan(run_epb, case_dir)
    assert envelope["data"]["new"] == ["S001", "S002", "S003"]
    assert _record(case_dir, "S001")["paths"] == ["inputs/B.txt"]
    assert _record(case_dir, "S002")["paths"] == ["inputs/a.txt"]
    assert _record(case_dir, "S003")["paths"] == [unicodedata.normalize("NFC", nfd)]


def test_unchanged_rescan_writes_nothing(run_epb, case_dir):
    _init(run_epb, case_dir)
    _put(case_dir, "inputs/a/report.pdf", PDF_BYTES)
    _put(case_dir, "inputs/notes.txt", NOTES_BYTES)
    _put(case_dir, "inputs/.DS_Store", b"synthetic junk")
    first = _scan(run_epb, case_dir)
    assert first["data"]["run"] == "002"
    before = _case_snapshot(case_dir)
    again = _scan(run_epb, case_dir)
    assert again["_exit"] == 0, again
    assert again["data"]["changed"] is False
    assert again["data"]["run"] is None
    assert again["data"]["sources_total"] == 2
    assert _case_snapshot(case_dir) == before
    human = run_epb(["scan"], cwd=case_dir)
    assert human.returncode == 0, human.stderr
    assert NO_CHANGES in human.stdout
    assert _case_snapshot(case_dir) == before
    assert sorted(path.name for path in (case_dir / ".epb" / "runs").iterdir()) == ["001", "002"]


# --- archives and the expander seam (PF-11, D-14) ---------------------------------------------


def test_7z_is_an_ordinary_pending_source(run_epb, case_dir):
    _init(run_epb, case_dir)
    _put(case_dir, "inputs/bundle.7z", b"7z\xbc\xaf\x27\x1c\x00\x04synthetic archive bytes")
    envelope = _scan(run_epb, case_dir)
    assert envelope["data"]["new"] == ["S001"]
    record = _record(case_dir, "S001")
    assert record["status"] == "pending"
    assert record["parents"] == []
    assert record["versions"][0]["mime"] == "application/x-7z-compressed"
    assert sorted(path.name for path in (case_dir / ".epb" / "sources").iterdir()) == ["S001.json"]


def test_expander_registry_is_empty_in_phase_1():
    from epb.sources import expanders

    assert expanders.REGISTRY == []
    assert expanders.expanders_for("application/x-7z-compressed") == []
    assert expanders.expanders_for("application/zip") == []


def test_registered_expander_is_found_by_mime(monkeypatch):
    from epb.sources import expanders

    class Fake:
        name = "fake"
        mime_types = ("application/x-fake",)

        def expand(self, path, src_id, workdir):
            return []

    monkeypatch.setattr(expanders, "REGISTRY", [])
    fake = Fake()
    expanders.register(fake)
    assert expanders.expanders_for("application/x-fake") == [fake]
    assert expanders.expanders_for("application/pdf") == []
