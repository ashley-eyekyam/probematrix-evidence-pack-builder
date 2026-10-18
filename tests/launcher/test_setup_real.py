"""End-to-end first-time setup against the real package index (PKG-06, D-03, D-18).

Opt-in: runs only with ``EPB_NETWORK_TESTS=1``, because it downloads the core packages. The
autouse fake home from ``tests/conftest.py`` places the private environment under a throwaway
folder, so the real ``~/.local/share/probematrix-epb`` is never touched.

The test drives ``epb.py`` exactly as a user would, without ``EPB_IN_ENV``: setup builds the
environment, then ``init`` is re-run by the launcher inside that environment, then a second
setup reports that nothing needed doing.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
EPB_PY = REPO_ROOT / "plugin" / "skills" / "evidence-pack" / "scripts" / "epb.py"

pytestmark = pytest.mark.network


def _epb(args, cwd, timeout):
    env = dict(os.environ)
    env.pop("EPB_IN_ENV", None)
    return subprocess.run(
        [sys.executable, str(EPB_PY), *args],
        cwd=cwd,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
        timeout=timeout,
    )


def _envelope(completed):
    assert completed.stdout, completed.stderr
    return json.loads(completed.stdout)


def test_setup_then_init_runs_inside_the_new_environment(home_dir, tmp_path):
    work = tmp_path / "work"
    work.mkdir()

    first = _epb(["doctor", "--setup", "--json"], work, timeout=1200)
    envelope = _envelope(first)
    assert first.returncode == 0, json.dumps(envelope["errors"]) + first.stderr
    setup = envelope["data"]["setup"]
    assert setup["status"] == "created"
    assert Path(setup["environment"]).is_relative_to(home_dir)
    assert [step["name"] for step in setup["steps"]] == [
        "create environment",
        "upgrade pip",
        "install core packages",
        "install reviewed security pins",
        "verify",
    ]
    launch = envelope["data"]["environment"]["launch"]
    assert Path(launch[0]).exists()
    assert Path(launch[0]).is_relative_to(home_dir)
    assert launch[1] == str(EPB_PY)
    assert all(package["ok"] for package in envelope["data"]["core_packages"])
    assert (Path(setup["environment"]) / "epb-env.json").is_file()

    case = tmp_path / "case"
    case.mkdir()
    init = _epb(
        [
            "init",
            "--title",
            "Network Setup Check",
            "--prefix",
            "NSC",
            "--timezone",
            "UTC",
            "--json",
        ],
        case,
        timeout=300,
    )
    assert init.returncode == 0, init.stdout + init.stderr
    assert _envelope(init)["ok"] is True
    assert (case / ".epb" / "case.yaml").is_file()

    second = _epb(["doctor", "--setup", "--json"], work, timeout=600)
    again = _envelope(second)
    assert second.returncode == 0, json.dumps(again["errors"]) + second.stderr
    assert again["data"]["setup"]["status"] == "ready"
    assert [item["code"] for item in again["warnings"]] == ["ALREADY_SET_UP"]
