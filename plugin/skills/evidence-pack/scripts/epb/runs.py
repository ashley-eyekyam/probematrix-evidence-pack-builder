"""Run records ``.epb/runs/<NNN>/run.json`` (research Q11). Interface stub for TDD RED."""

RUNS_DIR = ".epb/runs"


def run_json_path(run_id):
    raise NotImplementedError


def new_run(state, command, *, started_at, summary, scan=None, upgrade=None):
    raise NotImplementedError


def load_runs(case_root):
    raise NotImplementedError
