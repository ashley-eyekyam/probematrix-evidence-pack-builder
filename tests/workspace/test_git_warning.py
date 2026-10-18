"""``epb init`` warns, in plain language and with exit 0, when the new case folder appears to
be inside a cloud sync folder or a git repository that tracks or would track
``.epb/private/`` (WS-11, WS-12, design A1, A2). The checks run only after the init
transaction has committed, and a failing check never fails init."""

import json
import subprocess

import pytest
from epb.doctor import gitcheck, syncfolders
from epb.state import STATE_FILE

FLAGS = [
    "--title",
    "Acme Pump Trip",
    "--slug",
    "acme-pump-trip",
    "--prefix",
    "APT",
    "--timezone",
    "UTC",
]
INIT = ["init", *FLAGS, "--json"]
GIT_CODES = {"GIT_TRACKS_PRIVATE", "GIT_PRIVATE_NOT_IGNORED", "GIT_UNAVAILABLE"}


def git(cwd, *args):
    return subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True, text=True, encoding="utf-8"
    )


def codes(envelope):
    return [item["code"] for item in envelope["warnings"]]


def _init(run_epb, case, **kwargs):
    proc = run_epb(INIT, cwd=case, **kwargs)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    return json.loads(proc.stdout)


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


# --- git --------------------------------------------------------------------------------------


def test_init_in_a_repository_ignores_the_raw_text_folders(run_epb, repo):
    case = repo / "cases" / "acme"
    case.mkdir(parents=True)
    envelope = _init(run_epb, case)
    assert not GIT_CODES & set(codes(envelope))
    probe = subprocess.run(
        ["git", "check-ignore", "-q", ".epb/private/x"], cwd=case, capture_output=True
    )
    assert probe.returncode == 0
    status = git(repo, "status", "--porcelain", "--untracked-files=all").stdout.splitlines()
    for folder in ("private", "runs", "tmp"):
        assert not [line for line in status if f".epb/{folder}/" in line], status
    assert any("INDEX.md" in line for line in status)
    assert any(".epb/state.json" in line for line in status)


def test_init_warns_when_private_files_are_already_tracked(run_epb, repo):
    old = repo / ".epb" / "private" / "old.txt"
    old.parent.mkdir(parents=True)
    old.write_text("synthetic\n", encoding="utf-8")
    git(repo, "add", "-f", ".epb/private/old.txt")
    git(repo, "commit", "-q", "-m", "tracked by mistake")
    envelope = _init(run_epb, repo)
    assert envelope["exit_code"] == 0
    assert "GIT_TRACKS_PRIVATE" in codes(envelope)
    warning = next(item for item in envelope["warnings"] if item["code"] == "GIT_TRACKS_PRIVATE")
    assert "must never be committed" in warning["message"]
    assert (repo / STATE_FILE).is_file()


def test_init_without_git_inside_a_repository(run_epb, tmp_path):
    (tmp_path / "work" / ".git").mkdir(parents=True)
    case = tmp_path / "work" / "case"
    case.mkdir()
    no_git = tmp_path / "empty-bin"
    no_git.mkdir()
    envelope = _init(run_epb, case, env={"PATH": str(no_git)})
    assert codes(envelope) == ["GIT_UNAVAILABLE"]
    assert "git is not installed" in envelope["warnings"][0]["message"]


def test_init_outside_any_repository_or_sync_folder_is_quiet(run_epb, case_dir):
    envelope = _init(run_epb, case_dir)
    assert envelope["warnings"] == []


# --- sync folders -----------------------------------------------------------------------------


def test_init_inside_dropbox_warns(run_epb, home_dir, tmp_path):
    synced = tmp_path / "Shared Work"
    case = synced / "acme"
    case.mkdir(parents=True)
    info = home_dir / ".dropbox" / "info.json"
    info.parent.mkdir(parents=True)
    info.write_text(json.dumps({"personal": {"path": str(synced)}}), encoding="utf-8")
    envelope = _init(run_epb, case)
    assert envelope["exit_code"] == 0
    assert codes(envelope) == ["SYNC_FOLDER"]
    message = envelope["warnings"][0]["message"]
    assert "appears to be inside Dropbox" in message
    assert ".epb/private/" in message
    assert (case / STATE_FILE).is_file()


def test_human_output_shows_the_warning(run_epb, home_dir, tmp_path):
    synced = tmp_path / "Shared Work"
    case = synced / "acme"
    case.mkdir(parents=True)
    info = home_dir / ".dropbox" / "info.json"
    info.parent.mkdir(parents=True)
    info.write_text(json.dumps({"personal": {"path": str(synced)}}), encoding="utf-8")
    proc = run_epb(["init", *FLAGS], cwd=case)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "Warning: This folder appears to be inside Dropbox" in proc.stderr


def test_rerun_does_not_repeat_the_checks(run_epb, home_dir, tmp_path):
    synced = tmp_path / "Shared Work"
    case = synced / "acme"
    case.mkdir(parents=True)
    _init(run_epb, case)
    info = home_dir / ".dropbox" / "info.json"
    info.parent.mkdir(parents=True)
    info.write_text(json.dumps({"personal": {"path": str(synced)}}), encoding="utf-8")
    envelope = _init(run_epb, case)
    assert codes(envelope) == ["ALREADY_SET_UP"]


# --- the checks never fail init and run only after the commit ---------------------------------


def test_checks_run_after_the_commit(cli, case_dir, monkeypatch):
    seen = []

    def git_check(case_root, **kwargs):
        seen.append(("git", (case_root / STATE_FILE).is_file()))
        return []

    def sync_check(path, **kwargs):
        seen.append(("sync", (path / STATE_FILE).is_file()))
        return []

    monkeypatch.setattr(gitcheck, "check", git_check)
    monkeypatch.setattr(syncfolders, "check", sync_check)
    result = cli(INIT, cwd=case_dir)
    assert result.exit_code == 0, result.stdout + result.stderr
    assert sorted(seen) == [("git", True), ("sync", True)]


@pytest.mark.parametrize(
    "failure",
    [RuntimeError("boom"), subprocess.TimeoutExpired(["git"], 10), OSError("no such file")],
    ids=["error", "timeout", "oserror"],
)
@pytest.mark.parametrize("which", ["git", "sync"])
def test_a_failing_check_never_fails_init(cli, case_dir, monkeypatch, failure, which):
    def broken(*args, **kwargs):
        raise failure

    target = gitcheck if which == "git" else syncfolders
    monkeypatch.setattr(target, "check", broken)
    result = cli(INIT, cwd=case_dir)
    assert result.exit_code == 0, result.stdout + result.stderr
    assert result.envelope["ok"] is True
    assert result.envelope["warnings"] == []
    for rel in ("INDEX.md", STATE_FILE, ".epb/case.yaml", ".epb/runs/001/run.json"):
        assert (case_dir / rel).is_file(), rel
    assert list((case_dir / ".epb" / "tmp").glob("txn-*")) == []
