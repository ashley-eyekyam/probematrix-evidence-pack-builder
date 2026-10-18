"""Run records ``.epb/runs/<NNN>/run.json`` (research Q11).

Only pipeline-level commands allocate a run: ``init`` and ``scan`` in Phase 1, the automatic
upgrade, and later ``run`` and ``build``. The run number comes from ``state["counters"]["run"]``
in the same transaction as the record, so a number is never reused. It has at least three
digits (``001``) and simply grows past ``999``.

Runs are reports, not state: ``load_runs`` skips a missing or damaged record instead of
failing, and nothing else depends on them.
"""

from pathlib import Path

from epb import __version__, fsio, schema

RUNS_DIR = ".epb/runs"
RUN_FILE = "run.json"
SCHEMA_VERSION = 1


def run_json_path(run_id: str) -> str:
    """The case-relative path of a run's record."""
    return f"{RUNS_DIR}/{run_id}/{RUN_FILE}"


def new_run(state, command, *, started_at, summary, scan=None, upgrade=None):
    """Allocate the next run number in ``state`` and return ``(run_id, record)``.

    The caller stages the record with ``stage_json(run_json_path(run_id), record, "run")``
    in the same transaction as ``state``.
    """
    counters = state["counters"]
    counters["run"] += 1
    run_id = f"{counters['run']:03d}"
    record = {
        "schema_version": SCHEMA_VERSION,
        "run": run_id,
        "command": command,
        "started_at": started_at,
        "finished_at": fsio.utc_now_iso(),
        "plugin_version": __version__,
        "summary": summary,
        "scan": scan,
        "upgrade": upgrade,
    }
    return run_id, record


def load_runs(case_root) -> list[dict]:
    """Every readable, schema-valid run record, sorted by run number."""
    folder = Path(case_root) / RUNS_DIR
    if not folder.is_dir():
        return []
    found = []
    for path in folder.glob(f"*/{RUN_FILE}"):
        try:
            record = fsio.read_json(path)
        except (OSError, UnicodeDecodeError, ValueError):
            continue
        if not isinstance(record, dict) or schema.validate(record, "run"):
            continue
        if record["run"] != path.parent.name:
            continue
        found.append(record)
    return sorted(found, key=lambda record: int(record["run"]))
