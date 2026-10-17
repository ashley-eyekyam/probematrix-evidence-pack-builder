---
phase: "1"
slug: "foundations"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-10-17"
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution. Derived from `01-RESEARCH.md` § Validation Architecture.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest ≥9.0 (9.1.1 under the two-week cutoff); ruff 0.16.10 |
| **Config file** | `pyproject.toml` (none yet, so Wave 0 creates it): pytest `testpaths=["tests"]`, `pythonpath` covering `plugin/skills/evidence-pack/scripts` and `tools`, `filterwarnings=["error::EncodingWarning"]`; ruff `target-version="py311"` |
| **Quick run command** | `.venv/bin/python -m pytest -x -q tests/<area>` |
| **Full suite command** | `.venv/bin/ruff check . && .venv/bin/ruff format --check . && .venv/bin/python -m pytest -q` |
| **Estimated runtime** | ~60 seconds (the crash-resume subprocess matrix is the slowest part) |

---

## Sampling Rate

- **After every task commit:** Run the quick command for the area touched, plus `ruff check` on the changed files
- **After every plan wave:** Run the full suite command
- **Before `/gsd-verify-work`:** The full suite must be green on CI (3.11 + 3.14), with the dependency-age and licence steps green
- **Max feedback latency:** 120 seconds

---

## Per-Task Verification Map

Task IDs filled in by the planner (2026-10-17). Commands run from the repo root with `.venv/bin/python -m pytest`. Paths that differ from the research draft: the stdlib-only bootstrap check lives in `tests/launcher/test_launcher.py`, the metadata-layout checks in `tests/formats/test_contract.py`, the git unit tests in `tests/doctor/test_gitcheck.py`, and init defaults in `tests/workspace/test_init_defaults.py`.

| Requirement | Plan-Task | Behavior | Test Type | Automated Command | File Exists | Status |
|-------------|-----------|----------|-----------|-------------------|-------------|--------|
| WS-01 | 01-07 T1, 01-09 T1–T2, 01-11 T1 | init tree, case.yaml, state.json (registry/counters/chunks), .gitignore | integration | `pytest tests/workspace/test_init.py tests/workspace/test_init_defaults.py tests/workspace/test_layout.py -x` | ❌ W0 | ⬜ pending |
| WS-02 | 01-13 T1–T2 | fingerprint (sha256/size/MIME/mtime), `S001…`, junk ignored, links ignored | integration | `pytest tests/sources/test_scan_fingerprint.py -x` | ❌ W0 | ⬜ pending |
| WS-03 | 01-13 T1, 01-14 T1–T2 | new version `S004v2`, rename, duplicate, removed, content swap, case-only rename, NFD | integration | `pytest tests/sources/test_scan_classify.py -x` | ❌ W0 | ⬜ pending |
| WS-04 | 01-14 T3 | sidecar pairing and hashing; orphan sidecar reported | integration | `pytest tests/sources/test_sidecars.py -x` | ❌ W0 | ⬜ pending |
| WS-06 / TST-07 | 01-07 T1/T3, 01-12 T1, 01-14 T3 | crash at every checkpoint then resume; no tmp left; no ID reuse | subprocess | `pytest tests/store/test_validate.py tests/store/test_crash_resume.py -x` | ❌ W0 | ⬜ pending |
| WS-07 | 01-12 T2 | second mutating run waits; `LOCK_TIMEOUT` exit 4; read-only runs while locked | subprocess | `pytest tests/store/test_lock.py -x` | ❌ W0 | ⬜ pending |
| WS-08 | 01-07 T3, 01-09 T2 | invalid record refused; strict YAML keeps `12:30`/`0123`/`no` as text | unit | `pytest tests/core/test_yamlio.py tests/store/test_validate.py -x` | ❌ W0 | ⬜ pending |
| WS-09 | 01-11 T1–T2 | INDEX six sections in order, "none yet" | unit + integration | `pytest tests/index/test_index.py -x` | ❌ W0 | ⬜ pending |
| WS-11 | 01-08 T2, 01-11 T1/T3 | `.epb/.gitignore` exact list; git-tracking warning | integration | `pytest tests/doctor/test_gitcheck.py tests/workspace/test_git_warning.py -x` | ❌ W0 | ⬜ pending |
| WS-12 | 01-08 T2, 01-11 T3 | sync-folder warning (fake home/env) | unit | `pytest tests/doctor/test_syncfolders.py tests/workspace/test_git_warning.py -x` | ❌ W0 | ⬜ pending |
| WS-13 | 01-07 T2 | state.json schema requires workbooks, counters, chunks | unit | `pytest tests/schemas/test_state_schema.py -x` | ❌ W0 | ⬜ pending |
| D-09 | 01-12 T3 | newer workspace exits 4; older upgrades with backup on mutating commands only | integration | `pytest tests/store/test_upgrade.py -x` | ❌ W0 | ⬜ pending |
| D-13 | 01-13 T3 | magic bytes beat extension; mismatch recorded | unit | `pytest tests/core/test_mime.py -x` | ❌ W0 | ⬜ pending |
| BLD-01 | 01-04 T1–T2, 01-15 T2 | format constants equal the transcribed contract; reference doc in step | unit | `pytest tests/formats/test_contract.py tests/packaging/test_references.py -x` | ❌ W0 | ⬜ pending |
| BLD-02 | 01-04 T1 | string-only cells, no `<f>`, text cell types only, control chars removed | unit | `pytest tests/formats/test_writer.py -x` | ❌ W0 | ⬜ pending |
| BLD-03 | 01-04 T2 | validator rejection classes; minimal pack passes; prototype pack gives `LIST_FRAGMENT_UNBALANCED` | unit | `pytest tests/formats/test_validator.py -x` | ❌ W0 | ⬜ pending |
| BLD-08 | 01-04 T1–T2 | metadata 10 rows exact; totals; attachments headers | unit | `pytest tests/formats/test_contract.py tests/formats/test_writer.py -x` | ❌ W0 | ⬜ pending |
| D-16 | 01-04 T3 | smoke pack builds, validates, checklist covers every A10 value | unit | `pytest tests/tools/test_smoke_pack.py -x` | ❌ W0 | ⬜ pending |
| PKG-01 | 01-06 T1, 01-15 T1 | manifests, marketplace `source: "./plugin"`, name/version parity, isolated install | unit + opt-in CLI | `pytest tests/packaging/test_manifests.py -x` and `EPB_HOST_TESTS=1 pytest tests/packaging/test_host_install.py` | ❌ W0 | ⬜ pending |
| PKG-01 (skill) | 01-15 T1 | SKILL.md lint | unit | `pytest tests/packaging/test_skill_lint.py -x` | ❌ W0 | ⬜ pending |
| PKG-03 | 01-06 T2 | `plugin/AGENTS.md` present with required rules | unit | `pytest tests/packaging/test_plugin_agents_md.py -x` | ❌ W0 | ⬜ pending |
| D-01 | 01-06 T3 | Codex fallback installer layout and safety | subprocess | `pytest tests/packaging/test_install_codex.py -x` | ❌ W0 | ⬜ pending |
| PKG-05 | 01-03 T1, T3 | exit codes 0–4, `--json` error envelope | unit + subprocess | `pytest tests/cli/test_exit_codes.py -x` | ❌ W0 | ⬜ pending |
| PKG-06 | 01-03 T2–T3, 01-10 T1–T2 | stdlib-only launcher; `ENV_NOT_SET_UP`; re-exec; setup | unit + subprocess | `pytest tests/launcher -x` and `EPB_NETWORK_TESTS=1 pytest tests/launcher/test_setup_real.py` | ❌ W0 | ⬜ pending |
| PKG-07 | 01-08 T1 | doctor tool registry, versions, per-OS commands | unit | `pytest tests/doctor/test_probes.py -x` | ❌ W0 | ⬜ pending |
| PKG-08 | 01-01 T1, T3 | requirements floors; extras licence headers; no GPL in core or dev | unit | `pytest tests/packaging/test_requirements.py -x` | ❌ W0 | ⬜ pending |
| PKG-09 | 01-05 T1–T2 | dependency-age and licence-check logic | unit + CI step | `pytest tests/tools/test_dependency_checks.py -x` | ❌ W0 | ⬜ pending |
| PKG-11 | 01-05 T3, 01-16 T3 | root AGENTS.md == CLAUDE.md, ≤150 lines | unit | `pytest tests/repo/test_instructions_mirror.py -x` | ❌ W0 | ⬜ pending |
| TST-01 | 01-01 T3, 01-05 T3 | no-network guard; optional-tool skips | meta | `pytest tests/repo/test_no_network.py -x` | ❌ W0 | ⬜ pending |
| DOC-04 / DOC-05 | 01-16 T1–T2 | manual chapters, privacy statement, "not yet tested on this system", golden doctor output | unit | `pytest tests/docs/test_manual.py -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `pyproject.toml` — ruff and pytest config only
- [ ] `requirements-dev.txt`, `plugin/requirements.txt`, extras stubs with licence headers
- [ ] `tests/conftest.py` — no-network guard, `make_case(tmp_path)`, `run_epb()` subprocess helper, in-process `cli(argv)` helper, fake home/env fixtures
- [ ] `.github/workflows/ci.yml` skeleton
- [ ] `.gitignore` adds `scratch/`
- [ ] Dev env install via `--uploaded-prior-to P14D` (behind the package-legitimacy checkpoint)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Owner smoke import of the synthetic edge-case workbook | BLD-02 / SC4 | ProbeMatrix runs only on Replit; the owner does every import | Generate with `python tools/make-smoke-pack.py`, then the owner follows the UAT checklist |
| Plugin install via `/plugin` in Claude Code on Linux | PKG-01 / SC5 | Needs the interactive host | UAT numbered procedure |
| Real `doctor --setup` venv build | PKG-06 | Network + slow | `EPB_NETWORK_TESTS=1 pytest tests/launcher/test_setup_real.py` |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 120s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
