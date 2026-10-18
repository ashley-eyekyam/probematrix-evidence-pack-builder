# Roadmap: ProbeMatrix Evidence Pack Builder

## Overview

The milestone builds the plugin in the order the data flows: `scan → convert → segment → extract → reconcile → author → verify → build`. Phase 1 lays down the workspace, transactional state, the importer-exact workbook format and guided setup, and the owner proves the format with a smoke import. Phases 2–4 build the trust machinery in dependency order: frozen page-anchored segments with an exact quote verifier, then a claim ledger that keeps conclusions out of the evidence bank, then always-on de-identification and conflict detection. Phase 5 is the MVP: the first end-to-end master workbook on the synthetic text-only incident, passing all 12 hard gates and imported into ProbeMatrix by the owner. Phase 6 makes the pack live through master-plus-delta increments and correction items. Phases 7–9 widen intake to scans, media and web snapshots through contracts already declared earlier. Phase 10 runs the agent evals, finalises the non-technical manual and docs, and releases v0.1.0. Cross-cutting contracts (anchor types, citation forms, language and confidence fields, workbook registry, sidecars) are declared early and filled late, per research Phase-Order Fixes PF-01…PF-20, so no phase forces a migration of persisted state.

## Milestones

- 🚧 **v0.1.0 First public release** - Phases 1-10 (in progress)

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Foundations** - Workspace, transactional state, importer-exact format and validator, guided setup, `plugin/` packaging, Linux CI, first manual edition, owner smoke import
- [ ] **Phase 2: Text intake + quote verifier** - Every text format becomes frozen, page-anchored segments with a section map; exact quote verifier; synthetic incident generator v1
- [ ] **Phase 3: Extraction + claim ledger** - Chunked, resumable claim extraction with verification on write and the evidence-bank entry gate
- [ ] **Phase 4: Reconcile** - Rosters, always-on de-identification with a zero-hit scan, and conflict detection and confirmation
- [ ] **Phase 5: Authoring + verify + build** - MVP: items, all 12 hard gates, coverage, master workbook, first end-to-end run and owner import
- [ ] **Phase 6: Incremental** - Mark-imported locks, delta workbooks, correction items, rebuild and consolidated builds
- [ ] **Phase 7: Scans + OCR** - Per-page OCR with confidence carried to items, language packs, optional docling
- [ ] **Phase 8: Media + images** - Local transcription, keyframes, CCTV time OCR, images without GPS, sidecar notes
- [ ] **Phase 9: Web snapshot** - User-confirmed, dated web snapshots as inputs; the seven-skill and full CLI surface completed
- [ ] **Phase 10: Release** - Agent evals, fresh-machine install, final manual and docs, media CI job, v0.1.0 tag

## Phase Details

### Phase 1: Foundations

**Goal**: A user can set the plugin up once, create a case folder and inventory its inputs safely. The workbook format is proven against the real ProbeMatrix importer before any evidence logic exists.
**Depends on**: Nothing (first phase)
**Requirements**: WS-01, WS-02, WS-03, WS-04, WS-06, WS-07, WS-08, WS-09, WS-11, WS-12, WS-13, BLD-01, BLD-02, BLD-03, BLD-08, PKG-01, PKG-03, PKG-05, PKG-06, PKG-07, PKG-08, PKG-09, PKG-11, TST-01, TST-07, DOC-04, DOC-05
**Success Criteria** (what must be TRUE):
  1. In an empty folder, `epb init` creates `inputs/`, `outputs/`, `INDEX.md` and `.epb/`. The `.epb/` folder holds `case.yaml`, a `state.json` that already contains the workbook registry, the Evidence ID and Tag counters and chunk status, and a `.gitignore` covering `segments/`, `ledger/`, `inbox/`, `tmp/`, `media/`, `runs/` and `private/`. `INDEX.md` shows its six sections in order, with "none yet" where no producer exists. `init` and `doctor` warn in plain language when the folder is inside OneDrive, Dropbox, iCloud Drive or Google Drive, or inside a git repo that would track `.epb/private/`.
  2. On generated fixture folders, `epb scan` correctly reports new, changed (`S004v2`), renamed, duplicate and removed inputs, lists OS junk as ignored, and pairs `.note.md`/`.note.yaml` sidecars with their inputs. A crash injected at every transaction step resumes without corrupting state. A second mutating run waits for the lock. Every command returns exit codes 0–4, with a stable error code in its `--json` output. YAML values such as `12:30`, `0123` and `no` survive as text.
  3. The validator passes a generated minimal pack. It fails the prototype reference pack on its comma-bearing list fragments (a structural check for DEF-14). It also rejects formulas, non-string cells, a blank Description or Type, non-exact enum values, cells over 32,767 characters and invalid Chain of Custody JSON.
  4. Owner smoke import: the owner imports the synthetic edge-case workbook into a ProbeMatrix test incident. The workbook contains a Description beginning with `=`, a `0` value, a long numeric ID, a `YYYY-MM` date, multi-entry Tags and Linked Equipment, and every QA Status value. The owner reports that every value shows exactly as written, that nothing became a formula, a number or a blank, and that list entries split into the expected separate entries.
  5. On Linux, the plugin installs into Claude Code from this repo's marketplace (`source: "./plugin"`). `epb doctor --setup`, launched through the standard-library-only `epb.py`, finds Python 3.11+, builds the private environment, installs the core packages and reports in plain language what is ready and what is optional. `epb doctor` lists every tool with its version, the input types it enables and per-OS install commands. `AGENTS.md` is in `plugin/`. Linux CI runs pytest, ruff, the dependency-age check and the licence allow-list, all green. The first edition of the user manual covers installing Python, adding the plugin to Claude Code, first-time setup and the plain-language privacy statement, with the Windows and macOS sections marked "not yet tested on this system". The repo-root `AGENTS.md` and `CLAUDE.md` are identical and concise (150 lines at most), and a CI test fails otherwise (PKG-11).

**Plans**: 7/16 plans executed in 8 waves

Plans:
**Wave 1**
- [x] 01-01-PLAN.md — Dev toolchain, dependency manifests and the package-legitimacy checkpoint (wave 1)
- [x] 01-02-PLAN.md — Design amendments A16–A30 for the Phase 1 decisions (wave 1)

**Wave 2** *(blocked on Wave 1 completion)*
- [x] 01-03-PLAN.md — CLI shell: stdlib launcher, envelope, exit codes 0–4 (wave 2)
- [x] 01-04-PLAN.md — Importer-exact workbook format, validator and smoke pack (wave 2)
- [x] 01-05-PLAN.md — Supply-chain checks and Linux CI (wave 2)

**Wave 3** *(blocked on Wave 2 completion)*
- [x] 01-06-PLAN.md — Plugin manifests, plugin AGENTS.md and the Codex installer (wave 3)
- [x] 01-07-PLAN.md — `epb init` through the journalled, schema-validated store (wave 3)
- [ ] 01-08-PLAN.md — `epb doctor`: tools, packages, sync-folder and git warnings (wave 3)

**Wave 4** *(blocked on Wave 3 completion)*
- [ ] 01-09-PLAN.md — Case settings: case.yaml, strict YAML, init defaults (wave 4)

**Wave 5** *(blocked on Wave 4 completion)*
- [ ] 01-10-PLAN.md — `epb doctor --setup`: the private environment (wave 5)
- [ ] 01-11-PLAN.md — Complete case folder: layout, INDEX.md, runs, status, warnings (wave 5)

**Wave 6** *(blocked on Wave 5 completion)*
- [ ] 01-12-PLAN.md — Crash injection, lock and workspace upgrades (wave 6)
- [ ] 01-13-PLAN.md — `epb scan`: fingerprints, classification core, MIME detection (wave 6)

**Wave 7** *(blocked on Wave 6 completion)*
- [ ] 01-14-PLAN.md — Change detection corpus, sidecars and scan crash coverage (wave 7)

**Wave 8** *(blocked on Wave 7 completion)*
- [ ] 01-15-PLAN.md — Router skill, references and host install checks (wave 8)
- [ ] 01-16-PLAN.md — User manual first edition, mirrored instructions refresh, CI check (wave 8)

**UAT**: `/gsd-verify-work 1` with numbered step-by-step procedures (kickoff §8): prerequisites, exact commands, fixture paths, and the exact pass/fail strings to look for. It includes the owner's smoke-import procedure: the exact workbook path, a new ProbeMatrix test incident, and a checklist comparing each edge-case value as written with how it is shown after import. The agent never claims the import worked; the owner reports it.
**Defects addressed**: DEF-14 (structural list-fragment check only; the authoritative comma gate lands in Phases 4–5)
**Phase-order fixes**: PF-01, PF-04, PF-05, PF-06, PF-07, PF-11 (expander seam), PF-13 (Linux-only per §20 A9), PF-16, PF-18, PF-20
**Open decisions to discuss**: OD-13 (Codex route), OD-17 (dev-requirements split), OD-20 (schema location), OD-21 (workspace contract additions), OD-22 (`.claude/CLAUDE.md`, manifest `skills` key), OD-23 (MIME detection, `.7z`), OD-29 (`parent` as a list)
**Research**: Recommended. Dependency delivery and the launcher contract (`doctor --setup`), and the Codex and Cowork packaging routes.

### Phase 2: Text intake + quote verifier

**Goal**: Every supported text document in a case folder becomes frozen, page-anchored segments with a section map. Any quote can be checked verbatim against those segments, so an invented or altered quote is rejected before it can enter anything.
**Depends on**: Phase 1
**Requirements**: WS-05, INT-01, INT-02, INT-03, INT-04, INT-05, INT-06, INT-07, INT-08, INT-09, INT-10, INT-11, INT-12, INT-13, INT-14, INT-15, INT-16, QV-01, QV-02, QV-03, QV-04, QV-05, QV-06, TST-02
**Success Criteria** (what must be TRUE):
  1. On the bundled reference report, conversion yields 36 page segments whose printed labels equal the physical pages. The section map finds the briefing (p.5), eyewitness (p.7), observations (p.10) and improvements sections. The improvements and root-cause sections are screened `held_back`.
  2. The quote verifier accepts the prototype's genuinely verbatim quotes and rejects its known-invented ones ("instructed closure", "nearby fittings were intact"). It rejects every negative-corpus case: an inserted negation, a changed number, a changed case, a paraphrase in quote marks and a silently corrected typo. It accepts valid ellipsis quotes, cross-page quotes (cited as `pp.<a>–<b>`), `[sic]` quotes and bracketed-role-label quotes, the last through an injected stub resolver.
  3. Synthetic incident generator v1 produces a fully fictional case folder with the planted DEF traps and one input of every text type. Every input converts into ordered segments that carry a page label, physical index, heading path and confidence field. A two-column PDF reads in column order. A printed-versus-physical page offset is cited by its printed label, and a source with no reliable labels is cited as `PDF p.<n>`. DOCX tracked changes and comments are flagged, PPTX speaker notes are kept, spreadsheets become row-range segments, HTML keeps its main content and chat exports keep their timestamps. Repeated headers and footers are excluded from extraction.
  4. An `.eml` with RFC 2047 headers and an attachment, and a `.zip` containing a zip-slip member, register the attachment and the safe archive members as child sources with a parent link, and the unsafe path is refused. An unknown file type is listed as `unprocessed: unsupported type`. A corrupt or hostile PDF marks only that input `unprocessed: <reason>`. Document author metadata and email display names are captured as person entities and appear raw in no shareable file.
  5. Segments are frozen: re-running conversion changes nothing, and only `epb rebuild --from convert` re-converts and reports a diff. The `evidence-intake` skill drives scan, convert and segment. The manual gains a "what you can put in `inputs/`" section covering the supported text types and the optional `.msg` extra.

**Plans**: TBD
**UAT**: `/gsd-verify-work 2` with numbered step-by-step procedures (kickoff §8): prerequisites, the exact commands to generate the synthetic case folder and convert it, the fixture paths, the reference-report check run in a scratch folder, and the exact accept/reject strings expected from the verifier.
**Defects addressed**: DEF-01, DEF-02, DEF-03 (page labelling), DEF-13 (section screening, layer 1), DEF-15 (verifier side)
**Phase-order fixes**: PF-02 (stub resolver), PF-03, PF-08 (normaliser and language fields), PF-09 (segment confidence field), PF-11 (email and zip expanders), PF-12 (generator v1), PF-14 (`sources set`), PF-17
**Open decisions to discuss**: OD-23 (if not settled in Phase 1), OD-25 (fiscal-year, range and vague dates), OD-26 (source-literal versus omission ellipses), OD-31 (quoted reply blocks in email)
**Research**: Recommended. Column detection and quality heuristics for real-world PDFs, and printed-label detection.
**Note**: The prototype's quotes and the reference report are used only as regression targets, never as worked examples (clean-room rule).

### Phase 3: Extraction + claim ledger

**Goal**: The agent extracts every fact in the case folder into a verified claim ledger, chunk by chunk and resumably. Conclusions, lessons and recommendations are routed to a private held-back ledger and can never enter as evidence.
**Depends on**: Phase 2
**Requirements**: EXT-01, EXT-02, EXT-03, EXT-04, EXT-05, EXT-06, EXT-07, EXT-08, EVB-01, EVB-02, EVB-03
**Success Criteria** (what must be TRUE):
  1. On the synthetic incident, `epb plan-extract` builds section-bounded chunks of about 6–8k tokens with one segment of overlap. After extraction, every planted observation is a claim in `claims.jsonl` with its `kind`, `asserted_by`, verified anchor quotes, and dates at their stated precision.
  2. Every planted conclusion, lesson and recommendation lands only in `ledger/conclusions.jsonl`. `claims add` rejects a planted verdict disguised as an observation, and any evidence-kind claim from a held-back section, with a message telling the agent to reclassify or split the claim. Planted mixed fact-and-verdict sentences are split, and the run report lists the borderline splits.
  3. `claims add` rejects a claim that has an unverifiable anchor quote, a schema error, or an agent-set CLI-owned field (claim ID, offsets or page label), and lists every error with its path. A claim using each declared anchor type (page, cross-page, time range, sheet row range, visual and web snapshot) validates against the schema.
  4. An extraction interrupted mid-run resumes at the first unfinished chunk shown by `epb extract-status`. Chunk-suffixed submissions from parallel workers merge under the lock with no lost or duplicated claims. Every ledger write is recorded in the CLI write journal.
  5. The `evidence-extraction` skill, invoked by name in Claude Code on the synthetic incident, runs plan-extract, claims add and extract-status to completion while applying the evidence-bank entry rule. The manual gains a section on what happens during extraction and how to resume an interrupted run.

**Plans**: TBD
**UAT**: `/gsd-verify-work 3` with numbered step-by-step procedures (kickoff §8): prerequisites, exact commands, the synthetic case folder path, the planted verdict to submit and the exact rejection text expected, the steps to interrupt and resume a run, and the counts to compare in `claims.jsonl` and `conclusions.jsonl`.
**Defects addressed**: DEF-08 (date precision captured), DEF-10 (`asserted_by` required), DEF-13 (entry gate, layer 2)
**Phase-order fixes**: PF-10 (every anchor type declared), PF-19 (write journal starts)
**Research**: Optional. The ledger and gates are fully specified by the design and the architecture research.
**Note**: The shared `conclusions-policy.md` reference is drafted here for the extraction skill and completed under DOC-06 in Phase 5.

### Phase 4: Reconcile

**Goal**: Every person in the case material is reduced to a stable, comma-free role label that still lets quotes verify, and nothing shareable contains a name. Contradictions between sources are surfaced without the plugin picking a winner.
**Depends on**: Phase 3
**Requirements**: WS-10, DEID-01, DEID-02, DEID-03, DEID-04, DEID-05, DEID-06, DEID-07, DEID-10, REC-01, REC-02, REC-03, REC-04, REC-05
**Success Criteria** (what must be TRUE):
  1. On the synthetic incident, every planted name is caught: honorific forms (including Indian honorifics in Latin and Indic script), signature blocks, "Name:" fields, emails, phone numbers, ID patterns and document metadata authors. Each is mapped in `.epb/private/name-map.yaml` to a stable `<Designation> (<Function / Location>)` label with no commas, and its name variants are added to the scan list. With spaCy installed, an NER pass runs; without it, the run completes cleanly.
  2. `epb deid-scan` returns zero hits across `INDEX.md`, run reports, `run.json` and rendered test artefacts. It flags a planted name that was never added to the map. An allow-list entry without a justification is refused. An input whose file name contains a name appears in `INDEX.md` under its role label.
  3. A quote containing a planted name and honorific verifies after both are replaced by the bracketed role label, through the real name-map resolver (DEF-15).
  4. `epb conflicts detect` proposes the planted time conflict (beyond the 60 s tolerance, precision-aware), value conflict and actor conflict, and runs the sequence and framing checks. `conflicts resolve` records a confirm or dismiss with a reason and cannot pick a winner. Equipment-ID variants within one source become aliases with a source-inconsistency note and are never normalised inside a quote (DEF-18). Roster input containing commas, or names given on the command line, is refused.
  5. The `evidence-reconcile` skill runs rosters, de-identification and conflicts on the synthetic incident. The manual gains a section on what de-identification does, where the private name map lives and why it must never be shared, and what to do when `deid-scan` reports a hit.

**Plans**: TBD
**UAT**: `/gsd-verify-work 4` with numbered step-by-step procedures (kickoff §8): prerequisites, exact commands, the synthetic case folder path, the list of planted names and conflicts to check off, and the exact `deid-scan` output expected (zero hits on clean artefacts, one named hit on the planted unmapped name).
**Defects addressed**: DEF-04 (detection and confirmation), DEF-14 (comma-free labels at `roster add`), DEF-15, DEF-18
**Phase-order fixes**: PF-02 (real resolver), PF-04 (file-name substitution, INDEX scanned), PF-05 (comma check at `roster add`), PF-08 (honorifics in other scripts), PF-14 (roster input from file or stdin), PF-17 (metadata names routed through the map)
**Research**: Optional. Indic-script name-variant generation may need a short spike.

### Phase 5: Authoring + verify + build

**Goal**: MVP milestone. Starting from the router skill, the agent turns the synthetic text-only incident into a master workbook that passes every hard gate, and the owner imports it cleanly into ProbeMatrix. This is the first end-to-end, usable product.
**Depends on**: Phase 4
**Requirements**: AUT-01, AUT-02, AUT-03, AUT-04, AUT-05, AUT-06, AUT-07, AUT-08, AUT-09, AUT-10, VER-01, VER-02, VER-03, VER-04, VER-05, VER-06, VER-07, VER-08, VER-09, VER-10, VER-11, VER-12, VER-13, VER-14, VER-15, COV-01, COV-02, COV-03, BLD-04, BLD-05, BLD-06, BLD-07, EVB-04, EVB-05, DEID-09, REC-06, DOC-06, TST-03, TST-05
**Success Criteria** (what must be TRUE):
  1. Asked in Claude Code to "build an evidence pack from this folder", the `evidence-pack` router drives the synthetic text-only incident through intake, extraction, reconcile, authoring and verify, and writes `outputs/evidence-pack-<case>-master.xlsx`. `epb verify` passes all 12 hard gates. Items carry rule-based types, controlled tags, rubric priority and three-part Descriptions. A second build with no changes writes nothing and says so.
  2. Owner import: the owner imports the synthetic master into a new ProbeMatrix test incident and reports the following. The item count equals Total Evidence Items. Linked Equipment shows as separate entries, with no comma-split fragments. Tags are intact. QA/lifecycle status shows, including `disputed` items that state both versions. Related Evidence strings are present.
  3. Each hard gate demonstrably blocks the build on its planted defect: an invented or uncited quote, a wrong page, a format fault, a comma in a list element, an ID in prose, an HFACS term, a paraphrased held-back conclusion, a leaked name, an unaccounted observation claim, a Description over 1,800 characters, a padded date, and an item with no claim. `items add` refuses an item that references a held-back claim.
  4. The minimal eval scorer reports against the gold key: verbatim quotes 100%, page accuracy 100%, names leaked 0, conclusions leaked 0, plus coverage. The run report lists every soft warning and a seeded, reproducible 5-item spot-check with de-identified context. A synthetic low-confidence segment yields `status: low_confidence_source`. A non-English quote keeps its original script, followed by a `[translation]` rendering.
  5. The regression benchmark on the bundled reference report runs in a scratch, git-ignored folder. Its numbers (quotes verifiable, page accuracy, coverage of the DEF-12 findings, conclusion leakage) are reported in verification, and nothing from it is committed. All shared skill references are complete. The manual gains "build your first pack", "read INDEX.md" and "import the master into ProbeMatrix" sections.

**Plans**: TBD
**UAT**: `/gsd-verify-work 5` with numbered step-by-step procedures (kickoff §8): prerequisites, the exact prompt to give the agent, the exact commands, the synthetic case folder path, the gate-by-gate planted-defect checks, and the owner's ProbeMatrix import procedure. That procedure names the workbook file, says to create a new incident, and gives a checklist covering item count, separate Linked Equipment entries, no comma-split fragments, intact Tags, QA/lifecycle status and Related Evidence strings. The agent never claims the import worked; the owner reports it.
**Defects addressed**: DEF-01, DEF-02, DEF-03, DEF-04 (disputed items), DEF-05, DEF-06, DEF-07, DEF-08, DEF-09, DEF-10, DEF-12, DEF-13 (layers 3–4), DEF-14 (gate 4), DEF-15, DEF-16, DEF-17
**Phase-order fixes**: PF-01 (custody parsed from sidecars), PF-05 (authoritative comma gate), PF-07 (draft master), PF-08 (`[translation]` rule), PF-09 (low-confidence status), PF-10 (every citation form), PF-14 (`sections tag`, `coverage omit`, `items update/remove`, `run`), PF-15 (minimal scorer), PF-19 (`verify` enforces the journal)
**Open decisions to discuss**: OD-16 (machine-text labelling plumbing), OD-25 (Collection Date for range and fiscal-year dates)
**Research**: Optional. The gates are pure functions over design §14.
**Note**: This is the largest phase, with 39 requirements. Expect it to be split into many plans.

### Phase 6: Incremental

**Goal**: The owner can keep a pack current as new evidence arrives. Imported workbooks are locked. New items go out as delta workbooks that import into the same incident without duplicates. Fixes to shipped items go out as correction items.
**Depends on**: Phase 5
**Requirements**: INC-01, INC-02, INC-03, INC-04, INC-05, INC-06, INC-07, INC-08, INC-09, INC-10, INC-11, DOC-02
**Success Criteria** (what must be TRUE):
  1. Incremental eval: the master is marked imported, either by `epb mark-imported` or by ticking its box in `INDEX.md`. After 2 inputs are added and the pipeline is re-run, `evidence-pack-<case>-delta-NNN.xlsx` contains only the new items, and their Evidence IDs and Tags continue from the master (gaps are kept and nothing is reused). `INDEX.md` is updated. A re-run with no changes writes nothing.
  2. Owner import: the owner imports the delta into the same ProbeMatrix test incident used for the master, and reports that only the new items were added, with no duplicates and no `-IMPn` tag collisions.
  3. An imported workbook is never written again. If a draft was rewritten after a possible upload, `mark-imported` asks the user to confirm the item count and Tag range. `INDEX.md` ticks are one-way. The plugin never locks a workbook on its own. A draft master left un-imported for longer than `draft_warning_days` triggers a warning.
  4. A new version of an input is diffed, and claims whose anchors no longer verify are flagged. A fix to a locked item ships as a correction item in the next delta: its Description begins "CORRECTION to evidence tagged TAG-…", it links to the original tag, and `INDEX.md` gives the manual clean-up steps. `epb rebuild --from <stage>` leaves every shipped ID unchanged. `epb build --consolidated` writes a consolidated workbook only when asked.
  5. The manual covers everyday use end to end: creating a case folder, adding inputs, asking the agent to build, reading `INDEX.md`, importing the master and then each delta in order, and marking a workbook imported.

**Plans**: TBD
**UAT**: `/gsd-verify-work 6` with numbered step-by-step procedures (kickoff §8): prerequisites, the exact commands, the two input files to add, the steps to tick the `INDEX.md` box, and the owner's delta-import procedure. That procedure names the delta file and the same incident as the master, and gives a checklist covering new-item count, no duplicates, continuing Tags and the correction item's text.
**Defects addressed**: None new. This phase protects the shipped gates across increments.
**Phase-order fixes**: PF-06 (delta-specific recovery), PF-07 (mark-imported, deltas, locks)
**Research**: Optional. The patterns are specified in design §12 and the architecture research.

### Phase 7: Scans + OCR

**Goal**: Scanned and image-only documents become usable, honestly labelled evidence. OCR runs page by page, its confidence travels all the way to the items, and low-confidence material is flagged for review.
**Depends on**: Phase 6
**Requirements**: OCR-01, OCR-02, OCR-03, OCR-04, OCR-05
**Success Criteria** (what must be TRUE):
  1. The synthetic generator is extended with an image-only PDF and a mixed PDF (text pages plus scanned pages). Both convert page by page, with OCR running only on the scanned pages, and each segment carries its OCR text and the confidence of the quoted span.
  2. Low-confidence OCR pages appear in the "Open issues" section of `INDEX.md`. Items drawn from them get `status: low_confidence_source`, and their Descriptions say "(OCR, low confidence)".
  3. `epb doctor` reports Tesseract and each language pack listed under `languages` in `case.yaml`, and a non-English scanned page is OCRed with its pack. Without Tesseract, scanned pages are marked unprocessed, the run still succeeds, and the OCR tests skip cleanly.
  4. With docling installed, a complex-layout PDF converts through the docling path. Without docling, the default path is used and nothing fails.
  5. The manual gains step-by-step instructions for installing Tesseract and its language packs on Linux, Windows and macOS (the last two marked "not yet tested on this system"), together with the matching `doctor` messages.

**Plans**: TBD
**UAT**: `/gsd-verify-work 7` with numbered step-by-step procedures (kickoff §8): prerequisites (including the Tesseract install commands for the dev machine), the exact commands, the generated scan fixture paths, and the exact `INDEX.md` and item text expected for a low-confidence page.
**Defects addressed**: None new. This phase extends DEF-01/DEF-03 protection to OCR text.
**Phase-order fixes**: PF-08 (language packs only), PF-09 (OCR confidence producer), PF-12 (generator extended with scans)
**Open decisions to discuss**: OD-14 (primary OCR path), OD-16 (labelling all OCR-derived quotes), OD-28 (docling model licence)
**Research**: Recommended. The OCR confidence path, legacy-font and `(cid:` routing, and a docling spike.

### Phase 8: Media + images

**Goal**: Audio, video and photographs become time-anchored or visual evidence. Recordings are transcribed locally, video yields keyframes and real-world CCTV times, and images are described only by what is visible. Nothing shareable carries GPS data or identifies a face.
**Depends on**: Phase 7
**Requirements**: MED-01, MED-02, MED-03, MED-04, MED-05, MED-06, MED-07, MED-08, DEID-08, AUT-11
**Success Criteria** (what must be TRUE):
  1. The synthetic generator is extended with wav and mp4 fixtures, and they produce time-anchored transcript segments with per-segment confidence. A silent recording produces no transcript text. Without a transcriber, the input is marked `unprocessed: transcription unavailable` and the run succeeds.
  2. The mp4 yields keyframes at scene changes, with a frequency floor and a frame cap, and the keyframes keep their media timestamps. A burned-in CCTV timestamp is read by OCR and gives the real-world time. Media items cite `hh:mm:ss–hh:mm:ss` in the workbook's Source column.
  3. For a photo with GPS EXIF data, the capture time and device are recorded, and no GPS data survives in any rendered or shareable copy. Image and keyframe claims record only what is visible, are flagged `anchor: visual`, never identify a person, and are listed for review.
  4. Sidecar notes supply who recorded what, speaker roles, the camera and the custody, and they are cited when used. Speaker diarisation stays off unless its optional extra is installed and enabled.
  5. The manual gains install steps for ffmpeg and the media extra (including its GPL codec licence note), instructions for writing a sidecar note, and the matching `doctor` messages.

**Plans**: TBD
**UAT**: `/gsd-verify-work 8` with numbered step-by-step procedures (kickoff §8): prerequisites (ffmpeg, the media extra and the model fetch), the exact commands, the generated wav, mp4 and photo fixture paths, and the exact citation strings and GPS-absence check expected.
**Defects addressed**: None new. This phase extends DEF-01/DEF-03 protection to transcripts and keyframes.
**Phase-order fixes**: PF-01 (media-specific sidecar fields), PF-09 (transcript confidence producer), PF-12 (generator extended with wav and mp4)
**Open decisions to discuss**: OD-16 (labelling all transcript-derived quotes), OD-17 (media extra and GPL codecs), OD-18 (HEIC), OD-27 (transcription test fixture)
**Research**: Recommended. Run the spike first: faster-whisper hallucination settings and VAD, and the CCTV keyframe thresholds.

### Phase 9: Web snapshot

**Goal**: On request, the user can bring public web pages into the case as dated, user-confirmed snapshots that flow through the pipeline like any other input. The seven-skill and full CLI surface is complete.
**Depends on**: Phase 8
**Requirements**: WEB-01, WEB-02, WEB-03, PKG-02, PKG-04
**Success Criteria** (what must be TRUE):
  1. The `evidence-web-snapshot` skill runs only when the user asks. It proposes URLs and saves only the ones the user confirms. `epb snapshot <url>` writes raw HTML, extracted Markdown and `meta.yaml` to `inputs/web/<YYYY-MM-DD>-<domain>-<slug>/`. The metadata records the URL, retrieval time, status, title, a de-identified byline and the publication date.
  2. A saved snapshot flows through scan, extraction, authoring and build like any other input, and its items cite `[web snapshot <date>] <url>`.
  3. A failed or paywalled fetch is recorded as failed, and nothing is paraphrased from memory. A web claim with no saved snapshot is refused (DEF-11).
  4. All seven skills pass the SKILL.md lint: Agent Skills format, about 150 lines or fewer, and shared rules linked from `evidence-pack/references/`. A CLI surface test confirms that every §15.2 and §20 A12 command exists and accepts `--json`.
  5. The manual gains a "save a web page into your case" section that includes its privacy note.

**Plans**: TBD
**UAT**: `/gsd-verify-work 9` with numbered step-by-step procedures (kickoff §8): prerequisites, the exact prompt and commands, a URL to snapshot plus a URL that is expected to fail, the expected snapshot folder layout and `meta.yaml` fields, and the exact citation string in the rebuilt workbook.
**Defects addressed**: DEF-11
**Phase-order fixes**: PF-14 (CLI surface audit)
**Research**: Optional. The module is small and uses the standard library.
**Note**: Tests use no network. Snapshot tests run against a local fixture server, never the live web.

### Phase 10: Release

**Goal**: v0.1.0 is released. The agent evals meet their thresholds, a non-technical user can install and use the plugin from the finished manual, and the version tag is pushed.
**Depends on**: Phase 9
**Requirements**: TST-04, TST-06, TST-08, PKG-10, DOC-01, DOC-03, DOC-07
**Success Criteria** (what must be TRUE):
  1. The agent evals on the synthetic incident meet the thresholds: verbatim quotes 100%, page accuracy 100%, names leaked 0, conclusions leaked 0. They also report conflicts surfaced and type accuracy, and the incremental scenario passes.
  2. On a fresh Linux machine, following only the manual, the plugin installs in Claude Code via `/plugin marketplace add ashley-eyekyam/probematrix-evidence-pack-builder` plus `/plugin install`, on Codex through its supported route, and in Cowork through plugin upload. `doctor --setup` completes, and `doctor` reports a sensible capability profile.
  3. A fresh case folder holds a text PDF, a scanned PDF, a DOCX, an email with an attachment, a CSV export, an audio file and a short video. Asking the agent to "build an evidence pack from this folder" produces a master workbook, which the owner imports into ProbeMatrix. A second run with one added file produces a delta containing only the new items.
  4. Linux CI runs the core tests and lint on Python 3.11 and 3.14, plus the media job (ffmpeg, Tesseract and faster-whisper `tiny`), all green. The manual is final. It covers installing Python, the optional tools and the plugin on all three hosts, everyday use, and troubleshooting that maps every `doctor` message and exit-4 error code to a plain-language fix. Its Windows and macOS sections are still marked "not yet tested on this system". README, CHANGELOG, CONTRIBUTING and SECURITY are written.
  5. Once all ten phases are verified, the `v0.1.0` tag is pushed.

**Plans**: TBD
**UAT**: `/gsd-verify-work 10` with numbered step-by-step procedures (kickoff §8): the fresh-machine install walkthrough exactly as the manual states it, the definition-of-done case folder and the exact prompt, the owner's ProbeMatrix import procedure for the master (new incident) and then the delta (same incident), and the eval report thresholds to check.
**Defects addressed**: All DEF-01…DEF-18 (re-measured by the agent evals and the reference-report benchmark)
**Phase-order fixes**: PF-13 (media CI job), PF-18 (fresh-install verification), PF-20 (manual finalised)
**Research**: Recommended. The Cowork runtime capability profile is undocumented.
**Note**: TST-06's Linux core CI job is set up in Phase 1 (under TST-01 and PKG-09). The requirement completes here, when the media job is added. Windows and macOS CI and fresh-machine testing are v2 (V2-01).

## Cross-Phase Threads

**User manual (DOC-05).** The manual starts in Phase 1. Every phase that adds a tool or user step extends it (a success criterion in each of Phases 2–9), and Phase 10 finalises it and walks it through on a fresh Linux machine. Its Windows and macOS sections stay marked "not yet tested on this system" until a post-v0.1.0 release (§20 A9).

**Synthetic incident (TST-02).** Generator v1 arrives in Phase 2. It is extended with scans in Phase 7 and with wav, mp4 and photos in Phase 8, and DEF traps are planted as each one becomes testable. It is the only worked example. Nothing from the reference report or the prototype is used as an example.

**Owner imports into ProbeMatrix.** There are four: Phase 1 (edge-case smoke workbook, test incident), Phase 5 (synthetic master, new incident), Phase 6 (delta, same incident) and Phase 10 (definition-of-done master and delta). The owner reports every result; the agent never claims an import worked.

**UAT.** Every phase ends with `/gsd-verify-work N` using numbered step-by-step procedures: prerequisites, exact commands, fixture paths and exact pass/fail strings (kickoff §8). Phase completion is gated on the verification result, not on executor ticks (kickoff §9).

### Phase-Order Fixes Placement

| Fix | Placement |
|-----|-----------|
| PF-01 | Phase 1 scan pairs sidecars; Phase 5 parses them into custody; Phase 8 adds media-specific fields |
| PF-02 | Phase 2 verifier takes an injected label resolver, tested with a stub; Phase 4 adds the real name-map resolver |
| PF-03 | Phase 2 section screening (`held_back`, `observation`, `mixed`) |
| PF-04 | Phase 1 INDEX section providers show "none yet" and fix the tick syntax; Phase 4 adds file-name substitution and scans INDEX |
| PF-05 | Phase 1 structural list-fragment check; Phase 4 comma check at `roster add`; Phase 5 authoritative gate 4 |
| PF-06 | Phase 1 full transaction and journal recovery with crash injection; Phase 6 delta-specific recovery only |
| PF-07 | Phase 1 state schema (workbook registry, counters, chunk status); Phase 5 draft master; Phase 6 locks and deltas |
| PF-08 | Phase 2 normaliser and language fields; Phase 4 honorifics in other scripts; Phase 5 `[translation]` rule; Phase 7 language packs only |
| PF-09 | Phase 2 segment `confidence` field; Phase 5 status derivation tested with a synthetic segment; Phases 7–8 producers |
| PF-10 | Phase 3 declares every anchor type; Phase 5 renders every citation form |
| PF-11 | Phase 1 expander seam; Phase 2 email and zip expanders (`.7z` optional) |
| PF-12 | Phase 2 generator v1; Phase 7 scans; Phase 8 wav, mp4 and photos |
| PF-13 | As amended by §20 A9: Linux-only core CI from Phase 1; media job in Phase 10 |
| PF-14 | Verbs fixed by §20 A12; delivered across Phases 2–5; surface audited in Phase 9 |
| PF-15 | Phase 5 minimal eval scorer |
| PF-16 | Phase 1 owner smoke import (§20 A10) |
| PF-17 | Phase 2 captures metadata authors and decoded email names; Phase 4 routes them through the map |
| PF-18 | Phase 1 launcher and private-environment strategy (§20 A8); Phase 10 verifies fresh installs |
| PF-19 | Phase 3 write journal starts; Phase 5 `verify` enforces it |
| PF-20 | Phase 1 manual starts; Phases 2–9 extend it; Phase 10 finalises it |

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundations | 7/16 | In Progress | - |
| 2. Text intake + quote verifier | 0/TBD | Not started | - |
| 3. Extraction + claim ledger | 0/TBD | Not started | - |
| 4. Reconcile | 0/TBD | Not started | - |
| 5. Authoring + verify + build | 0/TBD | Not started | - |
| 6. Incremental | 0/TBD | Not started | - |
| 7. Scans + OCR | 0/TBD | Not started | - |
| 8. Media + images | 0/TBD | Not started | - |
| 9. Web snapshot | 0/TBD | Not started | - |
| 10. Release | 0/TBD | Not started | - |
