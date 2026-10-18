"""The plugin's host-neutral rules for end users' agents (PKG-03, kickoff §6 and §6a).

``plugin/AGENTS.md`` ships inside the plugin. It is not the repo-root developer pair
(AGENTS.md / CLAUDE.md, PKG-11), and the plugin folder must never hold a CLAUDE.md, which
fails ``claude plugin validate --strict``.
"""

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
RULES = REPO_ROOT / "plugin" / "AGENTS.md"
REFERENCE_REPORT = next((REPO_ROOT / "docs" / "reference").rglob("*.pdf"), None)
MAX_LINES = 150
SHINGLE_WORDS = 8

HEADINGS = (
    "Just culture",
    "Roles only",
    "Inputs only",
    "Facts only",
    "Verbatim quotes",
    "Evidence-bank entry rule",
    "Working with the epb command",
)

# An honorific followed by a capitalised word is how a personal name usually appears.
HONORIFIC_NAME = re.compile(
    r"\b(?:Mr|Mrs|Ms|Miss|Dr|Shri|Smt|Sh|Er|Capt)\.?\s+[A-Z][a-z]+", re.MULTILINE
)


def rules_text():
    """The rules file, or an empty string when it does not exist yet."""
    return RULES.read_text(encoding="utf-8") if RULES.is_file() else ""


def flat(text):
    """Lower-case text with every run of whitespace collapsed to one space and the
    Markdown bold and code markers removed."""
    return re.sub(r"\s+", " ", re.sub(r"[*`]", "", text)).strip().lower()


def headings(text):
    return [line.lstrip("#").strip() for line in text.splitlines() if line.startswith("## ")]


def section(text, title):
    """The flattened body of the ``## title`` section, up to the next ``## `` heading."""
    match = re.search(rf"^## {re.escape(title)}\s*$(.*?)(?=^## |\Z)", text, re.M | re.S)
    return flat(match.group(1)) if match else ""


def words(text):
    return re.findall(r"[a-z0-9]+", text.lower())


def shingles(text, size=SHINGLE_WORDS):
    tokens = words(text)
    return {" ".join(tokens[i : i + size]) for i in range(len(tokens) - size + 1)}


def test_rules_file_exists():
    assert RULES.is_file(), "plugin/AGENTS.md is missing"


def test_headings_in_order():
    assert headings(rules_text()) == list(HEADINGS)


@pytest.mark.parametrize("title", HEADINGS)
def test_each_section_has_two_to_five_rules(title):
    match = re.search(rf"^## {re.escape(title)}\s*$(.*?)(?=^## |\Z)", rules_text(), re.M | re.S)
    body = match.group(1) if match else ""
    rules = [line for line in body.splitlines() if re.match(r"^- \S", line)]
    assert 2 <= len(rules) <= 5, f"{title}: {len(rules)} rules"


def test_evidence_bank_rule():
    body = section(rules_text(), "Evidence-bank entry rule")
    for phrase in (
        "conclusions",
        "lessons",
        "recommendations",
        "are never evidence",
        "split",
        "when in doubt, hold it back",
    ):
        assert phrase in body, f"evidence-bank section lacks {phrase!r}"


@pytest.mark.parametrize(
    "phrase",
    [
        "doctor --setup",
        "--json",
        "exit_code",
        "errors[].code",
        "never on message text",
        "exit code 4",
        "report the error code to the user",
        "never edit evidence or the .epb folder",
        "never hand-edit .epb/state.json",
        "never put personal names on the command line",
        "never claim that a probematrix import worked",
    ],
)
def test_cli_rules(phrase):
    assert phrase in section(rules_text(), "Working with the epb command")


def test_roles_only_uses_role_labels():
    body = section(rules_text(), "Roles only")
    assert "role label" in body
    assert "shift supervisor (control room)" in body


def test_verbatim_quotes_rule():
    body = section(rules_text(), "Verbatim quotes")
    assert "[sic]" in body
    assert "exact" in body


def test_at_most_150_lines():
    text = rules_text()
    assert text, "plugin/AGENTS.md is empty or missing"
    assert len(text.splitlines()) <= MAX_LINES


def test_no_personal_names():
    text = rules_text()
    assert text, "plugin/AGENTS.md is empty or missing"
    assert HONORIFIC_NAME.findall(text) == []


@pytest.mark.skipif(REFERENCE_REPORT is None, reason="reference report not present")
def test_no_text_from_the_reference_report():
    pypdf = pytest.importorskip("pypdf")
    text = rules_text()
    assert text, "plugin/AGENTS.md is empty or missing"
    reader = pypdf.PdfReader(str(REFERENCE_REPORT))
    report = " ".join(page.extract_text() or "" for page in reader.pages)
    shared = sorted(shingles(text) & shingles(report))
    assert shared == [], f"{len(shared)} eight-word runs shared with the reference report"


def test_plugin_folder_has_no_claude_md():
    assert not (REPO_ROOT / "plugin" / "CLAUDE.md").exists()
