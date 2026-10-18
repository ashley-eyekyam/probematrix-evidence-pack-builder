"""Root AGENTS.md and CLAUDE.md are byte-identical and concise (PKG-11)."""

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
MAX_LINES = 150


def check_instructions(agents: bytes | None, claude: bytes | None, max_lines=MAX_LINES):
    """Return a list of problems with the two instruction files; empty means they pass.

    ``None`` means the file does not exist. The comparison is byte-for-byte, so a CRLF
    versus LF or trailing-newline difference counts as a difference.
    """
    problems = []
    for name, data in (("AGENTS.md", agents), ("CLAUDE.md", claude)):
        if data is None:
            problems.append(f"{name} is missing")
        elif not data.strip():
            problems.append(f"{name} is empty")
        else:
            count = len(data.splitlines())
            if count > max_lines:
                problems.append(f"{name} has {count} lines; the limit is {max_lines}")
    if agents is not None and claude is not None and agents != claude:
        problems.append("AGENTS.md and CLAUDE.md differ; copy one over the other")
    return problems


def _read(name):
    path = REPO_ROOT / name
    return path.read_bytes() if path.exists() else None


def _lines(count, ending=b"\n"):
    return b"".join(b"Line %d of the agent instructions." % n + ending for n in range(count))


def test_root_instruction_files_mirror_each_other():
    assert check_instructions(_read("AGENTS.md"), _read("CLAUDE.md")) == []


def test_identical_150_line_files_pass():
    text = _lines(150)
    assert check_instructions(text, text) == []


def test_151_lines_fail():
    text = _lines(151)
    problems = check_instructions(text, text)
    assert any("AGENTS.md has 151 lines" in p for p in problems)
    assert any("CLAUDE.md has 151 lines" in p for p in problems)


def test_150_lines_without_a_final_newline_pass():
    text = _lines(150).rstrip(b"\n")
    assert check_instructions(text, text) == []


@pytest.mark.parametrize(
    ("agents", "claude", "missing"),
    [
        (None, _lines(3), "AGENTS.md is missing"),
        (_lines(3), None, "CLAUDE.md is missing"),
        (b"", _lines(3), "AGENTS.md is empty"),
        (_lines(3), b"", "CLAUDE.md is empty"),
        (b" \n\n", b" \n\n", "AGENTS.md is empty"),
    ],
    ids=["agents-missing", "claude-missing", "agents-empty", "claude-empty", "whitespace-only"],
)
def test_missing_or_empty_file_fails(agents, claude, missing):
    assert missing in check_instructions(agents, claude)


def test_crlf_versus_lf_fails():
    problems = check_instructions(_lines(3), _lines(3, ending=b"\r\n"))
    assert any("differ" in p for p in problems)


def test_trailing_newline_difference_fails():
    problems = check_instructions(_lines(3), _lines(3) + b"\n")
    assert any("differ" in p for p in problems)


def test_one_changed_byte_in_a_copy_is_reported(tmp_path):
    original = _read("CLAUDE.md")
    assert original, "root CLAUDE.md must exist for this test"
    copy = tmp_path / "CLAUDE.md"
    copy.write_bytes(original)
    changed = bytearray(copy.read_bytes())
    changed[len(changed) // 2] ^= 0x01
    copy.write_bytes(bytes(changed))
    problems = check_instructions(_read("AGENTS.md"), copy.read_bytes())
    assert any("differ" in p for p in problems)
