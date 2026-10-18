---
phase: 01-foundations
reviewed: 2026-10-18T15:58:17Z
depth: standard
scope: incremental (gap-closure plans 01-17 to 01-21, diff 599c253..HEAD)
supersedes: 01-REVIEW.md at 599c253
files_reviewed: 20
files_reviewed_list:
  - AGENTS.md
  - CLAUDE.md
  - docs/USER-MANUAL.md
  - plugin/skills/evidence-pack/references/workspace-contract.md
  - plugin/skills/evidence-pack/scripts/epb/commands/init.py
  - plugin/skills/evidence-pack/scripts/epb/index.py
  - plugin/skills/evidence-pack/scripts/epb/launcher.py
  - plugin/skills/evidence-pack/scripts/epb/mime.py
  - plugin/skills/evidence-pack/scripts/epb/workspace.py
  - plugin/skills/evidence-pack/SKILL.md
  - pyproject.toml
  - tests/core/test_mime.py
  - tests/docs/test_manual.py
  - tests/doctor/test_gitcheck.py
  - tests/index/test_index.py
  - tests/packaging/test_skill_lint.py
  - tests/repo/test_ci_workflow.py
  - tests/repo/test_text_subprocess_encoding.py
  - tests/workspace/test_init_defaults.py
  - tests/workspace/test_layout.py
findings:
  critical: 1
  warning: 1
  info: 6
  total: 8
status: issues_found
---

# Phase 01: Code Review Report (incremental, gap closure 01-17 to 01-21)

**Reviewed:** 2026-10-18T15:58:17Z
**Depth:** standard
**Files Reviewed:** 20
**Status:** issues_found

## Summary

This is an incremental review of the changes since `599c253`, the commit of the previous review. It covers the
INDEX.md single-line sanitiser (01-18), the refused-init-writes-nothing change (01-19), the text
byte-order mark and two-frame MPEG detection (01-20), the file-name privacy wording (01-21), and the
CI encoding parity work (01-17). I read each diff in the context of its surrounding code and ran the
suite under CI's `PYTHONWARNDEFAULTENCODING=1` (1978 passed, 3 skipped, on Python 3.14). I also ran
the CLI against hostile file names in scratch case folders.

The targeted fixes are sound. The MPEG frame-length tables and formulas match ISO/IEC 11172-3 and
13818-3. Every interpolated INDEX.md value now goes through `_inline`. A refused init on an empty or
populated folder leaves it byte-for-byte unchanged.

Two problems remain:

- **CR-01:** a file name that is not valid UTF-8 crashes `scan` with `INTERNAL_ERROR`. This is
  pre-existing and sits outside the listed files, but the new hostile-name tests miss it.
- **WR-01:** the new privacy guidance tells users to rename files to remove names, but renaming after
  a scan does not always remove the name. In one common case the name stays in `INDEX.md` for good.

### Status of the previous review's blockers

| Finding | Status | Evidence |
| --- | --- | --- |
| A-CR-01 (Markdown injection in INDEX.md) | **Fixed** | `index.py:79,100-108`; every value in `case_header`, `render_import_line`, `open_issues`, `run_history` and `render_index` goes through `_inline`, and table cells go through `_cell` -> `_inline`. The `_SINGLE_LINE` class covers every `str.splitlines()` boundary. Ignored paths always start with `inputs/`, so no list line can begin with `[x] Imported:`. Covered by `tests/index/test_index.py::test_hostile_values_cannot_break_index_structure` and the real-scan regression. Residual: non-break format characters, see IN-01. |
| A-CR-02 (failed init writes `.epb/`) | **Fixed** | `commands/init.py:62-67` validates before `open_for_init`. `_assert_nothing_written` now requires an empty folder (`test_init_defaults.py:194-198`), and `test_refused_init_leaves_a_populated_folder_unchanged` compares the whole tree. Settings are still resolved inside the session only after a pending-journal recovery, which is documented. |
| B-CR-01 (UTF-16LE text read as MP3) | **Fixed** | `mime.py:277-278` short-circuits on text byte-order marks. `_mpeg_frame` (`:177-190`) needs a second header exactly one computed frame length later. Verified with the 650-case matrix and an end-to-end scan test. Residual note in IN-02. |
| C-CR-01 (manual promised name-free INDEX.md) | **Fixed (documentation route)** | The manual's chapter 2 and step 1 of chapter 6, `workspace-contract.md`, `SKILL.md` step 6 and `CONTRACT_PATHS` now say that file names are shown as given. The new `review-before-sharing` class covers `INDEX.md`, `.epb/state.json` and `.epb/sources/`. Residual: the remedy offered is incomplete, see WR-01. |
| D-CR-01 (suite fails under `PYTHONWARNDEFAULTENCODING=1`) | **Fixed** | `pyproject.toml:13-16` scopes the ignore to `openpyxl.worksheet._writer`, and the launcher probe now passes `encoding="utf-8"`. The local run under the variable is green. The 01-22 CI read-back reports the tests step green on both the 3.11 and 3.14 legs. CI as a whole is still red: the 3.11 leg fails at the licence allow-list (setuptools 79.0.1). That is outside these files and is tracked as an open gap. |
| A-WR-09 (shareable INDEX.md shows raw names) | **Resolved by reclassification** | INDEX.md is now `review-before-sharing` (`workspace.py:67-71`, contract table). The later substitution is owned by the ROADMAP de-identification phase ("An input whose file name contains a name appears in `INDEX.md` under its role label"). |

## Narrative Findings (AI reviewer)

## Critical Issues

### CR-01: A file name that is not valid UTF-8 crashes `scan` with INTERNAL_ERROR (exit 4) and blocks the whole case

**File:** `plugin/skills/evidence-pack/scripts/epb/sources/scan.py:150-175` together with `plugin/skills/evidence-pack/scripts/epb/fsio.py:64-67`. This is pre-existing code outside the listed files. Its regression gap is in `tests/index/test_index.py:311-349` (01-18).

**Issue:** On Linux, `os.walk` returns a name whose bytes are not valid UTF-8 as a `str` that holds lone
surrogates (surrogateescape). `rel_key` keeps them. The scan then stages the source record, and
`fsio.json_bytes` calls `text.encode("utf-8")`, which raises. Reproduced in a scratch case:

```
$ python3 -c "open(b'inputs/bad\xffname.txt','wb').write(b'x')"
$ epb scan --json
UnicodeEncodeError: 'utf-8' codec can't encode character '\udcff' ... surrogates not allowed
{"ok": false, "command": "scan", "exit_code": 4, ... "code": "INTERNAL_ERROR", ...
 "hint": "Report this error code to the plugin maintainer. Do not edit the evidence or the .epb folder."}
```

Such names are realistic for incident material on Linux. Running `unzip` on a Windows ZIP with
CP437 or CP1252 names, or copying from an old FAT or SMB share, produces them. One such file stops every
scan of the case for good. The message does not say which file is at fault, and SKILL.md's exit-4
rule tells the agent to stop. The same crash happens when the bad name is a link or a special file,
because the `Ignored` path goes into the run record. The 01-18 hostile-name matrix covers line breaks
and separators but not undecodable bytes, so this class is untested.

**Fix:** catch undecodable names at the walk and turn them into a reported skip, never a crash. Store a
display-safe path:

```python
# scan.py, in walk(), before any other check on a file or directory name
def _undecodable(name: str) -> bool:
    try:
        name.encode("utf-8")
    except UnicodeEncodeError:
        return True
    return False

def _display(rel: str) -> str:
    return rel.encode("utf-8", "surrogateescape").decode("utf-8", "replace")

if _undecodable(name):
    result.ignored.append(Ignored(_display(rel_key(case_root, path)), "bad-name"))
    continue
```

Add `"bad-name": "a file whose name is not valid text; rename it"` to `index._IGNORED_REASONS` and
the run schema's reason enum. Add a POSIX-only regression test that scans `inputs/bad\xffname.txt`
and asserts exit 0, an Open issues line, and no `INTERNAL_ERROR`.

## Warnings

### WR-01: "Rename the file" does not remove the name once it has been scanned. After a rename plus edit, the name stays in INDEX.md for good

**File:** `plugin/skills/evidence-pack/SKILL.md:65,77`, `docs/USER-MANUAL.md:66-78`, `plugin/skills/evidence-pack/scripts/epb/index.py:161-168,343-344` (behaviour from `epb/sources/classify.py:148-221`)

**Issue:** The C-CR-01 fix makes renaming the remedy. SKILL.md step 6 tells the agent to react to a
personal name found in scan `data` by suggesting the user "rename the file themselves before they
share `INDEX.md`". That advice comes *after* the scan has recorded the name. The manual's chapter 2
step 2 tells users to check INDEX.md for names before sharing, but offers no way out if they find
one. The rename is not a clean remedy:

1. **Rename plus edit, or delete plus re-add under a new name.** `classify` cannot match the new
   content to the old record, because neither the hash nor the path overlaps. The old source becomes
   `removed from folder`, and its record keeps its last known paths. INDEX.md renders removed sources
   with that path, in both the Inputs table and Open issues, on every future run. Reproduced:
   ```
   $ mv "inputs/Statement - Jane Roe.txt" inputs/witness-1.txt; echo edited >> inputs/witness-1.txt; epb scan
   $ grep -n Jane INDEX.md
   23:| S001 | inputs/Statement - Jane Roe.txt | Text | 3 B | ... | removed from folder | ...
   32:- S001 (inputs/Statement - Jane Roe.txt) was removed from the folder. Its record is kept.
   ```
   Users who are told to "rename the statement" often also redact or re-save it, which changes the
   content, so this is the likely path.
2. **Pure rename of a file that already has two or more versions.** Only the current version's `paths` is
   rewritten (`classify.py:172`). Older `versions[].paths` in `.epb/sources/S001.json` keep the name
   for good. Reproduced: after v1, v2 and then a rename, `grep -rl Jane .epb` still lists
   `.epb/sources/S001.json`.

No supported command removes a record, and the contract forbids editing `.epb/` by hand. So a user who
follows the guidance after a scan can end up with a name in a review-before-sharing file that they
cannot remove. SKILL.md's "Taking stock" step 1, where the agent asks for files, also never gives the
before-you-copy warning that the manual has. So the agent first hears of a name only after it has
been recorded.

**Fix:** fix the guidance now, and choose a code change.
- SKILL.md step 1: "Before the user copies files in, ask them to check file and folder names and
  rename any that contain a person's name. Once scanned, the old name stays in the plugin's records."
- SKILL.md step 6 and the manual's chapter 2: say plainly that renaming after a scan removes the
  name from INDEX.md only when the content is unchanged. If the content also changed, the old name
  stays in INDEX.md as a removed input, and older versions keep it in `.epb/sources/`. The only clean
  fix is to set up a new case folder.
- Code, recommended: until de-identification ships, render removed sources in INDEX.md by ID only,
  for example `S001 (removed; name not shown)`. Do this in `inputs_snapshot` and `open_issues` when
  `presence == REMOVED`, so a removed file's name is not repeated on every run. Add a test for the
  rename-plus-edit sequence above.

## Info

### IN-01: `_inline` leaves bidi controls, zero-width characters and Markdown link syntax, so names can be disguised in a file users must read and check

**File:** `plugin/skills/evidence-pack/scripts/epb/index.py:79,100-102`
**Issue:** `_SINGLE_LINE` removes only line-breaking characters. Verified with a real scan:
- `inputs/report-\u202Efdp.exe` reaches INDEX.md with U+202E (RIGHT-TO-LEFT OVERRIDE) intact, so it
  displays as `report-exe.pdf`.
- `inputs/[open me](https:  example.invalid).txt` renders as a clickable link in the Inputs table.

INDEX.md is now a document the user is told to *read and check for names* before sharing. Format
characters (Unicode category `Cf`: U+200B to U+200F, U+202A to U+202E, U+2066 to U+2069, U+FEFF) can
reorder or split a name so it slips past that check.
**Fix:** also map `unicodedata.category(ch) == "Cf"` characters to a visible placeholder such as
U+FFFD. Consider wrapping paths in a code span, or escaping `[`, `]`, `<`, `>` and `` ` `` in `_cell`
and `_inline`.

### IN-02: `_TEXT_BOMS` ordering comment is meaningless, and the `FF FE` short-circuit also masks CRC-protected MPEG-1 Layer I

**File:** `plugin/skills/evidence-pack/scripts/epb/mime.py:192-201,277-278`, docstring `:10-16`
**Issue:** `head.startswith(_TEXT_BOMS)` is true if any prefix matches, and every match returns
`None`, so the "longest first so a UTF-32LE mark is not read as UTF-16LE" order has no effect. The
comment suggests an invariant that the code does not need. `FF FE` is also a valid MPEG-1 Layer I
header with CRC (`.mp1` or `.mpa`), and such a file is now classed by its name only. That is
acceptable, but undocumented. The module docstring also breaks a sentence mid-line ("lets the
content win: when / the name suggests").
**Fix:** reword the comment ("order is irrelevant while every mark returns None; keep it longest
first if a later version returns the encoding"). Note the Layer I trade-off, and reflow the docstring.

### IN-03: The `review-before-sharing` promise "a later version shows role labels instead" cannot hold for `state.json` or `sources/`, and the contract and manual disagree about `.epb`

**File:** `plugin/skills/evidence-pack/references/workspace-contract.md:12-15,29-30,66-68`, `plugin/skills/evidence-pack/scripts/epb/workspace.py:8-10,73-82`, `docs/USER-MANUAL.md:79`
**Issue:** Fingerprint keys in `state.json` and `paths` and `versions[].paths` in source records must
hold the real on-disk path, or `classify` cannot match files. So role-label substitution can only
ever apply to INDEX.md. These two entries will hold names permanently. The contract also says the
three files may be kept in version control after a name check, while the manual's step 3 says "Do
not share, send or upload the `.epb` folder". A user who commits the case folder gets contradictory
advice.
**Fix:** limit the "later version shows role labels" sentence to INDEX.md. State that `state.json`
and `sources/` keep real paths permanently. Then either add them to `GITIGNORE_LINES`, or make the
manual and the contract give the same version-control advice.

### IN-04: The text-mode subprocess guard is narrower than its docstring claims

**File:** `tests/repo/test_text_subprocess_encoding.py:21-29`
**Issue:** The docstring says it "catches the whole class statically", but:
- `encoding=None` passes, because the check is key presence and `None` still warns.
- A non-literal truthy value such as `text=flag` or `text=1` passes, and so do `**kwargs`.
- `open()`, `Path.read_text()` and `write_text()` without `encoding` are not checked. They are the
  usual source of `EncodingWarning` and are caught only on code paths the suite happens to execute.
- Any non-subprocess call with `text=True` is a false positive.
**Fix:** reject `encoding` when it is the constant `None`, and treat any non-`False` constant as text
mode. Narrow the docstring, or add a sibling guard for `open` and `read_text`/`write_text` calls in
text mode.

### IN-05: The "full check matches CI" guards check one substring. Local parity still omits the step that turned CI red

**File:** `tests/repo/test_ci_workflow.py:121-171`, `AGENTS.md:28`
**Issue:**
- `test_documented_full_check_matches_ci` checks only that AGENTS.md contains the pytest command and
  that CI sets the variable. CI also runs `tools/check_dependency_age.py` and
  `tools/check_licences.py`. The licence step is what fails on the 3.11 leg (01-22 summary), and the
  documented full check never runs it.
- `_relaxed_encoding_entries` inspects only entries whose category ends in `EncodingWarning`. A later
  `ignore::Warning`, `ignore` or `default::UserWarning`-style blanket entry would still disable the
  guard silently.
**Fix:** either add the two tool checks to the AGENTS.md and CLAUDE.md full check and assert every
CI `run:` step has a documented counterpart, or rename the test to say what it checks. Extend the
relaxed-entry filter to any non-`error` entry whose category is empty, `Warning` or
`EncodingWarning`.

### IN-06: The git-walk test was made to skip, not made hermetic

**File:** `tests/doctor/test_gitcheck.py:142-154`
**Issue:** Commit `f8237df` says the test was made "hermetic". It now skips when any parent of the
pytest temp folder has `.git`, so on such a machine the "no git binary, not in a repository" branch
of `gitcheck.check` is never exercised, and the only sign is a skip line.
**Fix:** make the walk's stop point injectable, for example a `ceiling` argument to
`_inside_git_by_walk`, or honour `GIT_CEILING_DIRECTORIES`. Then pass `tmp_path` so the test always
runs.

---

_Reviewed: 2026-10-18T15:58:17Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
