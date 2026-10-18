"""Shared test fixtures (TST-01).

Every test runs with two autouse guards: socket connections are refused, and the home
directory, app-data folders and git identity point at a throwaway fake home. Nothing here
imports ``epb`` at module level, so this file loads before the package exists; the ``cli``
fixture imports it lazily.
"""

import importlib
import json
import os
import shutil
import socket
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
EPB_PY = REPO_ROOT / "plugin/skills/evidence-pack/scripts/epb.py"

NETWORK_REFUSED = "network access is not allowed in tests"

# Variables that would let a test see the real user profile or a leaked test switch.
_ENV_TO_CLEAR = (
    "XDG_DATA_HOME",
    "XDG_CONFIG_HOME",
    "OneDrive",
    "OneDriveConsumer",
    "OneDriveCommercial",
    "EPB_IN_ENV",
    "EPB_TEST_CRASH_AT",
    "EPB_TEST_RECORD_CHECKPOINTS",
)

_ENV_TO_SET = {
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_AUTHOR_NAME": "EPB Test",
    "GIT_AUTHOR_EMAIL": "epb-test@example.invalid",
    "GIT_COMMITTER_NAME": "EPB Test",
    "GIT_COMMITTER_EMAIL": "epb-test@example.invalid",
}


@pytest.fixture(autouse=True)
def _no_network(monkeypatch):
    """Refuse every outgoing socket connection made in the test process.

    Subprocesses do not inherit this patch, so tests spawn only ``epb`` (which makes no
    network calls) and never pip.
    """

    def refuse(*args, **kwargs):
        raise RuntimeError(NETWORK_REFUSED)

    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(socket.socket, "connect_ex", refuse)
    monkeypatch.setattr(socket, "create_connection", refuse)


@pytest.fixture(autouse=True)
def _isolated_home(monkeypatch, tmp_path_factory):
    """Point the home directory and app-data folders at a fresh fake home."""
    home = tmp_path_factory.mktemp("home")
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    monkeypatch.setenv("LOCALAPPDATA", str(home / "AppData" / "Local"))
    monkeypatch.setenv("APPDATA", str(home / "AppData" / "Roaming"))
    for name, value in _ENV_TO_SET.items():
        monkeypatch.setenv(name, value)
    for name in _ENV_TO_CLEAR:
        monkeypatch.delenv(name, raising=False)
    return home


@pytest.fixture
def home_dir(_isolated_home):
    """The fake home directory for this test."""
    return _isolated_home


@pytest.fixture
def case_dir(tmp_path):
    """A new, empty case folder."""
    path = tmp_path / "case"
    path.mkdir()
    return path


@pytest.fixture
def run_epb():
    """Run the ``epb`` launcher in a subprocess and return the ``CompletedProcess``.

    With ``in_env`` true the child sees ``EPB_IN_ENV=1``: the test suite treats the dev venv
    as the plugin's private environment.
    """

    def run(args, cwd, *, env=None, in_env=True, timeout=120):
        child_env = dict(os.environ)
        if in_env:
            child_env["EPB_IN_ENV"] = "1"
        if env:
            child_env.update(env)
        return subprocess.run(
            [sys.executable, str(EPB_PY), *args],
            cwd=cwd,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=child_env,
            timeout=timeout,
        )

    return run


@pytest.fixture
def cli(monkeypatch, capsys):
    """Call ``epb.cli.main`` in-process and return its exit code and captured output.

    ``envelope`` is the parsed JSON stdout when ``--json`` is in argv, else ``None``.
    """

    def call(argv, cwd=None):
        if cwd is not None:
            monkeypatch.chdir(cwd)
        epb_cli = importlib.import_module("epb.cli")
        capsys.readouterr()  # discard anything printed before this call
        try:
            exit_code = epb_cli.main(list(argv))
        except SystemExit as exc:
            exit_code = exc.code
        captured = capsys.readouterr()
        envelope = json.loads(captured.out) if "--json" in argv else None
        return SimpleNamespace(
            exit_code=exit_code,
            stdout=captured.out,
            stderr=captured.err,
            envelope=envelope,
        )

    return call


@pytest.fixture
def need_tool():
    """Return the path of an external tool, or skip the test when it is not installed."""

    def need(name):
        path = shutil.which(name)
        if path is None:
            pytest.skip(f"{name} not installed")
        return path

    return need


_OPT_IN_MARKERS = {
    "network": ("EPB_NETWORK_TESTS", "network test; set EPB_NETWORK_TESTS=1 to run"),
    "host": ("EPB_HOST_TESTS", "host CLI test; set EPB_HOST_TESTS=1 to run"),
}


def pytest_collection_modifyitems(config, items):
    """Skip ``network`` and ``host`` tests unless their opt-in variable is set to 1."""
    for marker, (variable, reason) in _OPT_IN_MARKERS.items():
        if os.environ.get(variable) == "1":
            continue
        skip = pytest.mark.skip(reason=reason)
        for item in items:
            if marker in item.keywords:
                item.add_marker(skip)
