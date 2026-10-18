---
phase: 01-foundations
plan: 22
subsystem: infra
tags: [ci, github-actions, licence-check, push, gap-closure]

requires:
  - phase: 01-foundations
    provides: "plans 01-17 to 01-21 merged on phase-01-foundations (CI workflow, PYTHONWARNDEFAULTENCODING, licence and dependency-age tools)"
provides:
  - "phase-01-foundations pushed to origin (fast-forward a24d0d4..8c84d0d, 161 commits) after the owner answered push"
  - "the real GitHub ci result for HEAD 8c84d0d: core (3.14) success, core (3.11) failure at the Licence allow-list step"
  - "diagnosis for the follow-up gap plan: setuptools 79.0.1 preinstalled on the Python 3.11 runner has no usable licence metadata"
affects: [01-foundations verification, gap 1 / truth 21, PKG-11, ROADMAP SC5]

actuals:
  tokens: 0
  tasks: 3
  commits: 0
plan_head_before: 8c84d0d353f9b1711a4989e0896972887639f02e
plan_head_after: 8c84d0d353f9b1711a4989e0896972887639f02e

tech-stack:
  added: []
  patterns:
    - "Select CI runs by workflow name or by commit, never by workflow file name, while ci.yml is absent from main"

key-files:
  created: []
  modified: []

key-decisions:
  - "Owner chose push at the blocking checkpoint; pushed as a plain fast-forward (no force)"
  - "CI run failed on core (3.11); recorded the failure and stopped as the plan requires; no fix and no new push in this plan"

patterns-established:
  - "gh run list --workflow ci.yml returns HTTP 404 until ci.yml exists on the default branch; use --workflow ci or --commit <sha>"

requirements-completed: []

coverage:
  - id: D1
    description: "Local CI-equivalent run on the merged branch passes (ruff check, ruff format --check, pytest under PYTHONWARNDEFAULTENCODING=1, licence check, AGENTS.md/CLAUDE.md identical) and nothing unpublishable is tracked"
    requirement: TST-01
    verification:
      - kind: other
        ref: ".venv/bin/ruff check . && .venv/bin/ruff format --check . && PYTHONWARNDEFAULTENCODING=1 .venv/bin/python -m pytest -q && .venv/bin/python tools/check_licences.py && cmp AGENTS.md CLAUDE.md"
        status: pass
      - kind: other
        ref: "test -z \"$(git ls-files scratch)\" && test \"$(git ls-files '*.xlsx')\" = docs/reference/hazira-2020/prototype-evidence-pack-hazira-2020.xlsx"
        status: pass
    human_judgment: false
  - id: D2
    description: "GitHub ci run for the pushed HEAD concludes success on both core legs (Python 3.11 and 3.14)"
    requirement: PKG-11
    verification:
      - kind: other
        ref: "gh run view 39141925712 --json conclusion,jobs (https://github.com/ashley-eyekyam/probematrix-evidence-pack-builder/actions/runs/39141925712)"
        status: fail
    human_judgment: true
    rationale: "Run concluded failure (core (3.11), Licence allow-list); the owner also confirms the result on the Actions page (end-of-phase human-check)"

duration: 3min (Task 3; Tasks 1-2 ran in the earlier agent)
completed: 2026-10-18
status: halted
---

# Phase 1 Plan 22: Push and GitHub CI Read-back Summary

**Pushed phase-01-foundations to origin after the owner approved. The ci run for HEAD 8c84d0d failed: core (3.14) is fully green, but core (3.11) fails the licence allow-list because setuptools 79.0.1, preinstalled on the 3.11 runner, has no usable licence metadata. Gap 1 (truth 21) stays open.**

## Performance

- **Duration:** about 3 min for Task 3 (push at 2026-10-18T15:45:27Z, run finished about 15:47Z). Tasks 1 and 2 ran in the earlier agent.
- **Started (Task 3):** 2026-10-18T15:45:27Z
- **Completed:** 2026-10-18T15:47:55Z
- **Tasks:** 3 of 3 executed. Task 3's verify fails, so the plan is halted, not complete.
- **Files modified:** 0 (no source changes; this SUMMARY is the only new file)

## Accomplishments

- **Task 1, the local tracer, passed.** This ran on the main checkout, branch phase-01-foundations, and the root-pin guard and precondition both passed. HEAD was 8c84d0d353f9b1711a4989e0896972887639f02e, 161 commits ahead of origin and 0 behind (121 at planning time; later merge and tracking commits added the rest). Results on local Python 3.14.4:
  - ruff check passed.
  - ruff format --check passed (98 files).
  - `PYTHONWARNDEFAULTENCODING=1 pytest -q`: 1977 passed, 4 skipped. A re-run gave 1978 passed, 3 skipped, because /tmp/.git had disappeared by then and test_no_git_binary_outside_a_repository ran and passed.
  - check_licences.py passed (35 distributions).
  - `cmp AGENTS.md CLAUDE.md`: identical.
  - The dependency-age check passed locally ("35 installed distributions, all at least 14 days old or reviewed exceptions").
  - `git ls-files scratch` printed nothing. The only tracked .xlsx is `docs/reference/hazira-2020/prototype-evidence-pack-hazira-2020.xlsx`.
  - `gh auth status`: logged in as the repository owner.
- **Task 2, the owner decision:** the owner chose **push** ("Push now (Recommended)") at the blocking-human checkpoint.
- **Task 3 pushed the branch and read back CI.** `git push origin phase-01-foundations` was a plain fast-forward, `a24d0d4..8c84d0d`. No force or force-with-lease was used. After the push the branch was level with origin. The run's results are below.

## CI Run (the authoritative result)

- **Run:** https://github.com/ashley-eyekyam/probematrix-evidence-pack-builder/actions/runs/39141925712 (databaseId 39141925712, workflow `ci`, event push)
- **Head SHA:** 8c84d0d353f9b1711a4989e0896972887639f02e, which equals local HEAD at push time
- **Run conclusion:** **failure**

| Job | Conclusion | Lint | Format | Tests | Dependency age (PKG-09) | Licence allow-list (D-12) | Plugin manifests (D-02) |
|-----|------------|------|--------|-------|-------------------------|---------------------------|-------------------------|
| core (3.11) | **failure** | pass | pass | pass: 1977 passed, 4 skipped | pass: 36 distributions | **FAIL** | skipped (did not run after the failure) |
| core (3.14) | success | pass | pass | pass: 1977 passed, 4 skipped | pass: 35 distributions | pass: all 35 allowed | pass: "claude CLI not installed; skipping plugin validate (D-02)" |

**Failing step:** core (3.11), "Licence allow-list (D-12)", `python tools/check_licences.py` on Python 3.11.17. Excerpt from `gh run view 39141925712 --log-failed`:

```
VIOLATION setuptools 79.0.1: licence unknown (no usable licence metadata; from none)
1 of 36 distributions failed the licence check.
##[error]Process completed with exit code 1.
```

**Diagnosis for the follow-up gap plan (not fixed here):**

- The 3.11 leg checks 36 distributions and the 3.14 leg checks 35. The extra one is `setuptools 79.0.1`. It is not in the dev set: the GitHub Python 3.11 toolcache preinstalls it, and 3.12 and later toolcaches do not ship setuptools. That is why the local 3.14 venv and the 3.14 leg never saw it.
- `tools/check_licences.py` looks for `License-Expression` (PEP 639), then `License`, then `License ::` classifiers. For this installed copy it found none of them (source "none").
- Candidate fixes are for the next plan to decide; none is made here:
  - Add a reviewed licence override for setuptools (it is MIT).
  - Exclude bootstrap tooling the runner preinstalls (pip, setuptools) from the check.
  - Remove or upgrade setuptools in the 3.11 job before the check.
- Separately, the local run cannot reproduce this, because the dev venv is Python 3.14. This is the TST-01 edge the plan anticipated: only the GitHub run shows the 3.11 leg.

## Task Commits

No task commits. Task 1 only read and ran checks, Task 2 was a decision, and Task 3 pushed and read CI.

**Plan metadata:** this SUMMARY's own commit (docs).

## Files Created/Modified

- `.planning/phases/01-foundations/01-22-SUMMARY.md`: this summary. No source files changed.

## Decisions Made

- I pushed only after the owner answered "push", as a fast-forward with no force (T-01-58).
- I read the verdict with gh from the run whose headSha equals local HEAD, not from local results (T-01-57). That verdict is failure, and it is reported as failure.
- As the plan instructs, I stopped at the failure: no code fix and no second push.

## Deviations from Plan

**1. [Rule 3 - Blocking] Selected the CI run by workflow name instead of file name**
- **Found during:** Task 3
- **Issue:** The plan's command `gh run list --branch phase-01-foundations --workflow ci.yml ...` returns `HTTP 404 Not Found (.../actions/workflows/ci.yml)`. `ci.yml` is not on `origin/main` yet, so GitHub cannot resolve the workflow by its file name.
- **Fix:** I used `gh run list --branch phase-01-foundations` and `gh run list --commit <HEAD>`. Both return the single `ci` run, 39141925712, with headSha 8c84d0d. The plan's verify command needs the same substitution, `--workflow ci`, until ci.yml reaches main.
- **Files modified:** none
- **Verification:** `gh workflow list --all` shows `ci active 388557553`, and the run's headSha matches HEAD.

**Total deviations:** 1, a blocking query substitution with no code change.
**Impact on plan:** None on the outcome. The run was identified unambiguously.

## Issues Encountered

- **Task 3's verify fails.** The run's conclusion is `failure`, not `success`. Truth 21 (both core jobs green) and the plan's success criterion (gap 1 closed) are **not met**. PKG-09 and TST-01 pass on both legs. The CI leg of PKG-11 (the licence allow-list) passes on 3.14 and fails on 3.11. I marked no requirement complete.
- **Acceptance check "level with origin":** this held right after the push. Committing this SUMMARY leaves the branch **1 commit ahead of origin**. As instructed, I did not push again; the orchestrator handles any further push.
- **Broken-windows ledger:** `.planning/WINDOWS.md` does not exist, so I did not append to it (the ledger is optional).

## Owner Check (end-of-phase, per human_verify_mode)

Owner CI check (ROADMAP SC5; PKG-09, TST-01, PKG-11):

1. Open https://github.com/ashley-eyekyam/probematrix-evidence-pack-builder/actions/runs/39141925712. This is the newest run of workflow "ci" for branch phase-01-foundations, at commit 8c84d0d.
2. Expected right now: "core (3.14)" is green. "core (3.11)" is red at the step "Licence allow-list (D-12)", and its log shows `VIOLATION setuptools 79.0.1: licence unknown (no usable licence metadata; from none)`.
3. The check **passes** only when both "core (3.11)" and "core (3.14)" are green on Lint, Format check, Tests, "Dependency age, two-week rule (PKG-09)" and "Licence allow-list (D-12)", and "Plugin manifests (D-02)" prints "claude CLI not installed; skipping plugin validate (D-02)". That needs a follow-up gap plan for the 3.11 licence failure and a new owner-approved push.

## User Setup Required

None. No external service configuration is required.

## Next Phase Readiness

- **Blocker:** Phase 1 cannot be marked complete. Gap 1 / truth 21 stays open until a new gap plan makes the 3.11 licence check pass (see the diagnosis above) and a new owner-approved push gives a green run on both legs.
- Everything else CI checks is green on both Python versions: lint, format, 1977 tests under PYTHONWARNDEFAULTENCODING=1, and the dependency-age rule.

---
*Phase: 01-foundations*
*Completed: 2026-10-18 (halted at the CI failure)*

## Self-Check: PASSED

- FOUND: .planning/phases/01-foundations/01-22-SUMMARY.md
- FOUND: origin/phase-01-foundations at 8c84d0d353f9b1711a4989e0896972887639f02e (push landed)
- FOUND: run 39141925712 for headSha 8c84d0d (conclusion failure, recorded above)
- No task commits to verify (read-only plan)
