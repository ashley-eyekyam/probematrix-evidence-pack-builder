---
phase: 01-foundations
plan: 17
subsystem: testing
tags: [ci, encoding, pytest, filterwarnings, launcher, gap-closure]

requires:
  - phase: 01-foundations
    provides: ci.yml with job-wide PYTHONWARNDEFAULTENCODING=1 and pyproject error::EncodingWarning (plan 01-05)
provides:
  - launcher interpreter probe decodes child output as UTF-8 (errors="replace")
  - AST guard that every text-mode subprocess call names an encoding
  - pytest filter that ignores EncodingWarning only from openpyxl.worksheet._writer, with guards on the filter list
  - documented full check identical to CI (PYTHONWARNDEFAULTENCODING=1 on the pytest leg) plus a drift test
  - hermetic gitcheck "outside a repository" test (skips when a .git sits above the temp folder)
affects: [01-18, 01-19, 01-20, 01-21, 01-22]

actuals:
  tokens: 2800
  tasks: 3
  commits: 6
plan_head_before: 2614803c5b12485be6457f2ee319a65f44e7c1a0
plan_head_after: f8237df44dd23fb9206a9db425179b9e017e5921

tech-stack:
  added: []
  patterns:
    - "Text-mode subprocess calls always pass encoding='utf-8', errors='replace' (now enforced by an AST test)"
    - "Third-party EncodingWarnings are ignored per module in pyproject filterwarnings, never globally"

key-files:
  created:
    - tests/repo/test_text_subprocess_encoding.py
  modified:
    - plugin/skills/evidence-pack/scripts/epb/launcher.py
    - pyproject.toml
    - tests/repo/test_ci_workflow.py
    - tests/doctor/test_gitcheck.py
    - AGENTS.md
    - CLAUDE.md
    - .planning/phases/01-foundations/01-VALIDATION.md

key-decisions:
  - "openpyxl EncodingWarning handled by a pyproject.toml ignore entry scoped to module openpyxl\\.worksheet\\._writer (message-matched), not catch_warnings in writer._save; product code untouched"
  - "The filter guard treats any non-error action on EncodingWarning (not only ignore) as relaxing, and requires each to be an ignore scoped to openpyxl"
  - "Local/CI parity is by documentation plus a drift test (test_documented_full_check_matches_ci), not a conftest hook"

patterns-established:
  - "Run the full check as: ruff check, ruff format --check, PYTHONWARNDEFAULTENCODING=1 pytest -q"

requirements-completed: [PKG-09, TST-01, PKG-11]

coverage:
  - id: D1
    description: "Launcher _probe passes encoding='utf-8', errors='replace'; launcher tests pass under PYTHONWARNDEFAULTENCODING=1 and the module still parses as Python 3.6"
    requirement: PKG-09
    verification:
      - kind: unit
        ref: "PYTHONWARNDEFAULTENCODING=1 .venv/bin/python -m pytest -q tests/launcher/test_launcher.py"
        status: pass
    human_judgment: false
  - id: D2
    description: "AST guard: text-mode subprocess calls in plugin/, tools/ and tests/ must name an encoding"
    requirement: TST-01
    verification:
      - kind: unit
        ref: "tests/repo/test_text_subprocess_encoding.py#test_text_mode_subprocess_calls_name_an_encoding"
        status: pass
    human_judgment: false
  - id: D3
    description: "pyproject filterwarnings keeps error::EncodingWarning and ignores it only from openpyxl.worksheet._writer; guards fail on any broader relaxation"
    requirement: TST-01
    verification:
      - kind: unit
        ref: "tests/repo/test_ci_workflow.py#test_encoding_warnings_stay_errors_for_project_code"
        status: pass
      - kind: unit
        ref: "tests/repo/test_ci_workflow.py#test_openpyxl_ignore_comes_after_the_error_entry"
        status: pass
    human_judgment: false
  - id: D4
    description: "AGENTS.md/CLAUDE.md full check carries PYTHONWARNDEFAULTENCODING=1 and matches ci.yml; mirror stays byte-identical"
    requirement: PKG-11
    verification:
      - kind: unit
        ref: "tests/repo/test_ci_workflow.py#test_documented_full_check_matches_ci"
        status: pass
      - kind: unit
        ref: "tests/repo/test_instructions_mirror.py"
        status: pass
    human_judgment: false
  - id: D5
    description: "Whole suite green under the CI encoding variable and without it"
    requirement: TST-01
    verification:
      - kind: integration
        ref: ".venv/bin/ruff check . && .venv/bin/ruff format --check . && PYTHONWARNDEFAULTENCODING=1 .venv/bin/python -m pytest -q"
        status: pass
      - kind: integration
        ref: ".venv/bin/python -m pytest -q"
        status: pass
    human_judgment: false

duration: 15min
completed: 2026-10-18
status: complete
---

# Phase 1 Plan 17: CI encoding gap closure Summary

**The suite now passes in the same environment as the CI Tests step (`PYTHONWARNDEFAULTENCODING=1`, warnings as errors). The launcher probe decodes as UTF-8, one pyproject filter ignores only openpyxl's temp-file warning, and three guard tests plus the documented full check keep local runs identical to CI.**

## Performance

- **Duration:** about 15 min
- **Started:** 2026-10-18T15:09Z
- **Completed:** 2026-10-18T15:24Z
- **Tasks:** 3
- **Files modified:** 8 (1 created, 7 modified)

## Accomplishments

- Before (with the variable): 87 failed, 1173 passed, 3 skipped, 2 errors. The failing file set was test_validator (57), test_writer (23), test_contract (3), test_launcher (3) and test_gitcheck (1), plus 2 errors in test_smoke_pack. This matches the plan's grounding exactly.
- After: **1265 passed, 4 skipped** with the variable and also without it. The 4 skips are the gitcheck test (`/tmp/.git` exists on this machine), one network test and two host-CLI tests.
- `epb.launcher._probe` now passes `encoding="utf-8", errors="replace"` and keeps `universal_newlines=True`, so `test_parses_as_python_36` still passes.
- `pyproject.toml` has one added filter: `ignore:'encoding' argument not specified:EncodingWarning:openpyxl\.worksheet\._writer`, placed after `error::EncodingWarning`. A scratch probe confirmed that a bare `open(..., "w")` in non-openpyxl code still raises EncodingWarning under the variable.
- `AGENTS.md`, `CLAUDE.md` and `01-VALIDATION.md` now give the CI-equivalent full check. `test_documented_full_check_matches_ci` fails if the documented check and `ci.yml` drift apart.

## Task Commits

1. **Task 1 (tracer): launcher probe and the text-mode subprocess guard**
   - RED `1116f2e` (test): `test_text_mode_subprocess_calls_name_an_encoding` fails naming `plugin/skills/evidence-pack/scripts/epb/launcher.py:217`. Under the variable, `test_find_python_posix_order`, `test_find_python_windows_py_launcher` and `test_find_python_none` fail with `EncodingWarning: 'encoding' argument not specified.`
   - GREEN `5b6fc48` (fix): with the variable, the guard and the launcher tests give 29 passed, and `-k find_python` gives 3 passed. Tracer gate: the `<verify>` is automated-only and the mode is end-of-phase, so I re-ran it, it passed, and I carried on.
2. **Task 2: openpyxl-scoped filter and the filter-list guards**
   - RED `bf2b916` (test): both new tests fail on their planned assertions ("expected the openpyxl temp-file ignore entry" and "no EncodingWarning ignore entry for openpyxl"). With the variable, `tests/formats` plus `tests/tools/test_smoke_pack.py` gave 83 failed, 94 passed, 2 errors.
   - GREEN `7d7849c` (fix): the same set gives 197 passed. The commit's stat lists only `pyproject.toml`.
3. **Task 3: local/CI parity, drift guard and hermetic git-walk test**
   - RED `dc1c090` (test): `test_documented_full_check_matches_ci` fails because the AGENTS.md full-check line has no variable.
   - GREEN `f8237df` (fix): updated the docs and made the gitcheck test skip. The full CI-equivalent check exits 0 and `cmp AGENTS.md CLAUDE.md` exits 0.

**RED semantic assessment:** In each RED, the named target test ran and failed on the assertion for the planned behaviour. There were no collection, import or fixture errors. The plan is task-level TDD in pytest console format, which the `tdd-red-evidence` classifier does not parse, so the evidence is the recorded runs above.

## Files Created/Modified

- `tests/repo/test_text_subprocess_encoding.py`: AST guard over plugin/, tools/ and tests/
- `plugin/skills/evidence-pack/scripts/epb/launcher.py`: `_probe` names its encoding and errors handler
- `pyproject.toml`: openpyxl-scoped EncodingWarning ignore, with a one-line rationale comment
- `tests/repo/test_ci_workflow.py`: `test_encoding_warnings_stay_errors_for_project_code`, `test_openpyxl_ignore_comes_after_the_error_entry` and `test_documented_full_check_matches_ci`
- `tests/doctor/test_gitcheck.py`: `test_no_git_binary_outside_a_repository` skips, naming the folder, when a `.git` entry sits above tmp_path
- `AGENTS.md` / `CLAUDE.md`: the full check runs pytest with `PYTHONWARNDEFAULTENCODING=1`. The files stay byte-identical at 43 lines.
- `.planning/phases/01-foundations/01-VALIDATION.md`: the "Full suite command" cell matches AGENTS.md

## Decisions Made

- I chose the pyproject.toml filter route the plan allowed. `epb/formats/writer.py` and `ci.yml` are unchanged.
- The filter guard is a little stricter than the plan's wording. It treats any non-`error` action on EncodingWarning (`ignore`, `default`, `always` and so on) as relaxing the error, and each such entry must be an `ignore` scoped to an openpyxl module. This closes the loophole where a `default::EncodingWarning` entry would get past an ignore-only check.

## Deviations from Plan

None. The plan was executed as written. One procedural note: the per-plan commit ledger went to the session scratchpad instead of the worktree's git dir, because the sandbox refused the compound git command. The measured count (`git rev-list --count 2614803..HEAD` = 6) uses the same base.

## Issues Encountered

- `/tmp/.git` (an empty folder outside the repo, not created by this plan) is still present and untouched. Because of it, the gitcheck test skips on this machine. I checked the assert path separately with `--basetemp=/var/tmp/...`, which has no `.git` above it, and it passed. The owner may want to delete `/tmp/.git`.
- Only Python 3.14 was exercised locally. The 3.11 leg is proven only by the GitHub run in plan 01-22.

## User Setup Required

None. No external service configuration is required.

## Next Phase Readiness

- Plans 01-18 to 01-21 can verify under the exact CI environment by using the documented full check.
- Plan 01-22 (owner-approved push) still has to observe the real GitHub run.

---
*Phase: 01-foundations*
*Completed: 2026-10-18*
