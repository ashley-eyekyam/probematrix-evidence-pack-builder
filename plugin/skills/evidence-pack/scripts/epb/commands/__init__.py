"""Command modules for the ``epb`` CLI.

Each command is one module in this package. A command module defines, at module level:

- ``NAME: str``: the command word, for example ``"scan"``
- ``HELP: str``: one line of help text
- ``MUTATING: bool``: whether the command changes the workspace
- ``add_arguments(parser) -> None``: adds the command's own options
- ``run(args, ctx) -> epb.cli.Result``: does the work

Module-level imports are limited to the standard library and ``epb.errors``,
``epb.launcher`` and ``epb.doctor``; third-party packages are imported inside ``run()`` so
that building the parser never needs them. Modules whose name starts with an underscore are
helpers, not commands, and are skipped.
"""

import importlib
import pkgutil

_CONTRACT = ("NAME", "HELP", "MUTATING", "add_arguments", "run")


def discover():
    """Import every command module in this package and return them sorted by ``NAME``."""
    modules = []
    for info in pkgutil.iter_modules(__path__):
        if info.name.startswith("_"):
            continue
        module = importlib.import_module(f"{__name__}.{info.name}")
        missing = [attr for attr in _CONTRACT if not hasattr(module, attr)]
        if missing:
            raise RuntimeError(f"command module {module.__name__} is missing {', '.join(missing)}")
        modules.append(module)
    return sorted(modules, key=lambda module: module.NAME)
