---
phase: 01-foundations
plan: 18
subsystem: workspace
tags: [index-md, sanitiser, markdown-injection, ws-09, pf-04, gap-closure]

requires:
  - phase: 01-foundations
    provides: "01-11 six-section INDEX.md renderer (epb/index.py); 01-17 CI-equivalent full check"
provides:
  - "_SINGLE_LINE pattern and _inline(value) helper in epb/index.py: C0, DEL, C1, U+2028 and U+2029 each become one space"
  - "Every interpolated INDEX.md value (title, slug, ID prefix, timezone, plugin version, run number, command, summary, workbook file, pack status, source paths, MIME-mismatch values, note target, ignored paths) is single-line"
  - "_cell sanitises with _inline before backslash and pipe escaping"
  - "End-to-end scan regression and a 13-break hostile-values matrix for the six-heading and tick-line invariants"
affects: [phase-04 file-name role substitution (WS-10), phase-06 Imported? tick read-back (INC-01)]

actuals:
  tokens: 3187
  tasks: 2
  commits: 4
plan_head_before: b979d9d3d5eb0cf3ff94761cb5bb3655989b8fd2
plan_head_after: 5de8f5a462eebb85ba4eb44a9ee3dbb38ee6448a

tech-stack:
  added: []
  patterns:
    - "Render-time sanitising: stored paths and records stay raw; only the Markdown view is made single-line"
    - "Sort keys use raw values; only the displayed text goes through _inline"

key-files:
  created: []
  modified:
    - plugin/skills/evidence-pack/scripts/epb/index.py
    - tests/index/test_index.py

key-decisions:
  - "Sanitise at render time rather than tightening run/source schemas, so one oddly named file never aborts a scan with RECORD_INVALID (A-IN-11 stays open as a warning)"
  - "One space per control or separator character, no collapsing, so CR LF becomes two spaces and the mapping is predictable"

patterns-established:
  - "Any new value written into INDEX.md must go through _inline (or _cell for table cells)"

requirements-completed: [WS-09]

coverage:
  - id: D1
    description: "A real scan of line-breaking input names (LF regular file, U+2028 PDF-under-.txt, LF symlink spelling a ticked Imported? line) leaves INDEX.md with exactly six headings and no tick line"
    requirement: WS-09
    verification:
      - kind: integration
        ref: "tests/index/test_index.py#test_scan_of_line_breaking_names_keeps_six_headings"
        status: pass
    human_judgment: false
  - id: D2
    description: "No record field or file name can change INDEX.md line structure in any section: one title line, six headings, exactly one unticked Imported? line in section 2, splitlines agreement, for 13 break characters"
    requirement: WS-09
    verification:
      - kind: unit
        ref: "tests/index/test_index.py#test_hostile_values_cannot_break_index_structure"
        status: pass
      - kind: unit
        ref: "tests/index/test_index.py#test_inline_maps_each_break_to_one_space"
        status: pass
      - kind: unit
        ref: "tests/index/test_index.py#test_table_cells_are_single_line"
        status: pass
    human_judgment: false
  - id: D3
    description: "Ordinary names render exactly as before (existing index, sources and workspace tests unchanged and passing)"
    requirement: WS-09
    verification:
      - kind: unit
        ref: "PYTHONWARNDEFAULTENCODING=1 .venv/bin/python -m pytest -q tests/index tests/sources tests/workspace"
        status: pass
    human_judgment: false

duration: 6min
completed: 2026-10-18
status: complete
---

# Phase 1 Plan 18: INDEX.md Single-Line Sanitiser Summary

**`_inline` maps every C0, DEL, C1, U+2028 and U+2029 character to one space in every value INDEX.md interpolates. A file name can no longer add a `## ` heading or forge a `- [x] Imported:` tick. This closes verification gap 2 (A-CR-01).**

## Performance

- **Duration:** about 6 min
- **Started:** 2026-10-18T15:26Z
- **Completed:** 2026-10-18T15:31:53Z
- **Tasks:** 2 (both completed)
- **Files modified:** 2

## Accomplishments

- Added `_SINGLE_LINE` and `_inline(value) -> str` to `epb/index.py`. These are applied in `open_issues`, `case_header`, `render_import_line`, `run_history`, `render_index` and `_cell`, 20 `_inline(` sites in all.
- Added a real-scan regression (POSIX only). It runs init and two scans over three hostile synthetic names: a removed source, a MIME mismatch and a skipped link. It proves six headings, no tick line, no forbidden characters and `splitlines()` agreement.
- Added a hostile-values matrix covering 13 break characters across every field. It asserts one title line, six headings and exactly one `- [ ] Imported:` line, which sits in section 2.
- Every existing test passes unchanged. Ordinary names render byte-for-byte as before.

## Task Commits

1. **Task 1 (tracer): a real scan of line-breaking names keeps six headings and forges no tick**
   - RED `1d894b2` (test)
   - GREEN `bce57d3` (fix)
2. **Task 2: every interpolated value in every section is single-line, proven by a hostile-values matrix**
   - RED `17f616b` (test)
   - GREEN `5de8f5a` (fix)

**Plan metadata:** the docs commit that follows this SUMMARY.

## TDD Evidence

- **Task 1 RED:** `pytest -q tests/index/test_index.py -k line_breaking_names` failed with 1 failed. The target test failed on the planned heading assertion. Index 5 of the `## ` lines was `'## Injected heading.txt) was removed from the folder. Its record is kept.'` and the list had a seventh item.
  - *Semantic assessment:* the target test ran and failed for the intended reason, an injected heading in section 5. There was no setup, import or collection fault.
- **Task 1 GREEN:** 17 passed in the file. The tracer gate (interactive, end-of-phase, automated-only verify) re-ran the verify and it passed, so expansion went ahead.
- **Task 2 RED:** 13 failed and 2 passed.
  - The LF and CR LF cases failed on the six-heading assertion, from extra `## Injected` lines out of the title, run and case fields.
  - The CR, VT, FF, FS, GS, RS, NEL, U+2028, U+2029, NUL and tab cases failed on the forbidden-character assertion.
  - `test_inline_maps_each_break_to_one_space` and `test_table_cells_are_single_line` already passed at RED, because `_inline` and the `_cell` change landed in Task 1 (see Deviations).
  - *Semantic assessment:* every matrix case failed on a planned structural or character assertion. None failed on a fixture error.
- **Task 2 GREEN:** the three tests gave 15 passed. `tests/index`, `tests/sources` and `tests/workspace` gave 231 passed.
- The RED evidence was judged by reading the pytest output; `gsd_run check tdd-red-evidence` was not run. `workflow.tdd_mode` is not enabled in config, and this plan is `type: execute` with `tdd="true"` tasks.

## Files Created/Modified

- `plugin/skills/evidence-pack/scripts/epb/index.py`: adds `_SINGLE_LINE` and `_inline`, a docstring sentence, and `_inline` applied to every interpolated value. `_cell` now calls `_inline` before escaping.
- `tests/index/test_index.py` adds:
  - `POSIX_ONLY`, `FORBIDDEN` and `TICK_LINE`
  - `test_scan_of_line_breaking_names_keeps_six_headings`
  - `test_hostile_values_cannot_break_index_structure` (13 cases)
  - `test_inline_maps_each_break_to_one_space`
  - `test_table_cells_are_single_line`

## Decisions Made

- Sanitise at render time and leave the schemas permissive, as the plan assumed. One oddly named file still scans, and INDEX.md stays safe.
- `display_id` also goes through `_inline` inside the Open issues label. This is harmless for schema-valid IDs and closes the label completely.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `_cell` sanitising moved forward from Task 2 to Task 1**
- **Found during:** Task 1 GREEN
- **Issue:** The Task 1 test requires that no forbidden character appears anywhere in INDEX.md. The U+2028 file name also shows up in the section 3 Inputs table, and the old `_cell` flattened only CR and LF. With `open_issues` fixed alone, the tracer still failed on a raw U+2028.
- **Fix:** In Task 1, `_cell` now calls `_inline` before backslash and pipe escaping. This is exactly the change Task 2 specifies, made one task earlier.
- **Files modified:** `plugin/skills/evidence-pack/scripts/epb/index.py`
- **Verification:** The tracer passed and the full suite passed.
- **Committed in:** `bce57d3`

---

**Total deviations:** 1 auto-fixed (blocking: an ordering change between tasks)
**Impact on plan:** No scope change. The final code is what the plan specifies. Two of Task 2's three new tests already passed at RED; the 13-case matrix still showed a valid RED.

## Issues Encountered

- The sandbox refused writes into the shared `.git/worktrees/<id>/` directory. The plan commit ledger and the spawn-toplevel sentinel files (executor protocol 0a/0c) could not be written there. The plan base `b979d9d` was recorded in-session instead, and `commits: 4` was measured with `git rev-list --count b979d9d..HEAD`.
- `tests/doctor/test_gitcheck.py::test_no_git_binary_outside_a_repository` skipped, as expected on this machine because `/tmp/.git` exists.

## Threat Flags

None. The plan adds no new endpoint, auth path, file access or schema change. T-01-48 and T-01-49 are mitigated, and the matrix and the scan regression test both. T-01-50 (bidirectional-control characters) stays accepted, deferred to Phase 4.

## User Setup Required

None. No external service configuration is required.

## Next Phase Readiness

- Gap 2 (truth 5) is closed: INDEX.md keeps six headings in order whatever the input names, and Imported? lines come only from `render_import_line`.
- Still open, as the plan intends: A-IN-11 (permissive `input_path` and `paths` schema patterns), the raw paths in scan stdout messages, and the Phase 4 role-label substitution in file names.

## Verification

- `.venv/bin/ruff check . && .venv/bin/ruff format --check . && PYTHONWARNDEFAULTENCODING=1 .venv/bin/python -m pytest -q` gave 1281 passed, 4 skipped (expected skips) and exit 0.
- `grep -c "def _inline" .../epb/index.py` printed 1.
- `grep -c "_inline(" .../epb/index.py` printed 20, against a requirement of at least 8.

---
*Phase: 01-foundations*
*Completed: 2026-10-18*

## Self-Check: PASSED

- FOUND: 1d894b2, bce57d3, 17f616b, 5de8f5a (all on this branch, via git log b979d9d..HEAD)
- FOUND: plugin/skills/evidence-pack/scripts/epb/index.py, tests/index/test_index.py, .planning/phases/01-foundations/01-18-SUMMARY.md
