"""The ``epb`` command-line front end: argparse shell, command discovery and the envelope.

Module-level imports are standard library and ``epb`` stdlib-only modules, so the parser can
be built before the private environment exists. The CLI never prompts and never reads stdin
(D-15).
"""

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

from epb import __version__, commands, launcher
from epb.errors import EXIT_OK, EpbError, warning

DEFAULT_WAIT = 60.0


@dataclass
class Context:
    """What a command needs besides its own arguments."""

    case: Path
    json: bool
    verbose: bool
    wait: float
    warnings: list = field(default_factory=list)

    def warn(self, code, message, hint=None):
        self.warnings.append(warning(code, message, hint))


@dataclass
class Result:
    """What a command returns on success."""

    data: dict = field(default_factory=dict)
    next: list = field(default_factory=list)
    message: str = ""


class EpbArgumentParser(argparse.ArgumentParser):
    """An ArgumentParser whose errors become ``USAGE`` failures instead of exiting."""

    def error(self, message):
        raise EpbError("USAGE", message, hint="Run with --help to see the accepted arguments.")


def _parser_kwargs():
    kwargs = {"allow_abbrev": False}
    if sys.version_info >= (3, 14):
        kwargs["color"] = False
    return kwargs


def _add_global_options(parser, suppress):
    """Add the global options. Subparsers get copies with suppressed defaults, so a value
    given after the command overrides the top-level default without resetting it."""

    def default(value):
        return argparse.SUPPRESS if suppress else value

    parser.add_argument(
        "--case",
        metavar="DIR",
        default=default(None),
        help="the case folder (default: the current folder)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        default=default(False),
        help="print one JSON envelope on stdout",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        default=default(False),
        help="show more detail",
    )
    parser.add_argument(
        "--wait",
        metavar="SECONDS",
        type=float,
        default=default(DEFAULT_WAIT),
        help="how long to wait for the workspace lock (default: 60)",
    )


def build_parser(modules=None):
    """Build the full parser: global options plus one subparser per command module."""
    if modules is None:
        modules = commands.discover()
    parser = EpbArgumentParser(
        prog="epb",
        description="ProbeMatrix Evidence Pack Builder.",
        **_parser_kwargs(),
    )
    _add_global_options(parser, suppress=False)
    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND", required=True)
    for module in modules:
        sub = subparsers.add_parser(
            module.NAME, help=module.HELP, description=module.HELP, **_parser_kwargs()
        )
        _add_global_options(sub, suppress=True)
        module.add_arguments(sub)
    return parser


def _envelope(command, exit_code, data, warnings, errors, next_steps):
    return {
        "ok": exit_code == EXIT_OK,
        "command": command,
        "exit_code": exit_code,
        "epb_version": __version__,
        "data": data,
        "warnings": list(warnings),
        "errors": list(errors),
        "next": list(next_steps),
    }


def _reconfigure_streams():
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8")
        except (OSError, ValueError):
            pass


def _render_human(envelope, message):
    if message:
        print(message)
    for item in envelope["warnings"]:
        print(f"Warning: {item['message']}", file=sys.stderr)
        if item.get("hint"):
            print(f"What to do: {item['hint']}", file=sys.stderr)
    for item in envelope["errors"]:
        print(f"Error: {item['message']}", file=sys.stderr)
        if item.get("hint"):
            print(f"What to do: {item['hint']}", file=sys.stderr)


def main(argv=None):
    """Run one command and return its exit code (0 OK, 1 gate, 2 usage, 3 missing
    dependency, 4 internal or environment)."""
    if argv is None:
        argv = sys.argv[1:]
    argv = list(argv)
    _reconfigure_streams()
    json_mode = "--json" in argv
    command = None
    ctx = None
    message = ""
    data = {}
    next_steps = []
    errors = []
    try:
        modules = commands.discover()
        by_name = {module.NAME: module for module in modules}
        parser = build_parser(modules)
        token = launcher.command_token(argv)
        if token in by_name:  # so a usage error after a valid command still names it
            command = token
        try:
            args = parser.parse_args(argv)
        except SystemExit as exc:  # --help and --version print and exit normally
            return exc.code if isinstance(exc.code, int) else EXIT_OK
        command = args.command
        json_mode = bool(args.json)
        ctx = Context(
            case=Path(args.case).expanduser().absolute() if args.case else Path.cwd(),
            json=json_mode,
            verbose=bool(args.verbose),
            wait=float(args.wait),
        )
        result = by_name[command].run(args, ctx)
        data = dict(result.data)
        next_steps = list(result.next)
        message = result.message
        exit_code = EXIT_OK
    except EpbError as exc:
        errors = [exc.to_dict()]
        data = dict(exc.data or {})
        exit_code = exc.exit_code
    warnings = ctx.warnings if ctx is not None else []
    envelope = _envelope(command, exit_code, data, warnings, errors, next_steps)
    if json_mode:
        print(json.dumps(envelope, ensure_ascii=False))
    else:
        _render_human(envelope, message)
    return exit_code
