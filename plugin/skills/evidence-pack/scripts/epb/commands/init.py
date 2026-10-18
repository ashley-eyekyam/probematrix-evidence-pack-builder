"""``epb init``: set up a case folder (WS-01, WS-09, D-06, D-15).

Creates ``inputs/``, ``outputs/`` and the ``.epb`` folders, then writes ``.epb/case.yaml``,
the ignore files, ``INDEX.md`` and ``.epb/state.json`` in one journalled transaction, the
store that every later changing command uses. The CLI never prompts: the skill asks the user
for the case title, and every other setting has a default. Running it again on a folder that
is already set up changes nothing, and it never overwrites an ``INDEX.md`` it did not make.
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


def _refuse_foreign_index(case, index_file):
    """Never overwrite an ``INDEX.md`` the plugin did not make (T-01-30)."""
    if (case / index_file).exists():
        raise EpbError(
            "BAD_ARGUMENT",
            "INDEX.md already exists in this folder and was not made by the plugin. "
            "Move it, or choose another folder.",
            hint="Move INDEX.md out of this folder, or set up the case in another folder.",
        )


def run(args, ctx):
    from epb import __version__, casefile, fsio, index, runs, txn, workspace, yamlio
    from epb.cli import Result
    from epb.state import STATE_FILE, load_state, new_state

    case = ctx.case
    if not case.is_dir():
        raise EpbError(
            "BAD_ARGUMENT",
            f"The case folder {case} does not exist or is not a folder.",
            hint="Create the folder first, or pass --case with an existing folder.",
        )
    if not (case / STATE_FILE).exists() and not txn.pending_journals(case):
        # Checked before anything is created, so a refusal leaves the folder untouched.
        _refuse_foreign_index(case, index.INDEX_FILE)
    new_dirs = workspace.missing_layout(case)
    with workspace.open_for_init(case, ctx) as session:
        if session.state_exists:
            load_state(case)
            record = casefile.load_case(case)
            fields = casefile.differences(record, args)
            if fields:
                flags = ", ".join(f"--{field}" for field in fields)
                raise EpbError(
                    "WORKSPACE_EXISTS",
                    "This folder is already set up as a case folder with different settings: "
                    f"{flags}. Case settings are fixed once set up.",
                    hint="Run init without those options, or set up a new folder for another case.",
                    data={"fields": fields},
                )
            ctx.warn("ALREADY_SET_UP", "This folder is already set up as a case folder.")
            return Result(
                data={"case_folder": str(case), "created": [], "case": _case_data(record)},
                message="Nothing to do: this folder is already set up as a case folder.",
            )
        _refuse_foreign_index(case, index.INDEX_FILE)
        started_at = fsio.utc_now_iso()
        settings = casefile.resolve_settings(args, case)
        record = casefile.new_case_record(settings, __version__, started_at)
        state = new_state(__version__)
        run_id, run_record = runs.new_run(
            state, NAME, started_at=started_at, summary="Case folder created."
        )
        workspace.create_layout(case)
        transaction = txn.Transaction(case, NAME)
        transaction.stage_record(casefile.CASE_FILE, record, "case", yamlio.dump_yaml_bytes)
        transaction.stage_text(workspace.GITIGNORE_FILE, workspace.GITIGNORE_TEXT)
        transaction.stage_text(workspace.GITATTRIBUTES_FILE, workspace.GITATTRIBUTES_TEXT)
        transaction.stage_text(workspace.PRIVATE_GITIGNORE_FILE, workspace.PRIVATE_GITIGNORE_TEXT)
        transaction.stage_json(runs.run_json_path(run_id), run_record, "run")
        transaction.stage_text(
            index.INDEX_FILE,
            index.render_index(index.IndexInputs(record, state, [], [run_record])),
        )
        transaction.set_state(state)
        transaction.commit()
    return Result(
        data={
            "case_folder": str(case),
            "created": [*new_dirs, *transaction.staged_paths],
            "case": _case_data(record),
        },
        next=["scan"],
        message=(
            f"Case folder set up: {settings.title}\n"
            "Put the evidence files in the inputs folder, then ask the agent to scan them."
        ),
    )


def _case_data(record):
    """The four settings ``init`` reports back."""
    return {key: record[key] for key in ("title", "slug", "id_prefix", "timezone")}
