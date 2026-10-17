# Project Research Summary

**Project:** ProbeMatrix Evidence Pack Builder
**Domain:** A local, open-source Agent Skills plugin (Claude Code, Cowork, Codex). Agents supply judgement; a deterministic Python CLI (`epb.py`) turns a case folder of incident material into a verbatim-cited, de-identified `EVIDENCE_PACK_V2` workbook for ProbeMatrix.
**Researched:** 2026-10-17
**Confidence:** HIGH for Python stack, workbook and verifier pitfalls, and architecture. MEDIUM for host packaging. LOW for the Cowork runtime and OCR/ASR tuning.

> **Ground rule:** the approved design (`docs/design/2026-10-17-evidence-pack-builder-design.md`) wins. Nothing here overrides it. Every place where research disagrees with the design, or adds something the design does not have, is listed under **Owner Decisions Needed**. Nothing is resolved until the owner decides.

> **Owner addition (2026-10-17, after research):** v0.1.0 must include a detailed, non-technical user manual for installing and using the plugin on Windows, macOS and Linux. Install-mechanics decisions (OD-07, OD-13) must be made with that audience in mind.

## Executive Summary

The product is closest to an e-discovery processing pipeline (hash, dedupe, families, exception reports, Bates-style locators) combined with a Presidio-class de-identifier and an LLM citation-grounding layer. Its unusual feature is a deterministic gatekeeper that sits between the agent and the evidence store. None of the comparable tools keeps a source's verdicts out of its facts, or verifies quotes exactly instead of fuzzily. Those two rules, together with zero-name output and importer-exact workbooks, are what the product is for. The research agrees on the overall shape: a **single-writer CLI**. Agents write proposals into `.epb/inbox/`. A CLI verb validates each proposal against a submission schema, verifies its quotes server-side, assigns IDs, pages and offsets, and commits it in a journalled transaction with `state.json` written last. The same pure gate functions run at `claims add`, at `items add` and at `verify`, so the three checks cannot drift apart.

The stack is settled and permissive:
- **Core:** openpyxl, pdfplumber/pdfminer.six, pypdf, pypdfium2, python-docx, python-pptx, bs4 with markdownify, Pillow, PyYAML through a strict loader, rapidfuzz (suggestions only), and jsonschema. Add lxml, defusedxml and charset-normalizer for security and correctness.
- **System tools:** Tesseract (called directly for TSV confidences) and ffmpeg, both run as subprocesses.
- **GPL-tainted extras:** extract-msg, faster-whisper/PyAV and pillow-heif stay optional.
- **Excluded:** PyMuPDF (AGPL) is kept out entirely.

The research also found real conflicts with the design. The most important are:
- Python 3.10 reached end of life on 2026-10-01.
- pypdf's security fixes are all younger than the two-week rule allows.
- No host installs Python dependencies for a plugin.
- The `python3 skills/...` invocation breaks once the plugin is installed.
- A plugin rooted at the repo would ship reference material that names real people.

The main risks are the four ways the product can fail outright:
1. **An invented quote** gets through a verifier that is too lenient. Fuzzy matching scored a negated quote at 92.3. NFKC normalisation changes meaning.
2. **A leaked name.** The zero-hit scan only searches for names already in the map. Indian honorifics, metadata fields and initials forms are the usual misses.
3. **A leaked verdict.** Part 3 of the Description is agent prose and can paraphrase the source's conclusion.
4. **A workbook the importer misreads.** A string starting with `=` becomes a formula and imports as blank, which rejects the whole file. Dates become serial numbers, and long IDs lose precision.

Each has a concrete mitigation, listed below. Most must be in place by Phase 1 or Phase 2, not in the phase where the feature becomes visible. The kickoff §5 phase order is broadly sound, but 15+ dependency-order problems need fixing. They are listed under **Phase-Order Fixes**.

## Key Findings

### Recommended Stack

The core set was resolved and probed on Python 3.10, 3.11 and 3.14, on Linux and Windows, with `--uploaded-prior-to P14D`. A transitive licence sweep found only MIT, BSD, PSF and Apache licences. Optional extras are in separate requirements files, and a missing extra marks inputs `unprocessed`; it never fails a run. The venv-bundled pip (25.x) does not support `--uploaded-prior-to`, so INSTALL must upgrade pip to 26.1 or later first.

**Core technologies:**
- **openpyxl ≥3.1.5:** writes the workbook and reads XLSX inputs. Write every cell as text (`data_type="s"`). Sanitise C0 control characters.
- **pdfplumber ≥0.11.9:** page text, words with positions, and tables. The version floor is a security fix (CVE-2025-64512 in pdfminer). Extraction collapses whitespace, so the verifier normalises it.
- **pypdf ≥6.19.0:** fallback text, `/PageLabels` and metadata. It has a high rate of security advisories, so isolate parsing in a subprocess with a timeout and a memory cap (OD-05).
- **pypdfium2 (already transitive):** renders pages for OCR. It replaces GPL `pdftoppm`.
- **python-docx ≥1.2.0 + lxml ≥6.1.0:** `paragraph.text` silently drops tracked insertions, so tracked changes must be read with lxml XPath. The lxml floor is the fix for an XXE CVE.
- **python-pptx, bs4 + markdownify, charset-normalizer, defusedxml:** handle slides, HTML, input encodings and XML hardening.
- **Pillow ≥12.3.0:** EXIF, GPS stripping (re-encode the pixels only) and fixtures. 12.3.0 fixes 4 CVEs. It cannot read HEIC.
- **jsonschema ≥4.25 (Draft 2020-12):** reports all errors with paths, which agents need to repair a submission. It is not in the design's §5 list.
- **PyYAML ≥6.0.3 via a strict loader:** implicit typing is turned off, because it turns `12:30` into 750, `0123` into 83 and `no` into False.
- **rapidfuzz:** "did you mean" suggestions and conclusion screening only. Never use it to accept a quote.
- **stdlib:** `email` with `policy.default`, `zipfile` with zip-slip guards, `mimetypes` plus magic bytes, and `argparse` (`allow_abbrev=False`, `color=False`).
- **Dev:** pytest ≥9, ruff ==0.16.10 (exact pin), and reportlab for test fixtures (not fpdf2, which is LGPL).
- **External tools, detected by `doctor`:** Tesseract ≥5 (`tsv` output for per-word confidence), ffmpeg ≥6 (also does scene detection, so opencv is not needed), and optionally ocrmypdf as a separate tool.

### Expected Features

The features are classified against the design: 35 table-stakes features (TS-01…TS-35) and 20 differentiators (DF-01…DF-20), all already in the design. The design defines v0.1.0 as all ten build steps, so "MVP" means the end-to-end milestone at Phase 5.

**Must have (table stakes):**
- SHA-256 inventory, dedup and renames, versions, parent/child families, junk filtering and an exception list (TS-01…TS-06)
- Per-modality extraction, `doctor` with graceful degradation, OCR, and chunked resumable processing (TS-07…TS-10)
- Stable never-reused IDs, page- and time-anchored segments, exact-match quote verification, generated citations, a section map and boilerplate detection (TS-11…TS-16)
- Layered name detection, stable role labels, an allow-list, a zero-hit scan, a private name map, and GPS and file-name de-identification (TS-17…TS-22)
- Register and custody fields, stored date precision, `asserted_by`, and an honest integrity flag (TS-23…TS-27)
- An importer-exact writer and stricter validator, plus comma-free lists (TS-28, TS-29)
- Sidecars, incremental runs, lock-on-import, INDEX.md, run logs and crash safety (TS-30…TS-35)

**Differentiators (why this product exists):**
- DF-01 conclusions-are-never-evidence, with four enforcement layers. This is the single biggest differentiator.
- DF-02 coverage matrix and gate. DF-03 conflicts kept without picking a winner.
- DF-04 classifying the underlying artefact, not the file it arrived in.
- DF-05 bracketed role labels that still verify. DF-06 ellipsis, cross-page and `[sic]` conventions.
- DF-08 Description standard plus lints. DF-09 correction items.
- DF-12 media turned into anchored text. DF-13 non-English verbatim quotes.
- DF-16 evals on a synthetic incident with planted traps. DF-17 the same behaviour on three hosts.

**Defer / owner decision:** 16 candidates not in the design (C-01…C-16) are listed under Owner Decisions. None of them is scope unless the owner accepts it. The design's anti-features stay out: HFACS classification, auto-import, other output formats, a GUI, cloud OCR, default diarisation, item-count targets and any opt-out switch.

### Architecture Approach

The architecture is a functional core with an imperative shell, behind a transactional file store:
- **Layers** run `core → store → pure domain → services → cli`. An `ast`-based pytest enforces the layering. The privacy rules become structural checks: only `deid.namemap` reads `private/`, and `render` and `formats` never import raw segments or claims.
- **Ownership:** each `.epb/` file has exactly one owning service.
- **Incrementality:** content-hash stage keys make the deterministic stages incremental and resumable.
- **Converters** sit behind a plug-in protocol and emit one modality-neutral `RawDocument` intermediate representation.
- **Segments** store only exact raw text. The char map is recomputed from a versioned normaliser.
- **Next actions:** `status --json` (or `run`) returns a `next[]` list, so the router SKILL.md stays short and behaves the same on every host.

**Major components:**
1. **core/ + store/:** atomic writes with a Windows retry, an OS advisory lock (never `os.kill`), the transaction journal with `state.json` written last, a strict YAML loader, `PreciseDate`, schema validation on write, and migrations.
2. **sources/ → convert/ → segments/:** scan with sidecar pairing and expanders; the converter registry with per-page PDF routing; page labels, sections, boilerplate, held-back screening and confidence.
3. **text/ + quotes/ (pure):** a versioned normaliser built from explicit fold tables, and a verifier that receives an injected `LabelResolver`.
4. **ledger/:** the chunk planner, the `claims add` entry gate, the held-back ledger and re-anchoring.
5. **deid/ → conflicts/ → items/ → coverage/:** rosters and the name map, then conflicts, then the item gate (which reuses the verify gate functions), then the omission matrix.
6. **verify/ → render/ → formats/ → build/ → index/:** the G01–G12 gate registry; semantic rendering (citations, dates, custody); the V2 adapter, plus an independent validator that re-reads the saved file; master, delta and correction builds; INDEX section providers.
7. **cli/ + doctor/ + web/:** a stdlib-only shim and the JSON envelope with stable error codes; capability probes; the only network code.

### Critical Pitfalls

1. **A lenient quote verifier (DEF-01/02).** Accept exact matches only, on a projection limited to §8.2. Never use NFKC/NFKD and never use fuzzy scores to accept. Cap the gap between ellipsis fragments and flag any elided negation. Set a minimum anchor length and warn when a quote is not unique. Phase 2 must ship a negative test corpus (inserted negation, changed number, changed case, corrected typo).
2. **Wrong segment text or pages (DEF-01/02/03).** Watch for:
   - pdfplumber interleaving two-column pages
   - extractors disagreeing about ligatures
   - pypdf `page_labels` returning physical indices when `/PageLabels` is absent
   - annexes that restart their page numbering

   Fixes: one recorded extractor per source, frozen segments, column detection, quality heuristics for `(cid:` text and legacy fonts, and a label scheme decided once per source. Add a fixture where printed ≠ physical; the Hazira reference cannot catch this bug.
3. **Circular de-identification (DEF-15, leaked names).** The zero-hit scan only finds names that are already in the map. Add a scan that does not depend on the map (unknown capitalised or Indic-script tokens), and generate name variants (initials, possessive, honorifics such as Shri/Smt/S/o, -bhai/-ben/ji, Devanagari/Gujarati, ZWJ-stripped). Route every rendered field through the map. Strip metadata author fields at conversion.
4. **Conclusions leaking through paraphrase (DEF-05/13).** Require a mapping from each part-3 sentence to a claim. Lint for causal connectives. Screen sections into three states (held-back, observation, mixed). Add an SOP exemption for "should" statements. Plant traps for paraphrase and prior knowledge.
5. **Workbook coercion and crash safety.** Write every cell as a string. The on-disk validator rejects `<f>`, non-string cells, cells over 32,767 characters and invalid custody JSON. Sanitise control characters at segmentation. IDs come from a durable reservation. Retry `os.replace` and tell the user "close it in Excel". Run fault-injection crash tests.

Other notable pitfalls:
- Whisper hallucinates on silent CCTV audio: run VAD first and emit no transcript when there is no speech.
- `dateutil` fabricates precision: ban it.
- The draft-overwrite rule creates an import race.
- Agents game the gates: keep a journal of CLI writes and a dispositions report.
- Skill and launch failures on fresh machines (Windows Store `python3` stub, macOS system Python older than 3.10, PEP 668).
- Commas in Regulatory Requirements fields.

## Implications for Roadmap

The research **keeps the kickoff §5 ten-phase order** (it matches the dependency graph). It **moves foundations earlier** into Phases 1–3, so later phases never force a migration of persisted state. The changes follow the rule "fix every schema field before the first consumer persists data".

### Phase 1: Foundations (workspace, store, format, packaging skeleton)
**Rationale:** Everything else writes through this layer. Windows defects and the importer format assumptions must surface now.
**Delivers:**
- core/store with the full transaction journal and crash-injection tests
- the complete `state.json` schema: workbook registry, ID and tag counters, chunk status
- the strict YAML loader, the CLI envelope and exit codes, and the stdlib-only version-guard shim with its launcher contract
- the `formats/probematrix_v2` writer and on-disk validator, with a structural comma check
- scan with sidecar pairing and an expander seam
- INDEX section providers that show "none yet" until their producers exist, and a tick syntax
- the `doctor` probe registry
- plugin and marketplace manifests, a SKILL.md lint, a licence allow-list check, and a **3-OS CI matrix**

**Addresses:** TS-01–TS-06, TS-08, TS-11, TS-28, TS-29 (structural), TS-33 (skeleton), TS-35.
**Avoids:** Pitfalls 8, 9, 11 and 13; Windows paths and encoding.
**Owner checkpoint:** a smoke import of an edge-case pack (OD-09).

### Phase 2: Text intake + quote verifier
**Rationale:** Segments and the verifier carry Core Value #1. Every later contract (anchors, language, confidence) is shaped here.
**Delivers:**
- the converter protocol with all IR unit kinds declared, and the text converters (PDF with column detection, DOCX including tracked changes and comments, PPTX, XLSX/CSV, EML with RFC 2047 decoding, HTML, TXT and chat)
- the email and zip expanders
- the versioned normaliser with explicit fold tables
- segments with page-label detection, boilerplate masks, **held-back, observation and mixed section screening**, and confidence fields
- the verifier with a `NullResolver` and a negative test corpus
- a content inventory for each converter
- the explicit date parser
- metadata author stripping
- `sources set`
- **synthetic incident generator v1**

**Avoids:** Pitfalls 1, 3, 4 and 14; silent converter loss.

### Phase 3: Extraction + ledger
**Rationale:** The entry gate must exist before any claim is persisted.
**Delivers:**
- the chunk planner
- submission schemas that forbid server-owned fields
- the `claims add` entry gate, including mixed-sentence splitting and the held-back ledger
- an anchor schema covering **every** anchor type (page, time, sheet range, visual, web)
- `extract-status` and resume
- the ledger lock with wait semantics
- the CLI write journal

**Addresses:** DF-01 (layers 1–2), TS-10, TS-26. **Avoids:** Pitfalls 6 and 12.

### Phase 4: Reconcile (rosters, de-identification, conflicts)
**Delivers:**
- rosters that reject commas
- the private name map and the real `LabelResolver`
- detection passes, name-variant generation, and the **map-independent capitalised-token scan**
- `deid-scan`
- file-name substitution in INDEX
- conflicts with tolerance that respects precision and timezone, ranked and capped
- the allow-list and dismissal dispositions in the report

**Addresses:** TS-17–TS-22, DF-03, DF-05, DF-07. **Avoids:** Pitfalls 7, 9, 12; conflict noise.

### Phase 5: Authoring + verify + build (MVP milestone)
**Delivers:**
- the item gate, which reuses the verify gates
- render: citations in every form, dates at their precision, custody built from sidecars
- the G01–G12 gate registry, including the straight-quote and single-quote lint and the part-3 sentence-to-claim mapping
- coverage with `coverage omit`
- the draft master build with IDs never reused
- the spot-check
- the next-action protocol and router skill
- a **minimal eval scorer**
- the first end-to-end run on the synthetic incident, then the owner's real import

**Addresses:** DF-02, DF-04, DF-06, DF-08, DF-15, TS-23–TS-27. **Avoids:** Pitfalls 2, 6 and 9 (regulatory rendering).

### Phase 6: Incremental (deltas, locks, corrections)
**Delivers:** `mark-imported` with a per-write fingerprint confirmation, a tolerant one-way tick parser, deltas, re-anchoring, correction items, `rebuild --from`, `--consolidated`, and a no-op run test.
**Addresses:** TS-31, TS-32, DF-09, DF-20. **Avoids:** Pitfall 10.

### Phase 7: Scans + OCR + language packs
**Delivers:** pypdfium2 rendering into Tesseract TSV with confidence per span; routing of `(cid:` and legacy-font pages to OCR; a docling spike; Tesseract language packs; Indic honorifics in OCR text.
**Addresses:** TS-09, DF-10, DF-13 (packs only; the contracts already exist). **Avoids:** Pitfalls 3 and 5.

### Phase 8: Media + images
**Delivers:**
- faster-whisper with VAD, hallucination screens and the language pinned from `case.yaml`
- an explicit model fetch in `doctor`
- keyframes using a per-video threshold, a frame cap and `pts_time`
- overlay OCR
- EXIF re-encode with no GPS
- media-specific sidecar fields

**Addresses:** DF-11, DF-12. **Avoids:** Pitfall 5; media timing.

### Phase 9: Web snapshot
**Delivers:** the `web/snapshot` module (stdlib urllib, trafilatura for snapshots only), safe slugs, and byline/URL de-identification.
**Addresses:** DF-14.

### Phase 10: Evals, sample, docs, release
**Delivers:** host-level agent evals, including long-input drift checks and trigger-rate evals; the public sample with a zero-hit scan; fresh-machine installs on all three hosts and Windows; the media CI job; and the v0.1.0 release. **Owner addition:** the non-technical installation and user manual for Windows, macOS and Linux, verified on fresh machines.

### Phase Ordering Rationale

- The order follows the data flow (`scan → convert → segment → ledger → deid → items → verify → build`), and each phase consumes only what earlier phases persisted.
- Cross-cutting contracts (anchor types, citation forms, language fields, confidence, workbook registry, sidecars) are **declared** early and **filled** late. This avoids migrating workspaces in the middle of the milestone.
- Platform risk (Windows, encoding, locking, the importer format) is brought forward into Phase 1. The owner can only test by importing, so their first import should be possible at Phase 1, not Phase 5.

### Research Flags

Phases likely to need `/gsd-plan-phase --research-phase <N>`:
- **Phase 1:** how dependencies reach the user's machine, the launcher contract, and Codex/Cowork packaging (MEDIUM/LOW vendor documentation; needs a fresh-machine spike).
- **Phase 2:** column detection and quality heuristics for real-world PDFs, and printed-label detection (heuristics left open by §19).
- **Phase 7:** OCR confidence path and docling (MEDIUM; needs a spike).
- **Phase 8:** faster-whisper hallucination settings and CCTV keyframe thresholds (LOW, community sources only; spike first).
- **Phase 10:** the Cowork runtime capability profile (LOW, undocumented).

Phases with well-documented patterns (research can be skipped): **Phase 3** (ledger and gates; the architecture is fully specified), **Phase 5** (gates are pure functions over the design's §14), **Phase 6** (patterns are specified in §12 plus the architecture research), and **Phase 9** (small and stdlib).

## Phase-Order Fixes

These are dependency-order problems against the kickoff §5 phases: something an earlier phase needs is built by a later one. Each fix keeps the phase order. ARCH = ARCHITECTURE.md P-numbers; PIT = PITFALLS.md.

| # | Problem | Phases | Proposed fix | Source |
|---|---|---|---|---|
| PF-01 | Sidecar notes are scheduled for P8, but P1 `scan` must recognise `*.note.md`/`.note.yaml` as sidecars, otherwise P2 converts them as sources and P8 has to migrate them. P5 custody also needs sidecars. | P1/P2/P5 vs P8 | Pair sidecars in P1 scan. Parse them into custody in P5. P8 adds only the media-specific fields. | ARCH P1 |
| PF-02 | The P2 verifier must accept bracketed role labels, but the name map arrives in P4. | P2 vs P4 | Inject a `LabelResolver` and test P2 with a stub. The real resolver lands in P4. | ARCH P2, FEAT deps |
| PF-03 | Held-back section screening (§11.3 layer 1) is not in P2 scope, yet the P3 entry gate depends on it. | P2/P3 | Put `segments/screening.py` (held-back, observation and mixed states) in P2. | ARCH P3, PIT 6 |
| PF-04 | The P1 INDEX generator needs data from P4–P7, and needs rosters for file-name de-identification. | P1 vs P4–P7 | P1 builds section providers that show "none yet" and fixes the tick syntax. P4 adds file-name substitution and scans INDEX. P1–P3 tests use only synthetic names. | ARCH P4 |
| PF-05 | The P1 exit criterion "validator fails on comma-bearing labels" is really a roster-level check (P4–P5). | P1 vs G4 | P1: a structural fragment check. P4–P5: the authoritative G4 at `roster add` and `items add`. | ARCH P5, PIT 9 |
| PF-06 | Crash-resume is filed under §17 step 6, but P1 owns the lock and atomic writes, and the P3 exit criterion needs resume. | §17.6 vs P1/P3 | Full transaction and journal recovery, with crash injection, in P1. P6 adds delta-specific recovery only. | ARCH P6, PIT 11 |
| PF-07 | The P5 master build needs the workbook registry, the ID and tag counters and draft status, which are filed under P6. | P5 vs P6 | Define them in the P1 state schema. P5 implements the draft master. P6 adds mark-imported, deltas and locks. | ARCH P7 |
| PF-08 | Multi-language is in P7 but shapes the P2 normaliser (NFC, zero-width characters), P4 honorifics in other scripts, and the P5 `[translation]` rule against G1 and the `language` field. | P7 vs P2/P4/P5 | Design the language fields and `[translation]` grammar in P2–P5 with Unicode fixtures. P7 adds only the language packs. | ARCH P8, PIT 7 |
| PF-09 | The confidence status and warning are P5 gates, but their producers arrive in P7 and P8. | P5 vs P7/P8 | Add the segment `confidence` field in P2 and status derivation in P5, tested with a synthetic low-confidence segment. | ARCH P9, PIT 5 |
| PF-10 | The claim schema (P3) and citation renderer (P5) must handle time, sheet-range, visual and web anchors whose producers arrive in P8 and P9. | P3/P5 vs P8/P9 | Declare every anchor type in P3 and every citation form in P5, with unit tests. | ARCH P10 |
| PF-11 | Email attachments and archive members are registered at scan time (P1), but email parsing is in P2. | P1 vs P2 | Expander seam in P1. Email and zip expanders in P2. `.7z` optional. | ARCH P11 |
| PF-12 | The synthetic incident fixture belongs to no phase, yet P3 exits on it. | all | Make the fixture generator a P2 deliverable. Extend it in P7 (scans) and P8 (wav/mp4). Plant DEF traps as each becomes testable. | ARCH P12 |
| PF-13 | Windows and macOS CI only arrive in P10. CRLF offsets, `os.replace` failures, cp1252 stdout and NFD paths would build up over nine phases. | §17.10 | A 3-OS core CI matrix in P1. The media job waits until P10. | ARCH P13, PIT 9/K, ARCH C9 |
| PF-14 | Verbs the workflow needs are missing from §15.2: `sources set`, `sections tag`, `coverage omit`, `items update/remove`, `run`, and roster input from a file. | P2–P6 | Decide before P3 planning (OD-11). | ARCH P14, C4, C5 |
| PF-15 | No eval scoring until P10, yet the P5 milestone is "end-to-end on the synthetic incident". | P5 vs P10 | A minimal scorer in P5 (verbatim rate, page accuracy, leak counts from the gold key). | ARCH P15 |
| PF-16 | The first owner import is at P5, but the format assumptions are P1 deliverables. | P1 vs P5 | Owner smoke import of a P1 edge-case pack (OD-09). | PIT K10 |
| PF-17 | De-identification channels outside P4: document metadata authors and RFC 2047 email display names enter at P2 conversion. | P2 vs P4 | Strip or tag metadata author fields and decode headers in P2, so P4 can route them through the map. | PIT 7 |
| PF-18 | Dependency delivery, the launcher path and interpreter discovery are first needed for P5 router testing on hosts, but they constrain the P1 shim and layout. | P1 vs P5/P10 | Decide the venv and launcher strategy in P1 (OD-07). P10 only verifies fresh installs. | STACK Gap 1, PIT 13 |
| PF-19 | The journal of CLI writes (detecting agent hand-edits) is needed by the P5 `verify`, but must start recording at the first P3 write. | P3 vs P5 | Journal from P3. Verify enforces it in P5. | PIT 12 |
| PF-20 | (Owner addition) A non-technical install manual written only in Phase 10 would document install mechanics nobody tested with that audience. | P1 vs P10 | Start the manual in P1 (install and `doctor` on all three OSes), extend it as each phase adds tools, finalise and fresh-machine-test it in P10. | Owner, 2026-10-17 |

## Owner Decisions Needed

This is one deduplicated list that merges every "Conflicts with design", "Candidates not in design" and "Open question / Gap" item from the four research files. Blocking items come first, then the rest by impact. **Blocking = yes** means it must be decided before requirements or the roadmap are fixed. **no** means it can wait for that phase's discussion.

### Blocking (decide before requirements and roadmap)

**OD-01. Should the "evidence never leaves the machine" claim be reworded, given that the host's LLM reads segment text?**
- Sources: PIT Conflict 1; Security table (synced folders)
- Design: §2 goal 10, §4; the PROJECT.md "Locality" constraint
- Recommend: yes. Change it to "conversion is local; the agent sends excerpts to your host's model provider". Add `init`/`doctor` warnings for case folders in OneDrive, Dropbox or iCloud. Reason: as written, it is a compliance misstatement about a privacy product.
- Blocking: **yes**

**OD-02. Should `.epb/.gitignore` ignore everything that holds raw text (segments, ledger, inbox, runs), not just `private/` and `media/`?**
- Sources: ARCH C7
- Design: §6 rules, §13.5
- Recommend: yes. Ignore `*` except `case.yaml`, `rosters/`, `items/`, `conflicts.yaml` and `coverage.json`, and include `runs/*/run.json` in the deid-scan scope. Reason: raw names would be committed if a case folder is a git repo.
- Blocking: **yes**

**OD-03. Should the shippable plugin move into a subdirectory (for example `plugin/`), so tests, evals and `docs/reference/` (which names real people) do not ship to users?**
- Sources: STACK C9
- Design: §5
- Recommend: Option B (subdirectory, marketplace `source: "./plugin"`). Reason: otherwise every install copies reference material that names real people into user caches and Cowork accounts, and the repo will grow towards Cowork's limits.
- Blocking: **yes** (repo layout is fixed in Phase 1)

**OD-04. Should the Python floor stay at 3.10 or rise to 3.11?**
- Sources: STACK C1; ARCH C8 (ARCH leans towards keeping 3.10; STACK recommends raising it)
- Design: §15.3, §18; PROJECT.md Constraints
- Recommend: raise it to **3.11**. CI covers 3.11–3.14, with 3.15 as allowed-failure after 2026-10-23. Reason: 3.10 has been EOL since 2026-10-01, and Pillow, rapidfuzz, rpds-py, soupsieve and ocrmypdf have already left it, so 3.10 users would be frozen on unpatched Pillow.
- Blocking: **yes**

**OD-05. Should there be a written security exception to the "no dependency younger than two weeks" rule?**
- Sources: STACK C2; STACK Gap 3 (CI enforcement)
- Design: §18; kickoff §7
- Recommend: yes. A release that fixes a published advisory in an untrusted-input parser may be adopted early after review, with an exception list checked by the CI two-week checker. Pin `pypdf>=6.19.0` for now and run PDF parsing in a subprocess with timeout and memory caps. Reason: six pypdf DoS advisories are fixed only in releases under two weeks old, and parsing untrusted PDFs is the product's job.
- Blocking: **yes**

**OD-06. Should the core dependency list add jsonschema, lxml ≥6.1.0, defusedxml and charset-normalizer?**
- Sources: ARCH C2; STACK C12
- Design: §5 (`requirements.txt`); kickoff §7 "validate on every write"
- Recommend: yes, all four (all permissive). Reason: validate-on-write needs a validator that reports every error to the agent, and lxml/defusedxml close XXE and billion-laughs holes in XLSX and DOCX parsing.
- Blocking: **yes**

**OD-07. How do Python dependencies reach the user, and how is the CLI launched on each host?**
- Sources: STACK Gap 1; PIT Conflict 6; PIT 13; STACK host notes
- Design: §15.2 (`python3 skills/…/epb.py`), §15.3, §18
- Recommend: a stdlib-only, version-guarded `epb.py` shim. `epb doctor --setup` creates one venv in a per-user data directory (`${CLAUDE_PLUGIN_DATA}` when present) with the two-week pip flag and re-execs inside it. Claude Code uses `${CLAUDE_PLUGIN_ROOT}`/`${CLAUDE_SKILL_DIR}` paths; Codex resolves the path relative to the skill. Interpreters are detected (`py -3`/`python`), never hard-coded as `python3`. Reason: no host installs Python dependencies, and the repo-relative `python3` call breaks when the plugin is installed, on Windows (Store stub) and on old macOS Python. **Owner addition:** this must be operable by a non-technical user following the manual.
- Blocking: **yes**

**OD-08. Should the 3-OS CI matrix run from Phase 1 instead of Phase 10?**
- Sources: ARCH C9, P13; PIT Conflict 9 (K)
- Design: §17.1/§17.10; kickoff §5
- Recommend: yes, a core-tests matrix from Phase 1, with the media job left in Phase 10. Reason: atomic writes, locking, encoding and paths are Phase 1 deliverables, and Windows defects would otherwise pile up.
- Blocking: **yes** (changes phase scope)

**OD-09. Should the owner do a smoke import of an edge-case workbook in Phase 1, rather than waiting for the first import at Phase 5?**
- Sources: PIT Conflict 10 (K); PIT 8
- Design: kickoff §8; §8.4
- Recommend: yes. Use a pack with a `=`-leading Description written safely, `0`, a 19-digit ID and a `YYYY-MM` date. Reason: format assumptions are cheap to fix in Phase 1 and expensive at Phase 5, and the owner can only test by importing.
- Blocking: **yes** (adds a Phase 1 UAT)

**OD-10. Should a fifth exit code (4) cover internal errors, lock timeouts and workspaces newer than the plugin?**
- Sources: ARCH C3; ARCH Anti-Pattern 6; PIT 11 (distinct lock exit)
- Design: §15.2
- Recommend: yes, exit 4 with the cause in `errors[].code`. Reason: today a crash exits 1, which the agent reads as "fix your evidence content".
- Blocking: **yes** (CLI contract fixed in Phase 1)

**OD-11. Should §15.2 add the missing verbs: `sources set`, `sections tag`, `coverage omit`, `items update/remove`, roster input from a file or stdin, and `run`?**
- Sources: ARCH C4, C5, P14
- Design: §8.1, §11.1–11.2, §12.1, §15.1 vs §15.2
- Recommend: add all of them. `run` executes the deterministic stages that are due and returns `next[]`. Reason: the documented flow cannot be performed without them, and names must never be passed on argv.
- Blocking: **yes** (before Phase 3 planning)

**OD-12. Should the `Source` citation show whether a page number is printed or physical?**
- Sources: PIT Conflict 3; PIT 4
- Design: §7.3, §8.4 Source format
- Recommend: decide the scheme once per source, and render physical indices distinctly (for example `PDF p.<n>`). Reason: `p.<n>` is ambiguous, and mixed schemes within one source bring back DEF-03.
- Blocking: **yes** (changes the §8.4 output contract)

### Non-blocking (decide at phase discussion)

**OD-13. Should Codex distribution go via a Codex plugin manifest plus a cross-platform installer, instead of the `.sh` installer and a committed symlink?**
- Sources: STACK C6; PIT Conflict 5
- Design: §5, §15.3
- Recommend: primary route `codex plugin marketplace add`, shipping `.codex-plugin/plugin.json`. Ship `tools/install-codex.py` (with `.sh`/`.ps1` wrappers) that copies `skills/` into `$HOME/.agents/skills`. Keep the symlink for contributors only. Reason: `.sh` does not run on Windows, the symlink becomes a text file there, and users run Codex in case folders, not in this repo. A fresh-machine test must confirm which manifest Codex reads.
- Blocking: no (Phase 1)

**OD-14. Which OCR path is primary, given that §7.2 names ocrmypdf + Tesseract with a `pdftoppm` fallback?**
- Sources: STACK C3; PIT Conflict 7; PIT minor (`--force-ocr`)
- Design: §7.2, §7.3, §14
- Recommend: pypdfium2 render, then `tesseract … tsv` as primary (per-word confidence). ocrmypdf stays an optional external tool for searchable copies only. Drop `pdftoppm` (GPL). Reason: ocrmypdf exposes no confidence values, and it needs Python ≥3.11 and Ghostscript.
- Blocking: no (Phase 7)

**OD-15. How should the import race be closed, where a draft rewritten after upload gets locked in its rewritten form?**
- Sources: PIT Conflict 4; PIT 10
- Design: §4, §12.1
- Recommend: a per-write fingerprint, plus count/Tag-range confirmation at `mark-imported` when the draft was rewritten. Ticks are one-way. Reason: otherwise items are silently never imported, or duplicated.
- Blocking: no (Phase 6)

**OD-16. Should all OCR- and transcript-derived quotes be labelled as machine text, not only low-confidence ones?**
- Sources: PIT Conflict 2; PIT 5
- Design: §8.4 QA Status, §14 soft warnings
- Recommend: yes ("machine transcript" / "OCR text" in the lead-in or Source). Reason: hallucinations can carry high confidence.
- Blocking: no (Phase 5 plumbing, Phases 7/8)

**OD-17. How should the media extra and dev requirements be handled?**
- Sources: STACK C5; STACK install note
- Design: §5 (`requirements-media.txt`, dev = "all optional")
- Recommend: document that the media extra pulls GPL codec binaries (PyAV), and drop opencv-python-headless (ffmpeg does scene detection; it clashes with docling's opencv). Dev requirements must not include the GPL extras: use a separate `requirements-dev-full.txt` for the CI media job. Reason: licence honesty, and contributors' environments are not GPL-tainted.
- Blocking: no (Phase 8, with the dev-requirements part in Phase 1)

**OD-18. How should HEIC images be supported?**
- Sources: STACK C4
- Design: §7.2
- Recommend: an optional GPL `requirements-heic.txt` (pillow-heif) or external `heif-convert`/`sips`; otherwise `unprocessed: HEIC decoder missing`. Reason: Pillow cannot read HEIC, and pillow-heif wheels are GPLv2.
- Blocking: no (Phase 8)

**OD-19. How should locking work when parallel subagents call `claims add`?**
- Sources: ARCH C10; PIT 11
- Design: §12.5 vs §15.3
- Recommend: mutating commands wait for the lock (60 s default, `--wait`), read-only commands take no lock, and transactions are per unit. A separate short ledger lock is optional. Reason: hard failure on contention makes agents skip claims silently.
- Blocking: no (Phase 1 discussion)

**OD-20. Where should the canonical schemas live?**
- Sources: ARCH C1
- Design: §5 (root `schemas/`)
- Recommend: canonical runtime copy in `scripts/epb/schemas/`, with the root copy kept as a test-verified mirror. Reason: Codex installs copy only `skills/`. (OD-03 interacts with this.)
- Blocking: no (Phase 1)

**OD-21. Should the §6 workspace contract document `.epb/inbox/`, `tmp/`, `ledger/chunks.json` and `.epb/.gitattributes`?**
- Sources: ARCH C6
- Design: §6
- Recommend: yes, add them to §6 and `workspace-contract.md`. Reason: inbox holds raw names, and `.gitattributes` (`* -text`) protects byte offsets.
- Blocking: no

**OD-22. Root `CLAUDE.md` and the `"skills"` key in `plugin.json`.**
- Sources: STACK C7, C8
- Design: §5
- Recommend: move the file to `.claude/CLAUDE.md`, and omit `skills` from the Claude manifest. Reason: `claude plugin validate --strict` warns on a root CLAUDE.md, and the key is redundant.
- Blocking: no (Phase 1)

**OD-23. MIME detection and `.7z` handling.**
- Sources: STACK C10, C11
- Design: §7.1
- Recommend: use stdlib `mimetypes` plus a magic-byte table (no python-magic), and handle `.7z` only through an external `7z` binary. Reason: libmagic is missing on Windows, and py7zr is LGPL.
- Blocking: no (Phase 1/2)

**OD-24. Should segments be frozen per source, with optional upper bounds on text-producing converters?**
- Sources: PIT Conflict 8; PIT 3
- Design: §18 "pin minimum versions"
- Recommend: freeze segments; re-convert only via explicit `rebuild --from convert` with a diff. Reason: library upgrades change segment text and break quotes that were already verified.
- Blocking: no (Phase 2)

**OD-25. How should fiscal-year, range and vague dates be handled?**
- Sources: PIT Conflict 11; PIT 14
- Design: §8.4 Collection Date
- Recommend: leave Collection Date blank, keep the exact text in the Description, and use internal `precision: range|fiscal_year`. Reason: no rule exists, and padding fabricates precision.
- Blocking: no (Phase 2/5)

**OD-26. How should source-literal ellipses be told apart from omission ellipses?**
- Sources: PIT Conflict 12
- Design: §8.2, G1
- Recommend: split on the agent's `…` before normalising, and match a source-literal ellipsis exactly. Reason: this affects gate 1 semantics.
- Blocking: no (Phase 2)

**OD-27. What should the transcription test fixture be?**
- Sources: STACK Gap 2
- Design: kickoff §7 (fixtures generated at test time)
- Recommend: allow one tiny committed synthetic-voice wav, generated once and documented. Reason: there is no permissive offline TTS.
- Blocking: no (Phase 8)

**OD-28. Docling and spaCy model licences.**
- Sources: STACK Gap 4
- Design: §13.1, §19
- Recommend: check them before either becomes a default. Keep both optional until then. Reason: model weights carry their own licences.
- Blocking: no (Phase 7)

**OD-29. Can an identical attachment carried by two emails have more than one parent?**
- Sources: FEAT C-03
- Design: §7.1, §8.1 (`parent`), §8.4 custody
- Recommend: clarify that `parent` becomes a list, so custody shows every carrier. Reason: this looks like a design ambiguity, not new scope.
- Blocking: no (Phase 1 schema, so decide early)

**OD-30. Near-duplicate detection (for example DOCX + PDF of the same report).**
- Sources: FEAT C-01
- Design: §7.1, §10.2, §11.1
- Recommend: consider it for after v0.1.0, and rely on the `duplicate` omission reason for now. Reason: useful, but it is new scope at MEDIUM cost.
- Blocking: no

**OD-31. Email threading and quoted-reply suppression.**
- Sources: FEAT C-02; PIT moderate (email quoting → DEF-10)
- Design: §7.1, §7.4
- Recommend: at minimum, split quoted blocks into their own perspective in Phase 2. Defer full threading. Reason: misattributing quoted text breaks `asserted_by`.
- Blocking: no (Phase 2)

**OD-32. A withheld-input register (for example privileged advice).**
- Sources: FEAT C-04
- Design: §6, §6.1, §12
- Recommend: owner's call based on their privilege practice. Lean towards deferring. Reason: today deletion is the only exclusion, and it shows as "removed".
- Blocking: no

**OD-33. Cheap audit additions: a de-identification replacement summary (C-05), an over-redaction eval metric (C-06), and re-hashing inputs at build (C-08).**
- Sources: FEAT C-05, C-06, C-08
- Design: §13.5, §14, §16, §7.1
- Recommend: accept all three. Reason: each is LOW cost and strengthens a Core Value claim.
- Blocking: no

**OD-34. An `epb search <term>` command over segments.**
- Sources: FEAT C-09
- Design: §15.2, §13
- Recommend: consider it, with de-identified or private-only output. Reason: it helps confirm omissions and aliases, but raw text holds names.
- Blocking: no

**OD-35. An evidence-category inventory in INDEX (people / paper / physical / recording).**
- Sources: FEAT C-10
- Design: §6.1, §9.2, §2 non-goals
- Recommend: decline, or allow neutral counts only. Reason: suggesting what to collect drifts towards performing the investigation.
- Blocking: no

**OD-36. A chronology table in the run report.**
- Sources: FEAT C-11
- Design: §2, §10
- Recommend: decline, or keep it private to `.epb/runs/`. Reason: it implies causal sequence and is not an output format.
- Blocking: no

**OD-37. Confirm the declined candidates: Citations API/LangExtract grounding (C-12), image/video redaction (C-13), Bates stamping (C-14), a hash manifest (C-15) and a per-user access log (C-16).**
- Sources: FEAT C-12…C-16
- Design: §2 goal 9, §6, §8.4
- Recommend: decline all five, except that C-15 may go in `.epb/runs/` only. Reason: each is host-specific, unneeded under the current output contract, or conflicts with read-only inputs.
- Blocking: no

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH (Python), MEDIUM (host packaging), LOW (Cowork runtime) | Versions, licences and behaviour were probed and executed locally, and advisories come from the GitHub Security Advisory API. Host facts come from vendor documentation that changes often. Context7 was unavailable. |
| Features | MEDIUM-HIGH | Mapping to the design is HIGH. Comparable-tool practice is MEDIUM; some vendor and ICAM sources are LOW. |
| Architecture | HIGH | Derived from the design and verified locally (PyYAML typing, argparse defaults, openpyxl formula coercion, script shadowing). Codex install specifics are MEDIUM. |
| Pitfalls | HIGH (workbook, PDF, verifier, YAML, dates), MEDIUM (hosts), LOW (OCR/ASR/CCTV tuning) | Workbook behaviour was round-tripped through the importer's own SheetJS reader. Media guidance is community-sourced and needs spikes. |

**Overall confidence:** HIGH for what to build and in what order. MEDIUM-LOW for host install mechanics and media tuning.

### Gaps to Address

- **Cowork runtime** (pip, ffmpeg, tesseract, path mapping) is undocumented. Treat text intake as the baseline, let `doctor` decide, and test in Phase 10.
- **Which manifest Codex actually reads** (`.claude-plugin` vs `.codex-plugin` vs root `plugin.json`). Needs a fresh-machine test in Phase 1.
- **Real-world fixture realism:** reportlab does not shape Indic text, and the Hazira reference has printed = physical page numbers. Real shaped-Devanagari and off-by-N fixtures are needed.
- **Strengthening measures the research recommends** but which are not design conflicts: a map-independent de-id scan, the part-3 sentence-to-claim mapping, a minimum quote anchor length, a cap on ellipsis gaps, and a CLI write journal. Planners should include them in the relevant phase requirements, and raise them with the owner if they are judged to be design changes.
- **Whisper and CCTV thresholds** are community-sourced only. Run the Phase 8 spike before committing to numbers.
- **Non-technical manual (owner addition):** needs real fresh-machine walkthroughs on Windows, macOS and Linux, including installing Python, Tesseract and ffmpeg, which a non-technical user may never have done.

## Sources

### Primary (HIGH confidence)
- The approved design §1–§19, `docs/GSD-KICKOFF.md` §3–§11, and `.planning/PROJECT.md`.
- PyPI JSON API (versions, upload dates, Requires-Python, licences, wheels), queried 2026-10-17. Local `uv pip compile --exclude-newer` on 3.10, 3.11 and 3.14 (Linux and Windows targets), and a pip 26.2.1 `--uploaded-prior-to P14D` install.
- Local probes on Python 3.14.4: openpyxl → SheetJS 0.18.5 importer round-trip; pypdf `page_labels`; pdfplumber columns and ligatures; python-docx tracked changes and comments; PyYAML implicit typing; NFKC folds; rapidfuzz scores; dateutil default filling; Pillow EXIF; argparse defaults; package shadowing.
- GitHub Security Advisories for pdfminer.six, pypdf, Pillow and lxml. PEP 619 (3.10 EOL). Python `os` docs (`os.replace`, Windows `os.kill`).

### Secondary (MEDIUM confidence)
- Claude Code docs (plugins reference, marketplace reference, skills), claude.com Cowork and platform-support pages, and the agentskills.io specification.
- EDRM processing guidelines, court ESI protocols, Presidio docs, Relativity Redact, TapRooT/ABS evidence categories, the Anthropic Citations cookbook, and FRONT (quote-first generation).
- OCRmyPDF docs and man page, pip NEWS, uv settings, PEP 686.

### Tertiary (LOW confidence)
- OpenAI Codex skills and plugin docs, and the Agent Plugins 1.0 specification (fast-moving).
- Community sources: faster-whisper and Whisper hallucination threads, WhisperX timestamp drift, ASR script confusion in South Asian languages, legacy Hindi PDF fonts, ffmpeg scene detection on static video, the Windows Store Python stub, and git symlinks on Windows.
- ISO/IEC 27037 (secondary descriptions only), ICAM PEEPO templates, and LangExtract alignment (community port docs).

---
*Research completed: 2026-10-17*
*Ready for roadmap: yes. Resolve the blocking items OD-01 to OD-12 first.*
