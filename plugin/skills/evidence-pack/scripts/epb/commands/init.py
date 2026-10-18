"""``epb init``: set up a case folder (WS-01).

Writes ``.epb/state.json`` through the journalled store that every later changing command
uses. Running it again on a folder that is already set up changes nothing.
"""

from epb.errors import EpbError

NAME = "init"
HELP = "Set up a case folder here"
MUTATING = True


def add_arguments(parser):
    """``init`` has no options of its own yet."""


def run(args, ctx):
    from epb import __version__, txn
    from epb.cli import Result
    from epb.state import STATE_FILE, new_state

    case = ctx.case
    if not case.is_dir():
        raise EpbError(
            "BAD_ARGUMENT",
            f"The case folder {case} does not exist or is not a folder.",
            hint="Create the folder first, or pass --case with an existing folder.",
        )
    (case / txn.TMP_DIR).mkdir(parents=True, exist_ok=True)
    for txn_id in txn.recover(case):
        ctx.warn(
            "RECOVERED",
            f"An interrupted change ({txn_id}) was finished before this command ran.",
        )
    if (case / STATE_FILE).exists():
        ctx.warn("ALREADY_SET_UP", "This folder is already set up as a case folder.")
        return Result(
            data={"case_folder": str(case), "created": []},
            message="Nothing to do: this folder is already set up as a case folder.",
        )
    txn.Transaction(case, NAME).set_state(new_state(__version__)).commit()
    return Result(
        data={"case_folder": str(case), "created": [STATE_FILE]},
        message="Case folder set up.",
    )
