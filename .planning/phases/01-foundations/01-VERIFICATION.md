---
phase: 01-foundations
verified: 2026-10-18T16:11:48Z
status: gaps_found
score: 19/23 must-haves verified
covered_files: [".claude-plugin/marketplace.json",".github/workflows/ci.yml",".gitignore",".planning/phases/01-foundations/01-01-PLAN.md",".planning/phases/01-foundations/01-01-SUMMARY.md",".planning/phases/01-foundations/01-02-PLAN.md",".planning/phases/01-foundations/01-02-SUMMARY.md",".planning/phases/01-foundations/01-03-PLAN.md",".planning/phases/01-foundations/01-03-SUMMARY.md",".planning/phases/01-foundations/01-04-PLAN.md",".planning/phases/01-foundations/01-04-SUMMARY.md",".planning/phases/01-foundations/01-05-PLAN.md",".planning/phases/01-foundations/01-05-SUMMARY.md",".planning/phases/01-foundations/01-06-PLAN.md",".planning/phases/01-foundations/01-06-SUMMARY.md",".planning/phases/01-foundations/01-07-PLAN.md",".planning/phases/01-foundations/01-07-SUMMARY.md",".planning/phases/01-foundations/01-08-PLAN.md",".planning/phases/01-foundations/01-08-SUMMARY.md",".planning/phases/01-foundations/01-09-PLAN.md",".planning/phases/01-foundations/01-09-SUMMARY.md",".planning/phases/01-foundations/01-10-PLAN.md",".planning/phases/01-foundations/01-10-SUMMARY.md",".planning/phases/01-foundations/01-11-PLAN.md",".planning/phases/01-foundations/01-11-SUMMARY.md",".planning/phases/01-foundations/01-12-PLAN.md",".planning/phases/01-foundations/01-12-SUMMARY.md",".planning/phases/01-foundations/01-13-PLAN.md",".planning/phases/01-foundations/01-13-SUMMARY.md",".planning/phases/01-foundations/01-14-PLAN.md",".planning/phases/01-foundations/01-14-SUMMARY.md",".planning/phases/01-foundations/01-15-PLAN.md",".planning/phases/01-foundations/01-15-SUMMARY.md",".planning/phases/01-foundations/01-16-PLAN.md",".planning/phases/01-foundations/01-16-SUMMARY.md",".planning/phases/01-foundations/01-17-PLAN.md",".planning/phases/01-foundations/01-17-SUMMARY.md",".planning/phases/01-foundations/01-18-PLAN.md",".planning/phases/01-foundations/01-18-SUMMARY.md",".planning/phases/01-foundations/01-19-PLAN.md",".planning/phases/01-foundations/01-19-SUMMARY.md",".planning/phases/01-foundations/01-20-PLAN.md",".planning/phases/01-foundations/01-20-SUMMARY.md",".planning/phases/01-foundations/01-21-PLAN.md",".planning/phases/01-foundations/01-21-SUMMARY.md",".planning/phases/01-foundations/01-22-PLAN.md",".planning/phases/01-foundations/01-22-SUMMARY.md","AGENTS.md","CLAUDE.md","README.md","docs/USER-MANUAL.md","docs/design/2026-10-17-evidence-pack-builder-design.md","plugin/.claude-plugin/plugin.json","plugin/.codex-plugin/plugin.json","plugin/AGENTS.md","plugin/requirements-docs.txt","plugin/requirements-email.txt","plugin/requirements-media.txt","plugin/requirements.txt","plugin/security-exceptions.json","plugin/skills/evidence-pack/SKILL.md","plugin/skills/evidence-pack/references/evidence-pack-v2.md","plugin/skills/evidence-pack/references/workspace-contract.md","plugin/skills/evidence-pack/scripts/epb.py","plugin/skills/evidence-pack/scripts/epb/__init__.py","plugin/skills/evidence-pack/scripts/epb/casefile.py","plugin/skills/evidence-pack/scripts/epb/cli.py","plugin/skills/evidence-pack/scripts/epb/commands/__init__.py","plugin/skills/evidence-pack/scripts/epb/commands/doctor.py","plugin/skills/evidence-pack/scripts/epb/commands/init.py","plugin/skills/evidence-pack/scripts/epb/commands/scan.py","plugin/skills/evidence-pack/scripts/epb/commands/status.py","plugin/skills/evidence-pack/scripts/epb/doctor/__init__.py","plugin/skills/evidence-pack/scripts/epb/doctor/gitcheck.py","plugin/skills/evidence-pack/scripts/epb/doctor/probes.py","plugin/skills/evidence-pack/scripts/epb/doctor/report.py","plugin/skills/evidence-pack/scripts/epb/doctor/setup.py","plugin/skills/evidence-pack/scripts/epb/doctor/syncfolders.py","plugin/skills/evidence-pack/scripts/epb/doctor/tools.py","plugin/skills/evidence-pack/scripts/epb/errors.py","plugin/skills/evidence-pack/scripts/epb/faults.py","plugin/skills/evidence-pack/scripts/epb/formats/__init__.py","plugin/skills/evidence-pack/scripts/epb/formats/probematrix_v2.py","plugin/skills/evidence-pack/scripts/epb/formats/validate.py","plugin/skills/evidence-pack/scripts/epb/formats/writer.py","plugin/skills/evidence-pack/scripts/epb/fsio.py","plugin/skills/evidence-pack/scripts/epb/index.py","plugin/skills/evidence-pack/scripts/epb/launcher.py","plugin/skills/evidence-pack/scripts/epb/lock.py","plugin/skills/evidence-pack/scripts/epb/mime.py","plugin/skills/evidence-pack/scripts/epb/runs.py","plugin/skills/evidence-pack/scripts/epb/schema.py","plugin/skills/evidence-pack/scripts/epb/schemas/case.schema.json","plugin/skills/evidence-pack/scripts/epb/schemas/chunks.schema.json","plugin/skills/evidence-pack/scripts/epb/schemas/envelope.schema.json","plugin/skills/evidence-pack/scripts/epb/schemas/run.schema.json","plugin/skills/evidence-pack/scripts/epb/schemas/source.schema.json","plugin/skills/evidence-pack/scripts/epb/schemas/state.schema.json","plugin/skills/evidence-pack/scripts/epb/sources/__init__.py","plugin/skills/evidence-pack/scripts/epb/sources/classify.py","plugin/skills/evidence-pack/scripts/epb/sources/expanders/__init__.py","plugin/skills/evidence-pack/scripts/epb/sources/scan.py","plugin/skills/evidence-pack/scripts/epb/sources/sidecars.py","plugin/skills/evidence-pack/scripts/epb/state.py","plugin/skills/evidence-pack/scripts/epb/txn.py","plugin/skills/evidence-pack/scripts/epb/upgrade.py","plugin/skills/evidence-pack/scripts/epb/workspace.py","plugin/skills/evidence-pack/scripts/epb/yamlio.py","pyproject.toml","requirements-dev-full.txt","requirements-dev.txt","tests/cli/test_exit_codes.py","tests/conftest.py","tests/core/test_mime.py","tests/core/test_yamlio.py","tests/docs/test_manual.py","tests/doctor/test_gitcheck.py","tests/doctor/test_probes.py","tests/doctor/test_syncfolders.py","tests/epbtest/crash.py","tests/epbtest/envkit.py","tests/epbtest/packkit.py","tests/formats/test_contract.py","tests/formats/test_validator.py","tests/formats/test_writer.py","tests/index/test_index.py","tests/launcher/test_launcher.py","tests/launcher/test_setup.py","tests/launcher/test_setup_real.py","tests/packaging/test_host_install.py","tests/packaging/test_install_codex.py","tests/packaging/test_manifests.py","tests/packaging/test_plugin_agents_md.py","tests/packaging/test_references.py","tests/packaging/test_requirements.py","tests/packaging/test_skill_lint.py","tests/repo/test_ci_workflow.py","tests/repo/test_instructions_mirror.py","tests/repo/test_no_network.py","tests/repo/test_text_subprocess_encoding.py","tests/schemas/test_state_schema.py","tests/sources/test_scan_classify.py","tests/sources/test_scan_fingerprint.py","tests/sources/test_sidecars.py","tests/store/test_crash_resume.py","tests/store/test_fsio_retry.py","tests/store/test_lock.py","tests/store/test_upgrade.py","tests/store/test_validate.py","tests/tools/test_dependency_checks.py","tests/tools/test_smoke_pack.py","tests/workspace/test_git_warning.py","tests/workspace/test_init.py","tests/workspace/test_init_defaults.py","tests/workspace/test_layout.py","tests/workspace/test_status.py","tools/check_dependency_age.py","tools/check_licences.py","tools/install-codex.py","tools/licence-allowlist.json","tools/make-smoke-pack.py"]
covered_digest: "v3:sha256:a56d2f70cff04fcbca1966de1a93cb51d33059410a8cdce2ad0a869a7f243271"
behavior_unverified: 1
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_score: 15/23
  gaps_closed:
    - "INDEX.md always has exactly six level-2 headings in order 1 to 6, and input file names cannot add headings or Imported? tick lines (gap 2, 01-18)"
    - "On a folder that is not set up, a refused init exits 2 and writes nothing (gap 3, 01-19)"
    - "epb scan records the correct MIME type for every input; magic bytes override the extension only for genuine signatures (gap 4, 01-20)"
    - "The manual's privacy chapter describes what the plugin does today and does not promise that INDEX.md uses role labels instead of names (gap 5, 01-21; owner read-through still pending as a human item)"
  gaps_remaining:
    - "Linux CI runs pytest, ruff, the dependency-age check and the licence allow-list, all green (gap 1: narrowed from pytest red on both legs to the licence step red on the 3.11 leg)"
  regressions: []
gaps:
  - truth: "Linux CI runs pytest, ruff, the dependency-age check and the licence allow-list, all green (ROADMAP SC5; PKG-09)"
    status: partial
    reason: "GitHub run 39141925712 for head 8c84d0d (read back by the verifier with gh) concluded failure. core (3.14) is green on every step. core (3.11) is green on Lint, Format, Tests (1977 passed, 4 skipped) and Dependency age, but fails 'Licence allow-list (D-12)': 'VIOLATION setuptools 79.0.1: licence unknown (no usable licence metadata; from none)', '1 of 36 distributions failed the licence check'. setuptools is preinstalled in the GitHub Python 3.11 toolcache and is absent from the 3.14 toolcache and from the local 3.14 dev venv, so no local run can reproduce it. Only planning documents changed between 8c84d0d and HEAD 835829c, so the run reflects the current source. The pytest half of the original gap (EncodingWarning) is closed."
    artifacts:
      - path: "tools/check_licences.py"
        issue: "Finds no License-Expression, License or License classifier for the runner's setuptools 79.0.1 and reports it as a violation"
      - path: "tools/licence-allowlist.json"
        issue: "No reviewed override for setuptools (MIT), and no rule for runner-preinstalled bootstrap tools"
      - path: ".github/workflows/ci.yml"
        issue: "The 3.11 job checks the toolcache's preinstalled setuptools along with the project's dependencies"
    missing:
      - "Make the 3.11 licence step pass in a reviewed way: a documented override for setuptools (MIT) in licence-allowlist.json, OR exclude runner-preinstalled bootstrap distributions (pip, setuptools) from the check, OR remove or upgrade setuptools in the 3.11 job before the check"
      - "Add a unit test in tests/tools for the chosen rule (a distribution with no licence metadata named setuptools)"
      - "Optionally add tools/check_licences.py (and the dependency-age check) to the documented full check in AGENTS.md/CLAUDE.md, so local parity covers the step that failed (review IN-05)"
      - "Owner-approved push, then a green ci run on both core legs for the pushed head SHA"
  - truth: "epb scan inventories every input in inputs/; one awkward file name cannot stop the scan of the whole case (ROADMAP SC2 / WS-02 'scan fingerprints every input'; review CR-01, new scope with deterministic evidence)"
    status: failed
    reason: "Reproduced by the verifier in a scratch case: a file created as b'inputs/bad\\xffname.txt' (bytes that are not valid UTF-8, as produced by unzip of a Windows CP437/CP1252 ZIP or a copy from an old FAT/SMB share) makes 'epb scan --json' exit 4 with INTERNAL_ERROR ('An internal error occurred (UnicodeEncodeError)') and the hint 'Report this error code to the plugin maintainer. Do not edit the evidence or the .epb folder.' No input is inventoried and the error does not name the file. A second reproduction, a name containing the raw byte 0x85, crashed the same way ('\\udc85 ... surrogates not allowed'). os.walk yields surrogate-escaped str names, and fsio.json_bytes encodes them as strict UTF-8. No test covers undecodable names. scan.py and fsio.py predate the gap round, so this is a new-scope finding; it stays blocking because a reproducible crash is deterministic evidence."
    artifacts:
      - path: "plugin/skills/evidence-pack/scripts/epb/sources/scan.py"
        issue: "walk() keeps surrogate-escaped names and passes them into source and run records"
      - path: "plugin/skills/evidence-pack/scripts/epb/fsio.py"
        issue: "json_bytes encodes with strict UTF-8 and raises UnicodeEncodeError on lone surrogates"
      - path: "plugin/skills/evidence-pack/scripts/epb/index.py"
        issue: "_IGNORED_REASONS has no reason for an undecodable name"
    missing:
      - "Detect names that do not encode as UTF-8 during the walk and record them as ignored with a new reason (for example 'bad-name': a file whose name is not valid text; rename it), using a display-safe path (surrogateescape then 'replace')"
      - "Add the reason to the run schema's ignored-reason enum and to INDEX.md Open issues wording"
      - "POSIX-only regression test: scan inputs/bad\\xffname.txt next to a normal file; assert exit 0, the normal file inventoried, an Open issues line for the bad name, and no INTERNAL_ERROR (also for a link with such a name)"
deferred:
  - truth: "INDEX.md and shareable output show role labels instead of personal names found in input file names (code side of C-CR-01)"
    addressed_in: "Phase 4"
    evidence: "Phase 4 SC2: 'An input whose file name contains a name appears in INDEX.md under its role label.' PF-04: 'Phase 4 adds file-name substitution and scans INDEX'. WS-10 and DEID-08 are Phase 4 requirements."
advisory: []
behavior_unverified_items:
  - truth: "epb doctor --setup, launched through the standard-library-only epb.py, finds Python 3.11+, builds the private environment, installs the core packages under the two-week rule and reports what is ready and optional; afterwards normal commands re-run inside the environment (ROADMAP SC5, PKG-06)"
    test: "On a Linux machine with internet access, from the repo root run: EPB_NETWORK_TESTS=1 .venv/bin/python -m pytest -q tests/launcher/test_setup_real.py. Then, as a real user, run python3 plugin/skills/evidence-pack/scripts/epb.py doctor --setup and then epb.py doctor."
    expected: "The networked test passes. doctor --setup ends with the Ready / Optional, not installed / What to do next checklist and exit 0; ~/.local/share/probematrix-epb/envs/0.1.0-dev.1/epb-env.json exists; a following 'epb.py doctor' exits 0 and 'epb.py init' runs inside the environment."
    why_human: "Needs network and a real package download; the verifier must not reach external services or write the real per-user data folder. The offline tests with fakes pass, but the only real venv/pip test is opt-in and was skipped in this run."
human_verification:
  - test: "Owner smoke import (ROADMAP SC4): run .venv/bin/python tools/make-smoke-pack.py (writes scratch/smoke/evidence-pack-smoke.xlsx), import it into a new ProbeMatrix test incident on Replit, and walk the 21-line checklist the tool prints."
    expected: "Every value shows exactly as written: =SUM(A1:A2), +44, -5 °C and @shift-lead stay text; 0 is not blank; 40000000000000000001 keeps all 20 digits; 2026-09 and 2026 stay as written; Tags and Linked Equipment split into 3 entries and Linked Individuals into 2; all eight QA Status values show. The owner reports the result; the agent never claims it."
    why_human: "ProbeMatrix runs only on Replit and only the owner imports. The verifier re-built the pack (0 validator findings) in this run."
  - test: "doctor --setup end to end (see behavior_unverified_items)"
    expected: "Networked test passes; setup completes with exit 0 and the environment marker written"
    why_human: "Network and the real per-user data folder"
  - test: "First-use install in Claude Code (ROADMAP SC5, PKG-01): EPB_HOST_TESTS=1 .venv/bin/python -m pytest -q tests/packaging/test_host_install.py, then follow manual chapter 4 on a clean Claude Code profile: /plugin marketplace add <repo path>, /plugin install probematrix-evidence-pack-builder."
    expected: "Both host tests pass; the plugin cache holds skills/evidence-pack/SKILL.md, scripts/epb.py, the schemas, AGENTS.md and the requirement files, and no docs/, tests/, tools/ or .planning/."
    why_human: "Drives real host CLIs; opt-in and skipped in this run"
  - test: "GitHub CI run after the licence gap is fixed and the owner approves the push (01-22 human-check)"
    expected: "Jobs core (3.11) and core (3.14) both green, including Lint, Format check, Tests, 'Dependency age, two-week rule (PKG-09)' and 'Licence allow-list (D-12)'; 'Plugin manifests (D-02)' prints 'claude CLI not installed; skipping plugin validate (D-02)'"
    why_human: "Needs an owner-approved push; only the hosted run shows the 3.11 leg"
  - test: "Owner read-through of the corrected privacy text (01-21 human-check; DOC-04; security T-01-55 high, open): read docs/USER-MANUAL.md chapter 2 'De-identification and file names' and chapter 6 'Put your files in inputs/' and 'Read INDEX.md'; read workspace-contract.md's review-before-sharing class."
    expected: "Chapter 2 says this version shows file names as given in INDEX.md and .epb, tells you to rename files containing a person's name before putting them in inputs/, and says role labels arrive later; chapter 6 repeats it briefly; you agree with the interim review-before-sharing label for INDEX.md, .epb/state.json and .epb/sources/ until Phase 4. Also decide on review WR-01 (see Gaps Summary): SKILL.md step 6 suggests renaming after a scan, which does not remove the name when the content also changed."
    why_human: "Plain-language quality and acceptance of the interim label are the owner's call; the security gate T-01-55 is held open for this read-through"
  - test: "Manual read-through of chapters 1-7 as a non-technical user (DOC-05)"
    expected: "Plain language; Windows and macOS sections each marked 'not yet tested on this system'; no claim that nothing leaves the computer"
    why_human: "Readability and tone are judgement calls"
  - test: "Judgment-tier prohibitions (non-authoritative LLM verdict: holds): 01-04 'never claim an import worked'; 01-15 'no real names, reference-report or prototype prose'; 01-16 'never imply nothing leaves the computer'; 01-21 'MUST NOT tell the agent to rename, move or edit a file in inputs/' (SKILL.md line 77: 'suggest they rename the file themselves ... You never rename, move or edit anything in inputs/'); 01-22 'no push without approval, no force-push, CI verdict only from the real run' (origin/phase-01-foundations at 8c84d0d is an ancestor of HEAD; verdict read from run 39141925712)."
    expected: "Owner confirms each. Earlier note C-IN-09: the GitHub handle 'ashley-eyekyam' in committed manifests contains the owner's own first name; decide whether that is acceptable under the 'never write real names' rule."
    why_human: "Judgment-tier prohibitions need explicit human resolution in interactive verify"
  - test: "Wording check of design amendments A16-A30 (docs/design/2026-10-17-evidence-pack-builder-design.md lines 672-686)"
    expected: "Each row states the decision as the owner intended and cites its D-NN or research item"
    why_human: "Spec wording is the owner's call"
---

# Phase 1: Foundations Verification Report

**Phase Goal:** A user can set the plugin up once, create a case folder and inventory its inputs safely. The workbook format is proven against the real ProbeMatrix importer before any evidence logic exists.
**Verified:** 2026-10-18T16:11:48Z
**Status:** gaps_found
**Re-verification:** Yes, after gap closure (plans 01-17 to 01-22)

Four of the five earlier gaps are closed. I reproduced each fix myself in scratch case folders, not from the summaries. Two blockers remain:

- **CI is still red (gap 1, narrowed).** The pytest failures under `PYTHONWARNDEFAULTENCODING=1` are fixed, and Tests pass on both CI legs. The 3.11 leg now fails the licence allow-list on the runner's preinstalled setuptools.
- **New, evidenced: a file name that is not valid UTF-8 crashes `scan` for the whole case** (review CR-01, reproduced).

No previously passing truth regressed. The owner-only items are still outstanding: smoke import, real setup, host install, a green CI run and the privacy read-through.

## Goal Achievement

### Observable Truths

The must-haves are carried over verbatim from the previous report (re-verification mode). For the four gaps marked closed, I re-ran the original failing scenario plus edge variants. For the previously passing truths, I ran the full CI-equivalent suite once plus a regression spot-check.

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | `epb init` in an empty folder creates the full layout (SC1, WS-01) | ✓ VERIFIED | Regression run: exit 0; `.epb/` holds `.gitattributes .gitignore case.yaml inbox lock private runs state.json tmp`; `inputs/`, `outputs/` and `INDEX.md` present |
| 2 | `state.json` holds workbook registry, counters and chunk status (SC1, WS-13) | ✓ VERIFIED | Unchanged since previous pass; tests/schemas/test_state_schema.py passes in the full run |
| 3 | `.epb/.gitignore` covers the seven folders (SC1, WS-11) | ✓ VERIFIED | Regression run: `segments/ ledger/ inbox/ tmp/ media/ runs/ private/` |
| 4 | INDEX.md shows six sections with "none yet" after init (SC1, WS-09) | ✓ VERIFIED | Regression run: 6 `## ` headings |
| 5 | INDEX.md keeps exactly six headings whatever the input names; names cannot forge `- [x] Imported:` lines (WS-09, PF-04) | ✓ VERIFIED (gap 2 closed) | Scratch scan with a regular file, a symlink, a FIFO, a folder, and a dangling link, all named with LF, CR, U+2028, U+0085 and U+001E plus `## …` and `- [x] Imported: …` text: exit 0, exactly 6 headings in order, zero tick lines, `splitlines()` equals `split("\n")`; Open issues render each hostile name on one line. `_inline` is used 20 times in index.py; `_SINGLE_LINE` covers C0, DEL, C1, U+2028 and U+2029. `test_scan_of_line_breaking_names_keeps_six_headings` passes |
| 6 | `init` and `doctor` warn in sync folders and in git repos that track `.epb/private/` (SC1, WS-11, WS-12) | ✓ VERIFIED | Unchanged code; test_gitcheck, test_syncfolders and test_git_warning pass in the full run |
| 7 | `scan` reports new, changed (`S004v2`), renamed, duplicate and removed inputs, ignores OS junk and pairs sidecars (SC2, WS-02-04) | ✓ VERIFIED | Regression corpus: new [S006], new_versions S004 v2, renamed S002, duplicates S001, removed [S003], ignored `.DS_Store` (junk), sidecar S005→S004; INDEX shows `S004v2`; rescan "No changes since the last scan." |
| 8 | `scan` records the correct MIME type for every input; content wins only for genuine signatures (WS-02, D-13) | ✓ VERIFIED (gap 4 closed) | Scratch scan: UTF-16LE `log.txt` and `export.csv`, UTF-16BE `be.txt`, UTF-8-BOM `u8.csv`, UTF-32LE `u32.txt` and UTF-16LE `w.txt` starting with U+00FF are all recorded by name (text/plain, text/csv), with `mime_mismatch` null and no warning. A synthetic 3-frame MPEG stream named `.txt` is still detected as MP3 (genuine mismatch warning). A PDF named `report.docx` is still application/pdf with MIME_MISMATCH. `_TEXT_BOMS` is checked before MAGIC_RULES (mime.py:277); `_mpeg_frame` requires a second header at `_mpeg_frame_length` (mime.py:176-190) |
| 9 | A crash injected at every transaction step resumes cleanly (SC2, WS-06, TST-07) | ✓ VERIFIED | txn/fsio unchanged; tests/store/test_crash_resume.py passes in the full CI-env run |
| 10 | A second mutating run waits for the lock (SC2, WS-07) | ✓ VERIFIED | tests/store/test_lock.py passes (01-19 moved validation before the lock; lock tests unchanged and green) |
| 11 | Exit codes 0-4 with stable error codes (SC2, PKG-05) | ✓ VERIFIED | Regression: unknown command, exit 2; refused init, exit 2 BAD_ARGUMENT; tests/cli/test_exit_codes.py passes |
| 12 | YAML `12:30`, `0123` and `no` survive as text (SC2, WS-08) | ✓ VERIFIED | yamlio unchanged; tests/core/test_yamlio.py passes |
| 13 | A refused `init` on a folder that is not set up writes nothing (WS-01) | ✓ VERIFIED (gap 3 closed) | Scratch runs: no `--title`, blank title, bad timezone, bad slug, lowercase prefix and an unusable title each exit 2 BAD_ARGUMENT and leave an empty folder empty. In a populated folder, two refused inits leave the tree unchanged (path, size and mtime hash), and a following valid init then sets it up fully. init.py:63-67 runs `resolve_settings` before `open_for_init`; `_assert_nothing_written` requires an empty folder |
| 14 | Validator passes a generated pack and fails the prototype on list fragments (SC3, DEF-14) | ✓ VERIFIED | Regression: smoke pack 0 findings; prototype: 24 LIST_FRAGMENT_UNBALANCED, 25 LIST_SEMICOLON |
| 15 | Validator rejects formulas, non-strings, blanks, inexact enums, over-long cells, bad custody JSON (SC3, BLD-03) | ✓ VERIFIED | tests/formats/test_validator.py now passes under the CI encoding variable too |
| 16 | Writer: text-only cells, 10-row metadata, headers-only manifest (BLD-01, -02, -08) | ✓ VERIFIED | formats/ unchanged; tests/formats/test_writer.py passes |
| 17 | Owner smoke import shows every edge value exactly as written (SC4) | ? UNCERTAIN | Pack builds with 0 findings; the import is owner-only (human item 1) |
| 18 | Plugin installs into Claude Code from the repo marketplace, `source: "./plugin"` (SC5, PKG-01) | ? UNCERTAIN | Manifests unchanged and correct; host test is opt-in and was skipped (human item 3) |
| 19 | `doctor --setup` builds the private environment (SC5, PKG-06) | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED | Offline tests pass; the networked real-path test was skipped |
| 20 | `doctor` tool report with per-OS commands; `plugin/AGENTS.md` rules (SC5, PKG-07, PKG-03) | ✓ VERIFIED | Unchanged; test_probes and test_plugin_agents_md pass |
| 21 | Linux CI runs pytest, ruff, dependency-age and licence checks, all green (SC5, PKG-09) | ✗ FAILED (gap 1 remains, narrowed) | `gh run view 39141925712`: conclusion failure, headSha 8c84d0d. core (3.14) all green; core (3.11) Tests 1977 passed, 4 skipped, but "Licence allow-list (D-12)" fails: `VIOLATION setuptools 79.0.1: licence unknown (no usable licence metadata; from none)`. Since 8c84d0d only `.planning/` files changed |
| 22 | Manual first edition; AGENTS.md == CLAUDE.md, ≤150 lines, CI test (SC5, DOC-05, PKG-11) | ✓ VERIFIED | `cmp` identical, 43 lines; the full check now carries `PYTHONWARNDEFAULTENCODING=1`; test_instructions_mirror and the drift guard test_documented_full_check_matches_ci pass, including in the CI Tests step on both legs |
| 23 | The manual's privacy statement matches current behaviour (DOC-04, goal "safely") | ✓ VERIFIED (gap 5 closed; owner read-through pending) | Manual lines 58-79: "This version does not replace any names yet. `INDEX.md` and the plugin's own records in the hidden `.epb` folder list your files by their file and folder names"; rename *before* putting files in `inputs/`; check INDEX.md before sharing; do not share `.epb`. Contract and `CONTRACT_PATHS` class INDEX.md, `.epb/state.json` and `.epb/sources/` as review-before-sharing. SKILL.md step 6 tells the agent to flag names by input ID and never to rename. A scratch scan confirms INDEX.md does show the raw file name, as the manual now says. test_no_paragraph_promises_a_name_free_index passes. See WR-01 below for a residual inaccuracy in SKILL.md's after-scan advice |

**Score:** 19/23 truths verified (1 present but behaviour-unverified, 2 uncertain pending owner, 1 failed). Separately, one new evidenced blocker (CR-01) sits outside the carried-over must-haves; see Anti-Patterns.

### Deferred Items

| # | Item | Addressed In | Evidence |
|---|------|-------------|----------|
| 1 | INDEX.md shows role labels for names in input file names (code side of C-CR-01) | Phase 4 | Phase 4 SC2 "An input whose file name contains a name appears in `INDEX.md` under its role label"; PF-04; WS-10, DEID-08 |

Neither open gap is deferred. Phase 10 SC4 also requires CI green on 3.11 and 3.14, but Phase 1 SC5 requires it now, and the ROADMAP note puts the core CI job in Phase 1 (PKG-09). No later phase names undecodable input file names; Phase 2's archive expanders (WS-05) cover zip-slip, not scan of the top-level walk.

### Advisory (New Scope, Unevidenced)

None. Both new-scope findings carry reproducible evidence: CR-01 (a crash) blocks, and WR-01 (a reproduction) is a warning because it does not falsify a must-have.

### Required Artifacts

`gsd-tools verify.artifacts`: plans 01-01 to 01-16 still 75/75; gap plans 01-17 6/6, 01-18 2/2, 01-19 2/2, 01-20 2/2, 01-21 5/5, 01-22 1/1.

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `epb/launcher.py` | probe decodes child output as UTF-8 | ✓ VERIFIED | `encoding="utf-8"`, `errors="replace"` at lines 223-224 |
| `pyproject.toml` | EncodingWarning error, openpyxl temp-file ignore only | ✓ VERIFIED | Two entries; the ignore is scoped to `openpyxl\.worksheet\._writer` |
| `tests/repo/test_text_subprocess_encoding.py`, `tests/repo/test_ci_workflow.py` | AST guard, filter guard, parity guard | ✓ VERIFIED | Present, pass (narrower than claimed: review IN-04, IN-05; security T-01-46 below threshold) |
| `epb/index.py` | `_inline` on every interpolated value | ✓ VERIFIED | Gap 2 reproduction now clean |
| `epb/commands/init.py` | validate before writing | ✓ VERIFIED | Gap 3 reproduction now clean |
| `epb/mime.py` | `_TEXT_BOMS`, two-header MPEG | ✓ VERIFIED | Gap 4 reproduction now clean |
| `docs/USER-MANUAL.md`, `workspace-contract.md`, `workspace.py`, `SKILL.md` | honest file-name privacy text, review-before-sharing class | ✓ VERIFIED | Gap 5 text present and pinned by tests |
| `.github/workflows/ci.yml` | Linux CI, green | ✗ FAILED | Run 39141925712 red on 3.11 licence step |
| `epb/sources/scan.py` + `epb/fsio.py` | scan every input | ✗ BLOCKER | Crashes on non-UTF-8 names (CR-01) |

### Key Link Verification

`gsd-tools verify.key-links`: 01-17 3/3, 01-18 2/2, 01-19 2/2 and 01-21 2/2. 01-20 scored 1/3 and 01-22 0/1 only because their `from:` fields are not plain paths. I checked those links by hand:

| From | To | Via | Status |
| ---- | -- | --- | ------ |
| mime.py `sniff` | `_TEXT_BOMS` | `head.startswith(_TEXT_BOMS)` before MAGIC_RULES (line 277) | WIRED |
| mime.py `_mpeg_frame` | `_mpeg_frame_length` | lines 181 and 185 locate and validate the second header | WIRED |
| `git push origin phase-01-foundations` | ci.yml | `push:` trigger (line 5); run 39141925712 was event push, headSha 8c84d0d | WIRED |
| init.py | casefile.resolve_settings | `resolve_settings(args, case)` before `open_for_init` (lines 63-67) | WIRED |
| index.py providers | `_inline` | every f-string value | WIRED |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| -------- | ------------- | ------ | ------------------ | ------ |
| INDEX.md section 3 / 5 | source records, ignored entries | `.epb/sources/S*.json`, run record `scan.ignored` | Yes: real sanitised paths, `S004v2` | ✓ FLOWING |
| Source record `versions[].mime` | mime | `mime.detect` (sniff, then extension) | Yes: correct for UTF-16/32 and BOM text | ✓ FLOWING |
| CI verdict | run conclusion | GitHub run 39141925712 | Yes: failure (3.11 licence) | ✓ FLOWING (red) |

### Behavioral Spot-Checks

The scripts are `gapcheck.sh` in the session scratchpad plus the inline runs shown. Each runs in a fresh scratch case with a fake HOME and `EPB_IN_ENV=1`.

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| CI-equivalent full check (single full run) | `ruff check . && ruff format --check . && PYTHONWARNDEFAULTENCODING=1 pytest -q`; `tools/check_licences.py`; `cmp AGENTS.md CLAUDE.md` | All checks passed; 98 files formatted; **1978 passed, 3 skipped**; licence check passed (35 distributions, local 3.14); mirror identical | ✓ PASS |
| Hosted CI | `gh run view 39141925712 --json jobs,conclusion,headSha` | failure; 3.14 success; 3.11 Licence allow-list failure | ✗ FAIL |
| Refused init writes nothing | 6 refusal variants, empty and populated folders | exit 2, folders unchanged; then valid init succeeds | ✓ PASS |
| INDEX.md heading/tick invariant | hostile names (LF, CR, U+2028, U+0085, U+001E) on file, link, FIFO, folder | 6 headings, 0 tick lines | ✓ PASS |
| UTF-16 / BOM text MIME | 6 BOM text files + MPEG and PDF controls | text by name, no mismatch; genuine signatures still win | ✓ PASS |
| Non-UTF-8 file name | `open(b'inputs/bad\xffname.txt','wb')` then `epb scan --json` | exit 4 INTERNAL_ERROR (UnicodeEncodeError) | ✗ FAIL (CR-01) |
| Rename plus edit after scan | WR-01 sequence | name remains in INDEX.md lines 23 and 32 and in `.epb/sources/S001.json` | ⚠️ reproduces WR-01 |
| Regression scan corpus | new / edit / rename / copy / delete / junk / sidecar | all correct, `S004v2`, idempotent rescan | ✓ PASS |
| Smoke pack + prototype | `make-smoke-pack.py --out <scratch>`; `validate_workbook` | 0 findings; prototype 24 LIST_FRAGMENT_UNBALANCED | ✓ PASS |
| Dependency-age check | not run (queries PyPI) | green on both hosted legs in run 39141925712 | ✓ PASS (hosted) |
| Real setup / host install | opt-in tests | not run | ? SKIP: human items 2-3 |

### Probe Execution

No `scripts/*/tests/probe-*.sh` exists and no plan declares a probe. Step 7c: not applicable.

### Requirements Coverage

All 27 phase requirement IDs are claimed by at least one plan (01-01 to 01-22). REQUIREMENTS.md maps no other ID to Phase 1, so none are orphaned. REQUIREMENTS.md currently shows every Phase 1 checkbox `[ ]` and the traceability status "Gaps Found" (PKG-11 "Pending"). The recommended statuses below follow from the evidence.

| Requirement | Source Plan | Description (short) | Status | Evidence |
| ----------- | ----------- | ------------------- | ------ | -------- |
| WS-01 | 01-07, 01-09, 01-11, 01-19 | init layout, case.yaml | ✓ SATISFIED | Truths 1, 13 |
| WS-02 | 01-13, 01-20 | scan fingerprints every input, MIME | ✗ BLOCKED (partial) | MIME fixed (truth 8); a non-UTF-8 name stops the whole scan (CR-01) |
| WS-03 | 01-13, 01-14 | change detection | ✓ SATISFIED | Truth 7 |
| WS-04 | 01-14 | sidecars | ✓ SATISFIED | Truth 7 |
| WS-06 | 01-07, 01-12 | atomic journalled writes | ✓ SATISFIED | Truth 9 |
| WS-07 | 01-12 | lock | ✓ SATISFIED | Truth 10 |
| WS-08 | 01-07, 01-09 | schema on write, strict YAML | ✓ SATISFIED | Truth 12 |
| WS-09 | 01-11, 01-18 | INDEX.md six sections | ✓ SATISFIED | Truths 4, 5 |
| WS-11 | 01-08, 01-11 | .gitignore, git warning | ✓ SATISFIED | Truths 3, 6 |
| WS-12 | 01-08, 01-11 | sync-folder warnings | ✓ SATISFIED | Truth 6 |
| WS-13 | 01-07 | state schema | ✓ SATISFIED | Truth 2 |
| BLD-01 | 01-04, 01-15 | format module + reference | ✓ SATISFIED | Truth 16 |
| BLD-02 | 01-04 | text-only cells | ✓ SATISFIED | Truth 16 |
| BLD-03 | 01-04 | strict validator | ✓ SATISFIED | Truth 15 |
| BLD-08 | 01-02, 01-04 | 10-row metadata, empty manifest | ✓ SATISFIED | Truth 16 |
| PKG-01 | 01-02, 01-06, 01-15 | plugin/ + marketplace | ? NEEDS HUMAN | Truth 18 |
| PKG-03 | 01-06, 01-15 | plugin AGENTS.md | ✓ SATISFIED | Truth 20 |
| PKG-05 | 01-03 | exit codes | ✓ SATISFIED | Truth 11 |
| PKG-06 | 01-03, 01-10 | stdlib launcher, doctor --setup | ? NEEDS HUMAN | Truth 19 |
| PKG-07 | 01-08 | doctor tool report | ✓ SATISFIED | Truth 20 |
| PKG-08 | 01-01, 01-02, 01-10 | permissive pinned core, GPL extras split | ✓ SATISFIED | test_requirements passes |
| PKG-09 | 01-05, 01-17, 01-22 | CI dependency-age and licence checks | ✗ BLOCKED | Age check green on both legs; licence check red on 3.11 (truth 21) |
| PKG-11 | 01-05, 01-16, 01-17, 01-22 | AGENTS.md == CLAUDE.md, ≤150 lines, CI test | ✓ SATISFIED | Truth 22; the mirror test runs green inside the CI Tests step on both legs. The red licence step belongs to PKG-09, not PKG-11 |
| TST-01 | 01-01, 01-05, 01-17, 01-22 | pytest + ruff, no network, optional skips | ✓ SATISFIED | Lint, Format and Tests green on both hosted legs (1977 passed, 4 skipped); locally 1978 passed, 3 skipped under the CI variable |
| TST-07 | 01-12, 01-14 | crash injection per step | ✓ SATISFIED | Truth 9 |
| DOC-04 | 01-16, 01-21 | privacy chapter | ? NEEDS HUMAN | Text is accurate and tested (truth 23); owner read-through is the open high threat T-01-55 |
| DOC-05 | 01-16 | manual started, Win/mac marked | ✓ SATISFIED | Truth 22 |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| 20 files changed since the previous pass | - | TBD / FIXME / XXX | none found | - |
| `epb/sources/scan.py` + `epb/fsio.py` | scan.py:150-175, fsio.py:64-67 | Surrogate-escaped names reach strict UTF-8 encoding | 🛑 Blocker (new scope, evidenced by reproduction) | CR-01: one file stops every scan of the case |
| `tools/check_licences.py` / CI 3.11 job | - | Runner-preinstalled package with no licence metadata | 🛑 Blocker | Gap 1 (carried forward) |
| `plugin/skills/evidence-pack/SKILL.md` | 77 | After-scan "suggest they rename the file" remedy does not hold for rename plus edit, or for older versions | ⚠️ Warning (WR-01, reproduced) | A name can persist in a review-before-sharing file with no supported way to remove it; the manual's "check before sharing" step still prevents an unknowing share |
| `epb/index.py` | 79 | `_inline` leaves bidi/zero-width (Cf) characters and Markdown link syntax | ℹ️ Info (IN-01) | Names can be visually disguised in a file the user is told to check |
| `workspace-contract.md` vs manual | 12-15 vs 79 | Contract allows keeping `.epb` records in version control after review; manual says never share `.epb` | ℹ️ Info (IN-03) | Mixed advice |
| `tests/repo/test_ci_workflow.py`, `test_text_subprocess_encoding.py` | - | Guards narrower than their docstrings | ℹ️ Info (IN-04, IN-05; T-01-46 below threshold) | Parity guard does not cover the licence step that failed |
| `tests/doctor/test_gitcheck.py` | 142-154 | Skips instead of being hermetic | ℹ️ Info (IN-06) | Branch untested on machines with a `.git` above the temp folder |

### Human Verification Required

1. **Owner smoke import (SC4).** Run `.venv/bin/python tools/make-smoke-pack.py`, import `scratch/smoke/evidence-pack-smoke.xlsx` into a new ProbeMatrix test incident, and check all 21 checklist lines. Expected: every value shows exactly as written. Only the owner reports the result.
2. **Real `doctor --setup` (PKG-06).** Run `EPB_NETWORK_TESTS=1 .venv/bin/python -m pytest -q tests/launcher/test_setup_real.py`, then `python3 plugin/skills/evidence-pack/scripts/epb.py doctor --setup`. Expected: the test passes, exit 0 and the marker is written.
3. **Claude Code install (PKG-01).** Run `EPB_HOST_TESTS=1 .venv/bin/python -m pytest -q tests/packaging/test_host_install.py`, then follow manual chapter 4 on a clean profile.
4. **GitHub CI (PKG-09)**, after the licence gap is fixed and the owner approves a push. Expected: both core legs green on every step.
5. **Privacy read-through (DOC-04, T-01-55).** Read chapters 2 and 6 and the review-before-sharing class, and decide on WR-01.
6. **Manual read-through of chapters 1-7 (DOC-05).**
7. **Judgment-tier prohibitions** (01-04, 01-15, 01-16, 01-21, 01-22) and the C-IN-09 handle question.
8. **Design amendments A16-A30 wording.**

### Gaps Summary

Two blockers, from two independent root causes:

1. **CI licence step on Python 3.11 (gap 1, carried forward and narrowed).** 01-17 fixed the EncodingWarning failures. The hosted Tests step is green on both legs, and so are lint, format and the dependency-age rule. The run is still red because the GitHub 3.11 toolcache ships setuptools 79.0.1, and `tools/check_licences.py` finds no licence metadata for it. The fix is a reviewed decision: override setuptools as MIT, exclude runner bootstrap tools, or remove or upgrade setuptools in the 3.11 job. Then an owner-approved push and a green run are needed. Blocks ROADMAP SC5 and PKG-09.
2. **Non-UTF-8 input file names crash `scan` (review CR-01, new scope, reproduced).** On Linux such names are realistic, for example from unzipping Windows ZIPs or copying from old shares. One such file stops every scan with INTERNAL_ERROR, and the error does not name the file. That contradicts the phase goal "inventory its inputs safely" and WS-02 "fingerprints every input". The fix is small: report the file as ignored with a rename hint and add a POSIX regression test. It was not part of the gap round, but a reproducible crash is deterministic evidence, so it blocks.

One warning, for the owner to decide at UAT:

- **WR-01.** The manual is accurate: rename before copying in, and check INDEX.md before sharing. But SKILL.md step 6 suggests renaming *after* a scan. If the content also changed, the old name stays in INDEX.md as a removed input. Older versions keep it in `.epb/sources/` in every case. No supported command removes it. Either reword SKILL.md (warn before the copy, and say the only clean fix after a scan is a new case folder) or render removed sources by ID only.

The phase should not be marked complete. REQUIREMENTS.md can move WS-01, WS-03, WS-04, WS-06, WS-07, WS-08, WS-09, WS-11, WS-12, WS-13, BLD-01/02/03/08, PKG-03/05/07/08/11, TST-01, TST-07 and DOC-05 to Complete on this evidence. WS-02 and PKG-09 wait for the two gaps. PKG-01, PKG-06 and DOC-04 wait for the owner items. Next step: `/gsd-plan-phase 1 --gaps`.

---

_Verified: 2026-10-18T16:11:48Z_
_Verifier: Claude (gsd-verifier)_
