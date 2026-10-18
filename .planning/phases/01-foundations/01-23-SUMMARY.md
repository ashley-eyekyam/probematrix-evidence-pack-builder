---
phase: 01-foundations
plan: 23
subsystem: infra
tags: [licence-allowlist, ci, setuptools, pkg-09, pkg-11, tdd]

requires:
  - phase: 01-foundations
    provides: "01-22 diagnosis of GitHub run 39141925712 (setuptools 79.0.1 on the 3.11 leg has no usable licence metadata)"
provides:
  - "Reviewed MIT override for setuptools in tools/licence-allowlist.json (owner decision 2026-10-18)"
  - "Six licence tests that reproduce the exact CI failure line and pin the reviewed override set"
  - "Documented full check in AGENTS.md/CLAUDE.md now runs the licence check, kept in step with ci.yml by two parity tests"
affects: [01-26 GitHub run (PKG-09 3.11 leg backstop), 01-foundations verification gap 1 / truth 21]

actuals:
  tokens: 2585
  tasks: 2
  commits: 4
plan_head_before: e8f42e30a59c59e0b765c2c3d75c7bd97a6b8ee9
plan_head_after: 542e274866e8adcb003059117fc3b5ede265a760

tech-stack:
  added: []
  patterns:
    - "A licence override is a reviewed, test-pinned set: adding or removing one means changing test_overrides_are_exactly_the_reviewed_set"
    - "The documented full check and ci.yml are compared step by step and in order (FULL_CHECK_STEPS)"

key-files:
  created: []
  modified:
    - tools/licence-allowlist.json
    - tests/tools/test_dependency_checks.py
    - tests/repo/test_ci_workflow.py
    - AGENTS.md
    - CLAUDE.md

key-decisions:
  - "setuptools gets a reviewed per-package MIT override. There is no bootstrap-exclusion rule, no CI change and no new allowed identifier (owner decision 2026-10-18)"
  - "The dependency-age check stays out of the commit-time full check because it queries PyPI. CI still runs it."

patterns-established:
  - "FULL_CHECK_STEPS in tests/repo/test_ci_workflow.py pairs each documented command with its ci.yml counterpart. Extend it when a step is added to the documented check."

requirements-completed: [PKG-09, PKG-11, TST-01]

coverage:
  - id: D1
    description: "Runner-preinstalled setuptools 79.0.1, which has no licence metadata, passes check_licences.main() with the shipped allow-list through the reviewed MIT override"
    requirement: PKG-09
    verification:
      - kind: unit
        ref: "tests/tools/test_dependency_checks.py#test_main_passes_runner_setuptools_with_the_shipped_allowlist"
        status: pass
      - kind: unit
        ref: "tests/tools/test_dependency_checks.py#test_runner_setuptools_has_the_reviewed_licence"
        status: pass
      - kind: unit
        ref: "tests/tools/test_dependency_checks.py#test_setuptools_override_is_reviewed"
        status: pass
    human_judgment: false
  - id: D2
    description: "Without the override, the same run exits 1 with the exact line from GitHub run 39141925712"
    requirement: PKG-09
    verification:
      - kind: unit
        ref: "tests/tools/test_dependency_checks.py#test_main_reports_runner_setuptools_without_the_override"
        status: pass
    human_judgment: false
  - id: D3
    description: "The overrides are exactly pypdfium2 and setuptools, and no requirements file names setuptools"
    requirement: PKG-09
    verification:
      - kind: unit
        ref: "tests/tools/test_dependency_checks.py#test_overrides_are_exactly_the_reviewed_set"
        status: pass
      - kind: unit
        ref: "tests/tools/test_dependency_checks.py#test_setuptools_is_not_a_project_dependency"
        status: pass
    human_judgment: false
  - id: D4
    description: "The documented full check runs ruff check, ruff format --check, pytest and the licence check in CI's order. AGENTS.md and CLAUDE.md are byte-identical at 43 lines."
    requirement: PKG-11
    verification:
      - kind: unit
        ref: "tests/repo/test_ci_workflow.py#test_documented_full_check_runs_every_local_ci_step"
        status: pass
      - kind: unit
        ref: "tests/repo/test_ci_workflow.py#test_documented_full_check_keeps_ci_order"
        status: pass
      - kind: unit
        ref: "tests/repo/test_instructions_mirror.py#test_root_instruction_files_mirror_each_other"
        status: pass
    human_judgment: false
  - id: D5
    description: "The Python 3.11 CI leg's licence step passes on the GitHub runner"
    requirement: PKG-09
    verification: []
    human_judgment: true
    rationale: "Only the hosted 3.11 toolcache carries setuptools 79.0.1. No local interpreter can show it, so plan 01-26's GitHub run confirms it (backstop truth)."

duration: 3min
completed: 2026-10-18
status: complete
---

# Phase 1 Plan 23: Setuptools Licence Override and Full-Check Parity Summary

**A reviewed MIT override for the setuptools 79.0.1 that the GitHub 3.11 runner preinstalls, proven against the exact CI failure line. The documented full check now ends with `.venv/bin/python tools/check_licences.py`, and parity tests keep it in step with ci.yml.**

## Performance

- **Duration:** about 3 min
- **Started:** 2026-10-18T16:47:15Z
- **Completed:** 2026-10-18T16:50:43Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- `tools/licence-allowlist.json` has a second override: `setuptools`, licence `MIT`, reviewed on 2026-10-18. Its reason says it is not a project dependency, that the 3.11 toolcache preinstalls it, and that 79.0.1 ships no readable licence metadata (run 39141925712).
- Six licence tests, run through `main()`. With the shipped allow-list a metadata-free setuptools 79.0.1 passes ("Licence check passed: all 1 installed distributions are allowed."). Without the override it prints `VIOLATION setuptools 79.0.1: licence unknown (no usable licence metadata; from none)` and exits 1. The override set is pinned, and a guard fails if any of the six requirements files names setuptools.
- The full-check line in AGENTS.md and CLAUDE.md now runs the licence check, and the lead-in reads "the same encoding and licence checks CI runs". `test_documented_full_check_runs_every_local_ci_step` (4 cases) and `test_documented_full_check_keeps_ci_order` fail if the documented check and ci.yml drift apart.

## Task Commits

1. **Task 1 (tracer): the runner's setuptools passes by reviewed override**
   - RED `1716e6f` (test): six tests, four failing
   - GREEN `fe2d4cd` (feat): the setuptools override
2. **Task 2: the documented full check runs the licence check**
   - RED `8cace43` (test): parity tests, two failing
   - GREEN `542e274` (feat): AGENTS.md and CLAUDE.md full-check line

No REFACTOR commits were needed.

## TDD Evidence

- **Task 1 RED:** `.venv/bin/python -m pytest -q tests/tools/test_dependency_checks.py -k "setuptools or reviewed_set"` gave `4 failed, 2 passed`. The four failures:
  - `test_main_passes_runner_setuptools_with_the_shipped_allowlist`: `assert 1 == 0`. `main()` returned 1, the same as the CI failure.
  - `test_setuptools_override_is_reviewed`: `KeyError: 'setuptools'`, because the entry did not exist yet.
  - `test_runner_setuptools_has_the_reviewed_licence`: `(None, 'none') != ('MIT', 'reviewed override')`.
  - `test_overrides_are_exactly_the_reviewed_set`: `['pypdfium2'] != ['pypdfium2', 'setuptools']`.

  `test_main_reports_runner_setuptools_without_the_override` and `test_setuptools_is_not_a_project_dependency` passed in RED, as the plan expected. They describe the state before and around the fix.

  Semantic assessment: each failure was on the planned assertion for the missing override. There were no collection, import or fixture faults.
- **Task 1 GREEN:** the same filter gave `6 passed`. The whole file gave `89 passed`. `tools/check_licences.py` printed "Licence check passed: all 35 installed distributions are allowed."
- **Tracer gate:** the run was interactive, in `end-of-phase` mode, with an automated-only verify. I re-ran the verify, it passed, and I moved on to Task 2.
- **Task 2 RED:** `tests/repo/test_ci_workflow.py` gave `2 failed, 22 passed`. The failures were `test_documented_full_check_runs_every_local_ci_step[licences]` (licence command not in the Full check line) and `test_documented_full_check_keeps_ci_order` (`-1` position for the licence step). The other three parametrized cases already passed.
- **Task 2 GREEN:** the filter `every_local_ci_step or keeps_ci_order` gave `5 passed`. The ci_workflow and instructions_mirror tests together gave `36 passed`.
- `gsd_run check tdd-red-evidence` was not run. Python pytest output has no supported adapter in the classifier, so this RED evidence is the captured pytest summary plus the semantic assessment above.

## Files Created/Modified
- `tools/licence-allowlist.json`: adds the `overrides.setuptools` entry (MIT, reviewed 2026-10-18).
- `tests/tools/test_dependency_checks.py`: adds six setuptools/override tests, the `RUNNER_SETUPTOOLS` and `REQUIREMENT_NAME` constants and `import re`.
- `tests/repo/test_ci_workflow.py`: adds `DOCUMENTED_LICENCES`, `FULL_CHECK_STEPS`, the `_full_check_line()` helper and two parity tests. The existing `test_documented_full_check_matches_ci` is unchanged.
- `AGENTS.md` and `CLAUDE.md`: line 28's full check now ends with the licence check. Both files are byte-identical at 43 lines.

## Decisions Made
- I followed the plan as specified.
- The order test also asserts that ci.yml runs the four counterparts in the same order, so "matching ci.yml's step order" is tested on both sides rather than assumed.

## Deviations from Plan

None. The plan was executed exactly as written.

## Verification

- `.venv/bin/ruff check . && .venv/bin/ruff format --check . && PYTHONWARNDEFAULTENCODING=1 .venv/bin/python -m pytest -q && .venv/bin/python tools/check_licences.py` passed: ruff was clean, 98 files were already formatted, pytest gave 1989 passed and 3 skipped, and the licence check passed for 35 distributions.
- `cmp AGENTS.md CLAUDE.md` exited 0. `wc -l < AGENTS.md` printed 43. `grep -c ".venv/bin/python tools/check_licences.py" AGENTS.md` printed 1. `grep -c "Full check" AGENTS.md` printed 1.
- `git diff --name-only origin/phase-01-foundations -- tools/check_licences.py .github/workflows/ci.yml` printed nothing, so the prohibition held.
- The allow-list probe printed `MIT 2026-10-18 ['pypdfium2', 'setuptools']`.

## Issues Encountered
None.

## User Setup Required
None. No external service configuration is required.

## Next Phase Readiness
- The code half of gap 1 is closed. Only the hosted run in plan 01-26 can confirm the Python 3.11 leg's licence step, because no local interpreter has the 3.11 toolcache's setuptools.
- Review IN-05's second bullet (widening `_relaxed_encoding_entries`) is out of scope and waits for the owner's IN-01 to IN-06 decisions at UAT.

---
*Phase: 01-foundations*
*Completed: 2026-10-18*
