"""Real crashes at every transaction checkpoint, then a clean resume (WS-06, TST-07).

Every crash is a real ``os._exit`` in a child process (research Pitfall 11), at a checkpoint
recorded from a real run rather than a hand-kept list, so a new transaction step is covered
automatically.
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from epb import faults, txn
from epb.state import STATE_FILE
from epbtest.crash import CRASH_VAR, RECORD_VAR, assert_workspace_consistent, list_checkpoints

SCRIPTS = Path(__file__).resolve().parents[2] / "plugin/skills/evidence-pack/scripts"
INIT_ARGS = ["init", "--title", "Acme Pump Trip", "--prefix", "APT", "--timezone", "UTC", "--json"]

# A transaction that stages only state.json, run in a child so it can really crash.
STATE_ONLY_SCRIPT = """
import sys
sys.path.insert(0, sys.argv[1])
from epb import state, txn
case = sys.argv[2]
current = state.load_state(case)
transaction = txn.Transaction(case, "state-only")
transaction.set_state(current)
transaction.commit()
"""


def _new_case(tmp_path, name):
    case = tmp_path / name
    case.mkdir()
    return case


def _crash(run_epb, case, point, args=INIT_ARGS):
    return run_epb(args, case, env={CRASH_VAR: point})


def _init_points(run_epb, tmp_path):
    return list_checkpoints(run_epb, INIT_ARGS, _new_case(tmp_path, "dry-run"))


def _strip_volatile(state):
    state = dict(state)
    state["last_txn"] = {"command": state["last_txn"]["command"]}
    return state


def test_checkpoints_recorded_in_order(run_epb, tmp_path):
    points = _init_points(run_epb, tmp_path)
    assert points, "a dry run of init recorded no checkpoints"
    kinds = [point.split(":")[0] for point in points]
    first_pre = kinds.index("pre-manifest")
    assert first_pre > 0 and set(kinds[:first_pre]) == {"stage"}
    assert kinds[first_pre : first_pre + 2] == ["pre-manifest", "manifest"]
    applied = kinds[first_pre + 2 : -1]
    assert applied and set(applied) == {"apply"}
    assert kinds[-1] == "cleanup"
    staged = [point for point in points if point.startswith("stage:")]
    assert staged == [f"stage:{i}" for i in range(len(staged))]
    assert [p for p in points if p.startswith("apply:")] == [
        f"apply:{i}" for i in range(len(staged))
    ]


def test_init_resumes_after_crash_at_every_checkpoint(run_epb, tmp_path):
    points = _init_points(run_epb, tmp_path)
    tried = []
    failures = []
    for number, point in enumerate(points):
        tried.append(point)
        case = _new_case(tmp_path, f"case-{number:02d}")
        crashed = _crash(run_epb, case, point)
        if crashed.returncode != faults.CRASH_EXIT_CODE:
            failures.append(f"{point}: crash run exited {crashed.returncode}")
            continue
        resumed = run_epb(INIT_ARGS, case)
        if resumed.returncode != 0:
            failures.append(f"{point}: resume exited {resumed.returncode}: {resumed.stdout}")
            continue
        try:
            assert_workspace_consistent(case)
        except AssertionError as exc:
            failures.append(f"{point}: {exc}")
    assert len(tried) == len(points)
    assert failures == [], "\n".join(failures)


def test_crash_during_recovery_is_recovered(run_epb, case_dir):
    first = _crash(run_epb, case_dir, "apply:1")
    assert first.returncode == faults.CRASH_EXIT_CODE
    assert txn.pending_journals(case_dir)
    second = _crash(run_epb, case_dir, "recover:0")
    assert second.returncode == faults.CRASH_EXIT_CODE
    assert txn.pending_journals(case_dir)
    third = run_epb(INIT_ARGS, case_dir)
    assert third.returncode == 0, third.stdout + third.stderr
    codes = [item["code"] for item in json.loads(third.stdout)["warnings"]]
    assert "RECOVERED" in codes
    assert_workspace_consistent(case_dir)


def test_pre_and_post_manifest(run_epb, tmp_path):
    before = _new_case(tmp_path, "pre")
    assert _crash(run_epb, before, "pre-manifest").returncode == faults.CRASH_EXIT_CODE
    assert txn.recover(before) == []
    assert not (before / STATE_FILE).exists()
    assert run_epb(INIT_ARGS, before).returncode == 0
    assert (before / STATE_FILE).is_file()
    assert_workspace_consistent(before)

    after = _new_case(tmp_path, "post")
    assert _crash(run_epb, after, "manifest").returncode == faults.CRASH_EXIT_CODE
    assert len(txn.recover(after)) == 1
    assert_workspace_consistent(after)
    clean = _new_case(tmp_path, "clean")
    assert run_epb(INIT_ARGS, clean).returncode == 0
    recovered = json.loads((after / STATE_FILE).read_bytes())
    expected = json.loads((clean / STATE_FILE).read_bytes())
    assert _strip_volatile(recovered) == _strip_volatile(expected)


def _run_state_only(case, env):
    return subprocess.run(
        [sys.executable, "-c", STATE_ONLY_SCRIPT, str(SCRIPTS), str(case)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
        timeout=120,
    )


def test_state_only_transaction(run_epb, tmp_path):
    probe = _new_case(tmp_path, "probe")
    assert run_epb(INIT_ARGS, probe).returncode == 0
    record = tmp_path / "state-only-checkpoints.txt"
    dry = _run_state_only(probe, {**os.environ, RECORD_VAR: str(record)})
    assert dry.returncode == 0, dry.stderr
    points = record.read_text(encoding="utf-8").split()
    assert points == ["stage:0", "pre-manifest", "manifest", "apply:0", "cleanup"]

    tried = []
    for number, point in enumerate(points):
        tried.append(point)
        case = _new_case(tmp_path, f"state-only-{number}")
        assert run_epb(INIT_ARGS, case).returncode == 0
        crashed = _run_state_only(case, {**os.environ, CRASH_VAR: point})
        assert crashed.returncode == faults.CRASH_EXIT_CODE, (point, crashed.stderr)
        txn.recover(case)
        assert_workspace_consistent(case)
        command = json.loads((case / STATE_FILE).read_bytes())["last_txn"]["command"]
        committed = point not in ("stage:0", "pre-manifest")
        assert command == ("state-only" if committed else "init"), point
    assert len(tried) == len(points)


# --- scan --------------------------------------------------------------------------------------

SCAN_ARGS = ["scan", "--json"]
SCAN_INPUTS = {
    "inputs/a.pdf": b"%PDF-1.4\n% synthetic crash-test report\n%%EOF\n",
    "inputs/b.txt": b"Synthetic crash-test notes.\n",
    "inputs/a.pdf.note.md": b"Synthetic note: scanned from the site copy.\n",
}


def _scan_template(run_epb, tmp_path):
    """An initialised case holding two inputs and one sidecar, not yet scanned."""
    case = _new_case(tmp_path, "scan-template")
    assert run_epb(INIT_ARGS, case).returncode == 0
    for rel, data in SCAN_INPUTS.items():
        (case / rel).parent.mkdir(parents=True, exist_ok=True)
        (case / rel).write_bytes(data)
    return case


def _copy_case(template, tmp_path, name):
    case = tmp_path / name
    shutil.copytree(template, case, symlinks=True)
    return case


def _sources_view(case):
    """Source IDs with their paths and pairing, for comparing two case folders."""
    view = {}
    for path in sorted((case / ".epb" / "sources").glob("*.json")):
        record = json.loads(path.read_bytes())
        view[record["src_id"]] = (
            record["paths"],
            record["presence"],
            record["current_version"],
            record["source_kind"],
            record["sidecar_of"],
            record["sidecars"],
        )
    return view


def test_scan_resumes_after_crash_at_every_checkpoint(run_epb, tmp_path):
    template = _scan_template(run_epb, tmp_path)
    reference = _copy_case(template, tmp_path, "scan-reference")
    points = list_checkpoints(run_epb, SCAN_ARGS, _copy_case(template, tmp_path, "scan-dry-run"))
    assert points, "a dry run of scan recorded no checkpoints"
    assert points[-1] == "cleanup"
    assert run_epb(SCAN_ARGS, reference).returncode == 0
    expected = _sources_view(reference)
    assert expected["S002"][3:5] == ("sidecar", "S001")  # inputs/a.pdf.note.md pairs with a.pdf

    tried = []
    failures = []
    for number, point in enumerate(points):
        tried.append(point)
        case = _copy_case(template, tmp_path, f"scan-{number:02d}")
        crashed = _crash(run_epb, case, point, SCAN_ARGS)
        if crashed.returncode != faults.CRASH_EXIT_CODE:
            failures.append(f"{point}: crash run exited {crashed.returncode}")
            continue
        resumed = run_epb(SCAN_ARGS, case)
        if resumed.returncode != 0:
            failures.append(f"{point}: resume exited {resumed.returncode}: {resumed.stdout}")
            continue
        try:
            assert_workspace_consistent(case)
            assert _sources_view(case) == expected
        except AssertionError as exc:
            failures.append(f"{point}: {exc}")
    assert len(tried) == len(points)
    assert failures == [], "\n".join(failures)
