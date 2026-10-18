"""The workspace state file ``.epb/state.json``: creation and guarded loading (WS-13, D-09,
D-19).

``state.json`` is written only through ``epb.txn.Transaction.set_state``, always last in its
transaction. ``load_state`` never repairs anything: damaged state exits 4 ``STATE_INVALID``,
state from a newer plugin exits 4 ``WORKSPACE_TOO_NEW``, and state from an older plugin is
returned as read so the D-09 upgrade can migrate it.
"""

import json
from pathlib import Path

from epb import schema
from epb.errors import EpbError

SCHEMA_VERSION = 1
STATE_FILE = ".epb/state.json"

_DAMAGED_MESSAGE = "The workspace state file .epb/state.json is damaged and cannot be read safely."
_DAMAGED_HINT = (
    "Restore .epb/state.json from a backup or from version control if you keep one. "
    "Do not edit it by hand, and do not ask the agent to repair it."
)


def new_state(plugin_version: str) -> dict:
    """The state of a freshly set-up case folder: every counter 0, every map and list empty."""
    return {
        "schema_version": SCHEMA_VERSION,
        "plugin_version": plugin_version,
        "last_txn": None,
        "counters": {
            "run": 0,
            "source": 0,
            "evidence": 0,
            "tag": 0,
            "claim": 0,
            "conflict": 0,
        },
        "fingerprints": {},
        "workbooks": [],
        "items": {},
        "chunks": {},
        "imports": [],
    }


def _damaged(data=None) -> EpbError:
    return EpbError("STATE_INVALID", _DAMAGED_MESSAGE, hint=_DAMAGED_HINT, pointer=None, data=data)


def load_state(case_root) -> dict:
    """Read and check ``.epb/state.json`` from the case folder."""
    path = Path(case_root) / STATE_FILE
    if not path.is_file():
        raise EpbError(
            "NOT_A_WORKSPACE",
            "This folder is not set up as a case folder.",
            hint="Run epb init here, or pass --case with the case folder.",
        )
    try:
        data = json.loads(path.read_bytes().decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        raise _damaged() from None
    if not isinstance(data, dict):
        raise _damaged()
    version = data.get("schema_version")
    if type(version) is not int or version < 1:
        raise _damaged()
    if version > SCHEMA_VERSION:
        raise EpbError(
            "WORKSPACE_TOO_NEW",
            "This case folder was last used by a newer version of the plugin. "
            "Update the plugin, then try again.",
            hint="Update the plugin, then run the command again.",
        )
    if version < SCHEMA_VERSION:
        return data  # the D-09 upgrade migrates it, then validates
    issues = schema.validate(data, "state")
    if issues:
        error = _damaged({"issues": [issue.to_dict() for issue in issues]})
        error.pointer = issues[0].pointer
        raise error
    return data
