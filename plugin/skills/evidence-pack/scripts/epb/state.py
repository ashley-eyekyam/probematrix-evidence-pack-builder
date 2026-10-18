"""The workspace state file ``.epb/state.json``: creation and guarded loading (WS-13, D-09).

``state.json`` is written only through ``epb.txn.Transaction.set_state``, always last in its
transaction.
"""

SCHEMA_VERSION = 1
STATE_FILE = ".epb/state.json"


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


def load_state(case_root) -> dict:
    """Read ``.epb/state.json`` from the case folder."""
    from pathlib import Path

    from epb import fsio

    return fsio.read_json(Path(case_root) / STATE_FILE)
