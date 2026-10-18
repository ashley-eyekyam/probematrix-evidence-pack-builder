"""The case-folder layout contract and the sessions commands open on it (WS-01, WS-11, D-06).

``CONTRACT_PATHS`` lists every path the plugin knows about in a case folder, with how it may
be shared:

- ``user-owned``: the user's own files; the plugin never changes them.
- ``shareable``: de-identified output meant to be read or shared.
- ``structural``: settings and bookkeeping that hold no source text, safe to keep in version
  control.
- ``raw-text-confidential``: working files that hold raw source text, including names; git
  ignores them (A2) and they are never published.
- ``private-never-shared``: the private folder; never shared, committed or copied.

Commands open the case folder through one of three sessions: ``open_for_init`` (only
``init``), ``open_for_mutation`` (every other changing command) and ``open_read_only``
(commands that only look). Only the first two finish an interrupted change; plan 01-12 adds
the workspace lock and the automatic upgrade inside them.
"""

from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from epb import txn
from epb.state import STATE_FILE

CASE_DIRS = ("inputs", "outputs")
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

CLASSIFICATIONS = (
    "user-owned",
    "shareable",
    "structural",
    "raw-text-confidential",
    "private-never-shared",
)

CONTRACT_PATHS = (
    ("inputs/", "user-owned", "The evidence files the user drops in; read-only to the plugin."),
    ("outputs/", "shareable", "Only the evidence-pack workbooks to import into ProbeMatrix."),
    ("INDEX.md", "shareable", "The case summary, rewritten every run; only its ticks are edited."),
    (".epb/case.yaml", "structural", "Case title, slug, ID prefix, timezone and fixed settings."),
    (".epb/state.json", "structural", "Fingerprints, counters, workbooks and chunk status."),
    (".epb/sources/", "structural", "One record per input file, with its versions and status."),
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


@contextmanager
def open_for_init(case_root, ctx):
    """The session ``init`` runs in: create ``.epb/tmp/``, finish any interrupted change,
    then report whether the folder is already set up."""
    case_root = Path(case_root)
    (case_root / txn.TMP_DIR).mkdir(parents=True, exist_ok=True)
    _recover(case_root, ctx)
    yield InitSession(case_root=case_root, state_exists=(case_root / STATE_FILE).exists())


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


def find_workspace(case_dir):
    raise NotImplementedError


def load_sources(case_root):
    raise NotImplementedError


def open_read_only(case_root, ctx):
    raise NotImplementedError


@contextmanager
def open_for_mutation(case_root, ctx, command):
    raise NotImplementedError
    yield
