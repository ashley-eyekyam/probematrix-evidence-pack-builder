"""The case settings file ``.epb/case.yaml``: defaults, validation and loading (WS-01, WS-08,
D-15).

``epb init`` writes it once, in the same transaction as ``state.json``. The CLI never prompts:
the title is required, and the slug, ID prefix and timezone default to values derived from
the folder name, the title and the computer's timezone. Every scalar in the file is text, and
it is read back through the strict text-only YAML loader, so a value such as ``0123`` or
``no`` never changes type.
"""

import os
import re
import unicodedata
import zoneinfo
from dataclasses import dataclass
from pathlib import Path

from epb import schema, yamlio
from epb.errors import EpbError
from epb.state import SCHEMA_VERSION

CASE_FILE = ".epb/case.yaml"

SLUG_MAX = 40
TITLE_MAX = 200
_SLUG = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
_PREFIX = re.compile(r"^[A-Z][A-Z0-9]{1,5}$")
_ZONE_SHAPE = re.compile(r"^[A-Za-z][A-Za-z0-9_+-]*(/[A-Za-z0-9_+-]+){0,2}$")
_CONTROL = re.compile(r"[\x00-\x1f\x7f]")
_WORD = re.compile(r"[A-Za-z][A-Za-z0-9]*")
# Names Windows refuses as file names; a slug ends up in workbook file names.
_RESERVED_SLUGS = frozenset(
    {"con", "prn", "aux", "nul"}
    | {f"com{n}" for n in range(1, 10)}
    | {f"lpt{n}" for n in range(1, 10)}
)
# Files in the zoneinfo folder that ZoneInfo opens but that are not IANA zone names.
_NOT_ZONES = frozenset({"localtime", "posixrules", "Factory"})

_DAMAGED_MESSAGE = "The case settings file .epb/case.yaml is damaged and cannot be read safely."
_DAMAGED_HINT = (
    "Restore .epb/case.yaml from a backup or from version control if you keep one. "
    "Do not edit it by hand, and do not ask the agent to repair it."
)
_PREFIX_RULE = (
    "Pass --prefix with 2 to 6 capital letters or digits, starting with a letter, "
    "for example --prefix ACM."
)


@dataclass(frozen=True)
class CaseSettings:
    """The four settings ``epb init`` takes from its flags or derives as defaults."""

    title: str
    slug: str
    id_prefix: str
    timezone: str


def _ascii(text: str) -> str:
    """``text`` with accents removed and every other non-ASCII character dropped."""
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")


def derive_slug(folder_name: str) -> str:
    """A default slug from the case folder's name: lowercase ASCII words joined by hyphens,
    at most 40 characters, ``case`` when nothing is left, and ``-case`` added to a name that
    Windows reserves."""
    slug = re.sub(r"[^a-z0-9]+", "-", _ascii(folder_name).lower()).strip("-")
    slug = slug[:SLUG_MAX].rstrip("-")
    if not slug:
        return "case"
    if slug in _RESERVED_SLUGS:
        slug = f"{slug}-case"
    return slug


def derive_prefix(title: str) -> str | None:
    """A default ID prefix from the title: the initials of its ASCII words (at most 6), or
    the first three letters of a one-word title. ``None`` when the title has no ASCII word
    or the result would not be a valid prefix."""
    words = _WORD.findall(_ascii(title))
    if not words:
        return None
    prefix = "".join(word[0] for word in words)[:6].upper()
    if len(prefix) < 2:
        prefix = words[0][:3].upper()
    return prefix if _PREFIX.fullmatch(prefix) else None


def _is_zone(name) -> bool:
    if not isinstance(name, str) or len(name) > 64 or not _ZONE_SHAPE.fullmatch(name):
        return False
    if name in _NOT_ZONES:
        return False
    try:
        zoneinfo.ZoneInfo(name)
    except (zoneinfo.ZoneInfoNotFoundError, ValueError, OSError):
        return False
    return True


def _zone_from(value) -> str | None:
    """An IANA name from a ``TZ`` value, an ``/etc/timezone`` line or a link target."""
    if not value:
        return None
    value = value.strip().replace("\\", "/")
    if value.startswith(":"):
        value = value[1:]
    if "zoneinfo/" in value:
        value = value.split("zoneinfo/", 1)[1]
    return value if _is_zone(value) else None


def detect_timezone(
    *,
    environ=os.environ,
    etc_timezone=Path("/etc/timezone"),
    localtime=Path("/etc/localtime"),
) -> str | None:
    """This computer's timezone as an IANA name, or ``None`` when none can be found.

    Tries ``TZ``, then the first line of ``/etc/timezone``, then the target of the
    ``/etc/localtime`` link. Never uses ``datetime.now().astimezone()``, which gives an
    abbreviation such as ``IST`` (research Pitfall 9).
    """
    zone = _zone_from(environ.get("TZ"))
    if zone:
        return zone
    try:
        lines = Path(etc_timezone).read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        lines = []
    zone = _zone_from(lines[0]) if lines else None
    if zone:
        return zone
    try:
        target = os.readlink(localtime)
    except (OSError, ValueError):
        return None
    target = str(target).replace("\\", "/")
    return _zone_from(target) if "zoneinfo/" in target else None


def validate_timezone(name: str) -> str:
    """Return ``name`` when it is an IANA timezone name, else raise ``BAD_ARGUMENT``."""
    if not _is_zone(name):
        raise EpbError(
            "BAD_ARGUMENT",
            f"Unknown timezone {name}. Use an IANA name such as Europe/London or Asia/Kolkata.",
            hint="Pass --timezone with an IANA name such as Europe/London.",
        )
    return name


def _normalise_title(title: str) -> str:
    return unicodedata.normalize("NFC", title.strip())


def _resolve_title(raw) -> str:
    if raw is None or not raw.strip():
        raise EpbError(
            "BAD_ARGUMENT",
            "init needs --title with the case title.",
            hint='Pass --title with the case title, for example --title "Acme Pump Trip".',
        )
    title = _normalise_title(raw)
    if len(title) > TITLE_MAX:
        raise EpbError(
            "BAD_ARGUMENT",
            f"The case title is longer than {TITLE_MAX} characters.",
            hint="Pass a shorter --title.",
        )
    if _CONTROL.search(title):
        raise EpbError(
            "BAD_ARGUMENT",
            "The case title contains a line break or another control character.",
            hint="Pass --title as one line of text.",
        )
    return title


def _resolve_slug(raw, case_root) -> str:
    if raw is None:
        return derive_slug(Path(case_root).name)
    if len(raw) > SLUG_MAX or not _SLUG.fullmatch(raw) or raw in _RESERVED_SLUGS:
        raise EpbError(
            "BAD_ARGUMENT",
            f"The slug {raw!r} cannot be used. Pass --slug with up to {SLUG_MAX} lowercase "
            "letters and digits, with single hyphens between words, for example "
            "--slug acme-pump-trip.",
            hint="Leave out --slug to use one made from the folder name.",
        )
    return raw


def _resolve_prefix(raw, title: str) -> str:
    if raw is None:
        prefix = derive_prefix(title)
        if prefix is None:
            raise EpbError(
                "BAD_ARGUMENT",
                f"Could not make an ID prefix from the title. {_PREFIX_RULE}",
                hint="Pass --prefix, for example --prefix ACM.",
            )
        return prefix
    if not _PREFIX.fullmatch(raw):
        raise EpbError(
            "BAD_ARGUMENT",
            f"The ID prefix {raw!r} cannot be used. {_PREFIX_RULE}",
            hint="Leave out --prefix to use the title's initials.",
        )
    return raw


def _resolve_timezone(raw) -> str:
    if raw is not None:
        return validate_timezone(raw)
    zone = detect_timezone()
    if zone is None:
        raise EpbError(
            "TIMEZONE_REQUIRED",
            "Could not find this computer's timezone as an IANA name.",
            hint="Pass --timezone with an IANA name such as Europe/London.",
        )
    return zone


def resolve_settings(args, case_root) -> CaseSettings:
    """The case settings from the ``init`` flags, with D-15 defaults for anything not given.

    Raises ``BAD_ARGUMENT`` for a missing, blank or unusable value and ``TIMEZONE_REQUIRED``
    when no ``--timezone`` was given and none can be detected.
    """
    title = _resolve_title(args.title)
    return CaseSettings(
        title=title,
        slug=_resolve_slug(args.slug, case_root),
        id_prefix=_resolve_prefix(args.prefix, title),
        timezone=_resolve_timezone(args.timezone),
    )


def differences(record: dict, args) -> list[str]:
    """The ``init`` flags (without ``--``) given with a value that differs from the stored
    settings, in the order title, slug, prefix, timezone."""
    fields = []
    if args.title is not None and _normalise_title(args.title) != record.get("title"):
        fields.append("title")
    if args.slug is not None and args.slug != record.get("slug"):
        fields.append("slug")
    if args.prefix is not None and args.prefix != record.get("id_prefix"):
        fields.append("prefix")
    if args.timezone is not None and args.timezone != record.get("timezone"):
        fields.append("timezone")
    return fields


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
