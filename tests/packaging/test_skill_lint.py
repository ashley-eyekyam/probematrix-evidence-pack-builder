"""Agent Skills format lint for every shipped SKILL.md (PKG-01, D-04, research Pattern 1).

``claude plugin validate --strict`` accepts frontmatter keys and names that other hosts
reject (it passed ``argument-hint:`` and ``name: Evidence_Pack``), so the portable format is
checked here: frontmatter keys from the Agent Skills list only, a lower-case kebab name equal
to the folder name, a description of at most 1,024 characters and a file of at most 150
lines.
"""

import re
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILLS_DIR = REPO_ROOT / "plugin" / "skills"
ROUTER = SKILLS_DIR / "evidence-pack" / "SKILL.md"
SKILL_FILES = sorted(SKILLS_DIR.glob("*/SKILL.md"))

ALLOWED_KEYS = frozenset(
    {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
)
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
MAX_NAME = 64
MAX_DESCRIPTION = 1024
MAX_COMPATIBILITY = 500
MAX_LINES = 150


def split_frontmatter(text):
    """The parsed frontmatter mapping and the body of a SKILL.md, or fail the test."""
    lines = text.splitlines()
    assert lines and lines[0] == "---", "SKILL.md must open with a '---' frontmatter line"
    try:
        end = lines.index("---", 1)
    except ValueError:
        pytest.fail("SKILL.md frontmatter has no closing '---' line")
    meta = yaml.safe_load("\n".join(lines[1:end]))
    assert isinstance(meta, dict), "SKILL.md frontmatter is not a YAML mapping"
    return meta, "\n".join(lines[end + 1 :])


def router_text():
    return ROUTER.read_text(encoding="utf-8") if ROUTER.is_file() else ""


def test_router_skill_exists():
    assert ROUTER.is_file(), "plugin/skills/evidence-pack/SKILL.md is missing"
    assert ROUTER in SKILL_FILES


@pytest.mark.parametrize("path", SKILL_FILES, ids=lambda p: p.parent.name)
def test_frontmatter_keys_are_portable(path):
    meta, _ = split_frontmatter(path.read_text(encoding="utf-8"))
    unknown = sorted(set(meta) - ALLOWED_KEYS)
    assert unknown == [], f"{path.parent.name}: keys outside the Agent Skills list: {unknown}"


@pytest.mark.parametrize("path", SKILL_FILES, ids=lambda p: p.parent.name)
def test_name_matches_folder(path):
    meta, _ = split_frontmatter(path.read_text(encoding="utf-8"))
    name = meta.get("name")
    assert isinstance(name, str), "name must be a string"
    assert name == path.parent.name
    assert NAME_RE.match(name), f"name {name!r} is not lower-case kebab"
    assert len(name) <= MAX_NAME


@pytest.mark.parametrize("path", SKILL_FILES, ids=lambda p: p.parent.name)
def test_description_length(path):
    meta, _ = split_frontmatter(path.read_text(encoding="utf-8"))
    description = meta.get("description")
    assert isinstance(description, str) and description.strip(), "description is empty"
    assert len(description) <= MAX_DESCRIPTION, f"description has {len(description)} chars"


@pytest.mark.parametrize("path", SKILL_FILES, ids=lambda p: p.parent.name)
def test_compatibility_length(path):
    meta, _ = split_frontmatter(path.read_text(encoding="utf-8"))
    if "compatibility" in meta:
        assert isinstance(meta["compatibility"], str)
        assert len(meta["compatibility"]) <= MAX_COMPATIBILITY


@pytest.mark.parametrize("path", SKILL_FILES, ids=lambda p: p.parent.name)
def test_at_most_150_lines(path):
    assert len(path.read_text(encoding="utf-8").splitlines()) <= MAX_LINES


def test_router_frontmatter():
    meta, _ = split_frontmatter(router_text())
    assert meta["name"] == "evidence-pack"
    assert meta.get("license") == "MIT"
    assert "ProbeMatrix" in meta["description"]
    assert "evidence pack" in meta["description"].lower()


@pytest.mark.parametrize(
    "phrase",
    [
        "doctor --setup",
        "init",
        "scan",
        "INDEX.md",
        "../../AGENTS.md",
        "references/plugin-rules.md",
        "data.environment.launch",
        "${CLAUDE_SKILL_DIR}/scripts/epb.py",
        "--timezone",
        "EVD-ACM-001",
        "STATE_INVALID",
        "waiting for conversion",
        "none yet",
    ],
)
def test_router_covers_phase_1_scope(phrase):
    assert phrase in router_text()


def test_router_says_later_stages_arrive_later():
    body = re.sub(r"\s+", " ", router_text()).lower()
    for stage in ("conversion", "extraction", "de-identification", "workbook"):
        assert stage in body
    assert "later version" in body


def test_router_forbids_elevated_commands_and_import_claims():
    body = re.sub(r"\s+", " ", router_text()).lower()
    assert "never run sudo" in body
    assert "never say a probematrix import worked" in body
    assert "never put personal names on the command line" in body


def test_router_says_file_names_are_shown_as_they_are():
    """Gap 5 (C-CR-01): INDEX.md and the records show input file names as given, so the agent
    flags a name that looks personal, by input ID, and leaves renaming to the user."""
    body = re.sub(r"\s+", " ", router_text()).lower()
    assert "names exactly as they are" in body
    assert "looks like a person's name" in body
    assert "never rename, move or edit" in body
