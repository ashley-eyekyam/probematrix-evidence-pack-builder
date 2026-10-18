---
phase: 01-foundations
plan: 20
subsystem: sources
tags: [mime, magic-bytes, byte-order-mark, utf-16, mpeg, gap-closure]

requires:
  - phase: 01-foundations
    provides: "epb/mime.py detect/sniff with MAGIC_RULES (01-13); CI-equivalent full check (01-17)"
provides:
  - "sniff gives no verdict after any text byte-order mark (_TEXT_BOMS), checked before every magic rule"
  - "_mpeg_frame_length: full MPEG-1/2/2.5 Layer I-III frame-length computation with reserved-field rejection"
  - "_mpeg_frame accepts MPEG audio only when a second valid header sits exactly at the computed frame length"
affects: [phase-02-conversion, scan, INDEX.md]

actuals:
  tokens: 3958
  tasks: 2
  commits: 2
plan_head_before: b979d9d3d5eb0cf3ff94761cb5bb3655989b8fd2
plan_head_after: 35cf728486f78a0d9074ad05d40e6ec5954892d7

tech-stack:
  added: []
  patterns:
    - "Text byte-order marks short-circuit content sniffing so the file name decides"
    - "A weak magic signature (MPEG frame sync) must be confirmed by a structurally computed second occurrence"

key-files:
  created: []
  modified:
    - plugin/skills/evidence-pack/scripts/epb/mime.py
    - tests/core/test_mime.py

key-decisions:
  - "A text byte-order mark means 'let the name decide' (sniff returns None), never text/plain from content, so a .csv/.md/.json with a mark is not a false mismatch"
  - "Layer I and Layer II keep full frame-length tables; the rule stays general rather than MP3-only"
  - "RED evidence captured by running the new tests before the fix, but each task committed test and fix together, because CLAUDE.md requires the full check to pass before every commit"

patterns-established:
  - "Byte-order-mark matrix: 5 marks x 65 first characters x 2 names, built from Python codecs in the test, never checked-in files"

requirements-completed: [WS-02]

coverage:
  - id: D1
    description: "scan records UTF-16LE (Notepad 'Unicode', Excel 'Unicode Text', PowerShell 5.1 Out-File) and UTF-8-mark text by name, with no MIME_MISMATCH, and INDEX.md shows Text/CSV"
    requirement: WS-02
    verification:
      - kind: integration
        ref: "tests/core/test_mime.py#test_scan_records_utf16_text_by_its_name"
        status: pass
      - kind: unit
        ref: "tests/core/test_mime.py#test_sniff_gives_no_verdict_after_a_text_bom"
        status: pass
      - kind: unit
        ref: "tests/core/test_mime.py#test_bom_matrix"
        status: pass
      - kind: unit
        ref: "tests/core/test_mime.py#test_windows_style_exports"
        status: pass
      - kind: unit
        ref: "tests/core/test_mime.py#test_bom_only_and_bom_then_signature"
        status: pass
    human_judgment: false
  - id: D2
    description: "MPEG audio is detected only when a second valid header with the same version, layer and sample rate starts exactly at the computed frame length"
    requirement: WS-02
    verification:
      - kind: unit
        ref: "tests/core/test_mime.py#test_mpeg_frame_needs_a_second_header"
        status: pass
      - kind: unit
        ref: "tests/core/test_mime.py#test_mpeg_two_frame_streams"
        status: pass
      - kind: unit
        ref: "tests/core/test_mime.py#test_mpeg_second_header_must_sit_exactly_at_the_frame_length"
        status: pass
      - kind: unit
        ref: "tests/core/test_mime.py#test_utf16le_text_is_not_mpeg_even_without_the_mark_check"
        status: pass
      - kind: unit
        ref: "tests/core/test_mime.py#test_sniff_identifies_each_magic"
        status: pass
      - kind: unit
        ref: "tests/core/test_mime.py#test_sniff_reads_at_most_4096_bytes"
        status: pass
    human_judgment: false

duration: 5min
completed: 2026-10-18
status: complete
---

# Phase 1 Plan 20: Text byte-order marks and two-frame MPEG rule Summary

**Windows UTF-16 text exports are no longer recorded as MP3. `sniff` now gives no verdict after any text byte-order mark, and an MPEG verdict needs a second valid frame header exactly at the frame length computed from the first (closes verification gap 4, review B-CR-01).**

## Performance

- **Duration:** about 5 min
- **Started:** 2026-10-18T15:28:43Z
- **Completed:** 2026-10-18T15:33:22Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- `_TEXT_BOMS` holds the UTF-32LE, UTF-32BE, UTF-8, UTF-16LE and UTF-16BE marks, longest first. `sniff` checks them before the `MAGIC_RULES` loop and returns `None`, so the extension decides, just as it does for text without a mark. `detect`, `_agree` and the tables are unchanged.
- `_MPEG_BITRATES_KBPS`, `_MPEG_SAMPLE_RATES` and `_mpeg_frame_length(header)` hold the ISO/IEC 11172-3 / 13818-3 tables and formulas. The function returns `None` for a missing sync, reserved version, layer, sample rate or emphasis, a free-format bitrate (index 0) or bitrate index 15. The worked values come out as expected: `FF FB 90 64` gives 417, `FF FB 92 64` gives 418, `FF F3 80 C4` gives 208, and `FF FE 41 00` gives 136. The largest legal frame is 2,881 bytes, so frame plus next header fits inside `HEAD_BYTES`.
- `_mpeg_frame` returns `audio/mpeg` only when the head holds at least frame length + 4 bytes and a valid second header sits exactly at that offset with the same version, layer and sample-rate index. It keeps its place after the `ID3` prefix rule.
- End to end, `epb scan` now records UTF-16LE `log.txt` as `text/plain` and UTF-16LE `export.csv` plus UTF-8-mark `readings.csv` as `text/csv`. `mime_mismatch` is null for all three, there is no `MIME_MISMATCH` warning, and INDEX.md shows Text / CSV.

## Task Commits

1. **Task 1 (tracer): a scan of Windows UTF-16 text exports records them as text** - `d489e1f` (fix)
2. **Task 2: the MPEG rule needs a second frame header, plus the byte-order-mark matrix** - `35cf728` (fix)

## TDD Evidence

- **Task 1 RED:** I ran `pytest tests/core/test_mime.py -k "utf16_text_by_its_name or no_verdict_after_a_text_bom"` before the fix. Result: 3 failed, 3 passed. The failures were `test_sniff_gives_no_verdict_after_a_text_bom[utf-16-le]` and `[utf-32-le]` (sniff returned `audio/mpeg`) and `test_scan_records_utf16_text_by_its_name` (`assert 'audio/mpeg' == 'text/plain'` for `inputs/log.txt`). Semantic assessment: every failure was on the planned assertion for the planned reason. There were no load, fixture or collection errors. The UTF-8, UTF-16BE and UTF-32BE cases already passed, as expected, because only `FF FE` collided with the frame rule. **GREEN:** 6 passed.
- **Task 2 RED:** I ran the full `tests/core/test_mime.py` with the new tests and the two-frame `SAMPLES["mpeg-frame"]`. Result: 10 failed, 768 passed. The failures were `test_mpeg_frame_needs_a_second_header`, all 8 cases of `test_mpeg_second_header_must_sit_exactly_at_the_frame_length`, and `test_utf16le_text_is_not_mpeg_even_without_the_mark_check`, each because the single-header rule returned `audio/mpeg`. Semantic assessment: each one failed on its target assertion. **GREEN:** 778 passed in the file. `-k mpeg` ran 14 tests, `-k bom_matrix` ran 650, and `-k "reads_at_most_4096 or d13_minimum or identifies_each_magic"` ran 29, all passing.
- The RED and GREEN for each task share one commit. See Deviations.

## Files Created/Modified

- `plugin/skills/evidence-pack/scripts/epb/mime.py`: adds `_TEXT_BOMS` and the mark check in `sniff`, the MPEG tables, and `_mpeg_frame_length`. `_mpeg_frame` is rewritten to confirm a second header, and the module, `sniff` and `_mpeg_frame` docstrings are updated.
- `tests/core/test_mime.py`: adds the `TEXT_BOMS` and `_bom_text` helpers, plus `_mpeg_frames` and the worked-value headers. `SAMPLES["mpeg-frame"]` is now a two-frame stream. The nine new tests are the ones named in the plan.

## Decisions Made

- A mark makes the name decide. A UTF-16 file misnamed `report.pdf` is therefore recorded as `application/pdf` with no mismatch, the same as ASCII text misnamed `.pdf`. This is the plan's flagged assumption, kept as written.
- Sources already recorded as `audio/mpeg` by an earlier scan are not re-detected until their content changes (review B-WR-09 is separate). Only development and UAT scratch folders can hold such records.

## Deviations from Plan

### Auto-fixed Issues

**1. [CLAUDE.md precedence] RED and GREEN committed together per task**
- **Found during:** Task 1
- **Issue:** The TDD reference asks for a separate failing `test(...)` commit. The project CLAUDE.md requires `ruff check`, `ruff format --check` and the full pytest run to pass before every commit, and a RED commit cannot pass.
- **Fix:** For each task I ran the new tests against the unfixed code and recorded the failure (TDD Evidence above), then committed the tests and the fix together once the full check passed. Plan type is `execute`, not `tdd`, and `workflow.tdd_mode` is not set, so no gate commit was mandatory.
- **Committed in:** d489e1f, 35cf728

**2. [Rule 2 - Test strength] The no-mark-check MPEG test uses longer UTF-16LE text than the literal "Alarm log"**
- **Found during:** Task 2
- **Issue:** "Alarm log" in UTF-16LE is 20 bytes, so `_mpeg_frame` would return `None` just for running out of bytes. That would never exercise the second-header check at offset 136.
- **Fix:** The text is "Alarm log" followed by 20 synthetic log lines. The test asserts the head is longer than 136 + 4 bytes before checking `_mpeg_frame` gives `None`.
- **Committed in:** 35cf728

**3. [Rule 2 - Boundary coverage] Two extra boundary cases**
- **Found during:** Task 2
- **Issue:** The plan's truths require the second header to match the first's version and sample rate as well as its layer. The behaviour list only tested a different layer.
- **Fix:** Added the `second-header-other-sample-rate` (`FF FB 94 64`) and `second-header-other-version` (`FF F3 90 64`) cases.
- **Committed in:** 35cf728

**Process note:** The worktree sandbox refused writes into the git directory, so I could not persist the commit ledger file (`gsd-plan-head-before-01-20`). `plan_head_before` is the verified spawn base `b979d9d`, and `commits: 2` was measured with `git rev-list --count b979d9d..HEAD` before this SUMMARY commit.

---

**Total deviations:** 3 (1 CLAUDE.md-driven commit-shape change, 2 test-strength additions)
**Impact on plan:** None on scope. The tests are stricter than planned, and production code matches the plan exactly.

## Issues Encountered

None.

## Verification

- `.venv/bin/ruff check . && .venv/bin/ruff format --check . && PYTHONWARNDEFAULTENCODING=1 .venv/bin/python -m pytest -q`: all checks passed, 98 files formatted, 1949 passed, 4 skipped (the network and host-CLI opt-in tests and the expected `/tmp/.git` skip).
- `PYTHONWARNDEFAULTENCODING=1 .venv/bin/python -m pytest -q tests/core/test_mime.py tests/sources`: 832 passed.
- `grep -c "_TEXT_BOMS" .../epb/mime.py` printed 2. `grep -c "def _mpeg_frame_length" .../epb/mime.py` printed 1.

## User Setup Required

None. No external service configuration is required.

## Next Phase Readiness

- Truth 8 (gap 4) holds. Phase 2 converters will get text routing for Windows UTF-16 and UTF-8-mark exports, and MPEG routing only for genuine streams (an ID3 tag or two consistent frames).

---
*Phase: 01-foundations*
*Completed: 2026-10-18*

## Self-Check: PASSED

- FOUND: d489e1f, 35cf728 (ancestors of HEAD)
- FOUND: plugin/skills/evidence-pack/scripts/epb/mime.py, tests/core/test_mime.py, .planning/phases/01-foundations/01-20-SUMMARY.md
