---
phase: 01-foundations
plan: 21
subsystem: docs
tags: [privacy, user-manual, workspace-contract, skill, de-identification, gap-closure]

requires:
  - phase: 01-foundations
    provides: "01-16 first-edition manual and its tests; 01-17 CI-equivalent full check"
provides:
  - "Manual chapter 2 section 'De-identification and file names' that describes Phase 1 behaviour and gives the rename-and-check step"
  - "Manual chapter 6 rename step, Inputs row described with file name and folder, and a check-before-sharing sentence"
  - "Contract class review-before-sharing applied to INDEX.md, .epb/state.json and .epb/sources/"
  - "SKILL.md step: names shown exactly as they are; flag a person-like name by input ID; the agent never renames inputs"
  - "Six new tests pinning all three (plus an _items helper test)"
affects: [phase-04-deidentification, DOC-04, WS-10, DEID-08, PF-04]

actuals:
  tokens: 4700
  tasks: 3
  commits: 6
plan_head_before: b979d9d3d5eb0cf3ff94761cb5bb3655989b8fd2
plan_head_after: a249622c90991193228ddcad9462f32da075a91a

tech-stack:
  added: []
  patterns:
    - "Paragraph-level manual tests: _items() splits the manual into paragraphs and list items (fences skipped) so a claim and its qualifier must sit in the same paragraph"
    - "Interim contract class for records that hold raw input paths until Phase 4 de-identifies file names"

key-files:
  created: []
  modified:
    - docs/USER-MANUAL.md
    - tests/docs/test_manual.py
    - plugin/skills/evidence-pack/scripts/epb/workspace.py
    - plugin/skills/evidence-pack/references/workspace-contract.md
    - tests/workspace/test_layout.py
    - plugin/skills/evidence-pack/SKILL.md
    - tests/packaging/test_skill_lint.py
    - .planning/REQUIREMENTS.md

key-decisions:
  - "review-before-sharing is an interim Phase 1 class for INDEX.md, .epb/state.json and .epb/sources/; Phase 4 (WS-10, DEID-08) moves them back once names in file names are replaced. GITIGNORE_LINES and schemas unchanged"
  - "The manual tells users to rename before files go into inputs/, and makes no promise about what records keep after a later rename (run records keep earlier paths)"
  - "Name detection stays agent judgement in SKILL.md; no detection code in Phase 1"

patterns-established:
  - "A manual paragraph that mentions INDEX.md and role labels must also say later version (test_no_paragraph_promises_a_name_free_index)"

requirements-completed: [DOC-04]

coverage:
  - id: D1
    description: "Manual chapter 2 states that this version does not de-identify, that INDEX.md and .epb list file and folder names as given, and gives the rename-before-inputs and check-before-sharing steps"
    requirement: DOC-04
    verification:
      - kind: unit
        ref: "tests/docs/test_manual.py#test_no_paragraph_promises_a_name_free_index"
        status: pass
      - kind: unit
        ref: "tests/docs/test_manual.py#test_privacy_chapter_says_file_names_are_shown_as_given"
        status: pass
      - kind: unit
        ref: "tests/docs/test_manual.py#test_privacy_chapter_has_a_file_names_section"
        status: pass
    human_judgment: true
    rationale: "Tests pin that the false promise is gone and the rename step is present; whether the wording is clear to a non-technical reader is the owner's read-through (plan human-check, verification human item 5)"
  - id: D2
    description: "Manual chapter 6 gives the rename step before copying files in, says the Inputs row shows each file name and folder, and says to check INDEX.md for names before sharing"
    requirement: DOC-04
    verification:
      - kind: unit
        ref: "tests/docs/test_manual.py#test_first_case_folder_chapter_warns_about_names_in_file_names"
        status: pass
    human_judgment: true
    rationale: "Plain-language clarity is judged in the owner's read-through"
  - id: D3
    description: "Workspace contract classes INDEX.md, .epb/state.json and .epb/sources/ as review-before-sharing in code and in workspace-contract.md, with the class explained"
    verification:
      - kind: unit
        ref: "tests/workspace/test_layout.py#test_records_that_list_file_names_are_review_before_sharing"
        status: pass
      - kind: unit
        ref: "tests/packaging/test_references.py#test_contract_path_listed_with_its_classification"
        status: pass
      - kind: unit
        ref: "tests/packaging/test_references.py#test_contract_explains_every_classification"
        status: pass
    human_judgment: true
    rationale: "Owner confirms the interim label until Phase 4 (plan human-check step 3)"
  - id: D4
    description: "SKILL.md tells the agent names appear exactly as they are, to flag a person-like name by input ID, and never to rename, move or edit inputs"
    verification:
      - kind: unit
        ref: "tests/packaging/test_skill_lint.py#test_router_says_file_names_are_shown_as_they_are"
        status: pass
      - kind: unit
        ref: "tests/packaging/test_skill_lint.py#test_at_most_150_lines"
        status: pass
    human_judgment: false

duration: 25min
completed: 2026-10-18
status: complete
---

# Phase 1 Plan 21: Honest file-name privacy wording Summary

**The manual, workspace contract and router skill now say what Phase 1 really does: INDEX.md and the .epb records list input file names as given and nothing is de-identified yet. Users are told to rename name-bearing files before they go into inputs/ and to check INDEX.md before sharing it. The three records carry a new interim `review-before-sharing` contract class, and paragraph-level tests stop the old role-label promise from coming back.**

## Performance

- **Duration:** about 25 min
- **Started:** 2026-10-18T15:08:00Z
- **Completed:** 2026-10-18T15:34:00Z
- **Tasks:** 3
- **Files modified:** 8 (7 planned, plus REQUIREMENTS.md)

## Accomplishments

- Chapter 2's "De-identification is always on" section is now "De-identification and file names". It covers what de-identification is and says it arrives in a later version, always on from then. It says this version lists files by their names as given, then gives three numbered steps: rename name-bearing files before they go into `inputs/`, check INDEX.md before sharing it, and never share `.epb`. The `.epb/private/` warning is kept.
- Chapter 6 has a new first step in "Put your files in inputs/" (rename first, with a synthetic example `witness-statement-1.pdf`). The Inputs bullet now says "its file name and folder", and a check-before-sharing sentence follows the six sections.
- `epb.workspace.CLASSIFICATIONS` gains `review-before-sharing` (right after `shareable`), and `CONTRACT_PATHS` moves `INDEX.md`, `.epb/state.json` and `.epb/sources/` to it. `workspace-contract.md` explains the class, updates the three rows and adds the name check to the version-control rule.
- SKILL.md has a new step 6 under "Taking stock of the inputs" and a clause on INDEX.md item 3. The file is 100 lines.

## Task Commits

1. **Task 1 (tracer): privacy chapter states what this version does with file names.** RED `8eddd06` (test), GREEN `636f434` (feat)
2. **Task 2: contract classes INDEX.md and the file-name records honestly.** RED `e74b48a` (test), GREEN `00cb8e1` (feat)
3. **Task 3: SKILL.md tells the agent how file names appear and who renames them.** RED `4eb2f1c` (test), GREEN `a249622` (feat)

No REFACTOR commits were needed.

## TDD evidence

- **Task 1 RED:** `pytest -q tests/docs/test_manual.py -k "items_splits or name_free_index or file_names_are_shown or file_names_section or names_in_file_names"` gave 4 failed and 1 passed (the helper's own test). `test_no_paragraph_promises_a_name_free_index` failed on its target assertion, naming the old chapter 2 bullet: "- Everything the plugin makes for you to share, such as the evidence pack workbook and `INDEX.md`, uses role labels instead of names." The other three failed on their content assertions (no matching item, no "file names" heading, no rename-plus-INDEX.md step in "Put your files in"). Semantic assessment: every target ran and failed for the planned reason. There were no collection, import or fixture faults.
- **Task 2 RED:** `test_records_that_list_file_names_are_review_before_sharing` failed 3 of 3 parametrised cases on `assert 'review-before-sharing' in CLASSIFICATIONS`, which is the planned reason.
- **Task 3 RED:** `test_router_says_file_names_are_shown_as_they_are` failed on `assert 'names exactly as they are' in body`, which is the planned reason.
- **GREEN:** each task's `<verify>` exited 0. The final full check (`ruff check`, `ruff format --check`, `PYTHONWARNDEFAULTENCODING=1 pytest -q`) gave 1275 passed and 4 skipped (network, host-CLI and the expected `/tmp/.git` skip).
- I used pytest's own output as the RED record. The GSD `tdd-red-evidence` classifier has no pytest adapter, and this plan is not `type: tdd`, so the classifier gate does not apply. The semantic assessment above is the evidence.

## Tracer gate

Task 1 is `type="tracer"`, its `<verify>` holds only `<automated>`, `human_verify_mode` is end-of-phase and auto mode is off (row 3). After the commit I re-ran the verify (32 passed) and continued to expansion without a checkpoint.

## Files Created/Modified

- `docs/USER-MANUAL.md`: chapter 2 section rewritten; chapter 6 inputs step and INDEX.md text.
- `tests/docs/test_manual.py`: `_items` helper plus its own test, and four new tests.
- `plugin/skills/evidence-pack/scripts/epb/workspace.py`: the new class in the docstring and `CLASSIFICATIONS`; three paths reclassified, with descriptions noting that they hold input paths.
- `plugin/skills/evidence-pack/references/workspace-contract.md`: class bullet, three table rows, the version-control rule, and the chunk-data note.
- `tests/workspace/test_layout.py`: new test for the review-before-sharing class.
- `plugin/skills/evidence-pack/SKILL.md`: new "Taking stock" step 6 and the INDEX.md item 3 clause.
- `tests/packaging/test_skill_lint.py`: new test for the router's file-name wording.
- `.planning/REQUIREMENTS.md`: DOC-04 marked complete through `requirements.mark-complete` (`ready-ids` reported it ready; the only other declaring plan, 01-16, has a SUMMARY).

## Decisions Made

- `review-before-sharing` is an interim label. Phase 4 moves the three paths back once file names are de-identified. `GITIGNORE_LINES` (design §20 A2) and every schema are unchanged.
- The advice is to rename before files go in. The manual promises nothing about records after a later rename.
- No name-detection code. "Looks like a person's name" is the agent's judgement, and the agent names the input by ID instead of repeating the name.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] The contract's chunk-data note still called `.epb/state.json` "safe to keep in version control"**
- **Found during:** Task 2
- **Issue:** The "Records and state" note in `workspace-contract.md` said state.json "stays safe to keep in version control". That contradicted the new class, because `fingerprints` is keyed by input path (confirmed in `epb/sources/classify.py`). The plan's done criterion is that the contract no longer calls a file holding raw file names safe without a caveat.
- **Fix:** I reworded it: chunk data adds no raw text to state.json, but its fingerprints are keyed by input path, so check its file names before keeping it in version control (review-before-sharing).
- **Files modified:** plugin/skills/evidence-pack/references/workspace-contract.md
- **Verification:** `tests/packaging/test_references.py` passes, and so does the full check.
- **Committed in:** `00cb8e1`

**2. [Rule 2 - Test strength] The chapter 6 test asserts more than the plan's minimum**
- **Found during:** Task 1 RED
- **Issue:** Chapter 6 already contained "renames" ("never changes, moves or renames anything") and "file names" ("used in file names"). The plan's two substring checks would have passed before any change.
- **Fix:** On top of the planned checks, the test now requires an item in "Put your files in inputs/" that holds both "rename" and "INDEX.md". It also requires the Inputs bullet to contain "file name", and a "Read INDEX.md" item to hold "before you share" and "person's name". All planned assertions are kept.
- **Files modified:** tests/docs/test_manual.py
- **Committed in:** `8eddd06`

---

**Total deviations:** 2 auto-fixed (1 bug, 1 test-strength). **Impact:** both keep the plan's goal intact. There is no scope creep.

## Issues Encountered

None.

## Known Stubs

None.

## User Setup Required

None. The owner's read-through is pending: the plan's Task 3 `<human-check>`, verification human item 5. The verifier collects it at the end of the phase.

## Next Phase Readiness

- Gap 5 (truth 23) is closed on the documentation side. The code side (role labels for names in file names, and INDEX.md scanned for names) is still deferred to Phase 4 (WS-10, DEID-08, PF-04). When Phase 4 lands, move the three paths back from `review-before-sharing` and rewrite the chapter 2 section.

---
*Phase: 01-foundations*
*Completed: 2026-10-18*

## Self-Check: PASSED

- All 8 key files exist; commits 8eddd06, 636f434, e74b48a, 00cb8e1, 4eb2f1c, a249622 are on this branch.
- workspace-contract.md has 5 review-before-sharing mentions (needs at least 4); SKILL.md has 100 lines (limit 150).
- Full CI-equivalent check: 1275 passed, 4 skipped.
