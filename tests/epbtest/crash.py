"""Crash-test helpers: enumerate transaction checkpoints and check a case folder (TST-07).

``list_checkpoints`` records the checkpoints a real command reaches, so a new transaction step
is covered without editing any list. ``assert_workspace_consistent`` is the end state every
crash test demands after recovery: no journal left, every record valid, counters equal to the
records that use them, no ID used twice.
"""

import json
from pathlib import Path

from epb import casefile, index, runs, schema, txn, workspace
from epb.state import load_state

RECORD_VAR = "EPB_TEST_RECORD_CHECKPOINTS"
CRASH_VAR = "EPB_TEST_CRASH_AT"


def list_checkpoints(run_epb, args, cwd) -> list[str]:
    """Run ``epb <args>`` once in ``cwd`` with checkpoint recording on and return the names
    reached, in order. The record file sits next to ``cwd``, never inside the case folder."""
    cwd = Path(cwd)
    record = cwd.parent / f"{cwd.name}-checkpoints.txt"
    record.unlink(missing_ok=True)
    result = run_epb(args, cwd, env={RECORD_VAR: str(record)})
    assert result.returncode == 0, result.stdout + result.stderr
    if not record.is_file():
        return []
    return [line for line in record.read_text(encoding="utf-8").splitlines() if line]


def assert_workspace_consistent(case) -> None:
    """Fail unless the case folder is a complete, self-consistent workspace."""
    case = Path(case)
    journals = sorted(path.name for path in (case / txn.TMP_DIR).glob("txn-*"))
    assert journals == [], f"journal folders left behind: {journals}"

    state = load_state(case)
    casefile.load_case(case)

    run_records = []
    for path in sorted((case / runs.RUNS_DIR).glob(f"*/{runs.RUN_FILE}")):
        record = json.loads(path.read_bytes().decode("utf-8"))
        issues = schema.validate(record, "run")
        assert issues == [], f"{path.relative_to(case)} is invalid: {issues}"
        assert record["run"] == path.parent.name
        run_records.append(record)
    assert state["counters"]["run"] == len(run_records), (
        f"counters.run is {state['counters']['run']} but {len(run_records)} run records exist"
    )
    numbers = sorted(int(record["run"]) for record in run_records)
    assert numbers == list(range(1, len(run_records) + 1)), (
        f"run numbers reused or skipped: {numbers}"
    )

    sources = workspace.load_sources(case)  # schema-checks every record
    ids = [source["src_id"] for source in sources]
    assert len(ids) == len(set(ids)), f"duplicate source ids: {ids}"
    assert state["counters"]["source"] == len(sources), (
        f"counters.source is {state['counters']['source']} but {len(sources)} source records exist"
    )
    for key, fingerprint in state["fingerprints"].items():
        assert fingerprint["src_id"] in ids, f"fingerprint {key} points at a missing source"

    text = (case / index.INDEX_FILE).read_text(encoding="utf-8")
    headings = [line for line in text.splitlines() if line.startswith("## ")]
    assert headings == [f"## {title}" for title in index.SECTION_TITLES], headings
