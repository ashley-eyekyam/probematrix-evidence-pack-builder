---
phase: 01-foundations
plan: 24
subsystem: sources-scan
tags: [scan, utf-8, surrogateescape, bad-name, warnings, run-schema, index]

requires:
  - phase: 01-foundations
    provides: walk_inputs, Ignored/WalkResult, _warn_ignored, run.schema.json scan.ignored, index.open_issues
provides:
  - "epb.sources.scan.name_is_text(name) and display_path(rel) (never raises)"
  - "BAD_NAME = 'bad-name' ignored reason for files, links, pipes and folders (folders pruned, shown with a trailing /)"
  - "BAD_NAME_IGNORED warning code, emitted on every scan"
  - "run.schema.json ignored-reason enum: bad-name, junk, link, special"
  - "INDEX.md Open issues wording for bad-name"
affects: [01-25 manual/skill/contract text, de-identification, any consumer of data.ignored]

actuals:
  tokens: 5400
  tasks: 2
  commits: 4
plan_head_before: e8f42e30a59c59e0b765c2c3d75c7bd97a6b8ee9
plan_head_after: b30759f57b9aa30acdde1790e468ec08d3175985

tech-stack:
  added: []
  patterns:
    - "Check name_is_text before any other check on a walked name; only display_path() values reach Ignored.rel"

key-files:
  created:
    - tests/sources/test_scan_bad_names.py
  modified:
    - plugin/skills/evidence-pack/scripts/epb/sources/scan.py
    - plugin/skills/evidence-pack/scripts/epb/schemas/run.schema.json
    - plugin/skills/evidence-pack/scripts/epb/index.py
    - plugin/skills/evidence-pack/scripts/epb/errors.py

key-decisions:
  - "A name that is not valid text is skipped (bad-name), never fingerprinted under a lossy key; the user renames it and scans again"
  - "The bad-name check runs first, so a link, pipe or junk-looking entry with such a name is reported as bad-name, not link/special/junk"
  - "Human-mode test asserts the BAD_NAME_IGNORED text on stderr, where the CLI prints every warning"

patterns-established:
  - "display_path(): surrogateescape round-trip with 'replace', falling back to a U+D800-U+DFFF -> U+FFFD substitution"

requirements-completed: [WS-02]

coverage:
  - id: D1
    description: "A file whose name is not valid UTF-8 no longer crashes scan; it is skipped as bad-name in data, the run record and INDEX.md while the rest of the case is registered"
    requirement: WS-02
    verification:
      - kind: integration
        ref: "tests/sources/test_scan_bad_names.py#test_scan_skips_a_file_whose_name_is_not_valid_text"
        status: pass
      - kind: unit
        ref: "tests/sources/test_scan_bad_names.py#test_run_schema_accepts_the_bad_name_reason"
        status: pass
    human_judgment: false
  - id: D2
    description: "Links, pipes and folders with such names are skipped as bad-name; folders are pruned with a trailing / and nothing inside is opened"
    requirement: WS-02
    verification:
      - kind: integration
        ref: "tests/sources/test_scan_bad_names.py#test_scan_skips_a_link_whose_name_is_not_valid_text"
        status: pass
      - kind: integration
        ref: "tests/sources/test_scan_bad_names.py#test_scan_skips_a_pipe_whose_name_is_not_valid_text"
        status: pass
      - kind: integration
        ref: "tests/sources/test_scan_bad_names.py#test_scan_skips_a_folder_whose_name_is_not_valid_text"
        status: pass
    human_judgment: false
  - id: D3
    description: "BAD_NAME_IGNORED is a registered warning code and is emitted on every scan, including an unchanged rescan and an inputs/ holding only a bad name; human output names the file"
    requirement: WS-02
    verification:
      - kind: unit
        ref: "tests/sources/test_scan_bad_names.py#test_bad_name_warning_code_is_registered"
        status: pass
      - kind: integration
        ref: "tests/sources/test_scan_bad_names.py#test_bad_name_warning_repeats_on_an_unchanged_rescan"
        status: pass
      - kind: integration
        ref: "tests/sources/test_scan_bad_names.py#test_only_a_bad_name_in_inputs"
        status: pass
      - kind: integration
        ref: "tests/sources/test_scan_bad_names.py#test_human_scan_names_the_skipped_file"
        status: pass
    human_judgment: false
  - id: D4
    description: "display_path never raises and turns undecodable bytes and Windows lone surrogates into U+FFFD; renaming the file lets the next scan register it and clears the Open issues line"
    requirement: WS-02
    verification:
      - kind: unit
        ref: "tests/sources/test_scan_bad_names.py#test_name_is_text"
        status: pass
      - kind: unit
        ref: "tests/sources/test_scan_bad_names.py#test_display_path_replaces_undecodable_bytes"
        status: pass
      - kind: unit
        ref: "tests/sources/test_scan_bad_names.py#test_display_path_survives_a_lone_surrogate"
        status: pass
      - kind: integration
        ref: "tests/sources/test_scan_bad_names.py#test_renamed_bad_file_is_inventoried"
        status: pass
    human_judgment: false

duration: 7min
completed: 2026-10-18
status: complete
---

# Phase 1 Plan 24: Undecodable file names are skipped as bad-name Summary

**`epb scan` now skips any file, link, pipe or folder whose name is not valid UTF-8 as `bad-name`, under a U+FFFD display path with a rename hint and a `BAD_NAME_IGNORED` warning on every scan, instead of exiting 4 with INTERNAL_ERROR (gap 2, review CR-01, WS-02).**

## Performance

- **Duration:** about 7 min of execution
- **Started:** 2026-10-18T16:47:42Z
- **Completed:** 2026-10-18T16:54:06Z
- **Tasks:** 2 (both TDD; 4 commits)
- **Files modified:** 5 (1 created, 4 modified)

## Accomplishments

- `name_is_text` and `display_path` in `epb/sources/scan.py`. `display_path` never raises: surrogateescape bytes become U+FFFD, and a stray Windows lone surrogate falls back to a direct U+D800 to U+DFFF substitution.
- `walk_inputs` checks `name_is_text` before any other check, both for files and for folders. A bad-named file, link or pipe becomes `Ignored(display_path(rel), BAD_NAME)`. A bad-named folder becomes `Ignored(display_path(...) + "/", BAD_NAME)` and is pruned, so nothing inside it is opened or registered. The read-error handler also routes its path through `display_path`. As a result, no lone surrogate can reach `fsio.json_bytes`, INDEX.md, an envelope or a message.
- `bad-name` is now in the run-schema ignored-reason enum (alphabetical). INDEX.md "5. Open issues" says: "named with characters that are not valid text; rename it, then scan again". The path still goes through `_inline`.
- The `BAD_NAME_IGNORED` warning has separate file and folder wording plus a plain rename hint. It is in `errors.WARNING_CODES` and in the errors docstring.
- The verifier's reproduction (`init`, `open(b'inputs/bad\xffname.txt','wb')`, `epb scan --json`) in a scratch case now exits 0 with `ok: true`, `data.ignored == [{"path": "inputs/bad�name.txt", "reason": "bad-name"}]` and one BAD_NAME_IGNORED warning.

## TDD record

**Task 1 RED** (`84e2b4e`): `tests/sources/test_scan_bad_names.py` had the tracer and the schema test, and both failed.
- `test_scan_skips_a_file_whose_name_is_not_valid_text`: `assert 4 == 0`. The envelope had `exit_code: 4`, `errors[0].code == "INTERNAL_ERROR"`, "An internal error occurred (UnicodeEncodeError)". This was confirmed by a manual run in a scratch case.
- `test_run_schema_accepts_the_bad_name_reason`: `schema.validate` returned a `/scan` issue because `bad-name` was not in the enum.
- Semantic assessment: both target tests ran and failed on the planned assertions, for the intended reasons (the CR-01 crash and the missing enum value). There were no collection, import or fixture faults. `workflow.tdd_mode` is off, so the `tdd-red-evidence` classifier gate does not apply.

**Task 1 GREEN** (`dba0165`): both tests pass. The Task 1 verify set had 114 passed. The full check had 1980 passed and 3 opt-in skips.

**Tracer feedback gate:** the run was interactive in `end-of-phase` mode, and the tracer's verify was automated only. The verify was re-run and passed, so Task 2 went ahead.

**Task 2 RED** (`8139ff4`): 7 tests failed and 6 passed.
- Failing: `warning_code_is_registered` (code absent), `link` and `pipe` (0 BAD_NAME_IGNORED warnings), `folder` (exit 4: os.walk descended into the folder and `inner.txt` carried a surrogate into JSON), `unchanged_rescan` and `only_a_bad_name` (no warning), and `human` (no warning text).
- Already passing because of Task 1: `name_is_text`, both `display_path` tests (the lone-surrogate fallback came in with Task 1), and `renamed_bad_file_is_inventoried`.

**Task 2 GREEN** (`b30759f`): all 13 pass with no skips on Linux. The full check had 1991 passed and 3 opt-in skips (network/host). No REFACTOR commit was needed.

## Task Commits

1. **Task 1: Tracer, a bad-named file is skipped as bad-name** - `84e2b4e` (test), `dba0165` (feat)
2. **Task 2: Links, pipes, folders, BAD_NAME_IGNORED, display_path** - `8139ff4` (test), `b30759f` (feat)

## Files Created/Modified

- `tests/sources/test_scan_bad_names.py`: 13 POSIX regression and unit tests. Entries are created from raw name bytes, the test skips with the OS error named if the file system refuses such a name, and `inputs/` is compared by raw bytes before and after every scan.
- `plugin/skills/evidence-pack/scripts/epb/sources/scan.py`: `BAD_NAME`, `name_is_text`, `display_path`, the file and folder skips, `display_path` in the read-error handler, and the BAD_NAME_IGNORED warnings.
- `plugin/skills/evidence-pack/scripts/epb/schemas/run.schema.json`: `bad-name` added to the `scan.ignored[].reason` enum.
- `plugin/skills/evidence-pack/scripts/epb/index.py`: the `_IGNORED_REASONS["bad-name"]` wording.
- `plugin/skills/evidence-pack/scripts/epb/errors.py`: `BAD_NAME_IGNORED` in the docstring and in `WARNING_CODES`.

## Decisions Made

- I followed the plan's flagged assumptions as written: skip rather than fingerprint, the "No files found" message is unchanged when the folder holds only bad names, and Open issues refreshes only on a scan that changes something.
- In the folder loop, the `Ignored(...)` is bound to a local `skipped` before it is appended. Written on one line, ruff format would wrap it, and the plan's fixed-string grep needs it on one line. Behaviour is the same.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug in plan's test spec] The human-mode test checks stderr, not stdout, for the warning text**
- **Found during:** Task 2 RED
- **Issue:** The plan's behaviour line said plain `scan` stdout should contain "inputs/bad�name.txt" and "not valid text". But `cli._render_human` prints the result message on stdout and every warning ("Warning: ..." / "What to do: ...") on stderr, and the plan's GREEN steps do not change the scan message. Asserting on stdout would have failed against a correct implementation.
- **Fix:** `test_human_scan_names_the_skipped_file` checks that stdout holds the run summary ("Run 002"). It checks that stderr holds `Warning: inputs/bad�name.txt was skipped`, "not valid text" and the rename hint. It also checks exit 0, no INTERNAL_ERROR, and `inputs/` unchanged. The behaviour under test is the same: the human output names the skipped file.
- **Files modified:** tests/sources/test_scan_bad_names.py
- **Commit:** 8139ff4

**2. [Rule 2 - Stronger check] The pipe test also asserts one BAD_NAME_IGNORED warning**
- **Found during:** Task 2 RED
- **Issue:** The plan's pipe behaviour asserted only `data.ignored`. The must-have truth says every bad-named entry warns once.
- **Fix:** Added `codes.count("BAD_NAME_IGNORED") == 1` to the pipe test.
- **Commit:** 8139ff4

---

**Total deviations:** 2 auto-fixed (1 test-spec bug, 1 stronger assertion). **Impact:** none on production behaviour, and no scope creep.

## Issues Encountered

- The worktree had no `.venv`, so I symlinked it to the main checkout's `.venv` as CLAUDE.md says. The symlink is git-ignored.

## Known Stubs

None.

## User Setup Required

None.

## Next Phase Readiness

- Plan 01-25 can now document `bad-name`, `BAD_NAME_IGNORED` and the rename remedy in the manual, the skill and the workspace contract. The code-side names and wording are final.
- Acceptance results: 13 passed and no SKIPPED line. `"bad-name"` appears once in the schema. The index wording appears once. `_inline(` appears 20 times. Both helpers are defined once each. There is no root `schemas/`. The three `display_path` sites each match once. `BAD_NAME_IGNORED` appears twice in errors.py. `links_and_fifos` still passes. The full ruff + format + pytest check exits 0.

## Self-Check: PASSED

- FOUND: tests/sources/test_scan_bad_names.py
- FOUND commits on this branch: 84e2b4e, dba0165, 8139ff4, b30759f
