"""``epb status``: a short summary of a case folder.

Read-only (research Pattern 2): it takes no lock, changes no file and never finishes an
interrupted change. If one is waiting, it warns ``RECOVERY_PENDING`` and leaves it for the
next command that changes the case folder.
"""

NAME = "status"
HELP = "Show a short summary of this case folder"
MUTATING = False

REMOVED = "removed from folder"


def add_arguments(parser):
    """status has no options of its own."""


def run(args, ctx):
    from epb import workspace
    from epb.cli import Result

    session = workspace.open_read_only(ctx.case, ctx)
    case = {key: session.case[key] for key in ("title", "slug", "id_prefix", "timezone")}
    sources = session.sources
    removed = sum(1 for source in sources if source.get("presence") == REMOVED)
    inputs = {
        "total": len(sources),
        "present": len(sources) - removed,
        "removed": removed,
        "pending": sum(1 for source in sources if source.get("status") == "pending"),
    }
    last = session.runs[-1] if session.runs else None
    last_run = (
        {key: last[key] for key in ("run", "command", "finished_at")} if last is not None else None
    )
    workbooks = len(session.state.get("workbooks") or [])
    lines = [
        f"Case: {case['title']} (ID prefix {case['id_prefix']}, timezone {case['timezone']})",
        f"Inputs: {inputs['total']} registered, {inputs['present']} in the folder, "
        f"{inputs['removed']} removed, {inputs['pending']} waiting for conversion",
        f"Runs: {len(session.runs)}"
        + (f", last was run {last['run']} ({last['command']})" if last is not None else ""),
        f"Workbooks in outputs/: {workbooks}",
        "See INDEX.md in the case folder for the full picture.",
    ]
    return Result(
        data={
            "case": case,
            "inputs": inputs,
            "runs": len(session.runs),
            "last_run": last_run,
            "workbooks": workbooks,
        },
        message="\n".join(lines),
    )
