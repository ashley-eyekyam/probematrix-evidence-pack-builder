"""Text-mode subprocess calls must name an encoding (verification gap 1, review D-CR-01).

CI runs the suite with ``PYTHONWARNDEFAULTENCODING=1`` and pyproject.toml turns every
``EncodingWarning`` into an error, so a ``subprocess.run(..., text=True)`` without
``encoding=`` fails there but passes in a plain local run. This guard catches the whole
class statically, with or without the variable.
"""

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCANNED_DIRS = ("plugin", "tools", "tests")
TEXT_MODE_KEYWORDS = {"text", "universal_newlines"}


def _is_true(node):
    return isinstance(node, ast.Constant) and node.value is True


def _offenders(path):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        keywords = {kw.arg: kw.value for kw in node.keywords if kw.arg is not None}
        text_mode = any(_is_true(keywords.get(name)) for name in TEXT_MODE_KEYWORDS)
        if text_mode and "encoding" not in keywords:
            yield node.lineno


def test_text_mode_subprocess_calls_name_an_encoding():
    offenders = []
    for folder in SCANNED_DIRS:
        for path in sorted((REPO_ROOT / folder).rglob("*.py")):
            relative = path.relative_to(REPO_ROOT).as_posix()
            offenders.extend(f"{relative}:{line}" for line in _offenders(path))
    assert not offenders, (
        "text-mode subprocess calls without encoding= (pass encoding='utf-8', "
        "errors='replace'): " + ", ".join(offenders)
    )
