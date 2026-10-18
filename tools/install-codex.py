"""Codex fallback installer (D-01). Interface skeleton only; the copy is not written yet."""

import argparse
import sys
from pathlib import Path


def parse_args(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dest", type=Path, default=Path.home() / ".agents" / "skills")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)


def main(argv):
    parse_args(argv)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
