"""Marketplace and plugin manifests for Claude Code and Codex (PKG-01, D-01, D-02).

Codex rejects a marketplace entry whose name differs from ``plugin.json`` ``name``, and each
host installs the version from its own manifest, so names and versions must never drift
(research Pitfall 8).
"""

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest
from epb import __version__

REPO_ROOT = Path(__file__).resolve().parents[2]
PLUGIN_DIR = REPO_ROOT / "plugin"
MARKETPLACE = REPO_ROOT / ".claude-plugin" / "marketplace.json"
CLAUDE_MANIFEST = PLUGIN_DIR / ".claude-plugin" / "plugin.json"
CODEX_MANIFEST = PLUGIN_DIR / ".codex-plugin" / "plugin.json"
ALL_MANIFESTS = (MARKETPLACE, CLAUDE_MANIFEST, CODEX_MANIFEST)

NAME = "probematrix-evidence-pack-builder"
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
BOM = b"\xef\xbb\xbf"
REPO_ONLY_FOLDERS = ("docs", "tests", "tools", "evals", ".planning")
VALIDATE_TIMEOUT = 60


def load(path):
    """Parse a manifest strictly as UTF-8 JSON."""
    return json.loads(path.read_bytes().decode("utf-8"))


@pytest.mark.parametrize("path", ALL_MANIFESTS, ids=lambda p: p.relative_to(REPO_ROOT).as_posix())
def test_manifest_is_utf8_json_without_bom(path):
    data = path.read_bytes()
    assert not data.startswith(BOM), f"{path.name} starts with a byte-order mark"
    assert isinstance(load(path), dict)
    assert data.endswith(b"\n"), f"{path.name} has no trailing newline"


def test_marketplace_has_one_plugin_from_the_plugin_folder():
    marketplace = load(MARKETPLACE)
    assert marketplace["name"] == NAME
    assert marketplace["owner"]["name"]
    assert marketplace["metadata"]["description"]
    plugins = marketplace["plugins"]
    assert len(plugins) == 1
    assert plugins[0]["source"] == "./plugin"
    assert plugins[0]["description"]


def test_names_match_across_all_manifests():
    names = {
        "marketplace": load(MARKETPLACE)["name"],
        "marketplace entry": load(MARKETPLACE)["plugins"][0]["name"],
        "claude plugin.json": load(CLAUDE_MANIFEST)["name"],
        "codex plugin.json": load(CODEX_MANIFEST)["name"],
    }
    assert set(names.values()) == {NAME}, names
    for label, name in names.items():
        assert NAME_RE.match(name), f"{label} name {name!r} is not lower-case kebab"


def test_plugin_versions_equal_the_package_version():
    assert load(CLAUDE_MANIFEST)["version"] == __version__
    assert load(CODEX_MANIFEST)["version"] == __version__


def test_codex_manifest_declares_skills_and_claude_manifest_does_not():
    assert load(CODEX_MANIFEST)["skills"] == "./skills/"
    assert "skills" not in load(CLAUDE_MANIFEST)


def test_claude_manifest_required_fields():
    manifest = load(CLAUDE_MANIFEST)
    for key in ("description", "homepage", "repository", "keywords"):
        assert manifest[key], key
    assert manifest["author"]["name"]
    assert manifest["license"] == "MIT"
    assert load(CODEX_MANIFEST)["license"] == "MIT"


def test_plugin_folder_holds_no_repo_only_folders():
    present = [name for name in REPO_ONLY_FOLDERS if (PLUGIN_DIR / name).exists()]
    assert present == [], f"repo-only folders inside plugin/: {present}"


def test_repo_root_has_no_agents_path():
    # D-01: the Codex fallback is tools/install-codex.py, never a committed .agents/skills.
    assert not (REPO_ROOT / ".agents").exists()
    assert not (REPO_ROOT / ".agents").is_symlink()


def test_claude_validate_strict():
    claude = shutil.which("claude")
    if claude is None:
        pytest.skip("claude CLI not installed")
    for target in (".", "./plugin"):
        completed = subprocess.run(
            [claude, "plugin", "validate", target, "--strict"],
            cwd=REPO_ROOT,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=VALIDATE_TIMEOUT,
        )
        assert completed.returncode == 0, (
            f"claude plugin validate {target} --strict failed:\n"
            f"{completed.stdout}\n{completed.stderr}"
        )
