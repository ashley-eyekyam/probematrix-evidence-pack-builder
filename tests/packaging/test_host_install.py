"""Isolated installs from this repo's marketplace into real Claude Code and Codex hosts
(PKG-01, D-05, research Pattern 1).

Marked ``host``: they run only with ``EPB_HOST_TESTS=1``, and each skips when its CLI is not
installed. Every install goes into a throwaway configuration folder under ``tmp_path``
(``CLAUDE_CONFIG_DIR`` or ``CODEX_HOME``) with the fake home from ``conftest.py``, so the
user's real host configuration is never read or changed.

The cache must hold the router skill, the launcher, the schemas (D-05: they travel with every
install because they sit inside ``skills/``), the plugin rules and the requirement files, and
none of the repo-only folders.
"""

import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
NAME = "probematrix-evidence-pack-builder"
PLUGIN_REF = f"{NAME}@{NAME}"
TIMEOUT = 120

EXPECTED = (
    "skills/evidence-pack/SKILL.md",
    "skills/evidence-pack/scripts/epb.py",
    "skills/evidence-pack/scripts/epb/schemas/state.schema.json",
    "AGENTS.md",
    "requirements.txt",
    "security-exceptions.json",
)
REPO_ONLY = ("docs", "tests", "tools", "evals", ".planning")

pytestmark = pytest.mark.host


def run_host(argv, env):
    """Run one host CLI command and fail with its output when it does not exit 0."""
    completed = subprocess.run(
        argv,
        cwd=REPO_ROOT,
        env=env,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=TIMEOUT,
    )
    assert completed.returncode == 0, (
        f"{' '.join(argv)} exited {completed.returncode}:\n{completed.stdout}\n{completed.stderr}"
    )
    return completed


def cached_plugin(config_dir):
    """The single installed plugin folder ``plugins/cache/<marketplace>/<plugin>/<version>``."""
    found = [p for p in (config_dir / "plugins" / "cache").glob(f"*/{NAME}/*") if p.is_dir()]
    assert len(found) == 1, f"expected one cached plugin folder, found {found}"
    return found[0]


def check_cache(root, expected):
    missing = [rel for rel in expected if not (root / rel).is_file()]
    assert missing == [], f"missing from the plugin cache: {missing}"
    leaked = [name for name in REPO_ONLY if (root / name).exists()]
    assert leaked == [], f"repo-only folders in the plugin cache: {leaked}"


def test_claude_code_install_from_marketplace(tmp_path):
    claude = shutil.which("claude")
    if claude is None:
        pytest.skip("claude CLI not installed")
    config = tmp_path / "claude-config"
    config.mkdir()
    env = dict(os.environ, CLAUDE_CONFIG_DIR=str(config))
    run_host([claude, "plugin", "marketplace", "add", str(REPO_ROOT)], env)
    run_host([claude, "plugin", "install", PLUGIN_REF], env)
    check_cache(cached_plugin(config), EXPECTED)


def test_codex_install_from_marketplace(tmp_path):
    codex = shutil.which("codex")
    if codex is None:
        pytest.skip("codex CLI not installed")
    codex_home = tmp_path / "codex-home"
    codex_home.mkdir()
    env = dict(os.environ, CODEX_HOME=str(codex_home))
    run_host([codex, "plugin", "marketplace", "add", str(REPO_ROOT)], env)
    run_host([codex, "plugin", "add", PLUGIN_REF], env)
    check_cache(cached_plugin(codex_home), EXPECTED)
