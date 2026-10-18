"""Crash-injection seam for the test suite only (WS-06, TST-07, research Pitfall 11).

This is not a user feature and is never documented to users. The transaction code calls
``checkpoint(name)`` at every step that matters for crash safety. Two environment variables,
set only by the tests, act on it:

- ``EPB_TEST_RECORD_CHECKPOINTS`` names a file; every checkpoint reached is appended to it,
  one name per line, so the tests enumerate the checkpoints from a real run instead of a
  hand-kept list.
- ``EPB_TEST_CRASH_AT`` names one checkpoint; reaching it ends the process at once with
  ``os._exit(CRASH_EXIT_CODE)``. That is a real crash: no ``finally`` block, ``__exit__`` or
  ``atexit`` handler runs, so the tests see what a power cut would leave behind.

Both variables are read at call time. With neither set, ``checkpoint`` does nothing.
"""

import os

CRASH_EXIT_CODE = 97

_RECORD_VAR = "EPB_TEST_RECORD_CHECKPOINTS"
_CRASH_VAR = "EPB_TEST_CRASH_AT"


def checkpoint(name: str) -> None:
    """Record ``name`` and crash here when the tests ask for it."""
    record = os.environ.get(_RECORD_VAR)
    if record:
        with open(record, "a", encoding="utf-8") as handle:
            handle.write(name + "\n")
    if os.environ.get(_CRASH_VAR) == name:
        os._exit(CRASH_EXIT_CODE)
