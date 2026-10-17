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

The planner fills in task IDs. Each requirement's automated command is listed here.

| Requirement | Behavior | Test Type | Automated Command | File Exists | Status |
|-------------|----------|-----------|-------------------|-------------|--------|
| WS-01 | init tree, case.yaml, state.json (registry/counters/chunks), .gitignore | integration | `pytest tests/workspace/test_init.py -x` | ❌ W0 | ⬜ pending |
| WS-02 | fingerprint (sha256/size/MIME/mtime), `S001…`, junk ignored, symlinks ignored | integration | `pytest tests/sources/test_scan_fingerprint.py -x` | ❌ W0 | ⬜ pending |
| WS-03 | new version `S004v2`, rename, duplicate, removed, content swap, case-only rename, NFD | integration | `pytest tests/sources/test_scan_classify.py -x` | ❌ W0 | ⬜ pending |
| WS-04 | sidecar pairing and hashing; orphan sidecar reported | integration | `pytest tests/sources/test_sidecars.py -x` | ❌ W0 | ⬜ pending |
| WS-06 / TST-07 | crash at every checkpoint then resume; no tmp left; no ID reuse | subprocess | `pytest tests/store/test_crash_resume.py -x` | ❌ W0 | ⬜ pending |
| WS-07 | second mutating run waits; `LOCK_TIMEOUT` exit 4; read-only runs while locked | subprocess | `pytest tests/store/test_lock.py -x` | ❌ W0 | ⬜ pending |
| WS-08 | invalid record refused; strict YAML keeps `12:30`/`0123`/`no` as text | unit | `pytest tests/core/test_yamlio.py tests/store/test_validate.py -x` | ❌ W0 | ⬜ pending |
| WS-09 | INDEX six sections in order, "none yet" | unit + integration | `pytest tests/index/test_index.py -x` | ❌ W0 | ⬜ pending |
| WS-11 | `.epb/.gitignore` exact list; git-tracking warning | integration | `pytest tests/workspace/test_git_warning.py -x` | ❌ W0 | ⬜ pending |
| WS-12 | sync-folder warning (fake home/env) | unit | `pytest tests/doctor/test_syncfolders.py -x` | ❌ W0 | ⬜ pending |
| WS-13 | state.json schema requires workbooks, counters, chunks | unit | `pytest tests/schemas/test_state_schema.py -x` | ❌ W0 | ⬜ pending |
| BLD-01 | format constants equal the transcribed contract | unit | `pytest tests/formats/test_contract.py -x` | ❌ W0 | ⬜ pending |
| BLD-02 | string-only cells, no `<f>`, inlineStr only, control chars removed | unit | `pytest tests/formats/test_writer.py -x` | ❌ W0 | ⬜ pending |
| BLD-03 | validator rejection classes; minimal pack passes; prototype pack gives `LIST_FRAGMENT_UNBALANCED` | unit | `pytest tests/formats/test_validator.py -x` | ❌ W0 | ⬜ pending |
| BLD-08 | metadata 10 rows exact; totals; attachments headers | unit | `pytest tests/formats/test_metadata.py -x` | ❌ W0 | ⬜ pending |
| PKG-01 | manifests, marketplace `source: "./plugin"`, name/version parity | unit + optional CLI | `pytest tests/packaging/test_manifests.py -x` | ❌ W0 | ⬜ pending |
| PKG-03 | `plugin/AGENTS.md` present with required rules | unit | `pytest tests/packaging/test_plugin_agents_md.py -x` | ❌ W0 | ⬜ pending |
| PKG-05 | exit codes 0–4, `--json` error envelope | unit + subprocess | `pytest tests/cli/test_exit_codes.py -x` | ❌ W0 | ⬜ pending |
| PKG-06 | stdlib-only launcher; `ENV_NOT_SET_UP`; re-exec into the env | unit + subprocess | `pytest tests/launcher -x` | ❌ W0 | ⬜ pending |
| PKG-07 | doctor tool registry, versions, per-OS commands | unit | `pytest tests/doctor/test_probes.py -x` | ❌ W0 | ⬜ pending |
| PKG-08 | requirements floors; extras licence headers; no GPL in core or dev | unit | `pytest tests/packaging/test_requirements.py -x` | ❌ W0 | ⬜ pending |
| PKG-09 | dependency-age and licence-check logic | unit + CI step | `pytest tests/tools/test_dependency_checks.py -x` | ❌ W0 | ⬜ pending |
| PKG-11 | root AGENTS.md == CLAUDE.md, ≤150 lines | unit | `pytest tests/repo/test_instructions_mirror.py -x` | ❌ W0 | ⬜ pending |
| TST-01 | no-network guard; optional-tool skips | meta | `pytest tests/repo/test_no_network.py -x` | ❌ W0 | ⬜ pending |
| DOC-04 / DOC-05 | manual chapters, privacy statement, "not yet tested on this system" | unit | `pytest tests/docs/test_manual.py -x` | ❌ W0 | ⬜ pending |

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
