"""``epb scan``: take stock of the files in ``inputs/`` (WS-02, WS-03, design §7.1).

Walks ``inputs/`` without following links, fingerprints every file and registers new content
as sources ``S001``, ``S002`` and so on, in one transaction with a run record and a fresh
``INDEX.md``. It only reads ``inputs/``. A scan that finds no change writes nothing.
"""

NAME = "scan"
HELP = "Take stock of the files in inputs/"
MUTATING = True


def add_arguments(parser):
    """scan has no options of its own."""


def run(args, ctx):
    from epb import workspace
    from epb.sources import scan

    case_root = workspace.find_workspace(ctx.case)
    with workspace.open_for_mutation(case_root, ctx, NAME) as session:
        return scan.run_scan(session, ctx)
