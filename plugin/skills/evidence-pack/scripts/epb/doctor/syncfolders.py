"""Sync-folder detection (WS-12, design A1).

A case folder inside a cloud sync service would upload ``.epb/private/``, where the private
name map is kept. ``check`` reports each provider whose folder appears to contain the case
folder, from two kinds of evidence:

- the provider's own settings or environment (Dropbox ``info.json``, the Linux OneDrive
  client's ``sync_dir``, the Windows OneDrive variables, the macOS ``CloudStorage`` and iCloud
  folders), and
- a name heuristic on whole path components, such as ``OneDrive - Contoso`` or ``My Drive``.

Everything except Dropbox's ``info.json`` is a research assumption (A5), so the result is
always worded "appears to be inside" and is a warning, never a refusal. The table is data:
fixing a rule is a one-line edit. ``init`` (plan 01-11) reuses this module.

Standard library only.
"""

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path

from epb.doctor import tools
from epb.errors import warning


@dataclass(frozen=True)
class SyncHit:
    """One provider that appears to contain the case folder. ``root`` is the provider's
    folder when it was found from settings, or None for a name-heuristic match."""

    provider: str
    root: str | None
    reason: str


@dataclass(frozen=True)
class Provider:
    """One sync service: functions that list its folders on an OS, and whole-component name
    patterns (matched case-insensitively). A ``generic`` provider is reported only when no
    named provider matched."""

    name: str
    roots: tuple
    patterns: tuple
    generic: bool = False


def _patterns(*expressions):
    return tuple(re.compile(expression, re.IGNORECASE) for expression in expressions)


def _read_json(path):
    try:
        with open(path, encoding="utf-8") as stream:
            return json.load(stream)
    except (OSError, ValueError):
        return None


def _env_path(environ, name):
    value = environ.get(name)
    return Path(value) if value else None


# --- root finders: (home, environ, os_id) -> [(folder, reason)] -------------------------------


def _dropbox_roots(home, environ, os_id):
    if os_id == "windows":
        bases = [
            _env_path(environ, "APPDATA") or home / "AppData" / "Roaming",
            _env_path(environ, "LOCALAPPDATA") or home / "AppData" / "Local",
        ]
        files = [base / "Dropbox" / "info.json" for base in bases]
    else:
        files = [home / ".dropbox" / "info.json"]
    found = []
    for info in files:
        accounts = _read_json(info)
        if not isinstance(accounts, dict):
            continue
        for account in accounts.values():
            path = account.get("path") if isinstance(account, dict) else None
            if isinstance(path, str) and path:
                found.append((Path(path), f"the Dropbox settings file {info}"))
    return found


_SYNC_DIR = re.compile(r"""^\s*sync_dir\s*=\s*["']?(.*?)["']?\s*$""")


def _onedrive_roots(home, environ, os_id):
    found = []
    if os_id == "linux":
        config = home / ".config" / "onedrive" / "config"
        try:
            lines = config.read_text(encoding="utf-8").splitlines()
        except (OSError, ValueError):
            lines = []
        for line in lines:
            match = _SYNC_DIR.match(line)
            if match is None or not match.group(1):
                continue
            value = match.group(1)
            if value == "~" or value.startswith(("~/", "~\\")):
                folder = home / value[2:] if len(value) > 1 else home
            else:
                folder = Path(value)
                if not folder.is_absolute():
                    folder = home / folder
            found.append((folder, f"the OneDrive client settings file {config}"))
    elif os_id == "macos":
        for folder in sorted((home / "Library" / "CloudStorage").glob("OneDrive-*")):
            found.append((folder, "the macOS OneDrive folder"))
    elif os_id == "windows":
        for name in ("OneDrive", "OneDriveConsumer", "OneDriveCommercial"):
            folder = _env_path(environ, name)
            if folder is not None:
                found.append((folder, f"the {name} environment variable"))
    return found


def _google_drive_roots(home, environ, os_id):
    if os_id != "macos":
        return []
    return [
        (folder, "the macOS Google Drive folder")
        for folder in sorted((home / "Library" / "CloudStorage").glob("GoogleDrive-*"))
    ]


def _icloud_roots(home, environ, os_id):
    if os_id == "macos":
        folder = home / "Library" / "Mobile Documents" / "com~apple~CloudDocs"
        return [(folder, "the macOS iCloud Drive folder")]
    if os_id == "windows":
        return [(home / "iCloudDrive", "the Windows iCloud Drive folder")]
    return []


PROVIDERS = (
    Provider(
        name="Dropbox",
        roots=(_dropbox_roots,),
        patterns=_patterns(r"dropbox", r"dropbox \(.+\)"),
    ),
    Provider(
        name="OneDrive",
        roots=(_onedrive_roots,),
        patterns=_patterns(r"onedrive", r"onedrive - .+", r"onedrive-.+"),
    ),
    Provider(
        name="Google Drive",
        roots=(_google_drive_roots,),
        # google-drive:... is the GNOME online-accounts mount under /run/user/<uid>/gvfs/.
        patterns=_patterns(r"google drive", r"googledrive-.+", r"my drive", r"google-drive:.*"),
    ),
    Provider(
        name="iCloud Drive",
        roots=(_icloud_roots,),
        patterns=_patterns(
            r"icloud drive", r"iclouddrive", r"mobile documents", r"com~apple~clouddocs"
        ),
    ),
    Provider(
        name="a cloud sync service",
        roots=(),
        patterns=_patterns(r"cloudstorage"),
        generic=True,
    ),
)


# --- matching ---------------------------------------------------------------------------------


def _resolve(path):
    try:
        return Path(path).resolve()
    except (OSError, RuntimeError):
        return Path(os.path.abspath(str(path)))


def _within(target, root, fold):
    """True when ``target`` is ``root`` or lies under it, comparing whole components."""
    target_parts, root_parts = target.parts, root.parts
    if len(root_parts) > len(target_parts):
        return False
    if fold:
        return [part.casefold() for part in target_parts[: len(root_parts)]] == [
            part.casefold() for part in root_parts
        ]
    return target_parts[: len(root_parts)] == root_parts


def _match(provider, target, home, environ, os_id):
    fold = os_id in ("windows", "macos")
    for finder in provider.roots:
        for folder, reason in finder(home, environ, os_id):
            root = _resolve(folder)
            if _within(target, root, fold):
                return SyncHit(provider.name, str(root), reason)
    for component in target.parts:
        if any(pattern.fullmatch(component) for pattern in provider.patterns):
            return SyncHit(provider.name, None, f'a folder named "{component}" in its path')
    return None


def check(path, *, home=None, environ=None, platform=None):
    """The sync providers that appear to contain ``path``, in ``PROVIDERS`` order, each
    reported once. ``home``, ``environ`` and ``platform`` default to this computer's."""
    home = Path(home) if home is not None else Path.home()
    environ = os.environ if environ is None else environ
    os_id = tools.os_id(platform)
    target = _resolve(path)
    hits = []
    for provider in PROVIDERS:
        if provider.generic and hits:
            continue
        hit = _match(provider, target, home, environ, os_id)
        if hit is not None:
            hits.append(hit)
    return hits


def warning_for(hit):
    """The plain-language ``SYNC_FOLDER`` warning for one hit."""
    return warning(
        "SYNC_FOLDER",
        f"This folder appears to be inside {hit.provider}. Sync services upload everything in "
        "it, including .epb/private/, where the private name map will be kept.",
        hint=f"Move the case folder to a folder that {hit.provider} does not sync, then continue.",
    )
