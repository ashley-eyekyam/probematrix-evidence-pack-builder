"""Stdlib-only launcher: decides where a command runs before anything else is imported.

Keep this module parseable and importable by old Python 3 interpreters (3.6 syntax and APIs:
no annotations, no walrus, no match, no ``text=``/``capture_output=`` in subprocess calls),
so that an outdated interpreter still reaches the friendly version message.
"""

import json
import os
import sys

from epb import __version__

# Global options that take a value; their value is never the command token.
_VALUE_OPTIONS = ("--case", "--wait")


def command_token(argv):
    """Return the command name in ``argv``: the first argument that is not an option or an
    option's value. Returns None when there is no command."""
    skip_next = False
    for arg in argv:
        if skip_next:
            skip_next = False
            continue
        if arg == "--":
            return None
        if arg in _VALUE_OPTIONS:
            skip_next = True
            continue
        if arg.startswith("-"):
            continue
        return arg
    return None


def _emit_error(code, message, hint, command, json_mode, next_steps, exit_code):
    """Print one error the same way ``epb.cli`` does: an envelope under --json, else plain
    language on stderr. Returns the exit code."""
    if json_mode:
        envelope = {
            "ok": False,
            "command": command,
            "exit_code": exit_code,
            "epb_version": __version__,
            "data": {},
            "warnings": [],
            "errors": [{"code": code, "message": message, "hint": hint, "pointer": None}],
            "next": list(next_steps),
        }
        sys.stdout.write(json.dumps(envelope, ensure_ascii=False) + "\n")
        sys.stdout.flush()
    else:
        sys.stderr.write("Error: " + message + "\n")
        if hint:
            sys.stderr.write("What to do: " + hint + "\n")
        sys.stderr.flush()
    return exit_code


def main(argv):
    argv = list(argv)
    json_mode = "--json" in argv
    command = command_token(argv)
    if os.environ.get("EPB_IN_ENV") == "1":
        from epb import cli

        return cli.main(argv)
    return _emit_error(
        "ENV_NOT_SET_UP",
        "First-time setup has not been run on this computer yet.",
        "Run: doctor --setup",
        command,
        json_mode,
        ["doctor --setup"],
        3,
    )
