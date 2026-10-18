"""Automatic upgrade of a case folder written by an older plugin (D-09).

Every persisted state file carries ``schema_version``. When ``.epb/state.json`` is older than
``epb.state.SCHEMA_VERSION``, the next command that changes the case folder upgrades it,
while holding the workspace lock and after recovery:

1. the registered steps from the stored version up to the current one are collected; a
   missing step is a plugin bug (``INTERNAL_ERROR``) and nothing is written;
2. a run is allocated, and byte copies of ``.epb/state.json``, ``.epb/case.yaml`` and every
   ``.epb/sources/*.json`` are staged under ``.epb/runs/<NNN>/pre-upgrade/``;
3. the steps run on an in-memory snapshot ``{"state", "case", "sources"}``, then the upgraded
   files, the run record and a re-rendered ``INDEX.md`` are staged, ``state.json`` last, and
   committed in one journalled transaction;
4. a plain-language ``WORKSPACE_UPGRADED`` warning says what happened and where the copy is.

Read-only commands never upgrade; they only warn ``UPGRADE_PENDING``. A step is a function
keyed by the version it upgrades *from*; it changes the snapshot in place and never touches
the disk. v0.1.0 is the first workspace version, so it registers no step.
"""

import copy
import re
from collections.abc import Callable
from pathlib import Path

from epb import __version__, casefile, fsio, index, runs, txn, yamlio
from epb import state as state_module
from epb.errors import EpbError

UPGRADE_STEPS: dict[int, Callable[[dict], None]] = {}

_SOURCE_NAME = re.compile(r"^S\d{3,}\.json$")
_REPORT_HINT = (
    "Report this error code to the plugin maintainer. Do not edit the evidence or the .epb folder."
)
_RESTORE_HINT = (
    "Restore the .epb folder from a backup or from version control if you keep one. "
    "Do not edit it by hand, and do not ask the agent to repair it."
)


def needs_upgrade(state_dict) -> bool:
    """Whether this state was written by an older workspace version than the plugin's."""
    return state_dict["schema_version"] < state_module.SCHEMA_VERSION


def _damaged(rel) -> EpbError:
    return EpbError(
        "STATE_INVALID",
        f"The file {rel} is damaged and cannot be read safely, so the case folder cannot be "
        "upgraded.",
        hint=_RESTORE_HINT,
    )


def _sources_dir() -> str:
    from epb.workspace import SOURCES_DIR  # imported here: epb.workspace imports this module

    return SOURCES_DIR


def _source_paths(case_root: Path) -> list[str]:
    folder = case_root / _sources_dir()
    if not folder.is_dir():
        return []
    names = sorted(path.name for path in folder.iterdir() if _SOURCE_NAME.match(path.name))
    return [f"{_sources_dir()}/{name}" for name in names]


def load_snapshot(case_root, state_dict) -> dict:
    """The files an upgrade step may change, read as they are on disk (no schema check: they
    follow the older version's schemas)."""
    case_root = Path(case_root)
    try:
        text = (case_root / casefile.CASE_FILE).read_bytes().decode("utf-8")
        case = yamlio.load_text_yaml(text, source=casefile.CASE_FILE)
    except (OSError, UnicodeDecodeError, yamlio.YamlTextError):
        raise _damaged(casefile.CASE_FILE) from None
    if not isinstance(case, dict):
        raise _damaged(casefile.CASE_FILE)
    sources = []
    for rel in _source_paths(case_root):
        try:
            record = fsio.read_json(case_root / rel)
        except (OSError, UnicodeDecodeError, ValueError):
            raise _damaged(rel) from None
        if not isinstance(record, dict) or not isinstance(record.get("src_id"), str):
            raise _damaged(rel)
        sources.append(record)
    return {"state": copy.deepcopy(state_dict), "case": case, "sources": sources}


def _steps(stored: int, current: int) -> list[tuple[int, Callable[[dict], None]]]:
    steps = []
    for version in range(stored, current):
        step = UPGRADE_STEPS.get(version)
        if step is None:
            raise EpbError(
                "INTERNAL_ERROR",
                f"No upgrade step from workspace version {version}; this is a plugin bug.",
                hint=_REPORT_HINT,
                data={"from": stored, "to": current},
            )
        steps.append((version, step))
    return steps


def run_upgrade(case_root, ctx, snapshot) -> dict:
    """Upgrade the case folder to the plugin's workspace version in one transaction, keeping
    a copy of the old state files, and return the upgraded snapshot."""
    case_root = Path(case_root)
    current = state_module.SCHEMA_VERSION
    stored = snapshot["state"]["schema_version"]
    steps = _steps(stored, current)  # before anything is staged
    started_at = fsio.utc_now_iso()
    backup_paths = [state_module.STATE_FILE, casefile.CASE_FILE, *_source_paths(case_root)]
    backups = [(rel, (case_root / rel).read_bytes()) for rel in backup_paths]

    upgraded = copy.deepcopy(snapshot)
    for _, step in steps:
        step(upgraded)
    new_state = upgraded["state"]
    new_state["schema_version"] = current
    new_state["plugin_version"] = __version__
    upgraded["case"]["schema_version"] = str(current)
    for source in upgraded["sources"]:
        source["schema_version"] = current

    run_id, record = runs.new_run(
        new_state,
        "upgrade",
        started_at=started_at,
        summary=f"Case folder upgraded from workspace version {stored} to {current}.",
    )
    backup_dir = f"{runs.RUNS_DIR}/{run_id}/pre-upgrade/"
    record["upgrade"] = {
        "from": stored,
        "to": current,
        "steps": [f"{version} → {version + 1}" for version, _ in steps],
        "backup_dir": backup_dir,
    }

    transaction = txn.Transaction(case_root, "upgrade")
    for rel, data in backups:
        transaction.stage_backup(backup_dir + rel, data)
    transaction.stage_record(casefile.CASE_FILE, upgraded["case"], "case", yamlio.dump_yaml_bytes)
    for source in upgraded["sources"]:
        transaction.stage_json(f"{_sources_dir()}/{source['src_id']}.json", source, "source")
    transaction.stage_json(runs.run_json_path(run_id), record, "run")
    inputs = index.IndexInputs(
        upgraded["case"], new_state, upgraded["sources"], [*runs.load_runs(case_root), record]
    )
    transaction.stage_text(index.INDEX_FILE, index.render_index(inputs))
    transaction.set_state(new_state)
    transaction.commit()
    ctx.warn(
        "WORKSPACE_UPGRADED",
        f"This case folder was upgraded from workspace version {stored} to {current}. "
        f"A copy of the previous state files is in {backup_dir}.",
    )
    return upgraded
