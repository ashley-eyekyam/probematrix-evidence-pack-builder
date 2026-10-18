---
phase: 01-foundations
verified: 2026-10-18T12:08:58Z
status: gaps_found
score: 15/23 must-haves verified
covered_files: [".claude-plugin/marketplace.json",".github/workflows/ci.yml",".gitignore",".planning/phases/01-foundations/01-01-PLAN.md",".planning/phases/01-foundations/01-01-SUMMARY.md",".planning/phases/01-foundations/01-02-PLAN.md",".planning/phases/01-foundations/01-02-SUMMARY.md",".planning/phases/01-foundations/01-03-PLAN.md",".planning/phases/01-foundations/01-03-SUMMARY.md",".planning/phases/01-foundations/01-04-PLAN.md",".planning/phases/01-foundations/01-04-SUMMARY.md",".planning/phases/01-foundations/01-05-PLAN.md",".planning/phases/01-foundations/01-05-SUMMARY.md",".planning/phases/01-foundations/01-06-PLAN.md",".planning/phases/01-foundations/01-06-SUMMARY.md",".planning/phases/01-foundations/01-07-PLAN.md",".planning/phases/01-foundations/01-07-SUMMARY.md",".planning/phases/01-foundations/01-08-PLAN.md",".planning/phases/01-foundations/01-08-SUMMARY.md",".planning/phases/01-foundations/01-09-PLAN.md",".planning/phases/01-foundations/01-09-SUMMARY.md",".planning/phases/01-foundations/01-10-PLAN.md",".planning/phases/01-foundations/01-10-SUMMARY.md",".planning/phases/01-foundations/01-11-PLAN.md",".planning/phases/01-foundations/01-11-SUMMARY.md",".planning/phases/01-foundations/01-12-PLAN.md",".planning/phases/01-foundations/01-12-SUMMARY.md",".planning/phases/01-foundations/01-13-PLAN.md",".planning/phases/01-foundations/01-13-SUMMARY.md",".planning/phases/01-foundations/01-14-PLAN.md",".planning/phases/01-foundations/01-14-SUMMARY.md",".planning/phases/01-foundations/01-15-PLAN.md",".planning/phases/01-foundations/01-15-SUMMARY.md",".planning/phases/01-foundations/01-16-PLAN.md",".planning/phases/01-foundations/01-16-SUMMARY.md","AGENTS.md","CLAUDE.md","README.md","docs/USER-MANUAL.md","docs/design/2026-10-17-evidence-pack-builder-design.md","plugin/.claude-plugin/plugin.json","plugin/.codex-plugin/plugin.json","plugin/AGENTS.md","plugin/requirements-docs.txt","plugin/requirements-email.txt","plugin/requirements-media.txt","plugin/requirements.txt","plugin/security-exceptions.json","plugin/skills/evidence-pack/SKILL.md","plugin/skills/evidence-pack/references/evidence-pack-v2.md","plugin/skills/evidence-pack/references/workspace-contract.md","plugin/skills/evidence-pack/scripts/epb.py","plugin/skills/evidence-pack/scripts/epb/__init__.py","plugin/skills/evidence-pack/scripts/epb/casefile.py","plugin/skills/evidence-pack/scripts/epb/cli.py","plugin/skills/evidence-pack/scripts/epb/commands/__init__.py","plugin/skills/evidence-pack/scripts/epb/commands/doctor.py","plugin/skills/evidence-pack/scripts/epb/commands/init.py","plugin/skills/evidence-pack/scripts/epb/commands/scan.py","plugin/skills/evidence-pack/scripts/epb/commands/status.py","plugin/skills/evidence-pack/scripts/epb/doctor/__init__.py","plugin/skills/evidence-pack/scripts/epb/doctor/gitcheck.py","plugin/skills/evidence-pack/scripts/epb/doctor/probes.py","plugin/skills/evidence-pack/scripts/epb/doctor/report.py","plugin/skills/evidence-pack/scripts/epb/doctor/setup.py","plugin/skills/evidence-pack/scripts/epb/doctor/syncfolders.py","plugin/skills/evidence-pack/scripts/epb/doctor/tools.py","plugin/skills/evidence-pack/scripts/epb/errors.py","plugin/skills/evidence-pack/scripts/epb/faults.py","plugin/skills/evidence-pack/scripts/epb/formats/__init__.py","plugin/skills/evidence-pack/scripts/epb/formats/probematrix_v2.py","plugin/skills/evidence-pack/scripts/epb/formats/validate.py","plugin/skills/evidence-pack/scripts/epb/formats/writer.py","plugin/skills/evidence-pack/scripts/epb/fsio.py","plugin/skills/evidence-pack/scripts/epb/index.py","plugin/skills/evidence-pack/scripts/epb/launcher.py","plugin/skills/evidence-pack/scripts/epb/lock.py","plugin/skills/evidence-pack/scripts/epb/mime.py","plugin/skills/evidence-pack/scripts/epb/runs.py","plugin/skills/evidence-pack/scripts/epb/schema.py","plugin/skills/evidence-pack/scripts/epb/schemas/case.schema.json","plugin/skills/evidence-pack/scripts/epb/schemas/chunks.schema.json","plugin/skills/evidence-pack/scripts/epb/schemas/envelope.schema.json","plugin/skills/evidence-pack/scripts/epb/schemas/run.schema.json","plugin/skills/evidence-pack/scripts/epb/schemas/source.schema.json","plugin/skills/evidence-pack/scripts/epb/schemas/state.schema.json","plugin/skills/evidence-pack/scripts/epb/sources/__init__.py","plugin/skills/evidence-pack/scripts/epb/sources/classify.py","plugin/skills/evidence-pack/scripts/epb/sources/expanders/__init__.py","plugin/skills/evidence-pack/scripts/epb/sources/scan.py","plugin/skills/evidence-pack/scripts/epb/sources/sidecars.py","plugin/skills/evidence-pack/scripts/epb/state.py","plugin/skills/evidence-pack/scripts/epb/txn.py","plugin/skills/evidence-pack/scripts/epb/upgrade.py","plugin/skills/evidence-pack/scripts/epb/workspace.py","plugin/skills/evidence-pack/scripts/epb/yamlio.py","pyproject.toml","requirements-dev-full.txt","requirements-dev.txt","tests/cli/test_exit_codes.py","tests/conftest.py","tests/core/test_mime.py","tests/core/test_yamlio.py","tests/docs/test_manual.py","tests/doctor/test_gitcheck.py","tests/doctor/test_probes.py","tests/doctor/test_syncfolders.py","tests/epbtest/crash.py","tests/epbtest/envkit.py","tests/epbtest/packkit.py","tests/formats/test_contract.py","tests/formats/test_validator.py","tests/formats/test_writer.py","tests/index/test_index.py","tests/launcher/test_launcher.py","tests/launcher/test_setup.py","tests/launcher/test_setup_real.py","tests/packaging/test_host_install.py","tests/packaging/test_install_codex.py","tests/packaging/test_manifests.py","tests/packaging/test_plugin_agents_md.py","tests/packaging/test_references.py","tests/packaging/test_requirements.py","tests/packaging/test_skill_lint.py","tests/repo/test_ci_workflow.py","tests/repo/test_instructions_mirror.py","tests/repo/test_no_network.py","tests/schemas/test_state_schema.py","tests/sources/test_scan_classify.py","tests/sources/test_scan_fingerprint.py","tests/sources/test_sidecars.py","tests/store/test_crash_resume.py","tests/store/test_fsio_retry.py","tests/store/test_lock.py","tests/store/test_upgrade.py","tests/store/test_validate.py","tests/tools/test_dependency_checks.py","tests/tools/test_smoke_pack.py","tests/workspace/test_git_warning.py","tests/workspace/test_init.py","tests/workspace/test_init_defaults.py","tests/workspace/test_layout.py","tests/workspace/test_status.py","tools/check_dependency_age.py","tools/check_licences.py","tools/install-codex.py","tools/licence-allowlist.json","tools/make-smoke-pack.py"]
covered_digest: "v3:sha256:d15e65643cb21a11eabedc30a05a07507811f22e2f9a7e61dda2e0636a68c11f"
behavior_unverified: 1
overrides_applied: 0
gaps:
  - truth: "Linux CI runs pytest, ruff, the dependency-age check and the licence allow-list, all green (ROADMAP SC5; PKG-09, TST-01, PKG-11 CI leg)"
    status: failed
    reason: "ci.yml sets PYTHONWARNDEFAULTENCODING=1 job-wide and pyproject.toml escalates EncodingWarning to an error. Under that environment the suite gives 86 failed, 1174 passed, 3 skipped, 2 errors (reproduced on Python 3.14.4, the CI's 3.14 leg). The same files pass without the variable (207 passed), so local green runs do not represent CI. The CI pytest step is red by construction."
    artifacts:
      - path: ".github/workflows/ci.yml"
        issue: "PYTHONWARNDEFAULTENCODING=1 on the job; local runs never set it"
      - path: "pyproject.toml"
        issue: "filterwarnings = ['error::EncodingWarning'] catches openpyxl's tempfile.NamedTemporaryFile(mode='w+') call reached via epb/formats/writer.py _save"
      - path: "plugin/skills/evidence-pack/scripts/epb/launcher.py"
        issue: "_probe calls subprocess.run(universal_newlines=True) with no encoding= (fails tests/launcher/test_launcher.py::test_find_python_*)"
    missing:
      - "Silence only the third-party openpyxl temp-file EncodingWarning (narrow filterwarnings entry or warnings.catch_warnings around wb.save in writer._save)"
      - "Add encoding='utf-8', errors='replace' to launcher._probe's subprocess.run"
      - "Make local runs match CI (set PYTHONWARNDEFAULTENCODING in a conftest hook or document it in the check command in AGENTS.md/CLAUDE.md)"
      - "Re-run the full suite with PYTHONWARNDEFAULTENCODING=1 and get 0 failed, then push and get a green GitHub CI run"
  - truth: "INDEX.md always has exactly six level-2 headings in order 1 to 6, and input file names cannot add headings or Imported? tick lines (ROADMAP SC1 six sections; 01-11 edge WS-09/ordering; PF-04 tick syntax that Phase 6 reads back)"
    status: failed
    reason: "Reproduced: two symlinks in inputs/ whose names contain a newline produced a seventh '## Injected heading' line and a forged '- [x] Imported: evidence-pack-inj-master.xlsx' line inside section 5 Open issues. Only table cells go through _cell(); open_issues() list lines interpolate raw paths and mime_mismatch values. Regular files are sanitised in the Inputs table, but the ignored-path and removed/mismatch lines are not."
    artifacts:
      - path: "plugin/skills/evidence-pack/scripts/epb/index.py"
        issue: "open_issues() interpolates _path_text(source), entry.get('path') and mime_mismatch values into list lines without single-line sanitising"
      - path: "plugin/skills/evidence-pack/scripts/epb/schemas/run.schema.json"
        issue: "input_path pattern allows embedded line breaks"
    missing:
      - "A single-line sanitiser (C0, C1, U+2028, U+2029 to space) applied to every interpolated value on non-table INDEX.md lines"
      - "Regression test: scan a newline-bearing file name and a newline-bearing symlink name; assert exactly six '## ' lines and no '- [x]' line outside section 2"
  - truth: "On a folder that is not set up, a refused init (no --title, blank title, TIMEZONE_REQUIRED) exits 2 and writes nothing (01-09 edge WS-01/empty)"
    status: failed
    reason: "Reproduced: 'epb init --timezone UTC --json' in an empty folder exits 2 BAD_ARGUMENT but leaves .epb/, .epb/lock and .epb/tmp/ behind, because workspace.open_for_init creates them before casefile.resolve_settings validates the arguments. tests/workspace/test_init_defaults.py _assert_nothing_written only checks case.yaml and state.json, so the test passes while the truth is false."
    artifacts:
      - path: "plugin/skills/evidence-pack/scripts/epb/commands/init.py"
        issue: "resolve_settings runs inside open_for_init, after the disk writes"
      - path: "plugin/skills/evidence-pack/scripts/epb/workspace.py"
        issue: "open_for_init creates .epb/, .epb/lock and .epb/tmp/ unconditionally"
      - path: "tests/workspace/test_init_defaults.py"
        issue: "_assert_nothing_written does not assert that .epb/ is absent"
    missing:
      - "Resolve and validate settings before opening the init session when the folder is not yet set up"
      - "Tighten _assert_nothing_written to assert not (case_dir / '.epb').exists()"
  - truth: "epb scan records the correct MIME type for every input; magic bytes override the extension only for genuine signatures, and a disagreement is a real mismatch (WS-02, D-13)"
    status: failed
    reason: "Reproduced: UTF-16LE text files with a BOM (Notepad 'Unicode', Excel 'Unicode Text', PowerShell 5.1 Out-File) whose first character is e.g. 'A' are recorded as versions[].mime = 'audio/mpeg', and the user is told 'inputs/log.txt looks like MP3 audio but its name says Text. The plugin will treat it by its content.' The _mpeg_frame sniff accepts the FF FE BOM as an MPEG frame header. Under the content-wins rule, Phase 2 would route this text evidence to audio handling."
    artifacts:
      - path: "plugin/skills/evidence-pack/scripts/epb/mime.py"
        issue: "_mpeg_frame accepts any 0xFF followed by a byte with the top three bits set, including the UTF-16LE BOM; it runs before any text-BOM check"
    missing:
      - "Return no content verdict for UTF-8/UTF-16LE/UTF-16BE BOMs (excluding UTF-32LE FF FE 00 00) before the audio rules, or confirm a second MPEG sync word at the computed frame length"
      - "Regression tests for UTF-16LE and UTF-16BE .txt and .csv inputs starting with several different letters"
  - truth: "The manual's privacy chapter describes what the plugin does today, so a user can inventory inputs safely: it does not promise that INDEX.md uses role labels instead of names (DOC-04; phase goal 'inventory its inputs safely')"
    status: partial
    reason: "docs/USER-MANUAL.md 'De-identification is always on' says 'Everything the plugin makes for you to share, such as the evidence pack workbook and INDEX.md, uses role labels instead of names.' In Phase 1, INDEX.md section 3 lists every raw input path (verified in a scratch case), Open issues and scan warnings repeat paths, and no de-identification code exists yet. workspace-contract.md classes INDEX.md as 'shareable' and .epb/sources/ and .epb/state.json as 'structural' (safe for version control), but both hold raw paths. Investigators commonly name files after people, so a user following the manual would share names. The code-side fix is scheduled for Phase 4 (see deferred); the present-tense documentation is a Phase 1 defect."
    artifacts:
      - path: "docs/USER-MANUAL.md"
        issue: "Lines 58-66 promise role labels in INDEX.md now"
      - path: "plugin/skills/evidence-pack/references/workspace-contract.md"
        issue: "INDEX.md 'shareable'; .epb/sources/ and .epb/state.json 'structural' despite holding raw input paths"
      - path: "plugin/skills/evidence-pack/SKILL.md"
        issue: "No instruction to warn when an input file name looks like a person's name"
    missing:
      - "Reword the manual: the workbook will use role labels (later version); INDEX.md and the plugin's records list files by file name until then; rename files that contain names and check INDEX.md before sharing"
      - "Reclassify INDEX.md as 'shareable after review' and .epb/sources/ and .epb/state.json as confidential until Phase 4, or add sources/ to GITIGNORE_LINES"
      - "Keep the tests/docs/test_manual.py golden blocks in step with the new wording"
deferred:
  - truth: "INDEX.md and shareable output show role labels instead of personal names found in input file names (code side of C-CR-01)"
    addressed_in: "Phase 4"
    evidence: "Phase 4 SC2: 'An input whose file name contains a name appears in INDEX.md under its role label.' PF-04: 'Phase 4 adds file-name substitution and scans INDEX'. WS-10 and DEID-08 are Phase 4 requirements."
behavior_unverified_items:
  - truth: "epb doctor --setup, launched through the standard-library-only epb.py, finds Python 3.11+, builds the private environment, installs the core packages under the two-week rule and reports what is ready and optional; afterwards normal commands re-run inside the environment (ROADMAP SC5, PKG-06)"
    test: "On a Linux machine with internet access, from the repo root run: EPB_NETWORK_TESTS=1 .venv/bin/python -m pytest -q tests/launcher/test_setup_real.py. Then, as a real user, run python3 plugin/skills/evidence-pack/scripts/epb.py doctor --setup and then epb.py doctor."
    expected: "The networked test passes. doctor --setup ends with the Ready / Optional, not installed / What to do next checklist and exit 0; ~/.local/share/probematrix-epb/envs/0.1.0-dev.1/epb-env.json exists; a following 'epb.py doctor' exits 0 and 'epb.py init' runs inside the environment."
    why_human: "Needs network and a real package download (45-60 s); the verifier must not reach external services or write the real per-user data folder. 35 offline tests with fakes pass, but only the opt-in networked test exercises the real venv/pip path, and it was skipped in this run."
human_verification:
  - test: "Owner smoke import (ROADMAP SC4): run .venv/bin/python tools/make-smoke-pack.py (writes scratch/smoke/evidence-pack-smoke.xlsx), import it into a new ProbeMatrix test incident on Replit, and walk the 21-line checklist the tool prints."
    expected: "Every value shows exactly as written: =SUM(A1:A2), +44, -5 °C and @shift-lead stay text; 0 is not blank; 40000000000000000001 keeps all 20 digits; 2026-09 and 2026 stay as written; Tags and Linked Equipment split into 3 entries and Linked Individuals into 2; all eight QA Status values show. The owner reports the result; the agent never claims it."
    why_human: "ProbeMatrix runs only on Replit and only the owner imports. The verifier confirmed the workbook builds, has only inlineStr cells and no <f> element in all three sheets, and has zero validator findings."
  - test: "doctor --setup end to end (see behavior_unverified_items)"
    expected: "Networked test passes; setup completes with exit 0 and the environment marker written"
    why_human: "Network and real per-user data folder"
  - test: "First-use install in Claude Code (ROADMAP SC5, 01-15): EPB_HOST_TESTS=1 .venv/bin/python -m pytest -q tests/packaging/test_host_install.py, then follow manual chapter 4 on a clean Claude Code profile: /plugin marketplace add <repo path>, /plugin install probematrix-evidence-pack-builder."
    expected: "Both host tests pass; the plugin cache holds skills/evidence-pack/SKILL.md, scripts/epb.py, the schemas, AGENTS.md and the requirement files, and no docs/, tests/, tools/ or .planning/."
    why_human: "Drives real host CLIs; opt-in and skipped in this run"
  - test: "GitHub CI run after the owner approves pushing phase-01-foundations (and after the CI gap is fixed)"
    expected: "Both matrix legs (3.11, 3.14) green on lint, format, pytest, the dependency-age check (queries PyPI) and the licence check"
    why_human: "Needs a push, which requires owner approval; the age check needs network. Locally the licence check passed (35 distributions allowed) and ruff check / ruff format --check were clean."
  - test: "Manual read-through (DOC-04, DOC-05, T-01-44): read docs/USER-MANUAL.md chapters 1-7 as a non-technical user."
    expected: "Plain language; Windows and macOS sections each marked 'not yet tested on this system' (confirmed at lines 140, 161, 470, 483); the privacy chapter is accurate once the gap above is fixed; no claim that nothing leaves the computer."
    why_human: "Readability and tone are judgement calls"
  - test: "Judgment-tier prohibitions (non-authoritative LLM verdict: holds): 01-04 'never claim an import worked', 01-15 'no real names, reference-report prose or prototype prose in SKILL.md, references, AGENTS.md, tests or fixtures', 01-16 'never imply nothing leaves the computer'."
    expected: "Owner confirms. Note review C-IN-09: the GitHub handle 'ashley-eyekyam' in committed manifests contains a personal first name (the owner's own); decide whether that is acceptable under the 'never write real names' rule."
    why_human: "Judgment-tier prohibitions need explicit human resolution in interactive verify"
  - test: "Wording check of design amendments A16-A30 (docs/design/2026-10-17-evidence-pack-builder-design.md lines 672-686)"
    expected: "Each row states the decision as the owner intended; each cites its D-NN or research item (verified present)"
    why_human: "Spec wording is the owner's call"
---

# Phase 1: Foundations Verification Report

**Phase Goal:** A user can set the plugin up once, create a case folder and inventory its inputs safely. The workbook format is proven against the real ProbeMatrix importer before any evidence logic exists.
**Verified:** 2026-10-18T12:08:58Z
**Status:** gaps_found
**Re-verification:** No, initial verification

Most of the phase is real and works: `init`, `scan`, the journalled store, crash recovery, the lock, the exit-code contract, strict YAML, the workbook writer and validator, `doctor`, manifests and the manual all exist, are wired and behave as specified in independent scratch-folder runs. Four observable defects and one documentation defect stop the goal: CI cannot go green as configured, input file names can inject headings and forged tick lines into INDEX.md, a refused `init` leaves `.epb/` behind, common Windows UTF-16 text files are inventoried as MP3 audio, and the manual promises name-free INDEX.md output that the code does not produce. The owner-only items (smoke import, real setup, host install, CI run) are still outstanding.

## Goal Achievement

### Observable Truths

ROADMAP success criteria decomposed into checkable truths, plus the plan edge truths that the review findings contradict. Each of the roughly 150 plan-level truths was traced to one of these rows; the plan truths not listed separately are covered by the artifact and key-link checks and by the passing test files named in the evidence column.

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | `epb init` in an empty folder creates `inputs/`, `outputs/`, `INDEX.md` and `.epb/` with `case.yaml`, `state.json`, `.gitignore`, `.gitattributes`, `inbox/`, `tmp/`, `runs/`, `private/` (SC1, WS-01) | ✓ VERIFIED | Scratch run: exit 0, all paths present; case.yaml has slug, title, id_prefix, timezone, plugin_version, all as text |
| 2 | `state.json` already holds the workbook registry, Evidence ID and Tag counters and chunk status (SC1, WS-13) | ✓ VERIFIED | state.json keys `workbooks`, `counters` {run, source, evidence, tag, claim, conflict}, `chunks`; schema `$defs/workbook` (file, kind, number, draft/imported status, writes with sha256) and `$defs/chunk_status` (no raw text) |
| 3 | `.epb/.gitignore` covers segments/, ledger/, inbox/, tmp/, media/, runs/, private/ (SC1, WS-11) | ✓ VERIFIED | File content is exactly the seven lines in A2 order |
| 4 | INDEX.md shows six sections in order with "none yet" where no producer exists, after init (SC1, WS-09) | ✓ VERIFIED | Fresh INDEX.md: `## 1. Case` to `## 6. Run history`, sections 2-5 "none yet", run history has Run 001 |
| 5 | INDEX.md keeps exactly six headings whatever the input names; names cannot forge `- [x] Imported:` lines (01-11 edge WS-09/ordering, PF-04) | ✗ FAILED | Newline-bearing symlink names produced 7 `## ` headings and a forged `- [x] Imported: evidence-pack-inj-master.xlsx` line (review A-CR-01 reproduced) |
| 6 | `init` and `doctor` warn in plain language inside OneDrive, Dropbox, iCloud Drive or Google Drive, or a git repo that would track `.epb/private/` (SC1, WS-11, WS-12) | ✓ VERIFIED | Scratch case under `~/OneDrive/`: init printed the plain-language warning with exit 0; doctor returned `SYNC_FOLDER`. Inside a git repo with the default `.epb/.gitignore`, no warning (correct: private/ is ignored). Git-tracking cases covered by passing tests/doctor/test_gitcheck.py and tests/workspace/test_git_warning.py |
| 7 | `scan` reports new, changed (`S004v2`), renamed, duplicate and removed inputs, lists OS junk as ignored, pairs `.note.md`/`.note.yaml` sidecars (SC2, WS-02, WS-03, WS-04) | ✓ VERIFIED | Scratch corpus: JSON data had new [S006], new_versions [S004 v2], renamed S002, duplicates S001, removed [S003] with INPUT_REMOVED, ignored .DS_Store and Thumbs.db, sidecars S005 to S004; INDEX.md shows `S004v2`; rescan "No changes since the last scan." |
| 8 | `scan` records the correct MIME type for every input (WS-02, D-13) | ✗ FAILED | UTF-16LE `log.txt` and `export.csv` recorded as `audio/mpeg` with MIME_MISMATCH "looks like MP3 audio" (review B-CR-01 reproduced) |
| 9 | A crash injected at every transaction step resumes without corrupting state (SC2, WS-06, TST-07) | ✓ VERIFIED | Independent run: recorded 15 real scan checkpoints (stage:0-5, pre-manifest, manifest, apply:0-5, cleanup); `os._exit(97)` at each, then the next scan exits 0 with 3 sources, no tmp journal, run counter equal to run folders, 6 headings, status exit 0. Named tests in tests/store/test_crash_resume.py (6) pass |
| 10 | A second mutating run waits for the lock (SC2, WS-07) | ✓ VERIFIED | tests/store/test_lock.py 9 passed, incl. test_init_waits_until_the_lock_is_released, test_second_init_times_out_while_lock_is_held, test_status_does_not_wait_for_the_lock, test_a_killed_holder_releases_the_lock_at_once |
| 11 | Every command returns exit codes 0-4 with a stable error code in `--json` (SC2, PKG-05) | ✓ VERIFIED | Spot-check: unknown command, exit 2 USAGE; no private env, exit 3 ENV_NOT_SET_UP; damaged state.json, exit 4 STATE_INVALID; tests/cli/test_exit_codes.py passes |
| 12 | YAML values such as `12:30`, `0123` and `no` survive as text (SC2, WS-08) | ✓ VERIFIED | yamlio round trip of 15 YAML 1.1 boundary values exact; raw load of `a: 12:30 / b: 0123 / c: no` gives strings |
| 13 | A refused `init` on a folder that is not set up writes nothing (01-09 edge WS-01/empty) | ✗ FAILED | `init --timezone UTC` without --title: exit 2 BAD_ARGUMENT, leaves `.epb/`, `.epb/lock`, `.epb/tmp/` (review A-CR-02 reproduced) |
| 14 | Validator passes a generated pack and fails the prototype reference pack on list fragments (SC3, DEF-14) | ✓ VERIFIED | Smoke pack: 0 findings. Prototype pack: 24 LIST_FRAGMENT_UNBALANCED + 24 LIST_SEMICOLON in Linked Equipment |
| 15 | Validator rejects formulas, non-string cells, blank Description/Type, non-exact enums, >32,767-char cells, invalid Chain of Custody JSON (SC3, BLD-03) | ✓ VERIFIED | tests/formats/test_validator.py value-level assertions pass in the normal environment (fail only under the CI encoding variable, see truth 21) |
| 16 | Writer: every cell text, no formula, Pack Metadata 10-row layout, Attachments Manifest headers only (BLD-01, BLD-02, BLD-08) | ✓ VERIFIED | Smoke workbook XML: sheet1 15, sheet2 142 and sheet3 11 cells, all `inlineStr`, 0 `<f>` elements |
| 17 | Owner smoke import shows every edge value exactly as written (SC4) | ? UNCERTAIN | Workbook builds and validates; the import itself is owner-only on Replit (human item 1) |
| 18 | The plugin installs into Claude Code from this repo's marketplace with `source: "./plugin"` (SC5, PKG-01) | ? UNCERTAIN | `.claude-plugin/marketplace.json` name and source correct; plugin.json has no skills key; `plugin/` holds only AGENTS.md, requirements, security-exceptions.json and skills/. Real host install test is opt-in and was skipped (human item 3) |
| 19 | `doctor --setup` through stdlib-only `epb.py` builds the private environment and reports ready/optional (SC5, PKG-06) | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED | setup.py, launcher wiring and 35 offline tests present and passing; the only real venv/pip test (test_setup_real.py) is network-gated and skipped |
| 20 | `doctor` lists every tool with version, enabled input types and per-OS install commands; `plugin/AGENTS.md` holds the host-neutral rules (SC5, PKG-07, PKG-03) | ✓ VERIFIED | `doctor --verbose` run before setup: Ready (Python, 7-Zip, ffmpeg, LibreOffice, git with versions), Optional (Tesseract, pandoc with Linux/macOS/Windows commands; email, media, docs extras with licences). plugin/AGENTS.md has Just culture, Roles only, Inputs only, Facts only, Verbatim quotes, Evidence-bank entry rule, CLI rules |
| 21 | Linux CI runs pytest, ruff, dependency-age and licence checks, all green (SC5, PKG-09, TST-01) | ✗ FAILED | Full suite under CI's `PYTHONWARNDEFAULTENCODING=1`: 86 failed, 1174 passed, 3 skipped, 2 errors (review D-CR-01 reproduced). Ruff clean; licence check passed locally |
| 22 | Manual first edition covers install Python, adding the plugin, first-time setup and privacy, Windows/macOS marked "not yet tested"; root AGENTS.md and CLAUDE.md identical, at most 150 lines, CI test fails otherwise (SC5, DOC-05, PKG-11) | ✓ VERIFIED | Manual chapters 1-7 in the required order; four "not yet tested on this system" markers directly under the Windows/macOS headings; `cmp AGENTS.md CLAUDE.md` identical, 43 lines; tests/repo/test_instructions_mirror.py passes (also under the CI variable); golden doctor blocks tested |
| 23 | The manual's privacy statement matches current behaviour, so inputs can be inventoried safely (DOC-04, goal "safely") | ✗ FAILED (partial) | Manual says INDEX.md "uses role labels instead of names"; INDEX.md lists raw input paths (review C-CR-01). Code fix deferred to Phase 4; the wording is a Phase 1 defect |

**Score:** 15/23 truths verified (1 present but not behaviorally verified, 2 uncertain pending owner, 5 failed)

### Deferred Items

| # | Item | Addressed In | Evidence |
|---|------|-------------|----------|
| 1 | INDEX.md and shareable output show role labels for names in input file names (code side of C-CR-01) | Phase 4 | Phase 4 SC2: "An input whose file name contains a name appears in `INDEX.md` under its role label"; PF-04; WS-10, DEID-08 |

### Required Artifacts

`gsd-tools verify.artifacts` across all 16 plans: 75/75 artifacts exist and pass their content checks (01-01 5/5, 01-02 2/2, 01-03 5/5, 01-04 4/4, 01-05 5/5, 01-06 5/5, 01-07 6/6, 01-08 6/6, 01-09 3/3, 01-10 3/3, 01-11 5/5, 01-12 4/4, 01-13 6/6, 01-14 3/3, 01-15 4/4, 01-16 4/4).

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `plugin/skills/evidence-pack/scripts/epb.py` + `epb/launcher.py` | stdlib launcher | ✓ VERIFIED | Routes doctor before setup; exit 3 ENV_NOT_SET_UP otherwise |
| `epb/txn.py`, `fsio.py`, `lock.py`, `faults.py` | journalled store, lock, crash seam | ✓ VERIFIED | Independent crash matrix passes |
| `epb/index.py` | six-section INDEX renderer | ⚠️ WARNING | Works on normal names; unsanitised list lines (gap 2) |
| `epb/mime.py` | extension table + magic bytes | ⚠️ WARNING | MPEG-frame false positive on UTF-16 BOM (gap 4) |
| `epb/commands/init.py` + `workspace.py` | init command | ⚠️ WARNING | Writes `.epb/` before validating arguments (gap 3) |
| `epb/formats/*` + `tools/make-smoke-pack.py` | format, writer, validator, smoke pack | ✓ VERIFIED | Text-only cells, validator findings as specified |
| `epb/doctor/*` | doctor, setup, sync, git | ✓ VERIFIED (setup behaviour unverified) | See truth 19 |
| `.github/workflows/ci.yml` | Linux CI | ✗ FAILED | Encoding variable makes pytest red (gap 1) |
| `docs/USER-MANUAL.md` | first edition | ⚠️ WARNING | Inaccurate INDEX.md privacy promise (gap 5) |
| `.claude-plugin/marketplace.json`, `plugin/.claude-plugin/plugin.json`, `plugin/.codex-plugin/plugin.json`, `plugin/AGENTS.md` | packaging | ✓ VERIFIED | Names match; source `./plugin` |

### Key Link Verification

`gsd-tools verify.key-links`: 37/38 automatically verified. The one unresolved link (01-02, design §20 to CONTEXT.md decisions) failed only because the from-path contains `§20`. A manual check found amendment rows A16 to A30 at design lines 672-686, each citing D-01, D-02, D-03, D-05, D-06, D-07, D-08, D-12, D-13, D-14, D-18, D-19, D-20, research Q7 or research Pattern 1. Status: WIRED.

| From | To | Via | Status |
| ---- | -- | --- | ------ |
| epb.py | launcher.main | sys.path insert | WIRED |
| init.py | txn.Transaction, index.render_index, syncfolders.check | init transaction, post-commit warnings | WIRED |
| scan.py (sources) | classify, sidecars.pair_sidecars, mime.detect | one transaction | WIRED |
| workspace.py | lock.acquire, upgrade.run_upgrade | open_for_mutation | WIRED |
| doctor.py | probes.collect, setup.run_setup | --setup flag | WIRED |
| writer.py | validate_rows / validate_workbook | before write, temp file before replace | WIRED |
| test_manual.py | report.render_human / render_setup_human | golden blocks | WIRED |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| -------- | ------------- | ------ | ------------------ | ------ |
| INDEX.md section 3 Inputs | source records | `.epb/sources/S*.json` written by scan | Yes: real paths, sizes, hashes, `S004v2` | ✓ FLOWING |
| INDEX.md section 6 Run history | runs | `.epb/runs/NNN/run.json` | Yes: one line per run | ✓ FLOWING |
| doctor report | tool probes | `shutil.which` + version probes | Yes: real versions (7z 26.00, ffmpeg 8.0.1) | ✓ FLOWING |
| state.json counters | counters | committed with records in the same transaction | Yes: run counter equals run folders after every crash point | ✓ FLOWING |

### Behavioral Spot-Checks

Scripts in the session scratchpad (`crash_check.sh`, `criticals_check.sh`, `criticals_check2.sh`, `exit_check.sh`), each in a fresh scratch folder with a fake HOME and `EPB_IN_ENV=1` against the dev venv.

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| init layout | `epb.py init --title "Pump Fire 2026" --timezone Europe/London --json` | exit 0, full layout | ✓ PASS |
| scan change corpus | `epb.py scan --json` after edit, rename, copy, delete, add | new, new version, renamed, duplicate, removed, ignored, sidecar all correct | ✓ PASS |
| crash at every scan checkpoint | `crash_check.sh` | 15/15 checkpoints recover cleanly | ✓ PASS |
| exit codes | `exit_check.sh` | 2 USAGE, 3 ENV_NOT_SET_UP, 4 STATE_INVALID | ✓ PASS |
| refused init writes nothing | `criticals_check.sh` | `.epb/`, `.epb/lock`, `.epb/tmp` left | ✗ FAIL |
| INDEX.md heading invariant | `criticals_check2.sh` | 7 headings + forged tick line | ✗ FAIL |
| UTF-16 text MIME | `criticals_check2.sh` | `audio/mpeg` | ✗ FAIL |
| YAML text preservation | yamlio round trip | exact | ✓ PASS |
| Smoke pack | `tools/make-smoke-pack.py --out <scratch>` | 21-line checklist, 0 findings, inlineStr only | ✓ PASS |
| Prototype pack fails | `validate_workbook(prototype)` | 24 LIST_FRAGMENT_UNBALANCED | ✓ PASS |
| doctor before setup | `python3 epb.py doctor --verbose` | grouped checklist, per-OS commands | ✓ PASS |
| Lint | `ruff check .` / `ruff format --check .` | clean / 97 files formatted | ✓ PASS |
| Licence allow-list | `tools/check_licences.py` | 35 distributions allowed | ✓ PASS |
| Full suite, CI environment (single full run) | `PYTHONWARNDEFAULTENCODING=1 python -m pytest -q` | 86 failed, 1174 passed, 3 skipped, 2 errors | ✗ FAIL |
| Failing files without the variable | `pytest tests/formats tests/launcher/test_launcher.py tests/tools/test_smoke_pack.py` | 207 passed | ✓ PASS (shows the failure is environment-only) |
| Dependency-age check | `tools/check_dependency_age.py` | not run (queries PyPI) | ? SKIP: human item 4 |
| Real `doctor --setup` / host install | opt-in networked and host tests | not run | ? SKIP: human items 2-3 |

### Probe Execution

No `scripts/*/tests/probe-*.sh` exists and no plan declares a probe. Step 7c: not applicable.

### Requirements Coverage

All 27 phase requirement IDs are claimed by at least one plan. REQUIREMENTS.md maps no other IDs to Phase 1, so none are orphaned.

| Requirement | Source Plan | Description (short) | Status | Evidence |
| ----------- | ----------- | ------------------- | ------ | -------- |
| WS-01 | 01-07, 01-09, 01-11 | `epb init` layout and case.yaml | ⚠️ PARTIAL | Layout verified; a refused init leaves `.epb/` (gap 3) |
| WS-02 | 01-13 | scan fingerprints, stable IDs, junk ignored | ✗ BLOCKED (partial) | SHA-256, size, mtime, IDs, junk OK; MIME wrong for UTF-16 text (gap 4) |
| WS-03 | 01-13, 01-14 | new version, rename, duplicate, removed | ✓ SATISFIED | Truth 7 |
| WS-04 | 01-14 | sidecars paired and hashed | ✓ SATISFIED | S005 sidecar of S004 |
| WS-06 | 01-07, 01-12 | atomic journalled writes, crash resume | ✓ SATISFIED | Truth 9 |
| WS-07 | 01-12 | lock with 60 s wait | ✓ SATISFIED | Truth 10 |
| WS-08 | 01-07, 01-09 | schema on write, strict text YAML | ✓ SATISFIED | Truth 12; RECORD_INVALID tests pass |
| WS-09 | 01-11 | INDEX.md six sections, none yet | ✗ BLOCKED (partial) | Holds after init; breakable through input names (gap 2) |
| WS-11 | 01-08, 01-11 | `.epb/.gitignore`, git warning | ✓ SATISFIED | Truths 3, 6 (see warning B-WR-01) |
| WS-12 | 01-08, 01-11 | sync-folder warnings | ✓ SATISFIED | Truth 6 |
| WS-13 | 01-07 | state schema registry, counters, chunks | ✓ SATISFIED | Truth 2 |
| BLD-01 | 01-04, 01-15 | format module and reference doc | ✓ SATISFIED | Artifacts; evidence-pack-v2.md dated 2026-10-17 |
| BLD-02 | 01-04 | text-only cells | ✓ SATISFIED | Truth 16 |
| BLD-03 | 01-04 | strict validator | ✓ SATISFIED | Truth 15 |
| BLD-08 | 01-02, 01-04 | 10-row metadata, empty manifest | ✓ SATISFIED | Truth 16 |
| PKG-01 | 01-02, 01-06, 01-15 | plugin/ + marketplace | ? NEEDS HUMAN | Manifests correct; real install pending (human item 3) |
| PKG-03 | 01-06, 01-15 | plugin AGENTS.md rules | ✓ SATISFIED | Truth 20 |
| PKG-05 | 01-03 | exit codes 0-4 + stable codes | ✓ SATISFIED | Truth 11 |
| PKG-06 | 01-03, 01-10 | stdlib launcher, doctor --setup | ? NEEDS HUMAN | Truth 19 |
| PKG-07 | 01-08 | doctor tool report | ✓ SATISFIED | Truth 20 |
| PKG-08 | 01-01, 01-02, 01-10 | permissive pinned core, GPL extras split | ✓ SATISFIED | tests/packaging/test_requirements.py passes; extras state licences |
| PKG-09 | 01-05 | CI dependency-age and licence checks | ✗ BLOCKED | Tooling present and unit-tested; CI job red (gap 1) |
| PKG-11 | 01-05, 01-16 | AGENTS.md == CLAUDE.md, at most 150 lines, CI test | ⚠️ PARTIAL | Mirror and test verified; CI not green (gap 1). REQUIREMENTS.md still shows `[ ]` / Pending |
| TST-01 | 01-01, 01-05 | pytest + ruff, no network, optional skips | ✗ BLOCKED (partial) | No-network guard and skips work; suite fails in the CI environment (gap 1) |
| TST-07 | 01-12, 01-14 | crash injection per step | ✓ SATISFIED | Truth 9 |
| DOC-04 | 01-16 | privacy chapter in plain language | ⚠️ PARTIAL | Topics covered; INDEX.md promise inaccurate (gap 5) |
| DOC-05 | 01-16 | manual started, Win/mac marked | ✓ SATISFIED | Truth 22 |

Bookkeeping note: REQUIREMENTS.md marks 26 of these IDs `[x]` / Complete before verification. WS-01, WS-02, WS-09, PKG-09, TST-01 and DOC-04 should not read Complete until the gaps close.

### Decision Coverage

All trackable CONTEXT.md decisions are honored by shipped artifacts (20/20, `check.decision-coverage-verify`).

### Test Quality Audit

| Test File | Linked Req | Active | Skipped | Circular | Assertion Level | Verdict |
| --------- | ---------- | ------ | ------- | -------- | --------------- | ------- |
| tests/store/test_crash_resume.py | WS-06, TST-07 | 6 | 0 | No | Behavioral | OK, but D-WR-07: the per-checkpoint tests do not assert the checkpoint list is non-empty (saved only by a sibling test). Independently confirmed non-vacuous here |
| tests/workspace/test_init_defaults.py | WS-01 | yes | 0 | No | Value | INSUFFICIENT for "writes nothing": does not check `.epb/` (gap 3) |
| tests/formats/test_validator.py | BLD-03, DEF-14 | yes | 0 | No (prototype is an external oracle) | Value | OK; D-WR-09: on-disk ordering test writes a valid pack |
| tests/launcher/test_setup_real.py | PKG-06 | 0 by default | 1 (opt-in network) | No | Behavioral | Only real-path test is opt-in, so PKG-06 is routed to human |
| tests/packaging/test_host_install.py | PKG-01 | 0 by default | 2 (opt-in host) | No | Behavioral | Opt-in, routed to human |
| tests/workspace/test_layout.py::test_no_absolute_path_user_or_host_in_any_file | 01-11 prohibition | 1 | 0 | No | Value | OK for init files (review D-IN-02 concerns a different test) |

Disabled tests on requirements: 0 (skips are the documented opt-in network/host markers). Circular patterns: none found. Insufficient assertions: 1 (test_init_defaults "nothing written").

### Prohibitions

| Plan | Prohibition | Tier | Disposition |
| ---- | ----------- | ---- | ----------- |
| 01-04 | No silent alteration of cell text | test | Enforced: test_edge_values_survive_as_exact_strings, test_formula_risk_depends_only_on_first_character |
| 01-04 | Never claim an import succeeded | judgment | LLM verdict holds (SKILL.md line 25, plugin/AGENTS.md); flagged for owner (human item 6) |
| 01-06 | install-codex never touches foreign folders | test | Enforced: test_foreign_folder_is_left_untouched |
| 01-08 | No git modification | test | Enforced: test_source_uses_only_read_only_subcommands, test_git_argv_uses_dash_c_and_never_a_shell |
| 01-10 | No downloads except doctor --setup; no sudo | test | Enforced: test_only_setup_builds_a_pip_command_line, test_no_module_runs_sudo_or_a_shell, tests/repo/test_no_network.py |
| 01-11 | No absolute paths, user or host names in trackable files | test | Enforced for init (test_no_absolute_path_user_or_host_in_any_file); scan records checked by hand here (relative paths only) |
| 01-13 | scan never modifies inputs/ | test | Enforced: snapshot assertion in tests/sources/test_scan_fingerprint.py lines 63-65 |
| 01-15 | No real names, reference-report or prototype prose | judgment | LLM verdict holds, with C-IN-09 (owner's handle) flagged; owner decision (human item 6) |
| 01-16 | Never imply nothing leaves the computer | judgment | LLM verdict holds (manual "Every excerpt the agent reads is sent to the AI host's model provider"); flagged for owner (human item 6) |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| (116 phase-changed files) | - | TBD / FIXME / XXX | none found | - |
| `tools/check_licences.py` | 32 | `_PLACEHOLDERS` | ℹ️ Info | Legitimate SPDX placeholder set, not a stub |
| `epb/index.py` | open_issues | unsanitised interpolation | 🛑 Blocker | Gap 2 |
| `epb/mime.py` | `_mpeg_frame` | over-broad magic signature | 🛑 Blocker | Gap 4 |
| `epb/commands/init.py` | run | side effects before validation | 🛑 Blocker | Gap 3 |
| `.github/workflows/ci.yml` + `pyproject.toml` | env / filterwarnings | CI-only failure mode | 🛑 Blocker | Gap 1 |
| `epb/doctor/gitcheck.py` | - | reports "safe" when git errors (review B-WR-01) | ⚠️ Warning | The WS-11 git warning can be silently missed |
| `.github/workflows/ci.yml` | - | `claude plugin validate --strict` never runs on GitHub runners (C-WR-06); actions on mutable tags, no `permissions:` (C-WR-05) | ⚠️ Warning | The D-02 gate runs only locally |
| `tests/store/test_crash_resume.py` | - | the upgrade transaction is outside the crash matrix (D-WR-06) | ℹ️ Info | v0.1.0 registers no upgrade step, so it never runs in production yet |

The remaining 01-REVIEW.md warnings and info findings (all disposition `open`) do not, on their own, falsify a phase must-have. They should be triaged in 01-REVIEW-DISPOSITION.md before the phase closes.

### Human Verification Required

1. **Owner smoke import (SC4).** Run `.venv/bin/python tools/make-smoke-pack.py`, import `scratch/smoke/evidence-pack-smoke.xlsx` into a new ProbeMatrix test incident, and check all 21 checklist lines. Expected: every value shows exactly as written and lists split into separate entries. Only the owner reports the result.
2. **Real `doctor --setup` (PKG-06).** Run `EPB_NETWORK_TESTS=1 .venv/bin/python -m pytest -q tests/launcher/test_setup_real.py`, then `python3 plugin/skills/evidence-pack/scripts/epb.py doctor --setup`. Expected: pass; exit 0; marker written; `init` then runs inside the environment.
3. **Claude Code install (PKG-01, 01-15).** Run `EPB_HOST_TESTS=1 .venv/bin/python -m pytest -q tests/packaging/test_host_install.py`, then follow manual chapter 4 on a clean profile. Expected: the cache holds only the plugin subtree.
4. **GitHub CI run (PKG-09, TST-01, PKG-11)** after the CI gap is fixed and the owner approves the push. Expected: both legs green, including the dependency-age check.
5. **Manual read-through (DOC-04, DOC-05).** Expected: plain language, accurate privacy chapter.
6. **Judgment prohibitions and C-IN-09.** Owner confirms the three judgment-tier prohibitions and decides on the GitHub handle.
7. **Design amendments A16-A30 wording.**

### Gaps Summary

Five gaps, from four independent root causes plus one documentation defect:

1. **CI cannot be green (gap 1).** This is one configuration mismatch: CI escalates EncodingWarning, which openpyxl and `launcher._probe` trigger. The fix is a narrow warning filter, `encoding=` on the probe, and local runs that match CI. Blocks SC5, PKG-09, TST-01 and the CI leg of PKG-11.
2. **INDEX.md integrity (gap 2).** List lines in Open issues interpolate raw paths. A newline in a file name adds headings and can forge an `Imported?` tick, which Phase 6 will read back as a workbook lock. This is a small sanitiser fix plus a regression test.
3. **Refused init leaves `.epb/` (gap 3).** Settings are validated after `open_for_init` writes. Move validation first and tighten the test.
4. **UTF-16 text inventoried as MP3 (gap 4).** The MPEG sniff matches the UTF-16LE BOM. Since content wins (D-13), Phase 2 would mis-route Windows text exports, which are common in investigations.
5. **Privacy promise (gap 5).** The manual says INDEX.md uses role labels; it shows raw file names. The code fix is Phase 4 (deferred). The wording, the workspace-contract classifications and a SKILL.md warning are Phase 1 fixes.

Gaps 2 to 4 are each well localised. The review supplies concrete fixes for all of them, and none requires redesign. The phase should not be marked complete, and REQUIREMENTS.md should not list WS-01, WS-02, WS-09, PKG-09, TST-01 or DOC-04 as Complete until `/gsd-plan-phase 1 --gaps` closes these and the owner-only items above are reported.

---

_Verified: 2026-10-18T12:08:58Z_
_Verifier: Claude (gsd-verifier)_
