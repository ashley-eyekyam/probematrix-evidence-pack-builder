"""The workspace lock ``.epb/lock`` (WS-07). Interface only; implemented in plan 01-12 GREEN."""

LOCK_FILE = ".epb/lock"


class LockHandle:
    """A held workspace lock."""

    def release(self) -> None:
        raise NotImplementedError

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.release()


def acquire(path, *, wait_s, command, poll_s=0.2) -> LockHandle:
    raise NotImplementedError
