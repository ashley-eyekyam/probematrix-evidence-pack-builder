---
phase: 01-foundations
plan: 25
subsystem: docs-skill
tags: [manual, skill, workspace-contract, bad-name, warnings, doc-drift]

requires:
  - phase: 01-foundations
    provides: "01-24: bad-name ignored reason, BAD_NAME_IGNORED warning code, index._IGNORED_REASONS['bad-name'] wording"
provides:
  - "USER-MANUAL.md chapter 6 'Put your files in inputs/' item 4: names that are not valid text are skipped, listed under 5. Open issues, and the user renames them"
  - "SKILL.md guidance for data.ignored bad-name entries and the BAD_NAME_IGNORED warning"
  - "workspace-contract.md lists bad-name files and folders among ignored entries"
  - "Tests that pin the manual to index._IGNORED_REASONS and the contract to errors.WARNING_CODES"
affects: [01 verification (gap 2), any later phase that edits chapter 6, SKILL.md or the contract]

actuals:
  tokens: 2000
  tasks: 2
  commits: 4
plan_head_before: 63e7ab502e4ff8fed91b1c0c67f99c58fb90dde3
plan_head_after: 0e3cff600ee9dfde002412c73f6c6f0205996a5f

tech-stack:
  added: []
  patterns:
    - "Docs-to-code drift tests import the code's own wording or code registry (index._IGNORED_REASONS, errors.WARNING_CODES) instead of repeating it"

key-files:
  created: []
  modified:
    - docs/USER-MANUAL.md
    - tests/docs/test_manual.py
    - plugin/skills/evidence-pack/SKILL.md
    - plugin/skills/evidence-pack/references/workspace-contract.md
    - tests/packaging/test_skill_lint.py
    - tests/packaging/test_references.py

key-decisions:
  - "The manual names no warning code (non-technical readers); SKILL.md and the contract carry BAD_NAME_IGNORED for the agent"
  - "SKILL.md step 4 tells the agent to name the skipped entry as the warning shows it, because a bad-named entry has no input ID"

patterns-established:
  - "A new user step in chapter 6 gets a test that ties its wording to the string the code writes into INDEX.md"

requirements-completed: [WS-02, DOC-05]

coverage:
  - id: D1
    description: "Manual chapter 6 tells the user that a file or folder whose name is not valid text is skipped, listed under 5. Open issues, and must be renamed before taking stock again; the wording shares 'not valid text' with INDEX.md"
    requirement: DOC-05
    verification:
      - kind: unit
        ref: "tests/docs/test_manual.py#test_first_case_folder_chapter_explains_names_that_are_not_valid_text"
        status: pass
      - kind: unit
        ref: "tests/docs/test_manual.py (33 tests)"
        status: pass
    human_judgment: false
  - id: D2
    description: "SKILL.md explains bad-name entries in data.ignored and BAD_NAME_IGNORED, asks the user to rename and scan again, and still says the agent never renames, moves or edits anything in inputs/"
    requirement: WS-02
    verification:
      - kind: unit
        ref: "tests/packaging/test_skill_lint.py#test_router_covers_phase_1_scope[BAD_NAME_IGNORED]"
        status: pass
      - kind: unit
        ref: "tests/packaging/test_skill_lint.py#test_router_covers_phase_1_scope[bad-name]"
        status: pass
      - kind: unit
        ref: "tests/packaging/test_skill_lint.py#test_router_says_file_names_are_shown_as_they_are"
        status: pass
      - kind: unit
        ref: "tests/packaging/test_skill_lint.py#test_at_most_150_lines"
        status: pass
    human_judgment: false
  - id: D3
    description: "workspace-contract.md lists bad-name files and folders (warned as BAD_NAME_IGNORED, nothing inside such a folder scanned) among the entries scan ignores"
    requirement: WS-02
    verification:
      - kind: unit
        ref: "tests/packaging/test_references.py#test_contract_names_the_bad_name_skip"
        status: pass
      - kind: unit
        ref: "tests/packaging/test_references.py#test_contract_lists_every_junk_pattern"
        status: pass
    human_judgment: false
  - id: D4
    description: "The new manual item reads plainly to a non-technical investigator"
    verification: []
    human_judgment: true
    rationale: "Tone and clarity for a non-technical reader cannot be asserted by a phrase test"

duration: 6min
completed: 2026-10-18
status: complete
---

# Phase 1 Plan 25: The manual, the skill and the contract explain the bad-name skip Summary

**Manual chapter 6 now tells the user that a file or folder whose name is not valid text is skipped, listed under "5. Open issues", and must be renamed. SKILL.md and the workspace contract describe `bad-name` and `BAD_NAME_IGNORED` for the agent. Tests tie the manual to `index._IGNORED_REASONS` and the contract to `errors.WARNING_CODES` (gap 2, WS-02, DOC-05).**

## Performance

- **Duration:** about 6 min
- **Started:** 2026-10-18T16:57:48Z
- **Completed:** 2026-10-18T17:03:20Z
- **Tasks:** 2 (both TDD; 4 commits)
- **Files modified:** 6 (0 created, 6 modified; 37 lines added and 6 removed)

## Accomplishments

- `docs/USER-MANUAL.md`, section "Put your files in `inputs/`", has a new item 4. It says some names cannot be read as text (for example names in a ZIP file made on an older Windows computer, or files copied from an old shared drive). The plugin skips such a file or folder, tells the user, and lists it in `INDEX.md` under **5. Open issues** as named with characters that are not valid text. The user renames it and asks the agent to take stock again. The item names no warning code and no real names, and no other line of the manual changed.
- `SKILL.md` has three in-place edits and stays at 100 lines:
  - Step 3: the `ignored` bullet now includes names that are not valid text (reason `bad-name`).
  - Step 4: `BAD_NAME_IGNORED` is added to the warnings the agent passes on. The agent names the entry as the warning shows it and asks the user to rename it, then scan again.
  - "Reading INDEX.md" item 5: names that are not valid text are added to the skipped entries.
  - "You never rename, move or edit anything in `inputs/`." is unchanged.
- `references/workspace-contract.md`: the ignored-entries bullet now lists files and folders whose names are not valid text. It says they are `bad-name`, warned as `BAD_NAME_IGNORED`, that nothing inside such a folder is scanned, and that the user renames it. Every junk pattern is still listed.

## TDD record

**Task 1 RED** (`dd14d1a`): `test_first_case_folder_chapter_explains_names_that_are_not_valid_text` failed with `assert 0 == 1`, because the inputs section had no item with "not valid text".
- Semantic assessment: the target test ran and failed on its first planned assertion, for the intended reason. There was no import, collection or fixture fault. `index._IGNORED_REASONS["bad-name"]` already holds the wording (from 01-24), so the code-side assertion was never the cause.
- `workflow.tdd_mode` is off, so the `tdd-red-evidence` classifier gate does not apply.

**Task 1 GREEN** (`bf779ec`): the new test passes (1 passed), and `tests/docs/test_manual.py` has 33 passed.

**Tracer feedback gate:** the run was interactive in `end-of-phase` mode, and the tracer's verify was automated only. I re-ran the verify (33 passed) and went on to Task 2.

**Task 2 RED** (`d07e791`): three cases failed and the other 215 passed.
- `test_router_covers_phase_1_scope[BAD_NAME_IGNORED]` and `[bad-name]` failed because the phrases were absent from SKILL.md.
- `test_contract_names_the_bad_name_skip` failed on its first assertion, because `` `bad-name` `` was not in the contract.
- Semantic assessment: all three are the planned assertions failing for the intended reason.

**Task 2 GREEN** (`0e3cff6`): the three cases pass, and the two packaging files have 218 passed. The full check passes: ruff check, ruff format --check, and pytest with 2006 passed and 3 opt-in skips (network/host). `tools/check_licences.py` also passes (35 distributions allowed). No REFACTOR commit was needed.

## Task Commits

1. **Task 1: Tracer, the manual explains a skipped bad name** - `dd14d1a` (test), `bf779ec` (feat)
2. **Task 2: SKILL.md and the contract describe bad-name and BAD_NAME_IGNORED** - `d07e791` (test), `0e3cff6` (feat)

## Files Created/Modified

- `docs/USER-MANUAL.md`: chapter 6 item 4 (5 lines added, 0 removed against `origin/phase-01-foundations`).
- `tests/docs/test_manual.py`: imports `index` from `epb`, and adds the new test.
- `plugin/skills/evidence-pack/SKILL.md`: steps 3 and 4, and INDEX item 5.
- `plugin/skills/evidence-pack/references/workspace-contract.md`: the ignored-entries bullet.
- `tests/packaging/test_skill_lint.py`: two router phrase cases.
- `tests/packaging/test_references.py`: imports `errors` from `epb`, and adds `test_contract_names_the_bad_name_skip`.

## Acceptance results

- Task 1:
  - The `-k names_that_are_not_valid_text` run gives 1 passed.
  - `tests/docs/test_manual.py` exits 0.
  - `grep -c "not valid text" docs/USER-MANUAL.md` gives 1.
  - numstat against `origin/phase-01-foundations` is `5 0`.
- Task 2:
  - The `-k "BAD_NAME_IGNORED or bad-name or bad_name_skip"` run gives 3 passed.
  - `BAD_NAME_IGNORED` is on 1 line in SKILL.md and on 1 line in the contract.
  - "You never rename, move or edit anything in" appears once.
  - `wc -l` of SKILL.md is 100.
  - The full check exits 0.

## Decisions Made

- No warning code goes in the manual, as the plan's flagged assumption says. SKILL.md and the contract carry `BAD_NAME_IGNORED`.
- SKILL.md step 4 tells the agent to name the skipped entry as the warning shows it. A bad-named entry is never registered, so it has no ID to use instead. Step 6's "name the input by its ID" advice is for registered inputs and stays as it is.
- I left REQUIREMENTS.md unchanged. WS-02 and DOC-05 read "Gaps Found" in the traceability table, and phase re-verification decides whether gap 2 is closed. The plan's `requirements` list is copied into `requirements-completed` as the template asks.

## Deviations from Plan

None. The plan was executed as written.

## Issues Encountered

- The worktree had no `.venv`, so I symlinked it to the main checkout's `.venv` as CLAUDE.md says. The symlink is git-ignored.

## Known Stubs

None.

## User Setup Required

None.

## Next Phase Readiness

- Gap 2 is now explained everywhere scan results are read: in INDEX.md (01-24), and in the manual, the skill and the contract (this plan). It is ready for phase 01 re-verification.
- UAT note for the owner: read chapter 6 item 4 as a non-technical user would (coverage D4).

## Self-Check: PASSED

- FOUND: docs/USER-MANUAL.md, tests/docs/test_manual.py, plugin/skills/evidence-pack/SKILL.md, plugin/skills/evidence-pack/references/workspace-contract.md, tests/packaging/test_skill_lint.py, tests/packaging/test_references.py
- FOUND commits on this branch: dd14d1a, bf779ec, d07e791, 0e3cff6
