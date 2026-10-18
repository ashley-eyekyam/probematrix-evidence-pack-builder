"""Build a fake private environment for launcher tests.

The environment is a real venv at ``epb.launcher.env_dir(version)``, which the autouse fake
home in ``tests/conftest.py`` places under a throwaway folder, so the real data folder is
never touched. A ``.pth`` file lets the venv see the dev environment's packages.
"""

import os
import sys
import sysconfig
import venv
from pathlib import Path

from epb import launcher


def make_fake_env(version=None) -> Path:
    """Create a venv at the fixed env path with a current marker and return its folder."""
    path = launcher.env_dir(version)
    venv.create(path, with_pip=False, symlinks=(os.name != "nt"))
    env_purelib = Path(
        sysconfig.get_path("purelib", vars={"base": str(path), "platbase": str(path)})
    )
    env_purelib.mkdir(parents=True, exist_ok=True)
    dev_paths = []
    for name in ("purelib", "platlib"):
        dev_path = sysconfig.get_path(name)
        if dev_path not in dev_paths:
            dev_paths.append(dev_path)
    (env_purelib / "epb-dev.pth").write_text("\n".join(dev_paths) + "\n", encoding="utf-8")
    launcher.write_marker(path, launcher.marker_record(tuple(sys.version_info[:3])))
    return path
