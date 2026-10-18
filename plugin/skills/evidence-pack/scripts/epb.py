# Entry point for the ProbeMatrix Evidence Pack Builder CLI.
#
# Keep this file parseable by old Python 3 interpreters (no annotations, no walrus, no match,
# no f-string "=") so that an outdated python3 reaches the launcher's friendly version message
# instead of a SyntaxError. Standard library only.
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from epb import launcher  # noqa: E402  (stdlib-only module, imported after the path insert)

if __name__ == "__main__":
    sys.exit(launcher.main(sys.argv[1:]))
