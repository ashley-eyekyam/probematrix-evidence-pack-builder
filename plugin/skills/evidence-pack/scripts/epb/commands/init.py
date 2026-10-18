"""``epb init``: set up a case folder (WS-01, D-15).

Writes ``.epb/case.yaml`` and ``.epb/state.json`` in one journalled transaction, the store
that every later changing command uses. The CLI never prompts: the skill asks the user for
the case title, and every other setting has a default. Running it again on a folder that is
already set up changes nothing.
"""

from epb.errors import EpbError

NAME = "init"
HELP = "Set up a case folder here"
MUTATING = True


def add_arguments(parser):
    parser.add_argument("--title", metavar="TEXT", help="the case title")
    parser.add_argument(
        "--slug",
        metavar="SLUG",
        help="short lowercase name for file names (default: from the folder name)",
    )
    parser.add_argument(
        "--prefix",
        metavar="PREFIX",
        help="ID prefix such as ACM, giving EVD-ACM-001 (default: the title's initials)",
    )
    parser.add_argument(
        "--timezone",
        metavar="ZONE",
        help="IANA timezone such as Europe/London (default: this computer's timezone)",
    )


def run(args, ctx):
    from epb import __version__, casefile, fsio, txn, yamlio
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
    settings = casefile.resolve_settings(args, case)
    record = casefile.new_case_record(settings, __version__, fsio.utc_now_iso())
    transaction = txn.Transaction(case, NAME)
    transaction.stage_record(casefile.CASE_FILE, record, "case", yamlio.dump_yaml_bytes)
    transaction.set_state(new_state(__version__))
    transaction.commit()
    return Result(
        data={
            "case_folder": str(case),
            "created": [casefile.CASE_FILE, STATE_FILE],
            "case": {
                "title": settings.title,
                "slug": settings.slug,
                "id_prefix": settings.id_prefix,
                "timezone": settings.timezone,
            },
        },
        message=f"Case folder set up: {settings.title}",
    )
