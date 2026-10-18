"""The case settings file ``.epb/case.yaml`` (WS-01, WS-08, D-15).

``epb init`` writes it once, in the same transaction as ``state.json``. Every scalar in it is
text, and it is read back through the strict text-only YAML loader, so a value such as
``0123`` or ``no`` never changes type.
"""

from dataclasses import dataclass
from pathlib import Path

from epb import schema, yamlio
from epb.errors import EpbError
from epb.state import SCHEMA_VERSION

CASE_FILE = ".epb/case.yaml"

_DAMAGED_MESSAGE = "The case settings file .epb/case.yaml is damaged and cannot be read safely."
_DAMAGED_HINT = (
    "Restore .epb/case.yaml from a backup or from version control if you keep one. "
    "Do not edit it by hand, and do not ask the agent to repair it."
)


@dataclass(frozen=True)
class CaseSettings:
    """The four settings ``epb init`` takes from its flags or derives as defaults."""

    title: str
    slug: str
    id_prefix: str
    timezone: str


def new_case_record(settings: CaseSettings, plugin_version: str, created_at: str) -> dict:
    """The ``case.yaml`` record for a newly set-up case folder; every scalar is text."""
    return {
        "schema_version": str(SCHEMA_VERSION),
        "slug": settings.slug,
        "title": settings.title,
        "id_prefix": settings.id_prefix,
        "timezone": settings.timezone,
        "created_at": created_at,
        "plugin_version": plugin_version,
        "languages": ["en"],
        "draft_warning_days": "7",
        "conflict_tolerance_seconds": "60",
        "tags_extra": [],
    }


def _damaged(data=None) -> EpbError:
    return EpbError("STATE_INVALID", _DAMAGED_MESSAGE, hint=_DAMAGED_HINT, data=data)


def load_case(case_root) -> dict:
    """Read and check ``.epb/case.yaml``; anything missing, unreadable, non-text or
    schema-invalid exits 4 ``STATE_INVALID``."""
    path = Path(case_root) / CASE_FILE
    try:
        text = path.read_bytes().decode("utf-8")
        data = yamlio.load_text_yaml(text, source=CASE_FILE)
    except (OSError, UnicodeDecodeError, yamlio.YamlTextError):
        raise _damaged() from None
    if not isinstance(data, dict):
        raise _damaged()
    issues = schema.validate(data, "case")
    if issues:
        error = _damaged({"issues": [issue.to_dict() for issue in issues]})
        error.pointer = issues[0].pointer
        raise error
    return data


def resolve_settings(args, case_root) -> CaseSettings:
    """The case settings from the ``init`` flags."""
    return CaseSettings(
        title=args.title,
        slug=args.slug,
        id_prefix=args.prefix,
        timezone=args.timezone,
    )
