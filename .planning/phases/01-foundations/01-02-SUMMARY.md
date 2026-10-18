---
phase: 01-foundations
plan: 02
subsystem: docs
tags: [design, spec, amendments, requirements, packaging, workspace-contract]

requires:
  - phase: 01-foundations
    provides: "01-CONTEXT.md decisions D-01 to D-20 and 01-RESEARCH.md findings Q7 and Pattern 1"
provides:
  - "Design §20 rows A16 to A30, each citing its D-NN or research reference"
  - "Design §5 tree in the final plugin/ subtree layout (two manifests, split requirements, schemas only under scripts/epb/schemas/, tools/install-codex.py, no root schemas/, samples/ or .agents/skills)"
  - "Design §6 .epb/ tree with .gitignore, .gitattributes, lock, inbox/, tmp/ and ledger/chunks.json"
  - "Design §8.1 parents[] and §8.4 metadata notes in rows 8-10"
  - "REQUIREMENTS.md PKG-08 lists tzdata on Windows only (D-20)"
affects: [01-03, 01-04, 01-05, 01-06, 01-07, 01-08, 01-09, 01-10, 01-11, 01-12, 01-13, 01-14, 01-15, 01-16]

plan_head_before: 7486fa5d7e0cb2b8073a72a8b14e0590cd5bb371
plan_head_after: fbeab4ee311ae8f5100fb547c9a9eba9da8f83fc
actuals:
  tokens: 3135
  tasks: 2
  commits: 2

tech-stack:
  added: []
  patterns:
    - "Phase decisions that change the spec become numbered §20 rows whose first cell cites the D-NN or research reference"
    - "Section text (§5, §6, §8) is updated in the same change as the §20 row, so a reader of any section sees the current rule"

key-files:
  created: []
  modified:
    - docs/design/2026-10-17-evidence-pack-builder-design.md
    - .planning/REQUIREMENTS.md

key-decisions:
  - "The §5 tree keeps CHANGELOG.md, CONTRIBUTING.md and SECURITY.md at the root; the plan removed only schemas/, samples/ and the .agents/skills symlink"
  - "docs/ in §5 now lists USER-MANUAL.md (A14) in place of INSTALL.md and USER-GUIDE.md, matching the name every other Phase 1 plan uses"
  - "A footnote under the §20 table says D-NN numbers refer to 01-CONTEXT.md and Q7 / Pattern 1 to 01-RESEARCH.md, so each citation can be traced"

patterns-established:
  - "Amendment rows: | A<n> (<D-NN or research ref>) | **Short title.** Decision text. | Amended sections |"

requirements-completed: [PKG-08, PKG-01, BLD-08]

coverage:
  - id: D1
    description: "D-20 tzdata carried through design §20 (A28), the §5 requirements comment and REQUIREMENTS.md PKG-08"
    requirement: PKG-08
    verification:
      - kind: other
        ref: "Task 1 <automated> python3 check: A28 (D-20) row, §5 tzdata mention, PKG-08 tzdata text"
        status: pass
    human_judgment: false
  - id: D2
    description: "§20 rows A16 to A30 present, sorted, each citing a D-NN or research reference; A1 to A15 byte-identical to 5aa588b"
    verification:
      - kind: other
        ref: "Task 2 <automated> python3 check (rows 16-30 present)"
        status: pass
      - kind: other
        ref: "git show 5aa588b:docs/design/2026-10-17-evidence-pack-builder-design.md | grep -E '^\\| A([1-9]|1[0-5]) ' | cmp - <(grep -E '^\\| A([1-9]|1[0-5]) ' docs/design/2026-10-17-evidence-pack-builder-design.md)"
        status: pass
    human_judgment: false
  - id: D3
    description: "§5 shows the plugin/ subtree layout and the marketplace file at .claude-plugin/marketplace.json (A30); §6, §8.1 and §8.4 updated"
    requirement: PKG-01
    verification:
      - kind: other
        ref: "Task 2 <automated> python3 check (§5 plugin/, scripts/epb/schemas, install-codex.py, no .agents/skills; §6 inbox/, chunks.json, .gitattributes; §8.1 parents; rows 8–10)"
        status: pass
    human_judgment: false
  - id: D4
    description: "Amendment wording faithfully transcribes the owner's locked decisions D-01 to D-20 (no transcription drift)"
    requirement: BLD-08
    verification: []
    human_judgment: true
    rationale: "The automated checks prove each row and section edit exists, not that its wording matches the owner's intent. A reviewer should read A16 to A30 against 01-CONTEXT.md."

duration: 3min
completed: 2026-10-18
status: complete
---

# Phase 1 Plan 02: Design Amendments for Phase 1 Decisions Summary

**Design §20 now carries amendments A16 to A30 for the Phase 1 owner decisions. §5 shows the final `plugin/` subtree, §6 lists the new `.epb/` paths, §8.1 uses `parents[]` and §8.4 puts the metadata notes in rows 8–10. PKG-08 now lists tzdata on Windows.**

## Performance

- **Duration:** about 3 min
- **Started:** 2026-10-18T09:16:33Z
- **Completed:** 2026-10-18T09:19:13Z
- **Tasks:** 2 of 2 (Task 1 tracer, Task 2 auto)
- **Files modified:** 2

## Accomplishments

- §20 gained 15 rows, A16 to A30, in numeric order. Each row's first cell cites its source: D-01, D-02, D-03, D-05, D-06, D-07, D-08, D-12, D-13, D-14, D-18, D-19 and D-20, research Q7 and research Pattern 1. A1 to A15 are byte-identical to `5aa588b`.
- The §5 tree is now the A4 layout:
  - The root holds `.claude-plugin/marketplace.json` (`source: "./plugin"`), the mirrored `AGENTS.md`/`CLAUDE.md`, `pyproject.toml`, `requirements-dev.txt`, `requirements-dev-full.txt`, `tests/`, `evals/`, `tools/` (with `install-codex.py`, `make-smoke-pack.py` and the two CI checkers) and `docs/USER-MANUAL.md`.
  - `plugin/` holds both manifests, `AGENTS.md`, the core and extras requirement files, `security-exceptions.json` and the seven skills.
  - The schemas live only in `plugin/skills/evidence-pack/scripts/epb/schemas/`.
  - The root `schemas/`, `samples/`, `tools/make-sample.py` and the `.agents/skills` symlink are gone.
- The §6 `.epb/` tree adds `.gitignore` (the A2 list), `.gitattributes`, `lock`, `inbox/`, `tmp/` and `ledger/chunks.json`. It also notes that `state.json` holds per-chunk status with no raw text.
- §8.1 now has `parents[]` (empty for top-level inputs, one entry per carrier). §8.4 now says row 7 is blank and rows 8–10 carry the notes.
- In `REQUIREMENTS.md`, PKG-08 adds "and `tzdata` on Windows only (D-20)", and the footer records the amendment.

## Task Commits

1. **Task 1: Tracer, D-20 tzdata carried through §20, §5 and PKG-08.** `2f93018` (docs). The tracer gate ran in interactive `end-of-phase` mode with an automated-only verify. The verify was re-run, passed, and the plan expanded with no checkpoint.
2. **Task 2: The remaining Phase 1 amendments, plus §5, §6, §8.1 and §8.4.** `fbeab4e` (docs).

## Files Created/Modified

- `docs/design/2026-10-17-evidence-pack-builder-design.md`: §5 tree and its follow-on paragraph, §6 `.epb/` tree, the §8.1 source record, the §8.4 Pack Metadata sentence, §20 rows A16 to A30 and the footnote under the table.
- `.planning/REQUIREMENTS.md`: PKG-08 text and the last-updated footer.

## Decisions Made

- The §5 tree keeps `CHANGELOG.md`, `CONTRIBUTING.md` and `SECURITY.md` at the root. The plan named only `schemas/`, `samples/` and `.agents/skills` for removal, so nothing else was dropped.
- §5 `docs/` lists `USER-MANUAL.md`, as the plan specified. It replaces the old `INSTALL.md` and `USER-GUIDE.md`, and matches the file name used by plans 01-03 to 01-16.
- The §5 comment for `install-codex.py` says the installer copies into "the user's Codex skills folder" and does not name `.agents/skills`. The plan's check forbids that string anywhere in §5. The exact `$HOME/.agents/skills` path is recorded in A16.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] §5 lacked the literal `scripts/epb/schemas` that the Task 2 verify requires**
- **Found during:** Task 2 verification
- **Issue:** The tree nests `schemas/` under `scripts/epb/` on a separate line, so the contiguous string never appeared in §5 and the automated check exited 1.
- **Fix:** Added a paragraph below the tree. It states that the JSON Schemas exist only in `plugin/skills/evidence-pack/scripts/epb/schemas/` (A19) and that Codex installs from the same `plugin/` tree with no symlink (A16).
- **Files modified:** `docs/design/2026-10-17-evidence-pack-builder-design.md`
- **Verification:** Both task verifies pass, and A1 to A15 are still byte-identical.
- **Committed in:** `fbeab4e` (Task 2 commit)

**2. [Rule 2 - Missing Critical] Added a source note for the D-NN citations under the §20 table**
- **Found during:** Task 2 (threat T-01-03, repudiation)
- **Issue:** The existing §20 intro says its OD numbers refer to the research summary, but nothing said where the D-NN and Q7 / Pattern 1 references in the new rows point.
- **Fix:** Added one sentence below the table that names `01-CONTEXT.md` and `01-RESEARCH.md`.
- **Files modified:** `docs/design/2026-10-17-evidence-pack-builder-design.md`
- **Committed in:** `fbeab4e`

---

**Total deviations:** 2 auto-fixed (1 bug, 1 missing critical).
**Impact on plan:** Both are one-paragraph additions to the design, with no scope creep.

## Issues Encountered

- Plan-level check: `git diff --stat 7486fa5..HEAD` lists only the two planned files. Before this plan started, the working tree already had an uncommitted change to `.planning/config.json` and untracked `.planning/state.json` and `.planning/milestone.lock`. They were left alone as instructed and are not part of this plan.
- Out of scope, left as is: the §6 "Rules" bullet still says `.epb/.gitignore` covers only `private/` and `media/`, and §15.3 still mentions `"skills": "./skills"`, `.agents/skills` and `install-codex.sh`. A2, A16 and A17 override these lines under the "§20 wins" rule, and the plan did not ask for them to be rewritten.

## User Setup Required

None. No external service configuration is required.

## Next Phase Readiness

- Later Phase 1 executors reading §5, §6 and §8 now see the final layout, the workspace contract and the source-record shape. The superseded root `schemas/`, the `.agents/skills` symlink and the off-by-one metadata rows are gone from those sections.
- Reviewer action (coverage D4): read A16 to A30 against `01-CONTEXT.md` to confirm the wording matches the owner's intent.

## Self-Check: PASSED

- Both modified files exist, and commits `2f93018` and `fbeab4e` are on `phase-01-foundations` (measured: 2 commits from `7486fa5`).
- Task 1 and Task 2 `<automated>` checks exit 0. The A1 to A15 `cmp` against `5aa588b` passes. `ruff format --check .` passes.

---
*Phase: 01-foundations*
*Completed: 2026-10-18*
