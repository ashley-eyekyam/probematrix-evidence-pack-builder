---
phase: 01-foundations
plan: 14
subsystem: sources-scan
tags: [python, scan, classification, sidecars, crash-injection, ws-03, ws-04, tst-07]

# Dependency graph
requires:
  - phase: 01-foundations (01-13)
    provides: classify (content-centred), run_scan, walk_inputs, FileFact, rel_key, source.schema.json, run scan lists (sidecars, orphan_sidecars)
  - phase: 01-foundations (01-12)
    provides: faults checkpoints in every transaction, tests/epbtest/crash.py (list_checkpoints, assert_workspace_consistent), the init crash tests, run_upgrade
  - phase: 01-foundations (01-11)
    provides: index.display_id (S004 / S004v2), the open-issues provider
provides:
  - epb/sources/sidecars.py (SIDECAR_SUFFIXES, sidecar_target, pair_sidecars, PairingResult, orphan_target)
  - scan pairs sidecar notes after classify and before staging, in the same transaction as the records
  - scan's human report has one plain-language line per change, led by the displayed ID (S001v2)
  - INPUT_REMOVED in the planned wording, SIDECAR_ORPHAN, and sidecars / orphan_sidecars in the run record and envelope
  - walk_inputs refuses two spellings of one name (NFD and NFC) with BAD_ARGUMENT
  - classify lets only one source claim a given current SHA-256
  - the WS-03 change corpus, sidecar pairing tests, and test_scan_resumes_after_crash_at_every_checkpoint
affects: [01-15 skill and workspace contract (content wins, reverted content, sidecar naming, two-spellings error), 01-16 manual (scan report lines, INPUT_REMOVED and SIDECAR_ORPHAN wording), Phase 5 (sidecar custody content is parsed there; PF-01)]

# Actuals (#2632)
actuals:
  tokens: 12569
  tasks: 3
  commits: 6
plan_head_before: 53f8db582eef0e72a0ed3ba17cb210e8a36c7e6f
plan_head_after: c7ffb0a172700b5e2f9b7953f3bf8f957c59e3e4

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Pairing is a pure function over the records classify returned plus the path-to-source map; scan recomputes plan.records against the session's originals afterwards, so any record whose pairing changed is staged in the same transaction"
    - "Crash coverage for scan: a prepared case is copied per checkpoint (shutil.copytree), crashed, resumed and compared with an uninterrupted reference copy"

key-files:
  created:
    - plugin/skills/evidence-pack/scripts/epb/sources/sidecars.py
    - tests/sources/test_scan_classify.py
    - tests/sources/test_sidecars.py
  modified:
    - plugin/skills/evidence-pack/scripts/epb/sources/scan.py
    - plugin/skills/evidence-pack/scripts/epb/sources/classify.py
    - plugin/skills/evidence-pack/scripts/epb/index.py
    - tests/store/test_crash_resume.py
    - tests/store/test_upgrade.py
    - tests/index/test_index.py

key-decisions:
  - "Two files whose names differ only in Unicode normalisation (one NFC key) stop the scan with BAD_ARGUMENT (exit 2) and change nothing, rather than silently keeping one of them; the message asks the user to rename one"
  - "Pairing reflects the folder now: only present sources pair; a removed sidecar keeps source_kind sidecar but has sidecar_of null and is not reported as an orphan; a removed target lists no sidecars"
  - "A source_kind other than null or sidecar (set by a later phase) is never overwritten by pairing; a sidecar renamed to an ordinary name goes back to null"
  - "When one note's content sits at several sidecar paths, every target lists it and sidecar_of is the target of its first path in sorted order; run and envelope sidecars hold one {src_id, target} entry per pair, so run.schema.json needed no widening"
  - "SIDECAR_ORPHAN is warned on every scan while the orphan exists (like LINK_IGNORED); INPUT_REMOVED only on the scan that marks the source removed"
  - "When a removed source's path still exists but holds other content (content wins), the change line and INPUT_REMOVED say the earlier content is gone rather than that the file is gone"

patterns-established:
  - "Scan change lines: '<displayed ID> <path>: <plain-language change>', in a fixed category order, with content-wins moves and duplicate splits explained on the line that reports them"

requirements-completed: [WS-03, WS-04, TST-07]

coverage:
  - id: D1
    description: "An edited input becomes S001v2 in the envelope, run record, source record (current_version 2, two versions, pending), INDEX.md and the human report; counters.source stays 1"
    requirement: WS-03
    verification:
      - kind: integration
        ref: "tests/sources/test_scan_classify.py#test_edited_input_becomes_a_new_version_everywhere"
        status: pass
      - kind: integration
        ref: "tests/sources/test_scan_classify.py#test_new_version_envelope"
        status: pass
    human_judgment: false
  - id: D2
    description: "WS-03 corpus: rename, copy of an existing source, removal (record kept, INPUT_REMOVED, INDEX open issue), all removed then restored, swap, content wins (moved + old source removed), duplicate split ('copies now differ'), case-only rename, NFD/NFC one key, reverted content as a new version, several changes in a fixed order, removed IDs never reused; no source record is ever deleted"
    requirement: WS-03
    verification:
      - kind: integration
        ref: "tests/sources/test_scan_classify.py"
        status: pass
    human_judgment: false
  - id: D3
    description: "Two spellings of one name are refused with BAD_ARGUMENT and change nothing; classify never gives one path to two sources"
    requirement: WS-03
    verification:
      - kind: integration
        ref: "tests/sources/test_scan_classify.py#test_two_spellings_of_one_name_are_refused"
        status: pass
      - kind: unit
        ref: "tests/sources/test_scan_classify.py#test_classify_never_gives_one_path_to_two_sources"
        status: pass
    human_judgment: false
  - id: D4
    description: "Sidecar pairing: .note.md and .note.yaml paired both ways and hashed; bare .note.md is ordinary; orphans get sidecar_of null, SIDECAR_ORPHAN, orphan_sidecars and an INDEX line; pairing follows renames, deletion and return of the target, a target added later; an edited sidecar is a new version; a removed sidecar is not an orphan; other source kinds are never overwritten"
    requirement: WS-04
    verification:
      - kind: integration
        ref: "tests/sources/test_sidecars.py"
        status: pass
    human_judgment: false
  - id: D5
    description: "A real crash at each of the 15 recorded scan checkpoints (two inputs and one sidecar), followed by a normal scan, leaves a consistent workspace whose source IDs and pairings equal an uninterrupted run"
    requirement: TST-07
    verification:
      - kind: integration
        ref: "tests/store/test_crash_resume.py#test_scan_resumes_after_crash_at_every_checkpoint"
        status: pass
    human_judgment: false
  - id: D6
    description: "The D-09 upgrade of a workspace with source records backs every record up byte for byte, restamps and validates them, and keeps sidecar pairing (01-12 follow-up)"
    verification:
      - kind: integration
        ref: "tests/store/test_upgrade.py#test_upgrade_backs_up_and_rewrites_source_records"
        status: pass
    human_judgment: false
  - id: D7
    description: "Scan change lines, INPUT_REMOVED, SIDECAR_ORPHAN and the two-spellings error read as plain language for a non-technical investigator"
    verification: []
    human_judgment: true
    rationale: "Wording quality is a judgement no test asserts; the 01-15 UAT and the 01-16 manual quote this text"

# Metrics
duration: 11min
completed: 2026-10-18
status: complete
---

# Phase 1 Plan 14: Change detection, sidecar pairing and scan crash coverage Summary

**`epb scan` now explains every change in plain words, led by the ID the user sees (`S001v2 inputs/report.pdf: new version (the file changed since run 002)`). The WS-03 corpus is proven: renames, copies, removals and restores, swaps, the content-wins move, duplicate splits, case-only renames, NFD names, reverted content and mixed changes. `<file>.note.md` and `<file>.note.yaml` notes are paired with their inputs in the same transaction as the records, with orphans reported. A real crash at all 15 scan checkpoints resumes to the same IDs and pairings as an uninterrupted run.**

## Performance

- **Duration:** 11 min
- **Started:** 2026-10-18T10:53:54Z
- **Completed:** 2026-10-18T11:04:54Z
- **Tasks:** 3
- **Files modified:** 9 (3 created, 6 modified)

## Accomplishments

- **Scan report (`sources/scan.py`).** The human message has one line per change, in a fixed order: new versions, new inputs, renames, copies, content-wins moves, restores, removals, then newly paired notes. Each line starts with `display_id` (`S004` or `S004v2`). `INPUT_REMOVED` uses the planned wording: "<path> is no longer in inputs/. Its record is kept, and anything already built from it stays."
- **Change corpus (`tests/sources/test_scan_classify.py`).** There are 21 tests, at least one per behaviour line. Every scan in the corpus also asserts that no source record was deleted and that every record and run validates.
  - The content-centred `classify` from 01-13 already handled all the planned cases.
  - Two gaps were found and fixed: names with two spellings, and a duplicate claim on one SHA-256.
- **Sidecars (`sources/sidecars.py`).** `sidecar_target` matches exact suffixes and needs a non-empty target name. `pair_sidecars` recomputes `source_kind`, `sidecar_of` and `sidecars` from the paths present now and returns the pairs, the orphans and the changed IDs.
  - `scan` calls it after `classify` and before staging.
  - It then recomputes which records changed, so pairing-only changes are staged in the same transaction.
- **Crash coverage.** `test_scan_resumes_after_crash_at_every_checkpoint` tries every recorded scan checkpoint, and the number tried equals the number recorded. The checkpoints are `stage:0-5`, `pre-manifest`, `manifest`, `apply:0-5` and `cleanup`. After each crash the case must be consistent and must match the reference run's IDs, paths, versions and pairings.

## Task Commits

1. **Task 1 (tracer): an edited input becomes S001v2 everywhere.** `90778f6` (feat).
   - Tracer gate: the run is interactive and `end-of-phase`, and the verify is automated only. I re-ran it (2 passed) and expansion continued.
2. **Task 2: the WS-03 change corpus.** RED `3ac9d95` (test), GREEN `ad290a5` (feat).
3. **Task 3: sidecar pairing and scan crash coverage.** RED `16727a4` (test), GREEN `202c61f` (feat).

Extra: `c7ffb0a` (test) adds the 01-12 follow-up, an upgrade of a workspace that has source records.

No REFACTOR commits were needed.

## TDD Gate Compliance

- **Task 2 RED (`3ac9d95`):**
  - JUnit XML was classified by `gsd-tools check tdd-red-evidence` as `RED_EVIDENCE_OK` (`target_test_failed`): 19 tests, 2 failing.
  - Target: `test_two_spellings_of_one_name_are_refused`, which failed on `assert 0 == 2` because scan exited 0 and silently kept one file.
  - The other failure, `test_classify_never_gives_one_path_to_two_sources`, was also planned: `inputs/a.txt` was given to S001 and S002.
  - The 17 that passed at RED cover behaviour that 01-13's `classify` and Task 1's report lines already had. The corpus pins them as regression tests.
- **Task 3 RED (`16727a4`):**
  - `RED_EVIDENCE_OK` (`target_test_failed`): 26 tests, 21 failing.
  - Target: `test_note_md_is_paired_with_its_input`, which failed on `(None, None, []) == (None, None, ['S002'])`.
  - Semantic check:
    - 10 failures were the interface stub's `NotImplementedError`.
    - The others were missing pairing, missing envelope keys, and the crash test's pairing precondition.
    - There was no import or collection fault.
    - The 5 tests that passed are the existing init crash tests.
- **GREEN:**
  - `pytest -q tests/sources tests/store` passes.
  - The full suite gives 1015 passed and 1 skipped (the opt-in network test), against 947 passed before this plan. The failing file set is empty.
  - `ruff check` and `ruff format --check` are clean.

## Files Created/Modified

- `plugin/skills/evidence-pack/scripts/epb/sources/sidecars.py`: sidecar naming, pairing and `orphan_target`.
- `plugin/skills/evidence-pack/scripts/epb/sources/scan.py`: the change lines, the `INPUT_REMOVED` wording, the two-spellings check, the pairing hook, `SIDECAR_ORPHAN`, and `sidecars`/`orphan_sidecars` in the run and envelope.
- `plugin/skills/evidence-pack/scripts/epb/sources/classify.py`: content is claimed once. The docstring is updated.
- `plugin/skills/evidence-pack/scripts/epb/index.py`: an orphan note's Open issues line names the missing file, and a removed note is no longer listed as an orphan.
- `tests/sources/test_scan_classify.py`, `tests/sources/test_sidecars.py`: new.
- `tests/store/test_crash_resume.py`: the scan crash test.
- `tests/store/test_upgrade.py`: the source-record upgrade test.
- `tests/index/test_index.py`: the orphan line's new wording.

## Decisions Made

See `key-decisions` in the frontmatter. In short:

- Two spellings of one name are refused, not silently merged.
- Pairing reflects the folder now.
- Kinds set by later phases are never overwritten.
- A note that sits next to several targets is listed by all of them.
- `SIDECAR_ORPHAN` repeats while the orphan exists.
- A content-wins removal says that the earlier content is gone, not that the file is gone.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical] Two spellings of one name are refused (the 01-13 carry-over)**
- **Found during:** Task 2 (the NFD behaviour line)
- **Issue:** On Linux, an NFD and an NFC spelling of the same name map to one NFC key. Only one file was registered and the other silently disappeared from custody.
- **Fix:** `walk_inputs` raises `BAD_ARGUMENT` (exit 2), naming the key and asking the user to rename one file. Nothing is written.
- **Files modified:** `epb/sources/scan.py`
- **Verification:** `test_two_spellings_of_one_name_are_refused` (skipped on a file system that stores both spellings as one name) and `test_nfd_and_nfc_spellings_are_one_path_key`.
- **Committed in:** `ad290a5`

**2. [Rule 1 - Bug] One SHA-256 could be claimed by two sources**
- **Found during:** Task 2
- **Issue:** If two records ever shared a current SHA-256 (only possible in a damaged or hand-edited folder), step 2 of `classify` gave both of them the same paths.
- **Fix:** Only the lowest ID claims a SHA-256. The docstring is updated.
- **Files modified:** `epb/sources/classify.py`
- **Committed in:** `ad290a5`

**3. [Rule 1 - Bug] INDEX listed a removed note as an orphan, and the orphan line did not name the missing file**
- **Found during:** Task 3
- **Issue:** `index.open_issues` called any sidecar with no `sidecar_of` an orphan, including one removed from the folder. Its text also did not say which file was missing.
- **Fix:** Removed notes are excluded. The line now reads "<id> (<note>) is a note for <target>, but that file is not in inputs/.", matching `SIDECAR_ORPHAN`.
- **Files modified:** `epb/index.py`, `tests/index/test_index.py` (the expected wording)
- **Committed in:** `202c61f`

**4. [Rule 2 - Missing critical] Content-wins removals were described as a missing file**
- **Found during:** Task 1
- **Issue:** When a path now holds another source's content, the old source is removed, but "inputs/a.txt is no longer in inputs/" was false, because the file is still there.
- **Fix:** In this case the change line and `INPUT_REMOVED` say that the earlier content is gone.
- **Files modified:** `epb/sources/scan.py`
- **Committed in:** `90778f6`

---

**Total deviations:** 4 auto-fixed (2 missing critical, 2 bugs).
**Impact on plan:** All four keep the planned interfaces. `index.py` and `tests/index/test_index.py` are outside the plan's file list, with one condition and one wording change each. There is no change to `workspace.py`, `txn.py` or any schema.

## Issues Encountered

None blocked the plan. These carry-over notes were not addressed here:

- **Stale INDEX skipped-file issues (01-13 carry-over, not changed).** A link added on its own still appears in that scan's warnings but not in INDEX Open issues until the next scan that changes something. Fixing it means a no-change scan would write a run, which reverses 01-13's "no change writes nothing" rule. That needs an owner decision. Suggested for 01-15.
- **`epb status` counts removed sources as waiting (01-13 carry-over, not changed).** `commands/status.py` counts `status == "pending"` without checking `presence`. It is a one-line fix outside this plan's files. Suggested for 01-15.
- **Case-insensitive new-version matching.** On every OS, a case-only rename that also changes the content (`Report.pdf` to `report.pdf` with new bytes) becomes a new source and a removal, not `S001v2`, because new-version candidates match paths exactly. Research Pattern 4 suggests case-insensitive keys on Windows and macOS. That is not done, because it would make classification OS-dependent. This needs a decision before CI covers those OSes.
- **`.epb/lock` churn** is still an open owner decision. The ignore list was not changed.

## User Setup Required

None. No external service configuration is required.

## Next Phase Readiness

- **01-15 (skill and workspace contract):** these need a sentence each:
  - content wins (Q4);
  - reverted content becomes a new version;
  - sidecar naming (exact `<file>.note.md` / `<file>.note.yaml`; a bare `.note.md` is an ordinary input);
  - the two-spellings error.

  The `status` count and the stale ignored-issues items above are candidates for this plan.
- **01-16 (manual):** quote the scan change lines and the `INPUT_REMOVED`, `SIDECAR_ORPHAN` and two-spellings wording.
- **Phase 5:** sidecar custody content (PF-01) can read `sidecar_of` / `sidecars`, which are already kept current by every scan.

---
*Phase: 01-foundations*
*Completed: 2026-10-18*

## Self-Check: PASSED

- All 3 created key files and the 6 modified key files exist on disk.
- Commits `90778f6`, `3ac9d95`, `ad290a5`, `16727a4`, `202c61f` and `c7ffb0a` are ancestors of HEAD on `gsd-wt-01-14`. `git rev-list --count 53f8db5..c7ffb0a` is 6, before the SUMMARY commits.
- Plan verification: `ruff check` and `ruff format --check` are clean, and `pytest -q` gives 1015 passed and 1 skipped.
- Key link: `scan.py` calls `pair_sidecars(` once, after `classify` and before staging. The scan crash test uses `list_checkpoints(`.
- STATE.md, ROADMAP.md and REQUIREMENTS.md are untouched, and nothing was written in the main checkout.
