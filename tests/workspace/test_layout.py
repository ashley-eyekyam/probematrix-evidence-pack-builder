"""``epb init`` creates the documented case-folder layout in one transaction (WS-01, WS-11,
D-06), refuses to overwrite a foreign INDEX.md, and writes no absolute path, home folder,
account name or host name into any file it creates (T-01-29)."""

import getpass
import json
import os
import socket
from pathlib import Path

import pytest
from epb import workspace
from epb.casefile import CASE_FILE
from epb.index import SECTION_TITLES
from epb.state import STATE_FILE

INIT = [
    "init",
    "--title",
    "Acme Pump Trip",
    "--slug",
    "acme-pump-trip",
    "--prefix",
    "APT",
    "--timezone",
    "UTC",
    "--json",
]

FOLDERS = (
    "inputs",
    "outputs",
    ".epb",
    ".epb/inbox",
    ".epb/tmp",
    ".epb/runs",
    ".epb/private",
)
FILES = (
    "INDEX.md",
    CASE_FILE,
    STATE_FILE,
    ".epb/.gitignore",
    ".epb/.gitattributes",
    ".epb/private/.gitignore",
)
CREATED = [
    "inputs/",
    "outputs/",
    ".epb/inbox/",
    ".epb/tmp/",
    ".epb/runs/",
    ".epb/private/",
    CASE_FILE,
    ".epb/.gitignore",
    ".epb/.gitattributes",
    ".epb/private/.gitignore",
    "INDEX.md",
    STATE_FILE,
]


def _init(run_epb, case_dir, *extra):
    proc = run_epb([*INIT, *extra], cwd=case_dir)
    envelope = json.loads(proc.stdout)
    return proc, envelope


def test_init_creates_every_folder_and_file(run_epb, case_dir):
    proc, envelope = _init(run_epb, case_dir)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    for rel in FOLDERS:
        assert (case_dir / rel).is_dir(), rel
    for rel in FILES:
        assert (case_dir / rel).is_file(), rel
    assert envelope["data"]["created"] == CREATED
    assert envelope["next"] == ["scan"]
    assert list((case_dir / ".epb" / "tmp").glob("txn-*")) == []


def test_ignore_files_have_exact_bytes(run_epb, case_dir):
    proc, _ = _init(run_epb, case_dir)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    gitignore = (case_dir / ".epb/.gitignore").read_bytes()
    assert gitignore == b"segments/\nledger/\ninbox/\ntmp/\nmedia/\nruns/\nprivate/\n"
    assert gitignore == ("\n".join(workspace.GITIGNORE_LINES) + "\n").encode()
    assert (case_dir / ".epb/.gitattributes").read_bytes() == b"* -text\n"
    assert (case_dir / ".epb/private/.gitignore").read_bytes() == b"*\n"


def test_index_has_six_sections_in_order(run_epb, case_dir):
    proc, _ = _init(run_epb, case_dir)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    text = (case_dir / "INDEX.md").read_text(encoding="utf-8")
    headings = [line[3:] for line in text.splitlines() if line.startswith("## ")]
    assert headings == list(SECTION_TITLES)
    assert headings == [
        "1. Case",
        "2. What to import where",
        "3. Inputs",
        "4. Outputs",
        "5. Open issues",
        "6. Run history",
    ]


def test_human_message_says_what_to_do_next(run_epb, case_dir):
    proc = run_epb(INIT[:-1], cwd=case_dir)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "Case folder set up: Acme Pump Trip" in proc.stdout
    assert "inputs" in proc.stdout
    assert "scan" in proc.stdout


def test_existing_inputs_are_kept(run_epb, case_dir):
    inputs = case_dir / "inputs"
    inputs.mkdir()
    (inputs / "report.txt").write_text("synthetic\n", encoding="utf-8")
    proc, envelope = _init(run_epb, case_dir)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert (inputs / "report.txt").read_text(encoding="utf-8") == "synthetic\n"
    assert "inputs/" not in envelope["data"]["created"]
    assert "outputs/" in envelope["data"]["created"]


def test_foreign_index_is_refused(run_epb, case_dir):
    (case_dir / "INDEX.md").write_text("My own notes\n", encoding="utf-8")
    proc, envelope = _init(run_epb, case_dir)
    assert proc.returncode == 2, proc.stdout + proc.stderr
    error = envelope["errors"][0]
    assert error["code"] == "BAD_ARGUMENT"
    assert "INDEX.md already exists" in error["message"]
    assert (case_dir / "INDEX.md").read_text(encoding="utf-8") == "My own notes\n"
    assert not (case_dir / ".epb").exists()
    assert not (case_dir / "inputs").exists()


def test_rerun_keeps_its_own_index(run_epb, case_dir):
    proc, _ = _init(run_epb, case_dir)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    before = (case_dir / "INDEX.md").read_bytes()
    proc, envelope = _init(run_epb, case_dir)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert [item["code"] for item in envelope["warnings"]] == ["ALREADY_SET_UP"]
    assert (case_dir / "INDEX.md").read_bytes() == before


# --- the prohibition: nothing machine- or person-specific in trackable files ------------------


def _forbidden_strings(tmp_path):
    found = {str(tmp_path), str(Path.home())}
    if os.name == "posix":
        import pwd

        found.add(pwd.getpwuid(os.getuid()).pw_dir)
    user = getpass.getuser()
    if len(user) >= 3:
        found.add(user)
    host = socket.gethostname()
    if len(host) >= 4:
        found.add(host)
    return found


def test_no_absolute_path_user_or_host_in_any_file(run_epb, tmp_path):
    case = tmp_path / "Acme case"
    case.mkdir()
    proc, _ = _init(run_epb, case)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    files = sorted(path for path in case.rglob("*") if path.is_file())
    assert {path.relative_to(case).as_posix() for path in files} >= set(FILES)
    forbidden = _forbidden_strings(tmp_path)
    for path in files:
        text = path.read_text(encoding="utf-8")
        for value in forbidden:
            assert value not in text, f"{value!r} appears in {path.relative_to(case)}"


# --- the contract table -----------------------------------------------------------------------


def test_gitignore_lines_follow_a2():
    assert workspace.GITIGNORE_LINES == (
        "segments/",
        "ledger/",
        "inbox/",
        "tmp/",
        "media/",
        "runs/",
        "private/",
    )


def test_contract_paths_are_complete_and_classified():
    paths = [path for path, _, _ in workspace.CONTRACT_PATHS]
    assert len(paths) == len(set(paths))
    required = {
        "inputs/",
        "outputs/",
        "INDEX.md",
        ".epb/case.yaml",
        ".epb/state.json",
        ".epb/sources/",
        ".epb/segments/",
        ".epb/media/",
        ".epb/ledger/claims.jsonl",
        ".epb/ledger/conclusions.jsonl",
        ".epb/ledger/chunks.json",
        ".epb/rosters/",
        ".epb/conflicts.yaml",
        ".epb/items/",
        ".epb/coverage.json",
        ".epb/runs/",
        ".epb/inbox/",
        ".epb/tmp/",
        ".epb/private/",
        ".epb/private/name-map.yaml",
        ".epb/.gitignore",
        ".epb/.gitattributes",
        ".epb/lock",
    }
    assert required <= set(paths)
    for path, classification, description in workspace.CONTRACT_PATHS:
        assert classification in workspace.CLASSIFICATIONS, path
        assert description.strip(), path


@pytest.mark.parametrize("line", workspace.GITIGNORE_LINES)
def test_every_ignored_folder_is_confidential(line):
    """A folder git ignores holds raw text, so the contract must not call it shareable."""
    classes = {
        classification
        for path, classification, _ in workspace.CONTRACT_PATHS
        if path == f".epb/{line}" or path.startswith(f".epb/{line}")
    }
    assert classes
    assert classes <= {"raw-text-confidential", "private-never-shared"}
