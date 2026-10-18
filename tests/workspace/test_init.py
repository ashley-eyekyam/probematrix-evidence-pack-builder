"""``epb init`` writes a schema-valid ``.epb/state.json`` through the journalled store (WS-01,
WS-06, WS-13)."""

import json

from epb import schema
from epb.casefile import CASE_FILE
from epb.state import SCHEMA_VERSION, STATE_FILE

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


def _envelope(proc):
    return json.loads(proc.stdout)


def test_init_creates_valid_state(run_epb, case_dir):
    proc = run_epb(INIT, cwd=case_dir)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    envelope = _envelope(proc)
    assert envelope["ok"] is True
    assert envelope["command"] == "init"
    assert envelope["data"]["created"] == [CASE_FILE, STATE_FILE]

    state_path = case_dir / STATE_FILE
    assert state_path.is_file()
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert schema.validate(state, "state") == []
    assert state["schema_version"] == SCHEMA_VERSION
    assert state["last_txn"]["command"] == "init"


def test_init_leaves_no_journal(run_epb, case_dir):
    proc = run_epb(INIT, cwd=case_dir)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    tmp_root = case_dir / ".epb" / "tmp"
    assert tmp_root.is_dir()
    assert list(tmp_root.glob("txn-*")) == []


def test_init_twice_changes_nothing(run_epb, case_dir):
    first = run_epb(INIT, cwd=case_dir)
    assert first.returncode == 0, first.stdout + first.stderr
    before = (case_dir / STATE_FILE).read_bytes()

    second = run_epb(INIT, cwd=case_dir)
    assert second.returncode == 0, second.stdout + second.stderr
    envelope = _envelope(second)
    assert [w["code"] for w in envelope["warnings"]] == ["ALREADY_SET_UP"]
    assert envelope["data"]["created"] == []
    assert (case_dir / STATE_FILE).read_bytes() == before


def test_init_missing_case_folder_is_bad_argument(run_epb, tmp_path):
    missing = tmp_path / "no-such-case"
    proc = run_epb([*INIT, "--case", str(missing)], cwd=tmp_path)
    assert proc.returncode == 2, proc.stdout + proc.stderr
    envelope = _envelope(proc)
    assert envelope["errors"][0]["code"] == "BAD_ARGUMENT"
    assert not missing.exists()


def test_init_with_case_option(run_epb, tmp_path, case_dir):
    proc = run_epb([*INIT, "--case", str(case_dir)], cwd=tmp_path)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert (case_dir / STATE_FILE).is_file()
