---
phase: 01-foundations
plan: 16
subsystem: docs
tags: [user-manual, golden-test, doctor, privacy, agents-md, readme]

# Dependency graph
requires:
  - phase: 01-foundations (01-08, 01-10)
    provides: epb.doctor.report.render_human / render_setup_human (pure functions of the report), the doctor registry and extras, the SYNC_FOLDER warning text
  - phase: 01-foundations (01-03)
    provides: launcher.data_root() per OS (D-03), the envs/<version> layout
  - phase: 01-foundations (01-11, 01-14)
    provides: INDEX.md six sections, "none yet", "waiting for conversion (coming in a later version)", <file>.note.md sidecars
  - phase: 01-foundations (01-02)
    provides: design §20 A1, A9, A14, A15
provides:
  - docs/USER-MANUAL.md, first edition (chapters 1 to 7 in the DOC-05 order)
  - tests/docs/test_manual.py, golden test for doctor and doctor --setup output plus structure tests
  - refreshed byte-identical AGENTS.md / CLAUDE.md (43 lines)
  - README status line, manual link and privacy note
affects: [every later phase that adds a tool or a user step (extend the manual), doctor wording changes (regenerate golden blocks), 01-15 router skill (the manual's suggested phrases mirror its flow)]

# Actuals (#2632)
actuals:
  tokens: 9682
  tasks: 3
  commits: 4
plan_head_before: 5bdf3d18e7d368bc53dffb568b9eb7b9ef11b604
plan_head_after: 1a4a5f62c0552b5b2109688ae696c97f1ee976d7

tech-stack:
  added: []
  patterns:
    - "Golden-block test: a fenced text block between <!-- golden:NAME --> markers must equal the renderer's output for a fixed fake report"
    - "Fake reports for doctor are built from tools.REGISTRY / tools.EXTRAS and probes.core_requirements, so a new tool row or core package fails the golden test until the manual is updated"
    - "OS-specific manual sections carry '*This section is not yet tested on this system.*' as their first line; a test checks adjacency per heading"

key-files:
  created:
    - docs/USER-MANUAL.md
    - tests/docs/test_manual.py
  modified:
    - AGENTS.md
    - CLAUDE.md
    - README.md

key-decisions:
  - "The manual is a single file, docs/USER-MANUAL.md (plan's location decision); chapters are '## N. Title' so the order is testable"
  - "The fake golden report uses a neutral home folder (/home/investigator) and env version 0.1.0, so the quoted path reads ~/.local/share/probematrix-epb/envs/0.1.0"
  - "Chapter 2 also quotes the real SYNC_FOLDER message and hint for OneDrive, checked against syncfolders.warning_for by a test"
  - "Chapter 2 states that excerpts can contain names and that the provider's handling is governed by the user's agreement with it, not by the plugin (flagged assumption DOC-04)"

patterns-established:
  - "Manual drift guard: change doctor wording or the registry, then regenerate the golden blocks and re-read the chapter"

requirements-completed: [DOC-04, DOC-05, PKG-11]

coverage:
  - id: D1
    description: "Chapter 5 quotes render_setup_human and render_human exactly; a golden test fails on any drift (D-17)"
    requirement: DOC-05
    verification:
      - kind: unit
        ref: "tests/docs/test_manual.py#test_manual_quotes_the_renderer_exactly"
        status: pass
      - kind: unit
        ref: "tests/docs/test_manual.py#test_golden_blocks_show_the_three_headings"
        status: pass
    human_judgment: false
  - id: D2
    description: "Seven chapters in the DOC-05 order; Windows and macOS sections each marked 'not yet tested on this system' directly under their heading; plugin commands, Codex note, INDEX.md sections and the three D-03 folders present"
    requirement: DOC-05
    verification:
      - kind: unit
        ref: "tests/docs/test_manual.py (27 tests)"
        status: pass
    human_judgment: false
  - id: D3
    description: "Privacy chapter: conversion is local, the agent's excerpts go to the AI host's model provider, sync folders upload .epb/private, de-identification is always on; never claims nothing leaves the computer"
    requirement: DOC-04
    verification:
      - kind: unit
        ref: "tests/docs/test_manual.py#test_privacy_chapter_names_what_leaves_and_why"
        status: pass
      - kind: unit
        ref: "tests/docs/test_manual.py#test_manual_never_claims_that_nothing_leaves_the_computer"
        status: pass
    human_judgment: true
    rationale: "Plan human-check: the owner must confirm chapter 2 is understandable without technical words and chapters 3 to 6 work for someone who has never used a terminal"
  - id: D4
    description: "AGENTS.md and CLAUDE.md refreshed for the phase transition, byte-identical, 43 lines"
    requirement: PKG-11
    verification:
      - kind: unit
        ref: "tests/repo/test_instructions_mirror.py"
        status: pass
      - kind: other
        ref: "cmp AGENTS.md CLAUDE.md"
        status: pass
    human_judgment: false
  - id: D5
    description: "README status line, manual link and two-sentence privacy note; 'No code yet' removed"
    requirement: DOC-04
    verification:
      - kind: other
        ref: "grep -c 'No code yet' README.md == 0"
        status: pass
    human_judgment: false
  - id: D6
    description: "Owner CI check (SC5): push phase-01-foundations and confirm ci jobs core (Python 3.11) and core (Python 3.14) are green"
    requirement: PKG-11
    verification: []
    human_judgment: true
    rationale: "Pushing needs the owner's yes and the CI result is only visible on GitHub; deferred to the orchestrator after merge"

duration: 7min
completed: 2026-10-18
status: complete
---

# Phase 1 Plan 16: First edition of the user manual Summary

**`docs/USER-MANUAL.md` now walks a non-technical user through the plugin in seven chapters: privacy, installing Python, adding the plugin, first-time setup, a first case folder and where the private environment lives. The `doctor` and `doctor --setup` checklists it quotes are compared word for word with the real renderers by a golden test. The Windows and macOS sections are each marked "not yet tested on this system". AGENTS.md/CLAUDE.md and the README are refreshed for the phase transition.**

## Performance

- **Duration:** about 7 min (wall clock from the recorded start)
- **Started:** 2026-10-18T11:10:32Z
- **Completed:** 2026-10-18T11:17:44Z
- **Tasks:** 3
- **Files modified:** 5 (2 created, 3 modified)

## Accomplishments

- **Golden test (D-17).** `tests/docs/test_manual.py` builds one fixed fake Linux report: Python 3.12.3, a current environment at `~/.local/share/probematrix-epb/envs/0.1.0`, 14 of 14 core packages, 7-Zip 26.00 and git 2.53.0 found, everything else missing, and setup status `created`. It asserts that `render_setup_human` and `render_human` equal the text between `<!-- golden:setup -->` and `<!-- golden:doctor -->` in the manual. The fake report is built from `tools.REGISTRY`, `tools.EXTRAS` and `probes.core_requirements`, so adding a tool or a core package fails the test until the manual is updated.
- **Manual chapters 1 to 7** follow the DOC-05 order. Chapter 1 says once which stages later editions add.
  - Chapter 2 gives the privacy story in plain words: what stays local, that excerpts go to the AI host's model provider and can contain names, that de-identification is always on, why `.epb/private/` must stay out of sync folders (with the real `SYNC_FOLDER` message and hint for OneDrive) and out of git.
  - Chapter 3 covers Python on Linux (tested on Ubuntu), Windows and macOS.
  - Chapter 4 gives the two `/plugin` commands and a Codex note.
  - Chapter 6 covers the case folder: the title-only question, the one-line settings proposal, `inputs/`, `.note.md` notes, taking stock, and the six `INDEX.md` sections with "none yet" and "waiting for conversion".
  - Chapter 7 names the three D-03 folders and gives hand-removal steps for each OS.
- **Untested markers.** The Windows and macOS sections in chapters 3 and 7, and the Codex note, each carry their own "not yet tested on this system" line directly under the heading. The inline Windows command in chapter 6 is marked too.
- **Mirrored instructions.** `AGENTS.md` and `CLAUDE.md` gained six pointer lines and stay byte-identical at 43 lines. They cover the dev environment and full check, the opt-in test switches, the CLI package and its single schema copy (D-05), stdlib-only command modules (enforced by `tests/launcher/test_launcher.py::test_bootstrap_imports_stdlib_only`), `scratch/` for the smoke pack, and extending the manual every phase.
- **README.** It has the Phase 1 status line, a link to the user manual and the two-sentence privacy note.

## Task Commits

1. **Task 1: Tracer, setup chapter with golden output** - `3ac2e9d` (feat)
2. **Task 2: The rest of the first edition** - `eec9ce7` (test, RED), `b6d8d8e` (feat, GREEN)
3. **Task 3: AGENTS.md/CLAUDE.md, README** - `1a4a5f6` (docs)

**Plan metadata:** the SUMMARY commit follows this file.

## TDD (Task 2)

- **RED (`eec9ce7`).** 19 new tests failed and the 8 Task 1 tests passed. The record went to the classifier `gsd-tools check tdd-red-evidence` as pytest JUnit XML, with target `test_chapters_appear_in_the_doc05_order`, and returned `RED_EVIDENCE_OK` (`target_test_failed`).
  - Semantic assessment: the target ran and failed on its planned assertion, because the level-2 headings were only `["5. First-time setup"]`. The other failures were `KeyError` on the missing chapters or failed assertions. There were no import, collection or fixture errors.
  - Two guard tests passed at RED, as expected, because the Task 1 text already satisfied them: no "nothing leaves" claim, and no placeholder headings.
- **GREEN (`b6d8d8e`).** All 27 tests pass.
- **REFACTOR.** None needed.

## Files Created/Modified

- `docs/USER-MANUAL.md` - first edition of the non-technical manual, about 490 lines.
- `tests/docs/test_manual.py` - golden tests and structure tests (27 tests).
- `AGENTS.md`, `CLAUDE.md` - phase-transition refresh, byte-identical.
- `README.md` - status line, manual link and privacy note.

## Decisions Made

- The fake golden report uses the neutral home `/home/investigator` and env version `0.1.0`, as the plan specifies. The live version is `0.1.0-dev.1`, and the manual explains that the folder name is the installed plugin version.
- The manual tells the user to start setup with the phrase "Run first-time setup for the evidence pack plugin". When the AI app blocks downloads, it tells them to paste the exact command the agent shows. It does not guess the plugin's cache path.
- For Ubuntu 22.04 (Python 3.10), the manual offers `sudo apt install python3.11 python3.11-venv`, relying on the launcher's `python3.11` candidate search. The manual says this route has not been tried with the plugin yet.
- For removing an old version by hand, the manual uses each OS's file manager (Files with Ctrl+H, Run with `%LOCALAPPDATA%`, Finder with Go to Folder) rather than `rm -rf`, which is safer for non-technical users.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] The RED test's section parser dropped fenced blocks from chapter bodies**
- **Found during:** Task 2 (GREEN)
- **Issue:** `chapter()` blanked every fenced block before splitting. Commands such as `python3 --version`, the `/plugin` lines and the quoted sync warning live in fenced blocks, so they would never have been found. The helper also ignored indented fences inside numbered steps.
- **Fix:** A fence-aware line parser now recognises headings only outside fences, indented or not, and keeps fenced text in section bodies. The placeholder-heading test uses the same parser.
- **Files modified:** `tests/docs/test_manual.py`
- **Verification:** 27/27 pass. The adjacency, command and warning assertions now read the real chapter text.
- **Committed in:** `b6d8d8e`

**2. [Rule 2 - Missing critical] Chapter 2 quotes the real sync-folder warning, and a test pins it**
- **Found during:** Task 2
- **Issue:** The plan asks chapter 2 to show what the warning looks like. Paraphrased text could drift from `syncfolders.warning_for`.
- **Fix:** The OneDrive message and hint are quoted verbatim. `test_privacy_chapter_quotes_the_real_sync_folder_warning` compares them with the code (T-01-44).
- **Files modified:** `docs/USER-MANUAL.md`, `tests/docs/test_manual.py`
- **Committed in:** `eec9ce7`, `b6d8d8e`

---

**Total deviations:** 2 auto-fixed (1 test bug, 1 missing critical).
**Impact on plan:** Both make the manual's honesty checks real. There is no scope creep.

## Issues Encountered

- The router skill (`plugin/skills/evidence-pack/SKILL.md`) does not exist on this branch yet, because plan 01-15 is writing it in parallel. Chapters 5 and 6 describe the agent's behaviour from the 01-15 plan and design D-04/D-15: the title-only question and the one-line proposal, using 01-15's own example sentence. Once both branches are merged, the owner's read-through should confirm that the agent's real phrasing matches.
- The Claude Code confirmation texts after `/plugin marketplace add` and `/plugin install` are described, not quoted. They were not run here, to avoid touching the real user configuration and the network.

## User Setup Required

None. No external service configuration is required.

## Pending Owner Checks (human-check, deferred)

1. **Manual read-through (DOC-04, DOC-05)**, as in the plan's Task 2 human-check:
   - Read chapter 2. Pass: you could explain to a colleague, without technical words, what leaves the computer and why a case folder must not be in a sync folder.
   - Read chapters 3 to 6 as a first-time terminal user. Pass: every step is one action, says what to type and says what you should see.
   - Check that the Windows and macOS sections say "not yet tested on this system".
2. **Owner CI check (SC5).** This was **not performed by this executor**. As the parallel-execution instructions require, there was no push and no question to the owner. After merge, the orchestrator asks the owner "Push phase-01-foundations to origin so CI can run?". On a yes, it runs `git push -u origin phase-01-foundations`. The owner then confirms that the `ci` jobs `core (Python 3.11)` and `core (Python 3.14)` are green and that the plugin-validate step prints "claude CLI not installed; skipping plugin validate (D-02)".

## Verification (plan-level)

- `.venv/bin/ruff check .`: All checks passed.
- `.venv/bin/ruff format --check .`: 90 files already formatted.
- `.venv/bin/python -m pytest -q`: 1042 passed, 1 skipped (network opt-in).
- `cmp AGENTS.md CLAUDE.md`: identical. `wc -l AGENTS.md` = 43.
- `tools/check_licences.py`: passed, 35 distributions allowed.
- `tools/check_dependency_age.py`: passed, with no VIOLATION lines.
- `grep -c "not yet tested on this system" docs/USER-MANUAL.md` = 5.
- `grep -c "No code yet" README.md` = 0.

## Next Phase Readiness

- Phase 1's manual and instruction clauses of SC5 hold on this branch. The CI clause waits on the owner's push decision.
- Later phases extend `docs/USER-MANUAL.md`, adding a chapter only when its feature exists. If doctor wording or a registry row changes, regenerate the golden blocks with `render_setup_human`/`render_human` on the test's `FAKE_REPORT`.

---
*Phase: 01-foundations*
*Completed: 2026-10-18*
