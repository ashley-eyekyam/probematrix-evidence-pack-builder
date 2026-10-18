---
phase: 01-foundations
plan: 15
subsystem: packaging
tags: [agent-skills, skill-md, claude-code, codex, marketplace, evidence-pack-v2, workspace-contract, pytest]

requires:
  - phase: 01-04
    provides: probematrix_v2 format constants and the validator's finding codes
  - phase: 01-06
    provides: marketplace and plugin manifests, plugin/AGENTS.md, install-codex.py plugin-rules copy
  - phase: 01-10
    provides: doctor --setup and data.environment.launch
  - phase: 01-11
    provides: workspace.CONTRACT_PATHS, GITIGNORE_LINES and INDEX.md sections
  - phase: 01-14
    provides: scan classification, sidecar pairing and the scan report
provides:
  - Router skill plugin/skills/evidence-pack/SKILL.md in its final location with Phase 1 scope (D-04)
  - references/workspace-contract.md, kept in step with epb.workspace and the scan code by a test
  - references/evidence-pack-v2.md, the importer-exact format checked on 2026-10-17 (BLD-01 documentation half)
  - In-house Agent Skills lint for every plugin/skills/*/SKILL.md
  - Opt-in isolated Claude Code and Codex install tests (EPB_HOST_TESTS=1)
affects: [01-16 manual, phase 2+ skill extensions, phase 10 host packaging]

actuals:
  tokens: 10748
  tasks: 2
  commits: 4
plan_head_before: 5bdf3d18e7d368bc53dffb568b9eb7b9ef11b604
plan_head_after: 89c3bdbd058f12191f2eabd9ffd7afce5345d5b5

tech-stack:
  added: []
  patterns:
    - "Reference docs are tested against the code constants they describe (CONTRACT_PATHS, format module, AST-extracted finding codes)"
    - "Host install tests run real host CLIs in throwaway CLAUDE_CONFIG_DIR / CODEX_HOME folders, opt-in with EPB_HOST_TESTS=1"

key-files:
  created:
    - plugin/skills/evidence-pack/SKILL.md
    - plugin/skills/evidence-pack/references/workspace-contract.md
    - plugin/skills/evidence-pack/references/evidence-pack-v2.md
    - tests/packaging/test_skill_lint.py
    - tests/packaging/test_references.py
    - tests/packaging/test_host_install.py
  modified: []

key-decisions:
  - "Finding codes are extracted from formats/validate.py by AST (upper-case snake-case string literals) because the validator has no code-list constant; a sanity test requires at least 20"
  - "The Codex install test checks the same file list as the Claude one (schemas, AGENTS.md, requirement files), not only SKILL.md, since the Codex cache was observed to hold them all"
  - "SKILL.md tells the agent to always pass --timezone to init (01-09 carry-over: Windows usually cannot detect it)"
  - "The workspace contract states content wins and that restoring an older version counts as new content, in one sentence each (01-13 carry-over)"

patterns-established:
  - "Skill references carry backticked code strings so a test can match them exactly against the module constants"

requirements-completed: [PKG-01, PKG-03, BLD-01]

coverage:
  - id: D1
    description: "Router skill SKILL.md with Phase 1 scope (setup, init with confirmed defaults, scan, INDEX.md, exit codes) that passes the Agent Skills lint"
    requirement: PKG-03
    verification:
      - kind: unit
        ref: "tests/packaging/test_skill_lint.py"
        status: pass
      - kind: other
        ref: "tests/packaging/test_manifests.py#test_claude_validate_strict"
        status: pass
    human_judgment: false
  - id: D2
    description: "An isolated marketplace install into Claude Code and Codex carries the skill, launcher, schemas, AGENTS.md and requirement files, and no docs, tests, tools, evals or .planning"
    requirement: PKG-01
    verification:
      - kind: integration
        ref: "EPB_HOST_TESTS=1 tests/packaging/test_host_install.py#test_claude_code_install_from_marketplace"
        status: pass
      - kind: integration
        ref: "EPB_HOST_TESTS=1 tests/packaging/test_host_install.py#test_codex_install_from_marketplace"
        status: pass
    human_judgment: false
  - id: D3
    description: "workspace-contract.md and evidence-pack-v2.md describe exactly what the code holds, enforced by a test"
    requirement: BLD-01
    verification:
      - kind: unit
        ref: "tests/packaging/test_references.py"
        status: pass
    human_judgment: false
  - id: D4
    description: "Owner install and first-use UAT: an agent sets up a case folder the way a user would (SC5, D-04)"
    verification: []
    human_judgment: true
    rationale: "Agent behaviour driven by SKILL.md in a live Claude Code session (asking only for the title, proposing defaults in one line, plain explanations) cannot be asserted by a test; the plan's human-check procedure is run by the owner at phase verification"

duration: 6min
completed: 2026-10-18
status: complete
---

# Phase 1 Plan 15: Router Skill and References Summary

**The evidence-pack router skill (setup, init, scan, INDEX.md), its workspace-contract and EVIDENCE_PACK_V2 references kept in step with the code by tests, and proof that real Claude Code and Codex marketplace installs carry exactly the plugin.**

## Performance

- **Duration:** about 6 min from the first write (context reading before that)
- **Started:** 2026-10-18T11:11:05Z
- **Completed:** 2026-10-18T11:16:48Z
- **Tasks:** 2
- **Files modified:** 6 (all created)

## Accomplishments

- `plugin/skills/evidence-pack/SKILL.md` (99 lines, frontmatter `name`, `description`, `license: MIT`) has eight sections: what this version does (later stages arrive later), rules, running the CLI, first-time setup, setting up a case folder, taking stock, reading INDEX.md and exit codes.
  - It points the agent at `../../AGENTS.md`, or at `references/plugin-rules.md` in a Codex copy.
  - It launches through `${CLAUDE_SKILL_DIR}/scripts/epb.py`, or the `scripts/epb.py` beside the skill on other hosts, then through `data.environment.launch` once setup has run.
  - It asks the user only for the title, then proposes slug, prefix (EVD-ACM-001 style) and timezone in one line, and always passes `--timezone`.
  - It forbids sudo, editing `.epb/` or `inputs/`, names on the command line and import claims. On exit 4 or `STATE_INVALID` the agent stops and reports.
- `test_skill_lint.py` enforces the Agent Skills format for every `plugin/skills/*/SKILL.md`: the six portable keys only, a kebab name equal to the folder, a description of at most 1,024 characters, compatibility of at most 500 and at most 150 lines. It also checks that the router covers the Phase 1 scope.
- `test_host_install.py` uses real installs in throwaway config folders: `claude plugin marketplace add` + `install`, and `codex plugin marketplace add` + `add`. Both caches hold the skill, `epb.py`, `state.schema.json`, `AGENTS.md`, `requirements.txt` and `security-exceptions.json`, and no repo-only folder. Both ran on this machine (claude 2.1.302, codex 0.154.0); neither skipped.
- `references/workspace-contract.md` covers:
  - all 23 `CONTRACT_PATHS` with their sharing class;
  - the rules, the A2 ignore list, `* -text` and the IDs (`S004v2`, `S1000`, runs `001`);
  - the scan rules: content wins, restored older versions count as new content, duplicates, removals, sidecar names, junk patterns and the two-spellings error;
  - `parents`, the chunk split, `schema_version` with `pre-upgrade/` copies, the lock and journals, and the exit 4 codes.
- `references/evidence-pack-v2.md` carries the provenance line "Checked against the ProbeMatrix importer on 2026-10-17". It also covers:
  - the sheet order and the 10-row metadata layout;
  - all 30 headers with their widths;
  - the list columns and the `, ` separator;
  - every enum and the custody entry shape;
  - the importer behaviours: appended rows with no dedup, `-IMP1`, replaced Evidence ID, and normalisation versus raw storage;
  - all 23 validator finding codes, each with a one-line meaning.
- `test_references.py` (191 tests) imports `epb.workspace`, the format module, `scan` and `sidecars`, and extracts the finding codes from `validate.py`, so any drift between code and docs fails.

## Task Commits

1. **Task 1: Tracer, router skill, lint and isolated host installs**
   - `d1984be` (test, RED): failing lint and host-install tests
   - `bc50455` (feat, GREEN): SKILL.md
2. **Task 2: Workspace-contract and evidence-pack-v2 references**
   - `bfcca8b` (test, RED): failing reference tests
   - `89c3bdb` (feat, GREEN): both references

No refactor commits; none were needed.

## TDD Gate Compliance

- **Task 1:** RED `d1984be`, then GREEN `bc50455`. Before SKILL.md existed, both host installs already succeeded and failed only on the missing `skills/evidence-pack/SKILL.md`. The lint tests failed on the missing file. The parametrised lint tests collected an empty set, as expected.
- **Task 2:** RED `bfcca8b`, then GREEN `89c3bdb`.
  - Evidence: `pytest tests/packaging/test_references.py --junitxml` exited 1, with 191 tests, 190 failed and 1 passed. `gsd-tools check tdd-red-evidence` returned `RED_EVIDENCE_OK` (`target_test_failed`) for target `tests.packaging.test_references#test_both_references_exist`.
  - Semantic assessment: the module imported and collected, and `test_validator_has_finding_codes` passed, which shows the AST extraction works. The target failed on its planned assertion "references/workspace-contract.md is missing", not on a collection or import fault.
- **Tracer feedback gate (Task 1):** the run was interactive, in `end-of-phase` mode, with an automated-only `<verify>`. That verify was re-run end to end (35 passed, host tests not skipped) before Task 2 started.

## Files Created/Modified

- `plugin/skills/evidence-pack/SKILL.md`: the router skill, Phase 1 scope.
- `plugin/skills/evidence-pack/references/workspace-contract.md`: every case-folder path, its class and the workspace rules.
- `plugin/skills/evidence-pack/references/evidence-pack-v2.md`: the importer-exact workbook format and the validator codes.
- `tests/packaging/test_skill_lint.py`: Agent Skills lint plus router scope phrases.
- `tests/packaging/test_references.py`: keeps both references in step with the code.
- `tests/packaging/test_host_install.py`: opt-in isolated Claude Code and Codex installs.

## Decisions Made

See `key-decisions` in the frontmatter. In short:

- Finding codes are read from `validate.py` by AST.
- The Codex install test checks the full file list.
- `init` always gets `--timezone`.
- The two carry-over sentences from 01-13 are in the contract.

## Deviations from Plan

None. The plan executed as written. Two small strengthenings within the plan's own files:

- The Codex test checks the full expected file list, not only SKILL.md.
- `test_references.py` also checks junk patterns, sidecar suffixes, the classification legend, header widths and the attachment headers.

## Issues Encountered

- A PreToolUse hook blocked an `rm -rf` of a scratchpad probe folder. The manual install probe was rerun in a fresh scratchpad folder instead. Nothing in the repo or the real home was touched; every install used a throwaway `HOME`, `CLAUDE_CONFIG_DIR` and `CODEX_HOME`.
- Codex warns that it cannot create PATH helper binaries under a temporary directory. This is harmless, and the install succeeds.

## Carry-over notes (outside this plan's files)

- **01-14 note, not fixed:** `epb status` still counts removed sources in "waiting for conversion" (`commands/status.py`), because a removed source keeps `status: pending`. It is a one-line fix in a file this plan does not own. SKILL.md and the contract describe INDEX.md, which already shows removed inputs as "removed from folder".
- **`.epb/lock`:** whether git should ignore it is still an open owner decision, and the ignore list was not changed. The contract only states the fact that every mutating command rewrites its content.

## User Setup Required

None. No external service configuration required.

## Next Phase Readiness

- 01-16 (manual, README, AGENTS/CLAUDE) can quote SKILL.md's flow and both references.
- The owner runs the plan's numbered human-check UAT (install from a local-path marketplace, set up a case folder by asking the agent) at phase verification. The agent never claims the result.
- Later phases extend SKILL.md in place; the lint keeps it within 150 lines.

---
*Phase: 01-foundations*
*Completed: 2026-10-18*
