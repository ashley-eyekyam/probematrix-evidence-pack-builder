"""The workspace lock ``.epb/lock`` (WS-07, research Pattern 3).

Every command that changes a case folder holds this lock for its whole run, so two commands,
for example from two agents, can never interleave their changes. Read-only commands take no
lock.

It is an OS advisory lock: ``fcntl.flock`` on POSIX, ``msvcrt.locking`` on the first byte on
Windows (the Windows branch is untested until after v0.1.0, research A10). The operating
system releases it when the holding process ends for any reason, including a crash, so there
is no stale-lock handling. The lock never checks whether a process is alive and never signals
one: on Windows, the call that probes a process elsewhere terminates it instead.

After taking the lock, the holder writes ``{"pid", "command", "started"}`` into the file so a
waiting command can say which command holds it. The host name is deliberately left out,
because host names often contain a person's name.
"""

import json
import os
import sys
import time

from epb import fsio
from epb.errors import EpbError

if sys.platform == "win32":  # pragma: no cover - Windows is untested until after v0.1.0
    import msvcrt
else:
    import fcntl

LOCK_FILE = ".epb/lock"

_HINT = (
    "Wait for it to finish, then try again. "
    "The lock is released automatically when that command stops."
)


def _try_lock(fd: int) -> bool:
    try:
        if sys.platform == "win32":  # pragma: no cover
            os.lseek(fd, 0, os.SEEK_SET)
            msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
        else:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        return False
    return True


def _unlock(fd: int) -> None:
    if sys.platform == "win32":  # pragma: no cover
        os.lseek(fd, 0, os.SEEK_SET)
        msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
    else:
        fcntl.flock(fd, fcntl.LOCK_UN)


class LockHandle:
    """A held workspace lock; release it with ``release()`` or a ``with`` block."""

    def __init__(self, fd: int, path: str):
        self._fd = fd
        self.path = path

    def release(self) -> None:
        """Unlock and close the lock file. Safe to call more than once."""
        fd, self._fd = self._fd, None
        if fd is None:
            return
        try:
            _unlock(fd)
        finally:
            os.close(fd)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.release()


def _write_holder(fd: int, command: str) -> None:
    data = json.dumps(
        {"pid": os.getpid(), "command": command, "started": fsio.utc_now_iso()},
        ensure_ascii=False,
    ).encode("utf-8")
    os.ftruncate(fd, 0)
    os.lseek(fd, 0, os.SEEK_SET)
    os.write(fd, data)


def _holder_text(path) -> str:
    """Who holds the lock, read best-effort from the lock file."""
    try:
        with open(path, "rb") as handle:
            record = json.loads(handle.read().decode("utf-8"))
        command, started = record["command"], record["started"]
        if isinstance(command, str) and isinstance(started, str) and command and started:
            return f"Another epb command ({command}, started {started})"
    except (OSError, UnicodeDecodeError, ValueError, KeyError, TypeError):
        pass
    return "Another epb command"


def acquire(path, *, wait_s, command, poll_s=0.2) -> LockHandle:
    """Take the lock at ``path``, waiting up to ``wait_s`` seconds, or exit 4
    ``LOCK_TIMEOUT`` naming the command that holds it."""
    path = os.fspath(path)
    fd = os.open(path, os.O_RDWR | os.O_CREAT, 0o644)
    deadline = time.monotonic() + max(float(wait_s), 0.0)
    try:
        while not _try_lock(fd):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise EpbError(
                    "LOCK_TIMEOUT",
                    f"{_holder_text(path)} is still changing this case folder.",
                    hint=_HINT,
                    data={"lock": LOCK_FILE, "waited_seconds": float(wait_s)},
                )
            time.sleep(min(poll_s, remaining))
    except BaseException:
        os.close(fd)
        raise
    handle = LockHandle(fd, path)
    try:
        _write_holder(fd, command)
    except BaseException:
        handle.release()
        raise
    return handle
