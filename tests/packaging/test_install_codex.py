"""The cross-platform Codex fallback installer, ``tools/install-codex.py`` (D-01, T-01-13).

The tool runs as a subprocess, exactly as a user would run it, always with ``--dest`` (or a
fake home) under ``tmp_path`` so the real ``~/.agents/skills`` is never touched.
"""

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
TOOL = REPO_ROOT / "tools" / "install-codex.py"
PLUGIN = REPO_ROOT / "plugin"
CODEX_MANIFEST = PLUGIN / ".codex-plugin" / "plugin.json"
MARKER = ".epb-installed"
MAIN_SKILL = "evidence-pack"
SKILLS = sorted(path.name for path in (PLUGIN / "skills").iterdir() if path.is_dir())

FOREIGN_MESSAGE = "A different skill named evidence-pack already exists in"


def run_tool(*args, env=None):
    child_env = dict(os.environ)
    if env:
        child_env.update(env)
    return subprocess.run(
        [sys.executable, str(TOOL), *args],
        cwd=REPO_ROOT,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=child_env,
        timeout=120,
    )


def tree(root):
    """Relative POSIX path -> sha256 of every file under ``root``."""
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def plugin_files_expected():
    names = sorted(path.name for path in PLUGIN.glob("requirements*.txt"))
    return names + ["security-exceptions.json"]


@pytest.fixture
def dest(tmp_path):
    return tmp_path / "skills"


@pytest.fixture
def installed(dest):
    completed = run_tool("--dest", str(dest))
    assert completed.returncode == 0, completed.stdout + completed.stderr
    return completed


def test_fresh_install_layout(dest, installed):
    skill = dest / MAIN_SKILL
    assert (skill / "scripts" / "epb.py").is_file()
    assert (skill / "scripts" / "epb" / "launcher.py").is_file()
    rules = skill / "references" / "plugin-rules.md"
    assert rules.read_bytes() == (PLUGIN / "AGENTS.md").read_bytes()
    plugin_files = skill / "plugin-files"
    assert sorted(path.name for path in plugin_files.iterdir()) == sorted(plugin_files_expected())
    for name in plugin_files_expected():
        assert (plugin_files / name).read_bytes() == (PLUGIN / name).read_bytes(), name


def test_every_skill_is_copied_with_a_marker(dest, installed):
    version = json.loads(CODEX_MANIFEST.read_text(encoding="utf-8"))["version"]
    assert sorted(path.name for path in dest.iterdir()) == SKILLS
    for name in SKILLS:
        marker = json.loads((dest / name / MARKER).read_text(encoding="utf-8"))
        assert marker["plugin_version"] == version
        stamp = datetime.fromisoformat(marker["installed_at"].replace("Z", "+00:00"))
        assert stamp.utcoffset() is not None and stamp.utcoffset().total_seconds() == 0


def test_prints_the_next_step(installed):
    assert "doctor --setup" in installed.stdout


def test_second_run_replaces_the_copy(dest, installed):
    first = tree(dest)
    stale = dest / MAIN_SKILL / "stale-file-from-an-old-version.txt"
    stale.write_text("old", encoding="utf-8")
    completed = run_tool("--dest", str(dest))
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert not stale.exists()
    assert sorted(path.name for path in dest.iterdir()) == SKILLS  # no leftover temp folders
    second = tree(dest)
    markers = {path for path in first if path.endswith(MARKER)}
    assert set(first) == set(second)
    assert {k: v for k, v in first.items() if k not in markers} == {
        k: v for k, v in second.items() if k not in markers
    }


def test_foreign_folder_is_left_untouched(dest):
    foreign = dest / MAIN_SKILL
    (foreign / "notes").mkdir(parents=True)
    (foreign / "SKILL.md").write_text("A different skill.\n", encoding="utf-8")
    (foreign / "notes" / "keep.txt").write_bytes(b"\x00keep me\xff")
    before = tree(foreign)
    entries_before = sorted(path.name for path in dest.iterdir())

    completed = run_tool("--dest", str(dest))

    assert completed.returncode == 1
    output = completed.stdout + completed.stderr
    assert FOREIGN_MESSAGE in output
    assert "not overwriting it" in output
    assert str(dest) in output
    assert tree(foreign) == before
    assert sorted(path.name for path in dest.iterdir()) == entries_before


def test_unrelated_folders_untouched_and_no_caches_or_symlinks(dest):
    other = dest / "someone-elses-skill"
    other.mkdir(parents=True)
    (other / "SKILL.md").write_text("Another skill.\n", encoding="utf-8")
    before = tree(other)

    completed = run_tool("--dest", str(dest))

    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert tree(other) == before
    everything = list(dest.rglob("*"))
    assert [p for p in everything if p.name == "__pycache__"] == []
    assert [p for p in everything if p.suffix == ".pyc"] == []
    assert [p for p in everything if p.is_symlink()] == []


def test_dry_run_writes_nothing(dest):
    completed = run_tool("--dest", str(dest), "--dry-run")
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert MAIN_SKILL in completed.stdout
    assert not dest.exists()


def test_default_destination_is_home_agents_skills(tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    completed = run_tool(env={"HOME": str(home), "USERPROFILE": str(home)})
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert (home / ".agents" / "skills" / MAIN_SKILL / MARKER).is_file()


def test_copied_launcher_finds_plugin_files(dest, installed):
    scripts = dest / MAIN_SKILL / "scripts"
    code = (
        "import sys; sys.path.insert(0, sys.argv[1]); import epb.launcher as launcher; "
        "print(launcher.__file__); print(launcher.locate_plugin_file('requirements.txt'))"
    )
    completed = subprocess.run(
        [sys.executable, "-I", "-c", code, str(scripts)],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=60,
    )
    assert completed.returncode == 0, completed.stderr
    module_file, located = completed.stdout.splitlines()
    assert Path(module_file).resolve().is_relative_to(scripts.resolve())
    expected = dest / MAIN_SKILL / "plugin-files" / "requirements.txt"
    assert Path(located).resolve() == expected.resolve()
