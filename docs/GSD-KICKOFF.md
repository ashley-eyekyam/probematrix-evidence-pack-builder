# GSD Kickoff Prompt: ProbeMatrix Evidence Pack Builder

> **How to use this file**
>
> 1. Open VS Code with **this repository folder** as the workspace root
>    (`probematrix-evidence-pack-builder/`, not the parent ProbeMatrix checkout).
> 2. Start a fresh Claude Code session there.
> 3. Run: `/gsd-new-project @docs/GSD-KICKOFF.md`
>    (Interactive mode is recommended. `--auto` works, but you lose the chance to correct the roadmap before it's written.)
> 4. After the roadmap is approved: `/gsd-discuss-phase 1` → `/gsd-plan-phase 1` → `/gsd-execute-phase 1` → `/gsd-verify-work 1`, and so on.
>
> Everything below the line is the prompt. It's written to the agent running GSD.

---

## 0. Who you are working for, and how they want to work

You are developing an open-source agent plugin for **Eyekyam Risk Resolutions** (owner: Ashley). The owner is an HSE and process-safety professional and the product owner of ProbeMatrix, an HFACS-based incident-investigation SaaS. They are technically fluent, use GSD as the main development framework, and test hands-on.

**Non-negotiable interaction rules (from the owner's global instructions):**
- **One question at a time.** Every `AskUserQuestion` call contains exactly one question. Never batch decisions.
- **Detailed options plus a recommendation.** Describe each option fully (meaning, trade-offs, implications). Put the recommended option **first**, labelled "(Recommended)".
- **Never proceed without an answer.** If a question times out, ask it again. Never substitute the recommended default and move on.
- **UAT needs step-by-step instructions.** Every `/gsd-verify-work` test comes with a numbered procedure: prerequisites, exact commands, fixture files, and exact pass/fail strings to look for. Never just a terse checkpoint.
- **Quality outranks token or API cost.** Never trade output quality for spend.
- Report outcomes faithfully. If a test fails, say so and show the output.

## 1. The single source of truth

**Read these fully before doing anything else:**

1. `docs/design/2026-10-17-evidence-pack-builder-design.md` is the approved design (sections §1–§19). It is the specification. Where this kickoff summarises it, **the design document wins**. If you find a contradiction or gap in the design, raise it as a question (one at a time). Don't silently resolve it.
2. `docs/reference/hazira-2020/README.md` and its two files:
   - `PNGRB-Hazira-enquiry-report-2021-01-15.pdf`: an official public enquiry report (36-page text PDF). It names real people. That's fine and normal for an official public report: it stays unmodified in the repo.
   - `prototype-evidence-pack-hazira-2020.xlsx`: the 60-item pack made by the earlier prototype, which has the 18 defects catalogued in design §3 (D1–D18).
3. `README.md`, `LICENSE` (MIT, © 2026 Eyekyam Risk Resolutions).
4. The **internal prototype tool** listed in §4a below: read-only inspiration and context.

Feed the design document into GSD's PROJECT.md and REQUIREMENTS.md generation. Requirements must trace to design sections (cite `§n` in each requirement). Don't invent scope beyond the design. Anything that seems missing becomes a question or a backlog item, never silent scope.

## 2. What we're building (summary; the design has detail)

An **open-source agent plugin** (Agent Skills format) for **Claude Code, Cowork and OpenAI Codex**. It turns a **case folder** of raw incident material into a citation-exact, de-identified **`EVIDENCE_PACK_V2` Excel workbook** that imports into ProbeMatrix, and keeps it current as new evidence arrives.

- **Case folder contract (§6):** `inputs/` (user drops anything: text and scanned PDFs, DOCX, PPTX, XLSX/CSV, email, HTML, chat exports, images, audio, video), `outputs/` (**only** evidence-pack workbooks), `INDEX.md` (human-readable snapshot of inputs, outputs, versions, open issues, run history) and `.epb/` (hidden working state; `.epb/private/` holds the only name→role map and is never shared).
- **Pipeline (§7):** `init → doctor → scan → convert → segment → extract → reconcile → author → verify → build → index`, plus an optional `web-snapshot`. Every stage is idempotent and incremental.
- **One Python CLI** (`skills/evidence-pack/scripts/epb.py` + package `scripts/epb/`) does all deterministic work. Agents provide judgement (extraction, de-identification roles, conflict confirmation, Description writing).
- **Seven skills (§15.1):** `evidence-pack` (start here, router), `evidence-intake`, `evidence-extraction`, `evidence-reconcile`, `evidence-authoring`, `evidence-verify-build`, `evidence-web-snapshot` (optional).

## 3. Locked decisions (don't reopen without asking the owner)

| Area | Decision | Design ref |
|---|---|---|
| Conversion | **Local open-source tools only** (pdfplumber/pypdf, docling optional, OCRmyPDF + Tesseract, python-docx, python-pptx, openpyxl, faster-whisper, ffmpeg). Detected at runtime; `epb doctor` reports. **No cloud OCR, transcription or document-AI.** | §4, §7.2 |
| Increments | **Master + deltas.** The first build writes `evidence-pack-<case>-master.xlsx`. Later builds write `evidence-pack-<case>-delta-NNN.xlsx` with **only new items**. Never re-emit already-imported items (the ProbeMatrix importer appends and has no duplicate check). | §4, §12 |
| Freeze point | Workbooks are **drafts** (overwritable by later runs) **until the owner marks them imported** (`epb mark-imported <file>` or the INDEX.md tick). Imported items are locked, and fixes ship as **correction items**. | §4, §12.1, §12.4 |
| Names | **Always de-identified, no opt-out.** Role labels only in anything the plugin produces. Zero-hit name scan is a hard build gate. Official public source reports bundled as reference are exempt and stay unmodified. | §4, §13 |
| Web | **Inputs only.** The optional web step saves dated snapshots into `inputs/web/` (user confirms URLs), and they're then processed as normal inputs. Never add a claim not read from a saved input. | §4, §7.9 |
| Hosts | **Claude Code + Cowork + Codex** at launch. Cowork capabilities decided at runtime by `doctor`; pure-Python text intake is the guaranteed baseline. | §4, §15.3 |
| Conclusions | **Facts only.** Source root causes, verdicts and recommendations go to a private held-back ledger, never into items. | §4, §11.3 |
| HFACS | **No HFACS pre-classification** anywhere (Descriptions or Tags). A blocked-term lint enforces it. | §2, §9.2 |
| Licence | MIT. Core dependencies must be permissive. `extract-msg` (GPL) is an **optional extra** only. | §18 |
| Clean-room | The internal prototype (§4a) **stays in ProbeMatrix as it is, indefinitely**. Read it for ideas and context. **Copy no code from it and no real-incident prose**: worked examples in this repo are synthetic. | §4, §16 |
| Language/runtime | Python **3.10+**, `pathlib` everywhere, Windows/macOS/Linux. | §15.3 |

## 4. External facts you'll need (verified 2026-10-17)

- **ProbeMatrix importer** (read-only reference, needed to transcribe the file format): this repo sits inside the ProbeMatrix checkout, so the importer source is at `../server/services/evidenceExportService.ts` (format marker, headers and widths near the top; the import parser around lines 260–437) and the evidence types at `../shared/schema.ts` (search `ChainOfCustodyEntry`, `EvidenceLifecycleStatus`, `RetentionCategory`). **Transcribe the file format** into `scripts/epb/formats/probematrix_v2.py` and `skills/evidence-pack/references/evidence-pack-v2.md`. Copy no ProbeMatrix code. Record the date you checked it. If `../server` isn't present (a standalone clone), rely on design §8.4 and say so.
- Importer behaviours that shape the design (§8.4): rows are **appended** to the incident in the URL; **comma splitting** of Tags, Linked Individuals, Linked Equipment, Related Evidence and Regulatory Requirements; `QA Status` → lifecycle enum (`collected, preserved, under_review, verified, disputed, released, destroyed, sealed`); `Retention Category` enum (`regulatory, legal, internal, permanent`); `Access Restrictions`, `QA Reviewed By/At` and `Verification Notes` are **dropped**; duplicate Evidence Tags get `-IMP1`/`-IMP2`; Evidence IDs are regenerated on import (Tags survive).
- **The analyser** sees only `[Evidence ID] (Type, Priority)`, Description (**cut at 2,000 characters**), Tags, Linked Individuals and Linked Equipment. Hence the Description hard limit of 1,800 characters.
- **ProbeMatrix's own rules don't apply here.** Its "never run the app locally" rule is about the ProbeMatrix web app. In *this* repo you **may and should** run the CLI, the tests and the converters locally. Never run ProbeMatrix's `npm run dev/build/start` from the parent folder.
- **Don't modify the parent ProbeMatrix checkout**, including the prototype. This repo is git-excluded there (`.git/info/exclude`). Work, commit and push only inside this repo.

## 4a. The internal prototype: read for inspiration, never copy

The idea for this plugin came from an internal developer tool in the parent ProbeMatrix checkout. Paths are relative to **this repo's root** (available only while this repo sits inside the ProbeMatrix checkout; a standalone clone won't have them, and nothing in this repo may depend on them).

| Path | What it is | Take from it | Design overrides / warnings |
|---|---|---|---|
| `../tools/evidence-pack-builder/SKILL.md` | The prototype's 7-phase workflow (source intake → research notes → de-identification → item authoring → generate → validate → QA spot-check) | The phase discipline: research notes before authoring, de-id before drafting, validate before shipping, spot-check at the end | Superseded by the design's pipeline (§7). Its "40–80 items" target is replaced by the coverage gate (§11.2). Its Phase-7 "HFACS justification matches" check contradicts the no-HFACS rule: ignore it |
| `../tools/evidence-pack-builder/README.md` | Pointer and quick-start | Context only | Node/`.cjs`, hard-coded `attached_assets/` paths: not applicable |
| `../tools/evidence-pack-builder/references/format-spec.md` | Column-by-column `EVIDENCE_PACK_V2` notes, naming conventions (`EVD-<PFX>-NNN`, `TAG-<PFX>-NNNNNNNN`), "how the importer reads a pack" | Cross-check against your own transcription of the importer | Says comma-lists without warning about comma-bearing labels (D14), and says "Importer regenerates IDs, existing values are kept": verify against the importer source, which wins |
| `../tools/evidence-pack-builder/references/description-quality.md` | The three-part Description shape (observation → anchor → operational inference), the "don't pre-classify HFACS" rationale, what counts as an anchor, length-by-source-type table | The three-part shape, the anchor definition, the no-HFACS rationale. These are carried into design §9.4 | **Contains real Hazira prose as "GOOD" examples, including phrases that are NOT in the report** (e.g. "instructed closure", "uniform deterioration pattern", "the skid superstructure was not designed to contain a flange-failure release"). That is how defect D1 happened. **Never reuse these examples or phrases.** Write synthetic good/bad pairs. Its 250–650 length guidance is replaced by §9.4 (300–900, hard 1,800). It mentions both a "3-part" and a "4-part" shape: the design's three-part rule wins |
| `../tools/evidence-pack-builder/references/source-research.md` | Research-notes template (overview, timeline, role roster, equipment roster, enumerated evidence by category, cross-cutting observations, "items NOT included and why") and the page-by-page reading method | The notes structure maps onto segments, claims, rosters and the coverage/omission log (§7.3–7.6, §11). The "items NOT included and why" idea is the seed of the coverage matrix | Manual whole-PDF reading is replaced by segmentation + chunked extraction. "40–80 bullets" target: drop it |
| `../tools/evidence-pack-builder/references/deidentification.md` | Role-label conventions (`<Designation> (<Dept / Position>)`, letter codes for externals, committee as body), what to anonymise and keep, two-pass name scan, edge cases (names in titles, URLs, quoted dialogue) | Role-label conventions and the edge-case list: carry them into `references/deidentification.md` (§13) | Its example labels contain commas (D14) and its quotes used ad-hoc placeholders like `[CE]` (D15). Use comma-free labels and full bracketed role labels. Its "keep the map outside the repo" rule becomes `.epb/private/` (§6) |
| `../tools/evidence-pack-builder/scripts/template.cjs` | Node items-file skeleton: role dictionary `R`, equipment dictionary `E`, `row(...)` helper, header list, column widths, metadata sheet writer | Header order and column-width list (cross-check with the importer/exporter source) | Items as code is replaced by YAML items + renderer (§8.3). Don't port it |
| `../tools/evidence-pack-builder/scripts/validate.cjs` | Format checks mirroring the importer, plus soft warnings (description < 250 chars, no digit and no quote, empty Source) | The idea of hard checks plus soft warnings; its list of enums | Far weaker than design §14 (no quote verification, no comma gate, no HFACS lint, no coverage). Re-implement from the design in Python |
| `../tools/evidence-pack-builder/scripts/scan-names.cjs` | Substring / whole-word (`--word`) name-fragment scanner over notes and xlsx | The whole-word option and "scan twice" habit | Replaced by the layered de-identification and `deid-scan` gate with allow-list (§13.1, §13.5) |
| `../tools/evidence-pack-builder/instances/hazira-2020.cjs` | The 60-item Hazira items file (source of the reference pack in `docs/reference/hazira-2020/`) | Useful to understand how the reference pack was built and why defects arose | **Real-incident prose with known invented and paraphrased quotes.** Never copy, imitate or use as a few-shot example. Use only to diagnose the reference pack |
| `../tools/evidence-pack-builder/instances/hazira-2020-notes.md` | The research notes behind that items file | Shows the notes format in practice; useful for designing the claim schema | Same warning: real-incident prose, not verified. Never copy into skills, references or tests |

**Rule of thumb:** ideas, structure and lessons may flow from the prototype. Text, examples and code may not. If you catch yourself pasting a sentence from these files, stop: write a synthetic equivalent instead.

## 5. Proposed milestone and phase structure

Create **one milestone, `v0.1.0`: first public release**, following the build order in design §17. Suggested phases (adjust granularity if GSD sizing suggests it, but keep the order and the milestones):

| Phase | Name | Scope (design refs) | Exit criteria (must be demonstrable) |
|---|---|---|---|
| 1 | Foundations | Repo scaffold (§5), `.claude-plugin/plugin.json` + `marketplace.json` (marketplace name `probematrix-evidence-pack-builder`), `AGENTS.md`, `CLAUDE.md` ("See @AGENTS.md"), `.agents/skills`, requirements split (§5), `formats/probematrix_v2.py` + importer-exact validator (§8.4–8.5), `epb init/scan/status`, state.json, source registry, fingerprinting/versioning/rename/removal (§7.1), INDEX.md generator (§6.1), lock file + atomic writes (§12.5), pytest + ruff + CI skeleton | Validator passes on a generated minimal pack and **fails** on the prototype reference pack's comma-bearing labels (D14); `scan` correctly classifies new/changed/renamed/removed fixtures; INDEX.md renders |
| 2 | Text-document intake | pdfplumber/pypdf per-page text + tables; DOCX (paragraph numbers, tracked changes flagged); PPTX; XLSX/CSV row-range segments; email (.eml stdlib, .msg optional extra); HTML; TXT/chat. Segments with printed page label vs physical index, section map, boilerplate removal, `norm_text` + char map (§7.2–7.3). **Quote verifier** (§8.2): whitespace/hyphenation/Unicode normalisation, ellipsis fragments, cross-page spans, `[sic]`, bracketed role labels | On the Hazira reference PDF: 36 segments, printed labels = physical pages, section map finds the briefing (5), eyewitness (7), observations (10) and improvements sections; verifier **accepts** the prototype's verbatim quotes and **rejects** `"instructed closure"` and `"nearby fittings were intact"` |
| 3 | Extraction + claim ledger | Chunk planner (§7.4), claim schema, `claims add` with verification on write, `extract-status`/resume, held-back conclusions ledger (§11.3), skill `evidence-extraction` | Synthetic fixture: every planted observation becomes a claim; recommendation sentences land in `conclusions.jsonl`; an interrupted run resumes at the right chunk |
| 4 | Reconcile | Role and equipment rosters with aliases, de-identification (pattern + agent + optional NER + roster scan list, §13), quote de-identification with bracketed labels, `deid-scan` gate, event alignment, conflict detection/confirmation (§10), skill `evidence-reconcile` | Synthetic fixture: all planted names/honorifics caught; planted time, value and actor conflicts detected; zero-hit scan on rendered artefacts |
| 5 | Authoring + verify + build (**MVP milestone**) | Item schema (§8.3), type rules (§9.1), tags + blocked list (§9.2), priority rubric (§9.3), Description standard (§9.4), renderer, **all hard gates and soft warnings (§14)**, coverage matrix + gate (§11), master workbook, spot-check report, skills `evidence-authoring`, `evidence-verify-build`, router `evidence-pack` | **End-to-end on the synthetic text-only incident**: master workbook passes every hard gate and imports cleanly into ProbeMatrix (owner-verified, see §8 below) |
| 6 | Incremental runs | Draft vs imported states, `mark-imported`, INDEX tick read-back, deltas, ID/Tag continuity with gaps, changed-input diffing, correction items, `rebuild --from`, `build --consolidated` (§12) | Incremental eval: add 2 inputs → delta contains only new items, IDs continue, INDEX updated; re-run with no changes writes nothing |
| 7 | Scans + OCR | Per-page scan detection, OCRmyPDF/Tesseract, confidence propagation, low-confidence status, multi-language packs (§7.2, §13.3a); optional docling path | Image-only PDF fixture converts; low-confidence pages flagged in INDEX and items |
| 8 | Media + images | ffmpeg audio extraction, faster-whisper with timestamps, keyframes (scene + floor), CCTV overlay OCR, image EXIF (GPS stripped), visual-observation claims, sidecar notes (§7.2, §7.5) | wav and mp4 fixtures produce time-anchored segments; media citations render as `hh:mm:ss–hh:mm:ss` |
| 9 | Web snapshot (optional skill) | `epb snapshot`, user-confirmed URL list, dated snapshot folders + meta.yaml (§7.9) | A saved snapshot flows through the pipeline like any input |
| 10 | Release | Agent evals (§16), public sample, `docs/INSTALL.md`, `docs/USER-GUIDE.md`, CI matrix (Linux/macOS/Windows + media job), `tools/install-codex.sh`, `tools/make-sample.py`, CHANGELOG, `v0.1.0` tag | Evals meet thresholds (verbatim 100%, page accuracy 100%, names leaked 0, conclusions leaked 0); fresh-machine install works on Claude Code and Codex |

**Requirements:** write REQUIREMENTS.md with IDs grouped by area (e.g. `WS-` workspace, `INT-` intake, `EXT-` extraction, `REC-` reconcile, `AUT-` authoring, `VER-` verification/gates, `BLD-` build/format, `INC-` incremental, `DEID-` de-identification, `MED-` media, `WEB-` web, `PKG-` packaging, `TST-` testing). Every hard gate in design §14 is its own requirement. Every defect D1–D18 in design §3 maps to at least one requirement and one test. Include a traceability table D-number → requirement → test.

## 6. Quality bar (these are product requirements, not suggestions)

- **Zero invented quotes.** Quotes are verified at claim-write time and again at build.
- **Zero names in plugin outputs.**
- **Zero held-back conclusions in items.**
- **Zero HFACS vocabulary.**
- **Page and time citations are generated** from the verified anchor segments, never typed by the agent.
- **Comma-free list elements** in comma-split columns.
- **Dates at stored precision** (`YYYY`, `YYYY-MM`, `YYYY-MM-DD`), never padded.
- **No IDs or row numbers in Description prose.** Cross-references go in `Related Evidence` as Evidence Tags.
- **Coverage gate:** every fact claim in observation sections is in an item or has a recorded omission reason.
- **Worked examples are synthetic only.** Never paste Hazira prose (from the reference files or the prototype in §4a) into skills, references or tests as an example to imitate. The Hazira files are for verification and regression tests only (e.g. "verifier rejects the prototype's invented quote").
- Each `SKILL.md` ≤ ~150 lines. Shared rules live in `skills/evidence-pack/references/`.

## 7. Engineering conventions

- Python 3.10+, type hints, `ruff` (lint + format), `pytest`. No network in tests. Optional-tool tests skip cleanly when the tool is absent.
- CLI: subcommands per design §15.2, `--json` on every command, exit codes 0/1/2/3 (§15.2).
- Schemas in `schemas/` (JSON Schema) for source, segment, claim, item, conflict and state. Validate on every write.
- YAML for items and rosters, JSONL for claims, JSON for state. Atomic writes (temp + rename). `state.json` written last.
- Fixtures: generate small synthetic fixtures at test time where possible (PDF via reportlab or similar, DOCX via python-docx, wav/mp4 via ffmpeg when present). Commit only tiny binaries when generation isn't practical.
- Dependencies: core permissive only. Optional extras in `requirements-media.txt`, `requirements-docs.txt`, `requirements-email.txt`. Pin minimum versions. No dependency younger than two weeks.
- Commits: conventional style (`feat(intake): …`, `fix(verify): …`, `docs: …`, `test: …`), path-scoped. Each commit message ends with the attribution line your environment supplies.
- Branching: this is a new public repo. Use a branch per phase (`phase-NN-<slug>`) merged to `main` with `--no-ff` after the phase is verified, unless the owner chooses otherwise at init. Ask them once, in GSD config.
- **Push the branch after any change the owner should look at.** Ask before the first push of a new branch if unsure.
- Docker isn't needed. If you ever add it, follow the owner's Docker rules (named volumes, pinned tags, `down -v --remove-orphans`).

## 8. Verification and UAT

- Per phase: automated tests plus a `/gsd-verify-work` UAT with **numbered step-by-step procedures** (prerequisites, exact commands, fixture paths, expected output strings).
- **ProbeMatrix import check (from Phase 5):** the owner imports generated workbooks into ProbeMatrix themselves (ProbeMatrix runs only on Replit). The UAT step must give exact instructions: which file, which incident (new for the master, the same for deltas), what to check afterwards (item count, Linked Equipment shown as separate entries, no comma-split fragments, Tags intact, QA/lifecycle status shown, Related Evidence strings present). Never claim an import worked: the owner reports it.
- **Regression benchmark (from Phase 5):** run the pipeline on the Hazira reference report in a scratch case folder (outside the repo, or a git-ignored path) and compare against the prototype pack: quotes verifiable, page accuracy, coverage of the dropped findings listed in D12, no conclusion leakage. Report the numbers. Don't commit real-incident outputs except as a deliberate public sample in Phase 10.

## 9. GSD gotchas observed on the owner's other project (watch for them here)

These were seen with the same GSD install. Treat them as hypotheses to check, not facts about this repo:
- **The executor may tick ROADMAP and STATE to complete before verification.** Gate phase completion on the VERIFICATION result; correct tracking if it jumped ahead.
- `gsd … commit --files A B` commits only the named paths. Pre-staged files stay staged silently. Check `git diff --cached --name-status` after.
- Quick-task executors have regressed STATE.md frontmatter. Diff STATE.md after `/gsd-quick` and repair by hand if needed.
- The plan-phase **decision-coverage gate** only counts `D-NN` decision tokens that appear in must_haves/truths/objective. Cite every tracked decision there.
- Parallel worktree executors **share one scratchpad**. Give every scratch file a plan-id suffix.
- `files_modified` region notation (`path[Lx-Ly]`) keeps same-file plans parallel. Back it with per-plan diff-hunk checks.
- UI gates may fire falsely. **This project has no UI**, so if a UI-SPEC gate demands a spec, use `--skip-ui` and note why.
- If a worktree base check complains, `worktree.baseRef: "head"` resolved it before.
- Some GSD CLIs make collateral edits (blank lines, dropped `progress.percent`). Review diffs of `.planning/` after CLI calls.
- Note the naming clash: GSD's own decision tokens are `D-NN`, and design §3's defects are `D1`–`D18`. In planning artefacts refer to the defects as `DEF-01`…`DEF-18` to avoid confusing the decision-coverage gate.

## 10. First-session checklist (do these in order)

1. Read design §1–§19, the reference README, and skim the prototype files in §4a (with the warnings in mind). Skim the importer source if `../server` exists.
2. Run `/gsd-new-project` questioning **using the design as the idea document**. Ask only what the design leaves open or what GSD config needs, one question at a time, with a recommended option first. Likely questions: commit `.planning/` publicly or not (recommend: commit, since the design is already public); branching model; parallelism level; research step on or off (recommend: on for Phases 2, 7, 8 where library choices need current docs, via Context7).
3. Produce PROJECT.md, REQUIREMENTS.md (with the DEF-01…DEF-18 traceability table), ROADMAP.md (phases as in §5 above unless the owner changes them) and STATE.md, then show the roadmap for approval.
4. Create the repo-level `AGENTS.md` (host-neutral rules for agents using and developing the plugin) and `CLAUDE.md` (`See @AGENTS.md`). These hold the **plugin's** rules for end users' agents: just culture, roles only, inputs-only, facts-only, verbatim quotes. Development-process notes go in `.planning/`.
5. Commit the planning artefacts. Ask before pushing.
6. Stop and hand back: summarise the roadmap and the first phase's plan outline, and recommend `/gsd-discuss-phase 1`.

## 11. Definition of done for v0.1.0

- All 10 phases verified. All hard gates implemented with tests. Evals meet the thresholds in §5 Phase 10.
- Installs via `/plugin marketplace add ashley-eyekyam/probematrix-evidence-pack-builder` + `/plugin install` on Claude Code, and via `tools/install-codex.sh` on Codex. `doctor` reports a sensible capability profile on a clean machine.
- A user can run "build an evidence pack from this folder" in a fresh case folder containing a text PDF, a scanned PDF, a DOCX, an email with an attachment, a CSV export, an audio file and a short video. They get a master workbook that imports into ProbeMatrix, an INDEX.md, and on a second run with one added file, a delta containing only the new items.
- README, INSTALL and USER-GUIDE complete. CHANGELOG entry. Tag `v0.1.0` pushed.
