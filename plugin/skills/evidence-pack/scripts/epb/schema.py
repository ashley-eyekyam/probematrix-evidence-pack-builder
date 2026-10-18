"""JSON Schema loading and validate-on-write (WS-08, D-05).

The only copy of the schemas lives in ``epb/schemas/`` and is read through
``importlib.resources``, so every install route carries them. Schemas use regex ``pattern``
for timestamps, IDs and hashes, never ``format``, which jsonschema ignores by default
(research Pitfall 6); validation therefore runs without a format checker.
"""

import json
from dataclasses import dataclass
from functools import cache
from importlib import resources

from epb.errors import EpbError


@dataclass(frozen=True)
class SchemaIssue:
    """One schema violation: where it is (a JSON pointer) and what is wrong."""

    pointer: str
    message: str

    def to_dict(self) -> dict:
        return {"pointer": self.pointer, "message": self.message}


@cache
def load_schema(name: str) -> dict:
    """Load ``epb/schemas/<name>.schema.json``."""
    text = resources.files("epb").joinpath("schemas", f"{name}.schema.json").read_text("utf-8")
    return json.loads(text)


@cache
def _validator(name: str):
    from jsonschema import Draft202012Validator

    schema = load_schema(name)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def _pointer(path) -> str:
    parts = [str(part).replace("~", "~0").replace("/", "~1") for part in path]
    return "/" + "/".join(parts) if parts else "/"


def validate(obj, name: str) -> list[SchemaIssue]:
    """Every way ``obj`` breaks schema ``name``, sorted by pointer then message."""
    issues = {
        SchemaIssue(_pointer(error.absolute_path), error.message)
        for error in _validator(name).iter_errors(obj)
    }
    return sorted(issues, key=lambda issue: (issue.pointer, issue.message))


def check(obj, name: str, *, label: str) -> None:
    """Raise ``RECORD_INVALID`` listing every issue when ``obj`` breaks schema ``name``."""
    issues = validate(obj, name)
    if not issues:
        return
    lines = "; ".join(f"{issue.pointer}: {issue.message}" for issue in issues)
    raise EpbError(
        "RECORD_INVALID",
        f"The record {label} does not match its schema ({name}): {lines}",
        hint="Nothing was written. Report this error code to the plugin maintainer.",
        pointer=issues[0].pointer,
        data={"issues": [issue.to_dict() for issue in issues]},
    )
