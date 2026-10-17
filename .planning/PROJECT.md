# ProbeMatrix Evidence Pack Builder

## What This Is

An open-source agent plugin (Agent Skills format) for Claude Code, Cowork and OpenAI Codex. It turns a **case folder** of raw incident material (text and scanned reports, witness statements, emails, spreadsheets and system exports, photos, audio, video and saved web pages) into a citation-exact, de-identified `EVIDENCE_PACK_V2` Excel workbook that imports into ProbeMatrix. It keeps that pack current as new evidence arrives, through a master workbook plus delta workbooks. It is for HSE investigators and ProbeMatrix users who need defensible evidence items without hand-authoring them.

The approved specification is `docs/design/2026-10-17-evidence-pack-builder-design.md` (§1–§20; §20 amendments win). **Where this file and the design disagree, the design wins.** The development brief is `docs/GSD-KICKOFF.md`.

## Core Value

Every item in a pack is **traceable and trustworthy**:
- every quote is verbatim on the cited page or time of a saved input
- every person appears only as a role label
- no source conclusion, lesson or recommendation is ever treated as evidence
- the workbook imports into ProbeMatrix cleanly, without duplicates

One invented quote, one leaked name or one leaked verdict makes the product a failure, even if everything else works.

## Business Context

- **Customer:** HSE and process-safety investigators, and enterprise teams who analyse incidents in ProbeMatrix.
- **Revenue model:** a free MIT-licensed plugin (Eyekyam Risk Resolutions) that feeds ProbeMatrix's paid HFACS analysis.
- **Success metric:** evals on the synthetic incident score 100% verbatim quotes, 100% page accuracy, 0 names leaked and 0 conclusions leaked. A fresh-machine install works on Claude Code and Codex.
- **Strategy notes:** design §1–§2; `docs/GSD-KICKOFF.md` §11 (definition of done for v0.1.0).

## Requirements

### Validated

(None yet. Ship to validate.)

### Active

- [ ] Case-folder workspace (`inputs/`, `outputs/`, `INDEX.md`, `.epb/`) with fingerprinting, versions, renames, removals and an INDEX.md regenerated every run (§6, §7.1)
- [ ] Importer-exact `EVIDENCE_PACK_V2` format module and validator, stricter than the importer (§8.4 including the importer re-check, §8.5)
- [ ] Text-document intake: PDF, DOCX, PPTX, XLSX/CSV, email, HTML, TXT and chat, producing page-anchored segments with a section map (§7.2–§7.3)
- [ ] Quote verifier: normalisation, ellipsis fragments, cross-page spans, `[sic]`, bracketed role labels (§8.2)
- [ ] Chunked claim extraction with verification on write, and resume after interruption (§7.4)
- [ ] Evidence-bank entry rule: conclusions, lessons and recommendations are never evidence, enforced at four points (§11.3)
- [ ] Rosters, always-on de-identification, a zero-hit `deid-scan` gate, and conflict detection and confirmation (§10, §13)
- [ ] Item authoring rules: types, tags, priority and the Description standard (§8.3, §9)
- [ ] All 12 hard gates and the soft warnings, the coverage gate and the spot-check report (§11, §14)
- [ ] Master and delta builds, `mark-imported`, correction items, `rebuild --from`, `build --consolidated` (§12)
- [ ] Scanned PDF OCR with confidence propagation, and multi-language support (§7.2, §13.3a)
- [ ] Media: audio and video transcription, keyframes, CCTV overlay OCR, images with GPS stripped, sidecar notes (§7.2, §7.5)
- [ ] Optional web snapshot into `inputs/web/` (§7.9)
- [ ] Seven skills plus one CLI (`epb.py`), packaged in `plugin/` for Claude Code, Cowork and Codex, with guided one-time setup (`doctor --setup`), evals, docs, Linux CI and the v0.1.0 release (§5, §15–§17, §20 A4/A8/A9)
- [ ] Detailed user manual for non-technical users: install and use on Windows, macOS and Linux, started in Phase 1 and extended per phase (§20 A14)

### Out of Scope

- Performing the investigation (HFACS classification, root-cause analysis, recommendations). That is ProbeMatrix's job (§2 non-goals).
- Automatic import into ProbeMatrix or an API client. The user uploads the workbook (§2).
- Output formats other than `EVIDENCE_PACK_V2` workbooks. A format seam is kept but only V2 ships (§2, §8.5).
- A GUI. The agent, the CLI and INDEX.md are the interface (§2).
- Cloud OCR, cloud transcription or document-AI services. Local open-source tools only (§2, §4).
- An opt-out for de-identification or for the conclusions rule. Both are always on (§4, §11.3).
- Copying prototype code or real-incident prose. The build is clean-room (§4, §16).
- Speaker diarisation by default. `pyannote` is optional because its model needs a licence acceptance (§7.2).
- Published samples (`samples/`, `make-sample.py`). The repo ships the plugin only; benchmarks run in scratch folders (§20 A3).
- Windows and macOS CI and fresh-machine testing for v0.1.0. Code stays cross-platform, and the testing follows after v0.1.0 (§20 A9).
- Anything in the parent ProbeMatrix checkout or other repos. This repo is separate; the parent is read-only reference (importer format, prototype ideas) and is never modified or depended on.

## Context

- **Origin:** an internal prototype (`../tools/evidence-pack-builder/` in the ProbeMatrix checkout: a Node script plus a 7-phase skill) built a 60-item pack for the ONGC Hazira 2020 fire. That pack has 18 catalogued defects (design §3, referred to as **DEF-01…DEF-18** in planning artefacts to avoid clashing with GSD's `D-NN` decision tokens). The prototype is read-only inspiration. **Copy no code and no prose from it.** Its example Descriptions contain invented phrases.
- **Reference material:** `docs/reference/hazira-2020/` holds the official PNGRB report (unmodified; it names real people, which is acceptable for an official public record) and the prototype pack. They are used for regression tests and benchmarks only, never as worked examples.
- **Importer:** the ProbeMatrix importer was re-read on 2026-10-17. The facts are recorded in design §8.4 under "Importer re-check":
  - Evidence IDs are regenerated on import; only Tags survive, with `-IMPn` added on collision.
  - Enums are not validated by the importer.
  - A single blank Description fails the whole file.
  - Every cell is read as a string, so dates and hashes must be written as text.
- **Environment:** this repo sits inside the ProbeMatrix checkout (git-excluded there) but is its own repo with origin `github.com/ashley-eyekyam/probematrix-evidence-pack-builder`. Never modify the parent checkout. ProbeMatrix's "never run the app locally" rule does not apply here: run the CLI and tests locally. The dev machine has Python 3.14, ffmpeg and pdftoppm; Tesseract and ocrmypdf are not installed yet.
- **Owner:** an HSE and process-safety professional and the ProbeMatrix product owner. They test hands-on, and they import workbooks into ProbeMatrix (Replit) themselves and report the result.

## Constraints

- **Tech stack:** Python 3.11+ for the whole package (§20 A5), `pathlib` everywhere, Windows, macOS and Linux. One CLI with `--json` output and exit codes 0–4 (§15.2, §20 A11). Why: identical behaviour across all three hosts.
- **Dependencies:** core dependencies must be permissive. GPL `extract-msg` is an optional extra only. Pin minimum versions, use no dependency younger than two weeks, and keep optional extras in separate requirements files (§18, kickoff §7). Why: MIT licence.
- **Locality:** conversion uses only local open-source tools, detected at runtime and reported by `doctor`. A missing tool marks inputs `unprocessed` and never fails a run (§4, §7.2). The agent's excerpts go to the AI host's model provider, and `init`/`doctor` warn about case folders inside sync folders (§20 A1). Why: no cloud conversion, and an honest privacy statement.
- **Audience:** end users may be non-technical. Setup, error messages and the manual must work for someone who has never used a terminal (§20 A8, A14).
- **Clean-room:** no prototype code and no real-incident prose. All worked examples, fixtures and tests are synthetic (§4, §16). Why: this stops the invented-quote defect, DEF-01, from coming back.
- **Content gates:**
  - zero invented quotes
  - zero names in outputs
  - zero conclusions, lessons or recommendations
  - zero HFACS vocabulary
  - comma-free list elements
  - dates at stored precision
  - no IDs in prose
  - Descriptions of at most 1,800 characters

  Why: these are product requirements (kickoff §6).
- **Skills:** each SKILL.md is about 150 lines or fewer. Shared rules live in `plugin/skills/evidence-pack/references/` (§5, §20 A4).
- **Tests:** pytest and ruff. Tests use no network. Tests for optional tools skip cleanly when the tool is absent. Fixtures are generated at test time where practical (kickoff §7).
- **Process:** one question at a time. Every UAT has numbered step-by-step procedures. Quality outranks token or API cost. Branch per phase (`phase-NN-<slug>`), merged to main with `--no-ff` only after the phase is verified.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Local open-source conversion only, with a `doctor` command | Evidence stays on the machine | — Pending |
| Master plus deltas; drafts are overwritable until marked imported; corrections go out as new items | The importer appends and never deduplicates | — Pending |
| Always de-identify, with a zero-hit scan as a hard gate | Names in shareable output are an anti-goal | — Pending |
| Conclusions, lessons and recommendations are never evidence (4-layer enforcement, no opt-out) | Fixes DEF-13: the official answer leaking into evidence | — Pending |
| No HFACS pre-classification; a blocked-term lint enforces it | Classification is ProbeMatrix's job (DEF-06) | — Pending |
| Web is inputs-only, as dated snapshots the user has confirmed | Fixes DEF-11: unverifiable online items | — Pending |
| Hosts: Claude Code, Cowork and Codex at launch | Wide reach; `doctor` sets the capability profile | — Pending |
| Seven skills and one Python CLI | Short SKILL.md files; deterministic work kept out of agents | — Pending |
| MIT licence, permissive core dependencies | Open source | — Pending |
| Clean-room relative to the prototype | Prevents copied invented prose (DEF-01) | — Pending |
| Design approved 2026-10-17; §8.4 amended after an importer re-check | Requirements must trace to a correct spec | ✓ Good |
| Branch per phase, `--no-ff` merge after verification | Main holds only verified work | — Pending |
| Post-research amendments A1–A14 (design §20): locality wording, `.epb` ignores, no samples, `plugin/` subfolder, Python 3.11+, security exception to two-week rule, four added core deps, guided setup, Linux-only CI for v0.1.0, Phase 1 smoke import, exit code 4, added CLI verbs, page-citation scheme, non-technical manual | Research findings; owner decided each one | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-10-17 after initialization*
