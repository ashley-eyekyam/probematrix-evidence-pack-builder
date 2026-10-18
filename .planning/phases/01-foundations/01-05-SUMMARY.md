---
phase: 01-foundations
plan: 05
subsystem: infra
tags: [ci, github-actions, supply-chain, licences, spdx, pypi, pytest]

requires:
  - phase: 01-foundations (plan 01-01)
    provides: "requirements-dev.txt, pyproject.toml pytest/ruff config, tests/conftest.py guards, the dev .venv"
provides:
  - ".github/workflows/ci.yml: Linux core CI (ubuntu-24.04, Python 3.11 and 3.14) with every SC5 step"
  - "tools/check_licences.py + tools/licence-allowlist.json: SPDX-aware licence allow-list check over every installed distribution (D-12)"
  - "tools/check_dependency_age.py: two-week PyPI upload-age check with reviewed exceptions, STALE warnings and --pins (PKG-09)"
  - "plugin/security-exceptions.json: the one reviewed exceptions file shared by CI and doctor --setup (D-18), shipped empty"
  - "tests/repo/: meta-tests for the no-network guard, the AGENTS.md/CLAUDE.md mirror (PKG-11) and the workflow shape"
affects: [01-10, 01-16]

plan_head_before: 1f380881546ba63a6d29e1d07df506794e90ea44
plan_head_after: a5532c643431eed6e728b6cebdda60bc059331b3
actuals:
  tokens: 13000
  tasks: 3
  commits: 5

tech-stack:
  added: []
  patterns:
    - "Repo tools under tools/ are stdlib-only scripts with pure decision functions; tests import them directly (tools/ is on the pytest pythonpath) and feed canned data"
    - "Network-using tools expose a monkeypatchable fetch seam (fetch_upload_time, installed_distributions); pytest never reaches PyPI because the conftest socket guard refuses it"
    - "Tool output lines start with a fixed prefix (VIOLATION, STALE, EXEMPT, EXCEPTION, ERROR) and are sorted by PEP 503 normalised name"

key-files:
  created:
    - .github/workflows/ci.yml
    - tools/check_licences.py
    - tools/licence-allowlist.json
    - tools/check_dependency_age.py
    - plugin/security-exceptions.json
    - tests/tools/test_dependency_checks.py
    - tests/repo/test_no_network.py
    - tests/repo/test_instructions_mirror.py
    - tests/repo/test_ci_workflow.py
  modified: []

key-decisions:
  - "Licence check: a License field is used only when it is a known alias or parses as an SPDX expression with no placeholder id (UNKNOWN/NONE/NOASSERTION); free text falls through to classifiers"
  - "Licence check: unmapped License classifiers are ignored when another classifier maps, and reported as 'licence unknown' when none maps"
  - "Dependency age: any PyPI lookup that still fails after one retry exits 2 (age unknown), not only a total outage; a 404 means 'not on PyPI' and is a violation"
  - "Dependency age: exceptions that are not installed are still looked up so STALE entries are reported"
  - "The allow-list maps free-text aliases such as PSFL and MIT License; pypdfium2 is the only reviewed override the dev set needs"

patterns-established:
  - "check_* tools exit 0 clean, 1 on findings, 2 when their own config file or data source is unusable"
  - "TDD RED for a not-yet-existing tool commits an inert interface skeleton with the tests, so RED fails on assertions instead of an import error"

requirements-completed: [PKG-09, PKG-11, TST-01]

coverage:
  - id: D1
    description: "Linux CI workflow: push/pull_request, ubuntu-24.04, Python 3.11 and 3.14, pip>=26.1, dev install with --uploaded-prior-to P14D, exception pins, ruff check, ruff format --check, pytest, dependency age, licences, and claude plugin validate guarded by command -v claude (D-02)"
    requirement: TST-01
    verification:
      - kind: unit
        ref: "tests/repo/test_ci_workflow.py#test_core_job_runs_python_3_11_and_3_14_on_ubuntu"
        status: pass
      - kind: unit
        ref: "tests/repo/test_ci_workflow.py#test_has_step"
        status: pass
      - kind: unit
        ref: "tests/repo/test_ci_workflow.py#test_steps_run_in_the_agreed_order"
        status: pass
      - kind: unit
        ref: "tests/repo/test_ci_workflow.py#test_plugin_validate_is_guarded_by_the_claude_cli"
        status: pass
    human_judgment: true
    rationale: "The workflow has not yet run on GitHub; it runs only once the owner approves pushing the branch (plan 01-16). The tests prove its shape, not that the GitHub run is green."
  - id: D2
    description: "SPDX-aware licence allow-list check (OR/AND/WITH, PEP 639, aliases, classifiers, reviewed overrides) passing on the real dev environment (D-12)"
    requirement: PKG-09
    verification:
      - kind: unit
        ref: "tests/tools/test_dependency_checks.py#test_allowed_expressions"
        status: pass
      - kind: unit
        ref: "tests/tools/test_dependency_checks.py#test_disallowed_or_malformed_expressions"
        status: pass
      - kind: unit
        ref: "tests/tools/test_dependency_checks.py#test_override_wins_over_every_metadata_field"
        status: pass
      - kind: other
        ref: ".venv/bin/python tools/check_licences.py (exit 0, 35 distributions allowed)"
        status: pass
    human_judgment: false
  - id: D3
    description: "Two-week dependency-age check with reviewed exceptions, STALE warnings, pip exemption, --pins, and exit codes 0/1/2; the shared plugin/security-exceptions.json ships empty (D-18)"
    requirement: PKG-09
    verification:
      - kind: unit
        ref: "tests/tools/test_dependency_checks.py#test_upload_just_under_14_days_is_a_violation"
        status: pass
      - kind: unit
        ref: "tests/tools/test_dependency_checks.py#test_upload_exactly_14_days_ago_passes"
        status: pass
      - kind: unit
        ref: "tests/tools/test_dependency_checks.py#test_exception_now_old_enough_is_stale_not_a_failure"
        status: pass
      - kind: unit
        ref: "tests/tools/test_dependency_checks.py#test_main_exits_2_on_unusable_exceptions_file"
        status: pass
      - kind: other
        ref: ".venv/bin/python tools/check_dependency_age.py --pins && .venv/bin/python tools/check_dependency_age.py (both exit 0; live PyPI lookup)"
        status: pass
    human_judgment: false
  - id: D4
    description: "Root AGENTS.md and CLAUDE.md byte-identical and at most 150 lines, with boundary tests for 150/151 lines, missing/empty files, CRLF and trailing newline (PKG-11)"
    requirement: PKG-11
    verification:
      - kind: unit
        ref: "tests/repo/test_instructions_mirror.py#test_root_instruction_files_mirror_each_other"
        status: pass
      - kind: unit
        ref: "tests/repo/test_instructions_mirror.py#test_151_lines_fail"
        status: pass
      - kind: unit
        ref: "tests/repo/test_instructions_mirror.py#test_crlf_versus_lf_fails"
        status: pass
      - kind: unit
        ref: "tests/repo/test_instructions_mirror.py#test_one_changed_byte_in_a_copy_is_reported"
        status: pass
    human_judgment: false
  - id: D5
    description: "Committed proof that the conftest no-network guard and need_tool skip apply in every test (TST-01)"
    requirement: TST-01
    verification:
      - kind: unit
        ref: "tests/repo/test_no_network.py#test_create_connection_is_refused"
        status: pass
      - kind: unit
        ref: "tests/repo/test_no_network.py#test_socket_connect_is_refused"
        status: pass
      - kind: unit
        ref: "tests/repo/test_no_network.py#test_need_tool_skips_a_missing_tool"
        status: pass
    human_judgment: false

duration: 7min
completed: 2026-10-18
status: complete
---

# Phase 1 Plan 05: Supply-Chain Checks and Linux CI Summary

**Linux CI on Python 3.11 and 3.14 that installs under the 14-day upload cutoff, then runs ruff, pytest, an in-house PyPI dependency-age check backed by the shared `plugin/security-exceptions.json`, and an SPDX-aware licence allow-list check. Repo meta-tests guard the no-network rule, the byte-identical AGENTS.md/CLAUDE.md, and the workflow shape.**

## Performance

- **Duration:** about 7 min
- **Started:** 2026-10-18T09:45:13Z
- **Completed:** 2026-10-18T09:52:03Z
- **Tasks:** 3 of 3 (Task 1 tracer, Tasks 2 and 3 TDD)
- **Files modified:** 9 (all created)

## Accomplishments

- `.github/workflows/ci.yml` has a job `core` on `ubuntu-24.04` with matrix `["3.11", "3.14"]`, `fail-fast: false` and `PYTHONWARNDEFAULTENCODING=1`. Its steps run in this order: checkout@v7, setup-python@v7, `pip>=26.1`, the dev install with `--uploaded-prior-to P14D`, the exception pins (installed only when `--pins` prints any), ruff check, ruff format --check, pytest, the dependency-age check, the licence check, and `claude plugin validate` (skipped with a D-02 message when there is no `claude` CLI).
- `tools/check_licences.py` evaluates SPDX expressions with a small recursive-descent parser. `AND` binds tighter than `OR`, `X WITH Y` counts as `X`, identifiers compare case-insensitively, and `LicenseRef-*` is never allowed. It reads the licence from a reviewed override first, then `License-Expression`, then the `License` field, then the classifiers. All 35 installed distributions pass, and pypdfium2 is the only override.
- `tools/check_dependency_age.py` takes the earliest `upload_time_iso_8601` from PyPI's release JSON and applies the 14-day rule with an inclusive boundary: exactly 14 days passes, 13 days 23 hours fails. It honours reviewed exceptions by normalised name and exact version, and reports exceptions that are now old enough as `STALE` without failing the run. pip is exempt. Run live against PyPI, it passed for all 35 installed distributions.
- `plugin/security-exceptions.json` ships with an empty `exceptions` list. Only a human may add an entry, after reviewing an advisory.
- The `tests/repo/` meta-tests are the committed coverage that the 01-01 summary said its fixtures still lacked.

## Task Commits

1. **Task 1 (tracer): CI workflow and licence check.** `d1edfad` (feat)
2. **Task 2: Two-week dependency-age check.** RED `3b17896` (test), GREEN `e0a6c67` (feat). No refactor was needed.
3. **Task 3: Repo meta-tests.** RED `190139f` (test), GREEN `a5532c6` (feat). No refactor was needed.

**Plan metadata:** recorded in the docs commit that adds this SUMMARY.

## Tracer Gate (Task 1)

The run was interactive in `end-of-phase` mode, and the tracer's verify was automated only. The verify was re-run after the commit and passed (49 licence tests passed, and `check_licences.py` exited 0), so expansion went ahead with no checkpoint.

## TDD Gate Compliance

**Task 2**
- **RED:** `3b17896`. Command: `.venv/bin/python -m pytest -q tests/tools/test_dependency_checks.py --junitxml=scratch/tdd/red-01-05-t2.xml`. Result: 31 failed, 52 passed, exit 1. The target `test_upload_just_under_14_days_is_a_violation` failed with `assert [] == [('newpkg', '2.0')]`. `gsd-tools check tdd-red-evidence` returned `RED_EVIDENCE_OK` (`target_test_failed`).
- **Semantic assessment:** the RED commit carried an inert interface skeleton of `tools/check_dependency_age.py` (signatures, `Report`, `Finding`, `PyPIUnavailable`, all returning empty values), so the module imported cleanly. The target ran and failed on the planned assertion because `evaluate()` had no logic yet. The 52 passing tests were the 49 Task 1 licence tests plus 3 that the inert skeleton satisfied by coincidence: exactly 14 days passes, an empty `--pins` prints nothing, and a clean run exits 0.
- **GREEN:** `e0a6c67`, with 83 passed.

**Task 3**
- **RED:** `190139f`. Command: `.venv/bin/python -m pytest -q tests/repo --junitxml=scratch/tdd/red-01-05-t3.xml`. Result: 9 failed, 23 passed, exit 1. The target `test_151_lines_fail` failed on its `any("AGENTS.md has 151 lines" ...)` assertion. `RED_EVIDENCE_OK` (`target_test_failed`).
- **Semantic assessment:** `check_instructions` was a stub returning `[]`, so every boundary test that expects a problem failed on its assertion. The 23 passing tests guard behaviour that already shipped: the conftest network refusal and the `need_tool` skip (01-01), the workflow shape (Tasks 1 and 2), and the valid-input cases where an empty list is the correct answer.
- **GREEN:** `a5532c6`, with 115 passed in `tests/repo` and `tests/tools/test_dependency_checks.py`, and 347 in the full suite.

## Files Created/Modified

- `.github/workflows/ci.yml`: the Linux core CI job (A9, D-02, D-12, D-18).
- `tools/check_licences.py`: the SPDX-aware licence check (`evaluate_expression`, `licence_of`, `check_distributions`, `load_config`, `main`).
- `tools/licence-allowlist.json`: the 8 allowed ids, aliases, the classifier map and the reviewed pypdfium2 override.
- `tools/check_dependency_age.py`: the two-week rule (`normalise`, `load_exceptions`, `evaluate`, `parse_upload_time`, `fetch_upload_time`, `installed_distributions`, `main`, `Report`, `Finding`, `EXEMPT`).
- `plugin/security-exceptions.json`: the empty reviewed-exceptions list shared with `doctor --setup`.
- `tests/tools/test_dependency_checks.py`: 83 tests on canned metadata and upload times, with no network.
- `tests/repo/test_no_network.py`: the socket refusal and the `need_tool` skip.
- `tests/repo/test_instructions_mirror.py`: the `check_instructions` helper and its PKG-11 boundaries.
- `tests/repo/test_ci_workflow.py`: the workflow triggers, matrix, actions, steps and their order.

## Decisions Made

- **The License field must parse to be used.** Free text such as pypdfium2's `BSD-3-Clause, Apache-2.0, dependency licenses`, or a full licence paragraph, falls through to the classifiers. Placeholders such as `UNKNOWN`, which old setuptools releases write, fall through as well, so the 3.11 runner's bundled tools are judged by their classifiers.
- **A single unrecognised word is judged, not skipped.** A word such as `Proprietary` parses as an SPDX id and is reported as not allowed. This errs towards a human review.
- **Partial PyPI failures exit 2.** The plan names exit 2 for "PyPI cannot be reached at all". The tool also exits 2 when any lookup still fails after one retry, because an unknown age is an infrastructure problem, not a violation. A 404 means the release is not on PyPI, which is a violation.
- **The output adds EXEMPT and EXCEPTION lines** next to the planned VIOLATION and STALE lines, so a CI log shows why pip and any excepted release passed.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Test data in the sorting test named the stale entry in lower case**
- **Found during:** Task 2 GREEN
- **Issue:** `test_violations_and_stale_entries_are_sorted_by_normalised_name` expected the stale finding `Gamma`, but the exception entry was written as `gamma`. Stale findings take their name from the exception entry.
- **Fix:** the exception entry is now `Gamma`, so the test still checks case-insensitive ordering.
- **Files modified:** `tests/tools/test_dependency_checks.py`
- **Verification:** 83 passed.
- **Committed in:** `e0a6c67`

**2. [Rule 3 - Blocking] The RED commits include interface skeletons**
- **Found during:** Task 2 RED (and Task 3 RED, for `check_instructions`)
- **Issue:** `tools/check_dependency_age.py` did not exist, so the tests would have failed on import. That is an INVALID_RED load failure under tdd.md.
- **Fix:** the RED commit carried an inert skeleton with the planned signatures and types, all returning empty values, so the RED evidence is a real assertion failure. Task 3's helper was stubbed the same way inside the test module.
- **Files modified:** `tools/check_dependency_age.py`, `tests/repo/test_instructions_mirror.py`
- **Verification:** `RED_EVIDENCE_OK` for both targets.
- **Committed in:** `3b17896`, `190139f`

---

**Total deviations:** 2 auto-fixed (1 bug in test data, 1 blocking TDD-evidence issue).
**Impact on plan:** no scope change. Every planned file, function, option and output prefix exists as specified.

## Issues Encountered

None. The plan's `.venv` symlink step did not apply, because this run used the main checkout, which owns `.venv`.

## User Setup Required

None. The workflow runs on GitHub only after the owner approves pushing the branch (plan 01-16).

## Next Phase Readiness

- Plan 01-10 (`doctor --setup`) should install pins from `plugin/security-exceptions.json` with the same `--pins` semantics: one `package==version` line per entry, with an empty file meaning nothing to install.
- Plan 01-16 pushes the branch. The first GitHub run is the proof for D1. On the 3.11 runner, the licence check will also see that runner's bundled pip and setuptools. The placeholder fallback covers setuptools' `UNKNOWN` License field.
- `tests/repo/test_instructions_mirror.py` fails the moment AGENTS.md and CLAUDE.md drift, or either grows past 150 lines.

## Self-Check: PASSED

- All 9 key files exist on disk.
- Commits `d1edfad`, `3b17896`, `e0a6c67`, `190139f` and `a5532c6` are ancestors of HEAD on `phase-01-foundations`.
- Plan verification: `.venv/bin/python -m pytest -q tests/repo tests/tools/test_dependency_checks.py` (115 passed), `.venv/bin/python tools/check_licences.py` (exit 0) and `.venv/bin/python tools/check_dependency_age.py` (exit 0) all pass. The full suite gives 347 passed, and ruff check and format are clean.
- Acceptance: the workflow contains `python-version: ["3.11", "3.14"]`, `--uploaded-prior-to P14D` and `command -v claude`. The allow-list has exactly the 8 ids. `--pins` prints nothing and exits 0. `plugin/security-exceptions.json` has an empty `exceptions` list.

---
*Phase: 01-foundations*
*Completed: 2026-10-18*
