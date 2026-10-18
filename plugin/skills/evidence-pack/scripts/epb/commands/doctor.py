"""``epb doctor``: check what is installed and what is optional (PKG-07, D-17).

doctor runs in the interpreter that launched ``epb.py`` (``launcher.BOOTSTRAP_COMMANDS``), so
it works before first-time setup. Everything it imports is standard library.

Exit codes: 0 when the private environment is current and every core package is installed;
3 (``ENV_NOT_SET_UP`` or ``CORE_PACKAGE_MISSING``) otherwise. The full report is returned
either way. Optional tools and extras never change the exit code.

Run inside a case folder, doctor also warns when the folder appears to be inside a cloud sync
service or a git repository that tracks or would track ``.epb/private/``.
"""

from epb.cli import Result
from epb.doctor import gitcheck, probes, syncfolders
from epb.doctor.report import command_text, render_human
from epb.errors import EpbError

NAME = "doctor"
HELP = "Check what is installed and what is optional"
MUTATING = False


def add_arguments(parser):
    """doctor has no options of its own yet; ``--setup`` arrives with first-time setup."""


def _fail(code, reason, hint, report, ctx):
    """Raise with the full report. A person (no --json) also gets the checklist, because the
    CLI prints only the error message on failure."""
    if ctx.json:
        raise EpbError(code, reason, hint=hint, data=report)
    # The checklist's "What to do next" already carries the hint.
    message = reason + "\n\n" + render_human(report, verbose=ctx.verbose)
    raise EpbError(code, message, data=report)


def _check_folder(report, ctx):
    """Inside a case folder (one with ``.epb``), warn about sync folders and git tracking
    (WS-11, WS-12). Anywhere else nothing is checked."""
    if not (ctx.case / ".epb").exists():
        return
    found = [syncfolders.warning_for(hit) for hit in syncfolders.check(ctx.case)]
    found.extend(gitcheck.check(ctx.case))
    report["folder"] = {"checked": True, "warnings": found}
    for item in found:
        ctx.warn(item["code"], item["message"], item.get("hint"))


def run(args, ctx):
    report = probes.collect(ctx.case)
    _check_folder(report, ctx)
    setup = command_text(report["setup_command"])
    environment = report["environment"]
    if not environment["current"]:
        if environment["exists"]:
            reason = "The private environment is out of date for this plugin version."
        else:
            reason = "First-time setup has not been run on this computer yet."
        _fail("ENV_NOT_SET_UP", reason, f"Run: {setup}", report, ctx)
    missing = [package["name"] for package in report["core_packages"] if not package["ok"]]
    if missing:
        reason = "Some core packages are missing from the private environment: " + ", ".join(
            missing
        )
        _fail("CORE_PACKAGE_MISSING", reason + ".", f"Run: {setup}", report, ctx)
    return Result(data=report, next=[], message=render_human(report, verbose=ctx.verbose))
