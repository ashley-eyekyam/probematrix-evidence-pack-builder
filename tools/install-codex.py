"""Install the plugin's skills for Codex without the marketplace (D-01).

The primary Codex route is the marketplace. This fallback copies every folder in
``plugin/skills/`` into a skills folder that Codex reads (``~/.agents/skills`` by default).
Each copy is a plain copy: no symlinks, no ``__pycache__``. The evidence-pack copy also gets
``references/plugin-rules.md`` (the plugin's ``AGENTS.md``) and ``plugin-files/`` (the
requirement and security-exception files), which ``epb.launcher.locate_plugin_file`` checks
first.

Safety (T-01-13): the installer only ever replaces a folder that carries its own
``.epb-installed`` marker. When a folder with the same name exists without the marker, it
stops before changing anything and exits 1.

Usage: python3 tools/install-codex.py [--dest DIR] [--dry-run]   (py -3 on Windows)
Standard library only.
"""

import argparse
import json
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN = REPO_ROOT / "plugin"
SKILLS = PLUGIN / "skills"
CODEX_MANIFEST = PLUGIN / ".codex-plugin" / "plugin.json"
RULES = PLUGIN / "AGENTS.md"

MAIN_SKILL = "evidence-pack"
MARKER = ".epb-installed"
RULES_COPY = Path("references") / "plugin-rules.md"
PLUGIN_FILES_DIR = "plugin-files"  # must match epb.launcher.PLUGIN_FILES_DIR
IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo", ".DS_Store")


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Copy the plugin's skills into a Codex skills folder."
    )
    parser.add_argument(
        "--dest",
        type=Path,
        default=Path.home() / ".agents" / "skills",
        help="skills folder to install into (default: ~/.agents/skills)",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="print what would be copied and write nothing"
    )
    return parser.parse_args(argv)


def plugin_version():
    return json.loads(CODEX_MANIFEST.read_text(encoding="utf-8"))["version"]


def skill_sources():
    return sorted(path for path in SKILLS.iterdir() if path.is_dir() and not path.is_symlink())


def plugin_files():
    """The files that ship at the plugin root and are needed beside a copied skill."""
    files = sorted(PLUGIN.glob("requirements*.txt"))
    files.append(PLUGIN / "security-exceptions.json")
    return files


def is_ours(target):
    """True when ``target`` is a real folder that this installer created earlier."""
    return target.is_dir() and not target.is_symlink() and (target / MARKER).is_file()


def foreign_targets(dest, sources):
    """Names in ``dest`` that exist but were not installed by this tool."""
    names = []
    for source in sources:
        target = dest / source.name
        present = target.is_symlink() or target.exists()
        if present and not is_ours(target):
            names.append(source.name)
    return names


def build_copy(source, staging, version):
    """Fill ``staging`` with a complete copy of one skill, ready to swap into place."""
    shutil.copytree(source, staging, symlinks=False, ignore=IGNORE, dirs_exist_ok=True)
    if source.name == MAIN_SKILL:
        rules = staging / RULES_COPY
        rules.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(RULES, rules)
        extra = staging / PLUGIN_FILES_DIR
        extra.mkdir(exist_ok=True)
        for path in plugin_files():
            shutil.copyfile(path, extra / path.name)
    marker = {
        "plugin_version": version,
        "installed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    (staging / MARKER).write_text(json.dumps(marker, indent=2) + "\n", encoding="utf-8")


def install_one(source, dest, version):
    """Copy one skill into ``dest``, replacing an earlier copy of ours only at the end."""
    target = dest / source.name
    staging = Path(tempfile.mkdtemp(prefix=f".{source.name}.epb-new-", dir=dest))
    old = None
    try:
        build_copy(source, staging, version)
        if target.exists():
            old = Path(tempfile.mkdtemp(prefix=f".{source.name}.epb-old-", dir=dest))
            old.rmdir()
            target.rename(old)
        staging.rename(target)
    except BaseException:
        if old is not None and old.exists() and not target.exists():
            old.rename(target)  # put the earlier copy back
        shutil.rmtree(staging, ignore_errors=True)
        raise
    if old is not None:
        shutil.rmtree(old, ignore_errors=True)


def next_step(dest):
    python = "py -3" if sys.platform == "win32" else "python3"
    script = dest / MAIN_SKILL / "scripts" / "epb.py"
    return (
        "Next step: open Codex and ask it to run first-time setup for the evidence pack "
        f'skill, or run this in a terminal:\n  {python} "{script}" doctor --setup'
    )


def main(argv):
    args = parse_args(argv)
    dest = args.dest.expanduser().absolute()
    sources = skill_sources()
    version = plugin_version()

    for name in foreign_targets(dest, sources):
        print(
            f"A different skill named {name} already exists in {dest}; not overwriting it.",
            file=sys.stderr,
        )
        return 1

    if args.dry_run:
        for source in sources:
            print(f"Would copy {source} -> {dest / source.name}")
        print(f"Would copy {RULES} -> {dest / MAIN_SKILL / RULES_COPY}")
        for path in plugin_files():
            print(f"Would copy {path} -> {dest / MAIN_SKILL / PLUGIN_FILES_DIR / path.name}")
        print("Dry run: nothing was written.")
        return 0

    dest.mkdir(parents=True, exist_ok=True)
    for source in sources:
        install_one(source, dest, version)
        print(f"Installed {source.name} {version} into {dest / source.name}")
    print(next_step(dest))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
