"""The case-folder layout contract and the sessions commands open on it (WS-01, WS-11, D-06).

``CONTRACT_PATHS`` lists every path the plugin knows about in a case folder, with how it may
be shared:

- ``user-owned``: the user's own files; the plugin never changes them.
- ``shareable``: de-identified output meant to be read or shared.
- ``review-before-sharing``: lists input file and folder names as the user gave them; share
  it or keep it in version control only after checking those names for personal names, until
  a later version shows role labels instead.
- ``structural``: settings and bookkeeping that hold no source text, safe to keep in version
  control.
- ``raw-text-confidential``: working files that hold raw source text, including names; git
  ignores them (A2) and they are never published.
- ``private-never-shared``: the private folder; never shared, committed or copied.

Commands open the case folder through one of three sessions: ``open_for_init`` (only
``init``), ``open_for_mutation`` (every other changing command) and ``open_read_only``
(commands that only look). Only the first two take the workspace lock ``.epb/lock`` (WS-07),
waiting up to ``--wait`` seconds for it, and finish an interrupted change while holding it.
Then, if the case folder was written by an older plugin, they upgrade it with a backup (D-09);
``open_read_only`` only warns ``UPGRADE_PENDING`` and never writes.
"""

import re
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from epb import casefile, fsio, lock, runs, schema, txn, upgrade
from epb.errors import EpbError
from epb.state import STATE_FILE, load_state

CASE_DIRS = ("inputs", "outputs")
SOURCES_DIR = ".epb/sources"
EPB_DIRS = (".epb/inbox", ".epb/tmp", ".epb/runs", ".epb/private")

GITIGNORE_FILE = ".epb/.gitignore"
GITATTRIBUTES_FILE = ".epb/.gitattributes"
PRIVATE_GITIGNORE_FILE = ".epb/private/.gitignore"

# Design §20 A2, in this order: every folder that holds raw source text.
GITIGNORE_LINES = ("segments/", "ledger/", "inbox/", "tmp/", "media/", "runs/", "private/")
GITIGNORE_TEXT = "".join(f"{line}\n" for line in GITIGNORE_LINES)
# D-06: no line-ending conversion of state files.
GITATTRIBUTES_TEXT = "* -text\n"
PRIVATE_GITIGNORE_TEXT = "*\n"

_SOURCE_NAME = re.compile(r"^S\d{3,}$")
_RESTORE_HINT = (
    "Restore the .epb folder from a backup or from version control if you keep one. "
    "Do not edit it by hand, and do not ask the agent to repair it."
)

CLASSIFICATIONS = (
    "user-owned",
    "shareable",
    "review-before-sharing",
    "structural",
    "raw-text-confidential",
    "private-never-shared",
)

CONTRACT_PATHS = (
    ("inputs/", "user-owned", "The evidence files the user drops in; read-only to the plugin."),
    ("outputs/", "shareable", "Only the evidence-pack workbooks to import into ProbeMatrix."),
    (
        "INDEX.md",
        "review-before-sharing",
        "The case summary, rewritten every run; lists input file names; only its ticks are edited.",
    ),
    (".epb/case.yaml", "structural", "Case title, slug, ID prefix, timezone and fixed settings."),
    (
        ".epb/state.json",
        "review-before-sharing",
        "Fingerprints keyed by input path, counters, workbooks and chunk status.",
    ),
    (
        ".epb/sources/",
        "review-before-sharing",
        "One record per input file, with its paths, versions and status.",
    ),
    (".epb/segments/", "raw-text-confidential", "Page- and time-anchored text of each input."),
    (".epb/media/", "raw-text-confidential", "Keyframes, audio and page images for conversion."),
    (".epb/ledger/claims.jsonl", "raw-text-confidential", "Every claim extracted from sources."),
    (
        ".epb/ledger/conclusions.jsonl",
        "raw-text-confidential",
        "Conclusions and recommendations held back from the evidence.",
    ),
    (
        ".epb/ledger/chunks.json",
        "raw-text-confidential",
        "The extraction chunk plan, including section headings.",
    ),
    (".epb/rosters/", "structural", "Role and equipment labels with aliases; never names."),
    (".epb/conflicts.yaml", "structural", "The register of conflicting accounts."),
    (".epb/items/", "structural", "The authored, de-identified evidence items."),
    (".epb/coverage.json", "structural", "Which claim became which item, or why it was omitted."),
    (".epb/runs/", "raw-text-confidential", "One record and report for each run."),
    (".epb/inbox/", "raw-text-confidential", "Agent submissions waiting to be checked."),
    (".epb/tmp/", "raw-text-confidential", "Journals that make every change atomic."),
    (".epb/private/", "private-never-shared", "The private folder; never shared or committed."),
    (
        ".epb/private/name-map.yaml",
        "private-never-shared",
        "Real names mapped to role labels; the only place names are kept.",
    ),
    (".epb/.gitignore", "structural", "Tells git to ignore every raw-text folder."),
    (".epb/.gitattributes", "structural", "Stops git from changing line endings in state files."),
    (".epb/lock", "structural", "Held while a command changes the case folder."),
)


@dataclass
class InitSession:
    """What ``open_for_init`` yields: whether the folder is already set up."""

    case_root: Path
    state_exists: bool


def _recover(case_root: Path, ctx) -> None:
    for txn_id in txn.recover(case_root):
        ctx.warn(
            "RECOVERED",
            f"An interrupted change ({txn_id}) was finished before this command ran.",
        )


def _upgrade_if_older(case_root: Path, ctx) -> None:
    """Upgrade an older workspace (D-09); damaged or newer state stops here with exit 4."""
    state = load_state(case_root)
    if upgrade.needs_upgrade(state):
        upgrade.run_upgrade(case_root, ctx, upgrade.load_snapshot(case_root, state))


@contextmanager
def _locked(case_root: Path, ctx, command: str):
    """Hold the workspace lock for the duration of the block."""
    handle = lock.acquire(case_root / lock.LOCK_FILE, wait_s=ctx.wait, command=command)
    try:
        yield
    finally:
        handle.release()


@contextmanager
def open_for_init(case_root, ctx):
    """The session ``init`` runs in: take the workspace lock, create ``.epb/tmp/``, finish any
    interrupted change, upgrade an older workspace, then report whether the folder is already
    set up."""
    case_root = Path(case_root)
    (case_root / ".epb").mkdir(parents=True, exist_ok=True)
    with _locked(case_root, ctx, "init"):
        (case_root / txn.TMP_DIR).mkdir(parents=True, exist_ok=True)
        _recover(case_root, ctx)
        state_exists = (case_root / STATE_FILE).exists()
        if state_exists:
            _upgrade_if_older(case_root, ctx)
        yield InitSession(case_root=case_root, state_exists=state_exists)


def missing_layout(case_root) -> list[str]:
    """The case and ``.epb`` folders ``init`` sets up that do not exist yet, as case-relative
    paths ending in ``/``."""
    case_root = Path(case_root)
    return [f"{rel}/" for rel in (*CASE_DIRS, *EPB_DIRS) if not (case_root / rel).is_dir()]


def create_layout(case_root) -> None:
    """Create the case folders and the ``.epb`` folders ``init`` sets up."""
    case_root = Path(case_root)
    for rel in (*CASE_DIRS, *EPB_DIRS):
        (case_root / rel).mkdir(parents=True, exist_ok=True)


def find_workspace(case_dir) -> Path:
    """The case folder itself when it is set up (it holds ``.epb/state.json``), else
    ``NOT_A_WORKSPACE``. Parent folders are never searched."""
    case_dir = Path(case_dir)
    if not (case_dir / STATE_FILE).is_file():
        raise EpbError(
            "NOT_A_WORKSPACE",
            "This folder is not set up as a case folder.",
            hint="Run epb init here, or pass --case with the case folder.",
        )
    return case_dir


def load_sources(case_root) -> list[dict]:
    """Every source record in ``.epb/sources/``, checked against its schema and sorted by
    source number; an empty list when there are none yet."""
    folder = Path(case_root) / SOURCES_DIR
    if not folder.is_dir():
        return []
    found = []
    for path in folder.glob("S*.json"):
        if not _SOURCE_NAME.fullmatch(path.stem):
            continue
        rel = f"{SOURCES_DIR}/{path.name}"
        try:
            record = fsio.read_json(path)
        except (OSError, UnicodeDecodeError, ValueError):
            raise EpbError(
                "STATE_INVALID",
                f"The source record {rel} is damaged and cannot be read safely.",
                hint=_RESTORE_HINT,
            ) from None
        schema.check(record, "source", label=rel)
        found.append((int(path.stem[1:]), record))
    return [record for _, record in sorted(found, key=lambda pair: pair[0])]


@dataclass
class Session:
    """A loaded case folder: its settings, state, source records and run records."""

    case_root: Path
    case: dict
    state: dict
    sources: list
    runs: list


def _load(case_root: Path) -> Session:
    state = load_state(case_root)  # first, so damaged state is reported before anything else
    return Session(
        case_root=case_root,
        case=casefile.load_case(case_root),
        state=state,
        sources=load_sources(case_root),
        runs=runs.load_runs(case_root),
    )


def open_read_only(case_root, ctx) -> Session:
    """Load the case folder for a command that only looks. It takes no lock, finishes no
    interrupted change and writes nothing; an interrupted change only gives a warning."""
    case_root = find_workspace(case_root)
    if txn.pending_journals(case_root):
        ctx.warn(
            "RECOVERY_PENDING",
            "The last command was interrupted. The next command that changes the case folder "
            "will finish it.",
        )
    session = _load(case_root)
    if upgrade.needs_upgrade(session.state):
        ctx.warn(
            "UPGRADE_PENDING",
            "This case folder uses an older workspace version. The next command that changes "
            "it will upgrade it and keep a backup.",
        )
    return session


@contextmanager
def open_for_mutation(case_root, ctx, command):
    """The session every changing command except ``init`` runs in: find the case folder,
    take the workspace lock, finish any interrupted change, upgrade an older workspace, then
    load it."""
    case_root = find_workspace(case_root)
    with _locked(case_root, ctx, command):
        _recover(case_root, ctx)
        _upgrade_if_older(case_root, ctx)
        yield _load(case_root)
