"""Read-only git tracking check (WS-11, design A2).

``.epb/private/`` holds raw-text state that must never be committed. ``check`` warns when the
case folder sits in a git work tree that already tracks files there (``GIT_TRACKS_PRIVATE``)
or would pick them up (``GIT_PRIVATE_NOT_IGNORED``). Without a usable git binary it walks up
from the case folder looking for ``.git`` and, if it finds one, says it could not check
(``GIT_UNAVAILABLE``).

Git is only ever queried, never changed (T-01-21): the only subcommands run are rev-parse,
ls-files and check-ignore, each as an argv list with ``-C <case folder>`` as separate
elements (so spaces and non-ASCII characters need no quoting), never through a shell, with a
10-second timeout. ``init`` (plan 01-11) reuses this module.

Standard library only.
"""

import os
import shutil
import subprocess
from pathlib import Path

from epb.errors import warning

GIT_TIMEOUT = 10
PRIVATE = ".epb/private"
PROBE = ".epb/private/probe"

_FAILURES = (OSError, subprocess.SubprocessError, ValueError)


def _tracks_private():
    return warning(
        "GIT_TRACKS_PRIVATE",
        "Files from .epb/private/ are tracked by git in this repository. They must never be "
        "committed.",
        hint="Stop git tracking them (for example, run git rm -r --cached .epb/private inside "
        "the case folder), then add .epb/private/ to the repository's .gitignore file.",
    )


def _private_not_ignored():
    return warning(
        "GIT_PRIVATE_NOT_IGNORED",
        ".epb/private/ is not ignored by git here, so its files could be committed.",
        hint="Add .epb/private/ to the repository's .gitignore file, so git never picks up its "
        "files.",
    )


def _unavailable(installed):
    if installed:
        reason = "git could not be run"
    else:
        reason = "git is not installed"
    return warning(
        "GIT_UNAVAILABLE",
        f"This folder is inside a git repository, but {reason}, so the plugin could not "
        "check whether .epb/private/ is ignored.",
        hint="Make sure .epb/private/ is listed in the repository's .gitignore file.",
    )


def _inside_git_by_walk(case_root):
    """True when the case folder or a folder above it has a ``.git`` entry (a folder, or the
    file a linked worktree or submodule uses)."""
    try:
        start = Path(case_root).resolve()
    except (OSError, RuntimeError):
        start = Path(os.path.abspath(str(case_root)))
    for folder in (start, *start.parents):
        if (folder / ".git").exists():
            return True
    return False


def _git(run, git, case_root, *args):
    return run(
        [git, "-C", str(case_root), *args],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=GIT_TIMEOUT,
        env=dict(os.environ, GIT_OPTIONAL_LOCKS="0"),
    )


def check(case_root, *, which=shutil.which, run=subprocess.run):
    """The git warnings for ``case_root``: a list of envelope warning entries, empty when the
    folder is not in a git work tree or ``.epb/private/`` is safely ignored."""
    git = which("git")
    if not git:
        return [_unavailable(installed=False)] if _inside_git_by_walk(case_root) else []
    try:
        top = _git(run, git, case_root, "rev-parse", "--show-toplevel")
    except _FAILURES:
        return [_unavailable(installed=True)] if _inside_git_by_walk(case_root) else []
    if top.returncode != 0:
        return []
    warnings = []
    try:
        tracked = _git(run, git, case_root, "ls-files", "--", PRIVATE)
        if tracked.returncode == 0 and tracked.stdout.strip():
            warnings.append(_tracks_private())
        ignored = _git(run, git, case_root, "check-ignore", "-q", "--", PROBE)
        if ignored.returncode == 1:
            warnings.append(_private_not_ignored())
    except _FAILURES:
        warnings.append(_unavailable(installed=True))
    return warnings
