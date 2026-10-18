"""Workbook format seam (design §8.5).

Each supported output format is a data-only constants module. A future format (for
example a V3 pack) is added here without touching the pipeline.
"""

import importlib
from types import ModuleType

FORMATS = {"probematrix_v2": "epb.formats.probematrix_v2"}


def get_format(name: str) -> ModuleType:
    """Return the constants module for the named format; an unknown name raises KeyError."""
    return importlib.import_module(FORMATS[name])
