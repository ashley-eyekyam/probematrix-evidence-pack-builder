---
phase: 01-foundations
plan: 06
subsystem: packaging
tags: [plugin, marketplace, claude-code, codex, agents-md, installer, pytest]

requires:
  - phase: 01-foundations (plan 01-03)
    provides: "epb.__version__, epb.launcher.locate_plugin_file and PLUGIN_FILES_DIR (plugin-files/ checked first)"
  - phase: 01-foundations (plan 01-05)
    provides: "plugin/security-exceptions.json, copied by the Codex installer"
provides:
  - ".claude-plugin/marketplace.json: one marketplace for Claude Code and Codex, single entry with source ./plugin"
  - "plugin/.claude-plugin/plugin.json (no skills key, D-02) and plugin/.codex-plugin/plugin.json (skills ./skills/, D-01), names and versions in lockstep with epb.__version__"
  - "plugin/AGENTS.md: host-neutral rules for end users' agents, including the evidence-bank entry rule and the epb CLI rules (PKG-03)"
  - "tools/install-codex.py: stdlib-only cross-platform Codex fallback installer with an .epb-installed ownership marker"
  - "tests/packaging/: manifest parity + claude plugin validate --strict, AGENTS.md content rules, installer behaviour"
affects: [01-15, 01-16, phase-10-PKG-10]

plan_head_before: 2490b590f6ff8423ce14703fbf16cb45faf470ef
plan_head_after: 535fcfe94f7fd3af4e698f8d28987e1478d71825
actuals:
  tokens: 6550
  tasks: 3
  commits: 5

tech-stack:
  added: []
  patterns:
    - "Manifest parity is a test, not a convention: every manifest name equals the marketplace entry and both plugin versions equal epb.__version__"
    - "Installer ownership marker: a tool may replace only folders carrying its own marker; anything else stops the run before the first write"
    - "Stage-then-swap install: build the full copy in a hidden sibling, rename the old copy aside, rename the new one in, restore the old one on failure"
    - "Clean-room guard for shipped prose: no honorific-plus-capitalised-word and no eight-word run shared with the reference report"

key-files:
  created:
    - .claude-plugin/marketplace.json
    - plugin/.claude-plugin/plugin.json
    - plugin/.codex-plugin/plugin.json
    - plugin/AGENTS.md
    - tools/install-codex.py
    - tests/packaging/test_manifests.py
    - tests/packaging/test_plugin_agents_md.py
    - tests/packaging/test_install_codex.py
  modified: []

key-decisions:
  - "Plugin version in both manifests is epb.__version__ (0.1.0-dev.1); the parity test fails on any drift"
  - "Codex installer replaces only folders carrying .epb-installed; a foreign same-name folder (or a symlink) stops the install with exit 1 before anything is written"
  - "Codex installer stages each copy in a hidden sibling of the target and swaps it in last, restoring the earlier copy if the swap fails"
  - "plugin/AGENTS.md is proven clean-room by a test: no eight-word run shared with the reference report and no honorific followed by a capitalised word"
  - "tools/install-codex.py uses datetime.timezone.utc rather than datetime.UTC so it stays importable on Pythons older than 3.11"

patterns-established:
  - "Tests that need the claude CLI skip with 'claude CLI not installed' when shutil.which finds nothing"
  - "Repo tools named with hyphens are exercised as subprocesses, the way a user runs them"

requirements-completed: [PKG-01, PKG-03]

coverage:
  - id: D1
    description: "Root marketplace plus Claude and Codex manifests: matching names, versions equal to epb.__version__, Codex skills ./skills/, no Claude skills key, UTF-8 without BOM, source ./plugin, no repo-only folders in plugin/, no .agents at the root"
    requirement: PKG-01
    verification:
      - kind: unit
        ref: "tests/packaging/test_manifests.py"
        status: pass
      - kind: integration
        ref: "tests/packaging/test_manifests.py#test_claude_validate_strict (claude 2.1.302, ran, not skipped)"
        status: pass
    human_judgment: false
  - id: D2
    description: "plugin/AGENTS.md: seven headings in order, two to five rules each, evidence-bank rule, epb CLI rules (exit 2/3/4, no .epb hand edits, no names on the command line, never claim an import worked), at most 150 lines, no names, no reference-report text"
    requirement: PKG-03
    verification:
      - kind: unit
        ref: "tests/packaging/test_plugin_agents_md.py"
        status: pass
    human_judgment: false
  - id: D3
    description: "Plain-language quality of plugin/AGENTS.md for an end user's agent: whether the rules read clearly and match the owner's intent"
    verification: []
    human_judgment: true
    rationale: "Tests prove required phrases and structure; whether the wording is clear and complete for a real agent is a judgement call for the owner"
  - id: D4
    description: "tools/install-codex.py: copies skills into --dest (default ~/.agents/skills), adds references/plugin-rules.md and plugin-files/, writes .epb-installed, replaces only its own copies, refuses a foreign folder byte-for-byte untouched with exit 1, no caches or symlinks, --dry-run writes nothing, the copied launcher finds plugin-files/requirements.txt"
    verification:
      - kind: integration
        ref: "tests/packaging/test_install_codex.py"
        status: pass
    human_judgment: false

duration: 5min
completed: 2026-10-18
status: complete
---

# Phase 1 Plan 06: Plugin Packaging for Claude Code and Codex Summary

**One root marketplace (`source ./plugin`) feeding a Claude manifest without a `skills` key and a Codex manifest with `./skills/`, kept in lockstep with `epb.__version__` and checked by `claude plugin validate --strict`. Alongside them ship a clean-room `plugin/AGENTS.md` with the just-culture, evidence-bank and epb CLI rules, and a stdlib Codex fallback installer that replaces only folders carrying its own `.epb-installed` marker.**

## Performance

- **Duration:** about 5 min
- **Started:** 2026-10-18T09:55:02Z
- **Completed:** 2026-10-18T10:00:00Z
- **Tasks:** 3
- **Files modified:** 8 (all created)

## Accomplishments
- Both hosts now have an install route: the marketplace for Claude Code and Codex, and `tools/install-codex.py` for Codex setups without marketplace support.
- Manifest drift (research Pitfall 8) is caught by a test: names match across all three files, both versions equal `epb.__version__`, and strict validation runs whenever the `claude` CLI is present.
- `plugin/AGENTS.md` (71 lines) states the agent rules once for every host, and a test proves it shares no eight-word run with the reference report.
- The installer is safe in a shared skills folder. It never touches a folder it did not create, and it stages each copy before swapping it in.

## Task Commits

1. **Task 1 (tracer): marketplace and both manifests** - `98aea4c` (feat)
2. **Task 2: plugin AGENTS.md** - RED `d3a629c` (test), GREEN `9c16d9c` (feat)
3. **Task 3: Codex fallback installer** - RED `cc3c039` (test), GREEN `535fcfe` (feat)

No REFACTOR commits were needed.

**Tracer gate:** this run was interactive with `human_verify_mode` set to `end-of-phase`, and the tracer had only automated checks. I re-ran `pytest tests/packaging/test_manifests.py` (11 passed, validate ran rather than skipped) and then continued to Tasks 2 and 3.

## TDD Gate Compliance

- **Task 2 RED:** `test_headings_in_order` failed on its assertion (`[] == ['Just culture', ...]`) because `plugin/AGENTS.md` did not exist. The evidence is in `scratch/tdd/red-01-06-t2.json` (JUnit), and `check tdd-red-evidence` returned `RED_EVIDENCE_OK`. Semantic assessment: the target test ran and failed for the intended reason, the missing file. It was not a collection or import fault.
- **Task 3 RED:** `test_foreign_folder_is_left_untouched` failed with `assert 0 == 1` because the committed inert skeleton exited 0 without checking. The evidence is in `scratch/tdd/red-01-06-t3.json`, and the classifier returned `RED_EVIDENCE_OK`. Semantic assessment: the target test ran and failed on the planned exit-code assertion.
- **GREEN:** both tasks pass. RED and GREEN commits are present for both TDD tasks.

## Files Created/Modified
- `.claude-plugin/marketplace.json`: marketplace `probematrix-evidence-pack-builder`, owner Eyekyam Risk Resolutions, one plugin from `./plugin`.
- `plugin/.claude-plugin/plugin.json`: Claude Code / Cowork manifest. It has no `skills` key (D-02).
- `plugin/.codex-plugin/plugin.json`: Codex manifest with `"skills": "./skills/"` (D-01).
- `plugin/AGENTS.md`: host-neutral rules for end users' agents (PKG-03).
- `tools/install-codex.py`: Codex fallback installer with `--dest` and `--dry-run`.
- `tests/packaging/test_manifests.py`: parity, encoding, layout and strict-validate tests.
- `tests/packaging/test_plugin_agents_md.py`: heading order, rule counts, key phrases, line limit, no names, no reference-report text.
- `tests/packaging/test_install_codex.py`: installer behaviour run as a subprocess under `tmp_path`.

## Decisions Made
- The marker records `plugin_version` from the Codex manifest and `installed_at` in UTC (`YYYY-MM-DDTHH:MM:SSZ`). A symlink at the target name counts as foreign.
- The installer writes its refusal message to stderr and checks every skill before writing anything, so a refusal leaves `--dest` exactly as it was.
- The installer uses `timezone.utc` instead of `datetime.UTC`, so a user running an older `python3` gets past the import. The plugin itself still requires 3.11 or newer at `doctor --setup`.
- For exit code 3, `plugin/AGENTS.md` says "something the plugin needs is missing or out of date: run `doctor --setup` and follow what it says". In `epb/errors.py`, exit 3 also covers `PYTHON_TOO_OLD` and `CORE_PACKAGE_MISSING`, not only a missing setup.

## Deviations from Plan

None. The plan was executed as written. The only extra tests go beyond the behaviour list: the default `~/.agents/skills` destination under a fake HOME, and the clean-room checks in the AGENTS.md test.

## Issues Encountered
- `claude plugin validate .` prints non-blocking advice: README.md has no marketplace install line. The verdict still passes under `--strict`. The README and manual install text belong to the documentation plans, so I did not change it here.
- A local hook blocked a `rm -rf` of a scratchpad folder during a manual check. I reran the check in a fresh `mktemp` folder instead; nothing was deleted.

## User Setup Required

None. No external service configuration is required.

## Next Phase Readiness
- Plan 01-15 can add `plugin/skills/evidence-pack/SKILL.md`. It must tell the agent to read `../../AGENTS.md`, or `references/plugin-rules.md` in the Codex copy (flagged assumption PKG-03: neither host loads a plugin's AGENTS.md automatically).
- Which manifest Codex actually reads is proved only in Phase 10 (PKG-10).
- Bump the dev version suffix per UAT build (research Pitfall 13). The parity test then forces both manifests to follow `epb.__version__`.

---
*Phase: 01-foundations*
*Completed: 2026-10-18*

## Self-Check: PASSED
