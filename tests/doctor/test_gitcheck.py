"""The read-only git tracking check (WS-11, design A2, T-01-21)."""

import hashlib
import json
import re
import subprocess
from pathlib import Path

import pytest
from epb.doctor import gitcheck

ALLOWED_SUBCOMMANDS = {"rev-parse", "ls-files", "check-ignore"}


def git(cwd, *args):
    subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True, text=True, encoding="utf-8"
    )


def codes(warnings):
    return [item["code"] for item in warnings]


@pytest.fixture
def repo(tmp_path, need_tool):
    need_tool("git")
    path = tmp_path / "repo"
    path.mkdir()
    git(path, "init", "-q")
    (path / "README.txt").write_text("synthetic\n", encoding="utf-8")
    git(path, "add", "README.txt")
    git(path, "commit", "-q", "-m", "first")
    return path


def private_file(case):
    target = case / ".epb" / "private" / "names.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("{}\n", encoding="utf-8")
    return target


def ignore_private(case):
    (case / ".epb" / ".gitignore").write_text("private/\n", encoding="utf-8")


def fingerprint(repo_root):
    found = {}
    for name in ("HEAD", "index", "config"):
        path = repo_root / ".git" / name
        if path.exists():
            found[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    return found


@pytest.fixture(params=["root", "nested"])
def case(request, repo):
    """The case folder at the repository root, and nested two levels down with a space and
    a non-ASCII character in its path."""
    if request.param == "root":
        return repo
    path = repo / "sub dir" / "caseé"
    path.mkdir(parents=True)
    return path


# --- real repositories ----------------------------------------------------------------------


def test_unignored_private_folder(case):
    private_file(case)
    assert codes(gitcheck.check(case)) == ["GIT_PRIVATE_NOT_IGNORED"]


def test_ignored_private_folder_is_quiet(case):
    private_file(case)
    ignore_private(case)
    assert gitcheck.check(case) == []


def test_tracked_private_file(case, repo):
    private_file(case)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "oops")
    ignore_private(case)
    assert codes(gitcheck.check(case)) == ["GIT_TRACKS_PRIVATE"]


def test_tracked_and_not_ignored(case, repo):
    private_file(case)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "oops")
    assert codes(gitcheck.check(case)) == ["GIT_TRACKS_PRIVATE", "GIT_PRIVATE_NOT_IGNORED"]


def test_messages_are_plain_language(case, repo):
    private_file(case)
    git(repo, "add", "-A")
    warnings = {item["code"]: item for item in gitcheck.check(case)}
    assert "must never be committed" in warnings["GIT_TRACKS_PRIVATE"]["message"]
    assert "could be committed" in warnings["GIT_PRIVATE_NOT_IGNORED"]["message"]


def test_git_folder_is_unchanged(case, repo):
    private_file(case)
    git(repo, "add", "-A")
    before = fingerprint(repo)
    assert set(before) == {"HEAD", "index", "config"}
    gitcheck.check(case)
    assert fingerprint(repo) == before


def test_outside_a_repository(tmp_path, need_tool):
    need_tool("git")
    case = tmp_path / "loose" / "case"
    private_file(case)
    assert gitcheck.check(case) == []


# --- without git ----------------------------------------------------------------------------


def test_no_git_binary_inside_a_repository(tmp_path):
    root = tmp_path / "repo"
    (root / ".git").mkdir(parents=True)
    case = root / "a" / "case"
    case.mkdir(parents=True)
    warnings = gitcheck.check(case, which=lambda name: None)
    assert codes(warnings) == ["GIT_UNAVAILABLE"]
    assert "git is not installed" in warnings[0]["message"]


def test_no_git_binary_and_a_git_file(tmp_path):
    """A linked worktree or submodule has a .git file instead of a folder."""
    root = tmp_path / "wt"
    root.mkdir()
    (root / ".git").write_text("gitdir: /elsewhere\n", encoding="utf-8")
    assert codes(gitcheck.check(root, which=lambda name: None)) == ["GIT_UNAVAILABLE"]


def test_no_git_binary_outside_a_repository(tmp_path):
    case = tmp_path / "loose" / "case"
    case.mkdir(parents=True)
    assert gitcheck.check(case, which=lambda name: None) == []


def test_git_that_cannot_run_falls_back_to_the_walk(tmp_path):
    root = tmp_path / "repo"
    (root / ".git").mkdir(parents=True)

    def broken(argv, **kwargs):
        raise OSError("cannot run")

    warnings = gitcheck.check(root, which=lambda name: "/opt/fake/git", run=broken)
    assert codes(warnings) == ["GIT_UNAVAILABLE"]


# --- how git is called ------------------------------------------------------------------------


def test_git_argv_uses_dash_c_and_never_a_shell(tmp_path):
    case = tmp_path / "Case Folder é"
    case.mkdir()
    calls = []

    def fake(argv, **kwargs):
        calls.append((argv, kwargs))
        sub = argv[3]
        if sub == "rev-parse":
            return subprocess.CompletedProcess(argv, 0, stdout=str(case) + "\n", stderr="")
        if sub == "ls-files":
            return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")
        return subprocess.CompletedProcess(argv, 1, stdout="", stderr="")

    warnings = gitcheck.check(case, which=lambda name: "/opt/fake/git", run=fake)
    assert codes(warnings) == ["GIT_PRIVATE_NOT_IGNORED"]
    assert [argv[3] for argv, _ in calls] == ["rev-parse", "ls-files", "check-ignore"]
    for argv, kwargs in calls:
        assert isinstance(argv, list)
        assert argv[:3] == ["/opt/fake/git", "-C", str(case)]
        assert not kwargs.get("shell")
        assert kwargs["timeout"] == 10


def test_not_a_work_tree_stops_after_rev_parse(tmp_path):
    calls = []

    def fake(argv, **kwargs):
        calls.append(argv)
        return subprocess.CompletedProcess(argv, 128, stdout="", stderr="fatal: not a git repo")

    assert gitcheck.check(tmp_path, which=lambda name: "/opt/fake/git", run=fake) == []
    assert len(calls) == 1


def test_source_uses_only_read_only_subcommands():
    source = Path(gitcheck.__file__).read_text(encoding="utf-8")
    quoted = set(re.findall(r'"([a-z][a-z-]+)"', source))
    git_words = {
        "add",
        "commit",
        "config",
        "init",
        "rm",
        "reset",
        "checkout",
        "stash",
        "update-index",
        "status",
    }
    assert quoted & git_words == set()
    for sub in ALLOWED_SUBCOMMANDS:
        assert f'"{sub}"' in source


# --- doctor shows the warning inside a case folder ------------------------------------------


def test_doctor_reports_git_warning_in_a_case_folder(run_epb, repo):
    case = repo / "case"
    private_file(case)
    proc = run_epb(["doctor", "--json"], case, in_env=False)
    envelope = json.loads(proc.stdout)
    assert "GIT_PRIVATE_NOT_IGNORED" in codes(envelope["warnings"])
    assert envelope["data"]["folder"]["checked"] is True
    assert "GIT_PRIVATE_NOT_IGNORED" in codes(envelope["data"]["folder"]["warnings"])
