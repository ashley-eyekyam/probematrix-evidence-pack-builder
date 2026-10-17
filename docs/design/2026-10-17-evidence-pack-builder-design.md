# ProbeMatrix Evidence Pack Builder: Design

**Date:** 2026-10-17
**Status:** Approved by the owner, 2026-10-17. §8.4 amended the same day after a re-check of the importer (see "Importer re-check" in §8.4), and amended again after project research (§20, which wins over earlier sections).
**Next step:** development runs under GSD, driven by [`docs/GSD-KICKOFF.md`](../GSD-KICKOFF.md), in the build order in §17.
**Repository:** `probematrix-evidence-pack-builder` (new, standalone, open source, MIT). It starts as a subfolder of the ProbeMatrix checkout (git-excluded there) and is initialised as its own git repository.

---

## 1. Intent

Investigators hold incident material in many forms: official enquiry reports (often hundreds of pages, sometimes scanned), witness statement bundles, interview audio, CCTV and phone video, site photographs, DCS/SAP/CMMS exports, permits, procedures, emails, and press or regulator notices. ProbeMatrix analyses an incident through its four-level HFACS engine, but it reasons over one thing only: the **text of each evidence item** in an `EVIDENCE_PACK_V2` Excel workbook. It cannot open a PDF, watch a video or listen to audio. The Description *is* the evidence as far as the analyser is concerned.

This plugin turns a folder of raw incident material into a high-fidelity, citation-exact, de-identified, ProbeMatrix-importable evidence pack. It keeps that pack current as new evidence arrives, without rebuilding what already exists.

**Why now:** an internal prototype (a Node script plus a 7-phase skill) produced a 60-item pack for the ONGC Hazira 2020 fire from the PNGRB enquiry report. The pack was good enough to prove the idea and showed exactly where a hand-driven process breaks: invented quotes, wrong page numbers, unflagged contradictions, comma-corrupted fields, broken cross-references, the official answer leaking into the evidence, and silently dropped high-value findings (§3). The prototype was also tied to one codebase, one input type (a single text PDF) and one-shot runs.

**What success looks like:**
- Point it at a folder, get a pack whose every quote can be found word-for-word on the cited page of a saved input, every date is as precise as the source and no more, every person is a role label, and every fact traces to a source span.
- Drop three new witness recordings into the same folder next week, run it again, and get a small delta pack containing only the new items, ready to import into the existing ProbeMatrix incident, with the folder's index updated.
- Someone who has never seen the project can install it in Claude Code, Cowork or Codex and do this on their own incident.

## 2. Goals, non-goals, anti-goals

### Goals
1. **Ingest anything** a real investigation produces: text and scanned PDF, DOCX/ODT/RTF, PPTX, XLSX/CSV, email (.eml/.msg with attachments), HTML/web snapshots, plain text/Markdown/chat exports, images, audio and video. Unknown types are listed as "unprocessed", never silently ignored.
2. **Handle very large documents** by converting every input into page- or time-anchored Markdown *segments* first, then extracting from segments in bounded chunks. No step ever needs a whole report in context.
3. **Exact provenance:** every evidence item carries structured anchors (input file, page or timestamp, verbatim span), which are machine-verified before a pack is written.
4. **Identify evidence types correctly** from the underlying artefact, not from the report that carries it (§9).
5. **Detect and surface disagreements** between and within sources, and record who is asserting each fact (§10).
6. **Make curation auditable:** a coverage matrix of everything extractable versus what became an item, with a reason for every omission (§11).
7. **Run incrementally:** a persistent workspace state and a human-readable `INDEX.md`, where each run processes only new or changed inputs and emits a delta pack (§6, §12).
8. **Always de-identify** people, with no opt-out (§13).
9. **Work the same way on Claude Code, Cowork and Codex**, with all deterministic work in one Python CLI so behaviour doesn't drift between hosts.
10. **Run locally:** conversion uses local open-source tools only. The agent reads excerpts, which are sent to the AI host's model provider under that host's terms; nothing else leaves the machine unless the user explicitly runs the optional web-snapshot step, which only *fetches* public pages. (Amended 2026-10-17, see §20 A1.)

### Non-goals
- Performing the investigation: no HFACS classification, no root-cause analysis, no recommendations. That is ProbeMatrix's job.
- Importing into ProbeMatrix automatically (no API client). The user uploads the workbook.
- Producing other output formats (DOCX reports, JSON for other tools). `outputs/` holds evidence-pack workbooks only. A format-adapter seam is kept (§8.5) but only `EVIDENCE_PACK_V2` ships.
- A GUI. The agent and the CLI are the interface. `INDEX.md` is the status view.
- Cloud OCR, transcription or document-AI services.

### Anti-goals (would make it a failure even if it "works")
- **Any quote in a pack that is not verbatim in a saved input.** One invented quote destroys trust in the whole pack and in ProbeMatrix's citations downstream.
- **Any personal name in `outputs/` or in any shareable workspace file.**
- **The official answer leaking into the evidence.** No conclusion, lesson or recommendation from any source report is ever evidence: not in the claim ledger used by items, not in any item, not in any workbook. It is screened out before it enters the evidence bank (§11.3).
- **HFACS pre-classification** in Descriptions or Tags (no level labels, no HFACS category vocabulary such as "precondition", "supervisory violation", "organisational influence").
- **Duplicates in ProbeMatrix** caused by re-importing items that were already imported.
- **Silent loss:** an input that couldn't be read, a finding that was dropped, or a contradiction that was smoothed over, with no record.
- **Fabricated precision:** "2017-12-31" when the source says "2017".

## 3. What the Hazira study found

The study source was the PNGRB Enquiry Committee Report (15-Jan-2021, 36 pages, a text PDF whose printed page numbers equal its PDF page numbers). The pack under study was the 60-item workbook made with the prototype and re-exported from ProbeMatrix. Both are in this repository at [`docs/reference/hazira-2020/`](../reference/hazira-2020/README.md) (`PNGRB-Hazira-enquiry-report-2021-01-15.pdf`, `prototype-evidence-pack-hazira-2020.xlsx`). Row numbers below are 1-based data rows of that workbook. Every quoted anchor was checked against the PDF text. Each defect below is matched to the mechanism in this design that prevents it.

| # | Defect found | Evidence | Prevented by |
|---|---|---|---|
| D1 | **Invented quote.** `"instructed closure"` appears nowhere in the report. It came from the prototype's worked example, as did "the skid superstructure was not designed to contain a flange-failure release". | Row 51, row 21 | Hard gate: quote verification against segments (§14). Worked examples ship as *synthetic* fixtures only, never real-incident prose an agent can copy (§16). |
| D2 | **Paraphrase inside quote marks:** `"nearby fittings were intact"` (source: "The nearby fittings were found intact"); a silently corrected typo ("though" → "through"); a quote spanning pp.16–17 cited to one page. | Rows 4, 17, 3 | Verbatim check after whitespace/hyphenation normalisation only; `[sic]` convention; cross-page spans cite both pages (§8.2, §14). |
| D3 | **Wrong page citations** (off by 1–2) on 8+ rows. | Rows 4, 16, 23, 27, 30, 31, 43, 49 | Pages come from the segment the verified quote was found in, not from the author. The citation string is generated, not typed (§8.4). |
| D4 | **Unflagged contradiction.** The timeline says CCTV verification was at 02:18; other passages imply 02:20. The operator's Section 5 briefing and the witness statements disagree on who closed which valve. | Rows 4, 7, 8, 51 | Assertion register plus conflict detection; disputed items carry both versions (§10). |
| D5 | **Author opinion presented as evidence:** "near-eightfold expansion", "inevitability of regulatory scrutiny", "functioned as designed, the failure was upstream". | Rows 50, 58, 25 | The Description's third part must be grounded in a cited span or limited to plain operational significance. Lint for evaluative and speculative phrases (§9.4, §14). |
| D6 | **HFACS vocabulary leaking** into tags and prose: `supervision`, `latent-precondition`, `environmental-precondition`, "integrity-management precondition". | Rows 33, 27, 5, 36 | Controlled tag vocabulary plus HFACS-term lint (§14). |
| D7 | **Cross-references broken on import.** The prose says "row 15", "row 30", but ProbeMatrix regenerates Evidence IDs (EVD-2130…) and several row numbers were already wrong. `Related Evidence` is empty on all 60 rows. | 20+ rows | No IDs or row numbers in Description prose; refer to the fact itself. Machine-filled `Related Evidence` uses Evidence Tags, which survive import (§8.4). |
| D8 | **Fabricated date precision:** 2017-12-31, 2019-12-31, 2016-08-31, 2018-02-28, 2020-12-31. | Rows 36–39, 41, 42, 48, 56 | Dates stored with explicit precision. The pack shows `YYYY`, `YYYY-MM` or `YYYY-MM-DD` exactly as known (§8.4). |
| D9 | **Inconsistent type and method:** committee observations typed `log_record` with "SAP/DCS export"; photos split arbitrarily between `photograph` and `physical_item`. | Rows 1, 28, 29, 15–23 | Deterministic evidence-type decision rules (§9). |
| D10 | **No record of who asserts what.** Operator briefing, witness accounts and committee findings are merged. | Section 5 vs 7 vs 10–11 | `asserted_by` perspective on every claim, shown in the Description lead-in (§10.1). |
| D11 | **Online items unverifiable.** Press and regulator items have no saved copy and no quote anchor. Their claims (37 hours, Rs 1 crore, "pipeline rupture", "three blasts") can't be traced back. | Rows 18, 55–60 | Inputs-only rule. The optional web step saves dated snapshots into `inputs/web/` and treats them as normal inputs (§7.9). |
| D12 | **High-value findings silently dropped:** "No inspection carried out in schedule of April 2020" for the lamps (p.32, the ignition source); 7,935 notifications with 1,060 pending; 79 incidents vs near-miss reporting; no fire-pump capacity tests; 310DT1 not configured in DCS; thickness-spot selection procedure; emergency phone numbers on a hanging sheet. | p.26–32 | Coverage matrix: every extracted claim is either in an item or in the omission log with a reason. Coverage gate on observation-type sections (§11). |
| D13 | **The official answer leaking into evidence:** committee recommendations (A.1, B.1, B.5, D.1.i, D.2.ii) and root-cause numbers quoted in 10+ fact items. | Rows 14, 22, 32, 33, 35, 40, 45, 47, 49, 50 | Conclusions are held back in a private ledger and a lint blocks recommendation and verdict language (§11.3). |
| D14 | **Comma corruption on import.** The importer splits Linked Individuals, Linked Equipment, Tags and Regulatory Requirements **on commas**. 25 rows have labels containing commas (e.g. `HPMV FLP Lamp Posts (125 W, 9 in metering blast radius)`). Semicolon-joined lists become one entry. | 25 rows | Labels may not contain commas, the list separator is `, `, and a hard gate checks this (§8.4, §14). |
| D15 | **Redaction artefacts inside quotes:** `Mr. [CE]`, `[DGM-GSP]`, `[JEA]`. These are ad-hoc placeholders inconsistent with the role labels, and the honorific is left behind. | Rows 5, 6, 7, 24, 53 | Quote de-identification replaces the name *and* its honorific with the canonical role label in square brackets (§13.3). |
| D16 | **Descriptions up to 1,125 characters** against the prototype's own 650 limit. Inconsistent, though still under the analyser's 2,000-character prompt cap. | 30+ rows | Length policy: target 300–900, soft warning above 1,200, hard error above 1,800 (§9.4). |
| D17 | **A meta-item about the report itself** (committee composition, structure) treated as evidence. | Row 54 | Source descriptions live in pack metadata and `INDEX.md`, not as evidence items (§8.4). |
| D18 | **Mismatched IDs in the source itself:** photo captions read "Meter ID 310 FF1/FF2" while the text says 310FE1/FE2. | p.31–32 | Equipment roster with aliases and a source-inconsistency note (§13.4). |

What the prototype got right, and this design keeps: the three-part Description (observation → verbatim or numeric anchor → operational significance); report-plus-page citations in `Source` with section-level `Storage Location`; role labels instead of names; operational, non-HFACS tags; one item per distinct artefact or observation; research notes as an audit trail.

## 4. Decisions made with the owner

| Decision | Choice |
|---|---|
| Conversion of heavy inputs | **Local open-source tools only**, detected at runtime, with a `doctor` command. No cloud services. |
| Incremental output | **Master + deltas.** The first run writes the master pack. Each later run writes a **new delta workbook containing only new items**, imported separately into the existing ProbeMatrix incident. The master is never rewritten. All files sit together in `outputs/`. |
| Personal names | **Always de-identified. No opt-out.** |
| Web sources | **Inputs only.** An optional, explicitly invoked step fetches public pages and saves dated snapshots into `inputs/web/`. They are then processed like any input. |
| Hosts | **Claude Code + Cowork + Codex** at launch. |
| Source conclusions, lessons, recommendations | **Never evidence.** No conclusion, lesson or recommendation from any source document is considered a piece of evidence. Screened out before entering the evidence bank (four-layer enforcement, §11.3), held in a private ledger for later comparison only. No opt-out. |
| Repository | Standalone open-source repo `probematrix-evidence-pack-builder`, unrelated to any other plugin. |
| Freeze point | A workbook is a **draft** that later runs may overwrite until the owner marks it imported (tick in `INDEX.md` or `epb mark-imported <file>`). From then on its items are locked, and fixes go out as correction items. |
| Internal prototype | ProbeMatrix's `tools/evidence-pack-builder/` and its CLAUDE.md rule **stay as they are, indefinitely**. The plugin is built clean-room: it may reuse ideas and the file-format spec, but no prototype code and no real-incident prose. |

## 5. Repository layout

```
probematrix-evidence-pack-builder/
├── .claude-plugin/
│   ├── plugin.json                 # Claude Code / Cowork plugin manifest ("skills": "./skills")
│   └── marketplace.json            # own marketplace entry (name: see §18)
├── .agents/skills -> ../skills     # Codex discovery (symlink; install script copies on Windows)
├── AGENTS.md                       # host-neutral agent instructions (Codex reads this)
├── CLAUDE.md                       # one line: "See @AGENTS.md"
├── README.md  LICENSE (MIT)  CHANGELOG.md  CONTRIBUTING.md  SECURITY.md
├── requirements.txt                # core: openpyxl, pyyaml, rapidfuzz, pdfplumber, pypdf, python-docx,
│                                   #       python-pptx, beautifulsoup4, markdownify, Pillow
├── requirements-email.txt          # optional: extract-msg (GPL) for Outlook .msg
├── requirements-media.txt          # optional: faster-whisper, opencv-python-headless (scene detection)
├── requirements-docs.txt           # optional: docling (layout/table-aware PDF/DOCX → Markdown)
├── requirements-dev.txt            # pytest, ruff, + all optional
├── skills/
│   ├── evidence-pack/              # START HERE: router, workspace setup, run loop
│   │   ├── SKILL.md
│   │   ├── scripts/epb.py          # the single CLI (thin entry; package in scripts/epb/)
│   │   ├── scripts/epb/            # python package: workspace, convert/, segments, ledger, deid,
│   │   │                           #   conflicts, coverage, verify, build, index, formats/
│   │   └── references/
│   │       ├── workspace-contract.md
│   │       ├── evidence-pack-v2.md          # importer-exact format spec (§8.5)
│   │       ├── evidence-types.md            # decision rules (§9)
│   │       ├── description-quality.md       # the bar + synthetic good/bad pairs
│   │       ├── deidentification.md
│   │       ├── assertions-and-conflicts.md
│   │       ├── conclusions-policy.md
│   │       ├── tag-vocabulary.md
│   │       └── citation-style.md
│   ├── evidence-intake/            # scan + convert + segment (large docs, scans, media)
│   ├── evidence-extraction/        # segments → claim ledger (chunked, parallel-safe)
│   ├── evidence-reconcile/         # rosters, de-identification, assertions, conflicts
│   ├── evidence-authoring/         # claims → items (descriptions, types, tags, priority)
│   ├── evidence-verify-build/      # gates, coverage, master/delta workbook, INDEX.md
│   └── evidence-web-snapshot/      # OPTIONAL: fetch + snapshot public sources into inputs/web/
├── schemas/                        # JSON Schemas: source, segment, claim, item, conflict, state
├── tests/                          # pytest; synthetic fixtures generated at test time
│   └── fixtures/synthetic-incident/ # fictional incident: text PDF, scanned PDF, docx, eml, csv,
│                                    #   wav, mp4, jpg; all invented, no real people
├── evals/                          # agent-level evals (§16)
├── samples/                        # published, de-identified sample runs on PUBLIC reports only
│   └── <slug>/{README.md, INDEX.md, outputs/}
├── tools/
│   ├── install-codex.sh
│   └── make-sample.py
└── docs/
    ├── design/                     # this document
    ├── reference/hazira-2020/      # study material: official report + prototype pack (§3)
    ├── INSTALL.md
    └── USER-GUIDE.md
```

Each `SKILL.md` stays under ~150 lines. Shared material goes in `skills/evidence-pack/references/`, and the other skills link there. Sub-skills can be invoked directly by name, but `evidence-pack` is the normal entry point and calls them in order.

## 6. The workspace contract

The plugin works **in the folder where it is invoked** (the "case folder"). On first run, `epb init` creates the structure:

```
<case-folder>/
├── inputs/                  # USER-OWNED. Drop anything here, any depth, any type.
│   └── web/                 # created only by the optional web-snapshot step
├── outputs/                 # ONLY evidence-pack workbooks
│   ├── evidence-pack-<case>-master.xlsx
│   ├── evidence-pack-<case>-delta-002.xlsx
│   └── evidence-pack-<case>-delta-003.xlsx
├── INDEX.md                 # human-readable status snapshot (regenerated every run)
└── .epb/                    # plugin working state (hidden; never hand-edited)
    ├── case.yaml            # case slug, title, ID prefix, timezone, created, plugin version
    ├── state.json           # input fingerprints, versions, item→version map, counters
    ├── sources/<src-id>.json            # per-input registry record (§7.1)
    ├── segments/<src-id>/NNNN.md        # page/time-anchored Markdown (§7.3)
    ├── segments/<src-id>/index.json
    ├── media/<src-id>/                  # extracted keyframes, audio wav, page images for OCR
    ├── ledger/claims.jsonl              # every extracted claim (§8.2)
    ├── ledger/conclusions.jsonl         # held-back conclusions & recommendations (§11.3)
    ├── rosters/roles.yaml               # role labels + aliases (NO names)
    ├── rosters/equipment.yaml           # equipment labels + aliases
    ├── conflicts.yaml                   # conflict register (§10)
    ├── items/<item-id>.yaml             # authored evidence items (§8.3)
    ├── coverage.json                    # claim → item | omission(reason)
    ├── runs/<NNN>/run.json              # per-run log: inputs processed, items added, gates
    ├── runs/<NNN>/report.md             # gate + quality report for the run
    └── private/                         # NEVER shared, NEVER committed, NEVER copied
        ├── name-map.yaml                # real name → role label (the only place names live)
        └── .gitignore                   # "*"
```

Rules:
- `inputs/` is read-only to the plugin, except that `evidence-web-snapshot` may write into `inputs/web/`. Inputs are never moved, renamed or modified.
- `outputs/` contains only `.xlsx` packs. Reports, logs and notes go in `.epb/runs/`.
- `.epb/` also gets a `.gitignore` covering `private/` and `media/` (large binaries). If the case folder is a git repo, `epb init` warns when `.epb/private/` isn't ignored.
- Segments and claims hold **raw source text, including names**, because quote verification needs the original. They are working files, treated as confidential, never published, and never copied into `samples/`. Only `items/`, `outputs/` and `INDEX.md` are de-identified artefacts. (This keeps verification exact while honouring "never in outputs".) See §13.5 for the guard that stops raw text escaping.

### 6.1 `INDEX.md` (regenerated each run, never hand-edited)

Sections, in order:
1. **Case header:** case title, slug, ID prefix, plugin version, last run timestamp, current pack version.
2. **What to import where:** a table of every workbook in `outputs/` with version, date, item count, Evidence ID range, and the instruction ("Import the master into a new incident; import each delta, in order, into the same incident. Never re-import a file already imported."). It includes a status (`draft` or `imported <date>`) and an "Imported?" checkbox the user can tick. Ticking locks the workbook (§12.1 step 5a). The plugin reads ticks back from the previous `INDEX.md` before regenerating it and records them in `state.json`, which is authoritative from then on.
3. **Inputs snapshot:** one row per input with relative path, type, size, SHA-256 (short), first-seen run, last-processed run, status (`processed`, `partial`, `unprocessed: <reason>`, `superseded by …`, `removed from folder`), segments, claims, items.
4. **Outputs snapshot:** per workbook, the inputs that contributed items.
5. **Open issues:** unresolved conflicts, low-confidence OCR/transcription segments awaiting review, unprocessed inputs, omissions marked "needs owner decision", pending corrections (§12.4).
6. **Run history:** one line per run: date, new or changed inputs, items added, gates passed.

No personal names appear in `INDEX.md`. Input *file names* that contain a person's name are shown with the name replaced by its role label (the real path is kept in `.epb/sources/`).

## 7. Pipeline

Each stage is a CLI command (deterministic) plus agent judgement where noted. Every stage is **idempotent** and **incremental**: it works only on sources whose fingerprint is new or changed, or on claims and items not yet processed.

```
init → doctor → scan → convert → segment → extract → reconcile → author → verify → build → index
                                     ↑ optional: web-snapshot (writes inputs/web/, then rejoins at scan)
```

### 7.1 `scan`: inventory and fingerprint
- Walk `inputs/` recursively. Ignore OS junk (`.DS_Store`, `Thumbs.db`, `~$*` lock files) and list it as ignored.
- For each file: SHA-256, size, MIME (python-magic or extension fallback), modified time.
- Assign a stable `src-id` (`S001`…) on first sight. The key is the content hash. A file whose **path is known but content changed** is a *new version* of the same logical source (`S004v2`). A file with a **known hash at a new path** is a rename, not new evidence. Identical content at two paths is recorded as one source with two paths.
- Missing files (previously seen, now absent) are marked `removed from folder`. Their items stay in the packs (they may already be imported). This is reported, not acted on.
- Archives (`.zip`, `.7z` if available) are expanded into `.epb/media/<src-id>/unpacked/` and each member registered as a child source.
- Email (`.eml`, `.msg`): the body is one source, and each attachment is registered as a child source with `parent` set.

### 7.2 `convert`: per-modality conversion (local tools, optional, auto-detected)

| Input | Primary tool | Fallback | Output |
|---|---|---|---|
| Text PDF | `pdfplumber` (text + words with positions, per page; tables) | `pypdf` | per-page text + tables |
| Complex/layout PDF (multi-column, heavy tables) | `docling` if installed | pdfplumber | per-page Markdown with tables |
| Scanned / image-only PDF pages (detected per page: no text layer or < N chars/page) | `ocrmypdf` + Tesseract (language packs from `case.yaml`) | Tesseract on rendered page images (`pdftoppm`) | per-page text + **OCR confidence** |
| Mixed PDF | per-page decision | | |
| DOCX / ODT / RTF | `python-docx` (paragraphs, tables, headers, comments, tracked changes flagged) | `pandoc` if present; LibreOffice headless → PDF | Markdown with paragraph numbers |
| PPTX | `python-pptx` (slide text + notes) | LibreOffice → PDF | per-slide Markdown |
| XLSX / CSV (DCS, SAP, CMMS, logs) | `openpyxl` / csv: per sheet, header detection, typed cells | | per-sheet Markdown table chunks with row ranges; very large tables summarised by schema + row-range segments |
| Email | stdlib `email` / `extract-msg` | | header block (from/to roles, date, subject) + body |
| HTML / web snapshot | `beautifulsoup4` + `markdownify` (readability-style main-content extraction) | | Markdown with retrieval metadata |
| TXT / MD / chat exports (WhatsApp, Teams text) | native | | line-numbered Markdown, message timestamps preserved |
| Images (JPG/PNG/HEIC/TIFF) | Pillow (EXIF: capture time, device; **GPS stripped from anything shareable**); Tesseract if text-heavy | | an image record; the *agent* describes the image (§7.5) |
| Audio (wav/mp3/m4a/ogg) | `ffmpeg` → 16 kHz mono wav → `faster-whisper` (model size from config; word timestamps; language auto or set) | none: marked `unprocessed: transcription unavailable` | time-anchored transcript segments with per-segment confidence |
| Video (mp4/mov/avi/mkv) | `ffmpeg` audio track → as audio; `ffmpeg` scene-change keyframes (`select='gt(scene,0.3)'`) plus a floor of 1 frame / N s, with burned-in timestamps read by OCR where present (CCTV overlays) | | transcript segments + keyframe set with media timestamps |
| Unknown | none | | `unprocessed: unsupported type`, listed in INDEX |

`epb doctor` reports, for each tool, whether it was found, its version, and which input types it enables. It prints install commands per OS. A missing optional tool never fails a run: affected inputs are marked `unprocessed: <tool> missing` and appear in INDEX "Open issues".

Speaker diarisation (who-spoke-when) is **optional** (`pyannote.audio` needs a model licence acceptance). Without it, transcripts are single-stream and the agent attributes speakers only from in-audio self-identification or a sidecar note.

**Sidecar notes:** the user may place `<file>.note.md` or `<file>.note.yaml` next to any input to give context the file can't (who recorded it, when, chain of custody, speaker roles, which camera). Sidecars are inputs too: they're hashed and cited when used.

### 7.3 `segment`: anchored Markdown

Every converted source becomes an ordered list of **segments**, the unit everything else cites.

- **Documents:** one segment per page (PDF) or per ~1,500-token run of paragraphs (DOCX, with paragraph numbers). Each segment records: `seg-id` (`S001-p017`), printed page label *and* physical page index (they differ in many reports; both are stored and the citation uses the printed label when detectable via header/footer patterns such as "Page N of M"), section heading path (built from heading detection: numbered headings such as "10. Observations", "A) Facilities"), text, tables, figure captions, OCR confidence.
- **Media:** one segment per ~30–60 s of transcript or per keyframe, with `start`/`end` timestamps and the file's real-world start time if known (CCTV overlay OCR, EXIF, sidecar).
- **Spreadsheets:** one segment per sheet × row range.
- **Hyphenation and line-wrap normalisation** is stored as a parallel `norm_text`, keeping a character map back to the raw text, so a quote can be verified across line breaks and *across page boundaries* (a cross-page quote cites both pages: "pp.16–17").
- **Section map:** `segments/<src-id>/index.json` holds the heading tree with page ranges. This becomes the `Storage Location` value ("Section 7: Eyewitness Statements") and drives chunk planning.
- **Repeated boilerplate** (running headers, footers, page numbers, letterheads) is detected across pages and excluded from extraction, but kept in raw text.

### 7.4 `extract`: segments → claim ledger (agent, chunked)

This is where large documents stop being a problem. `epb plan-extract` builds a **chunk plan**: groups of consecutive segments under one section, bounded at about 6–8k tokens, with one segment of overlap. Each chunk becomes an extraction task. The agent (or parallel subagents where the host supports them; sequentially on Codex) processes one chunk at a time and appends claims with `epb claims add --chunk <id> claims.json`.

A **claim** is one atomic, source-stated fact (or, in the separate held-back ledger, one conclusion, lesson or recommendation, which is never evidence) with:
- `claim_id`, `chunk_id`, `src_id`, `seg_ids`
- `kind`: `observation` | `statement` (what a person said they saw or did) | `record` (what a log, document or system shows) | `measurement` | `event` (timestamped) | `condition` | `document_fact` (a procedure exists, says X) | `context` (background, asset description). Held-back kinds, never evidence and written only to `conclusions.jsonl` (§11.3): `conclusion` | `lesson` | `recommendation`.
- `asserted_by`: the perspective (§10.1)
- `anchor_quotes`: one or more verbatim spans (verified at `claims add`; rejected if not found)
- `values`: structured numbers, times, dates (with precision), identifiers, counts
- `entities`: people (as raw mentions, de-identified later), equipment, locations, organisations
- `underlying_artefact`: what the evidence physically *is* (CCTV frame, SAP notification, witness statement, photograph, calibration record), the input to type assignment (§9)
- `event_time` (with precision) and `artefact_date` (with precision)

Extraction instructions emphasise reading **every** segment of a chunk, including tables, captions and footnotes. They push for completeness: in observation, finding and annex sections, every distinct numbered observation yields at least one claim. Claims are cheap and curation comes later.

`epb extract-status` shows chunks done and pending, so a run interrupted mid-report resumes exactly where it stopped.

### 7.5 Images and keyframes
The agent views each image or keyframe and writes a **visual observation** claim describing only what is visible: objects, damage, positions, readable text, timestamps. It never identifies people, describes faces or guesses intent. If the image came with a caption or report text, the claim links both. The verbatim anchor for an image claim is the caption or overlay text if any. Otherwise the anchor is the media reference itself (`IMG_0423.jpg`, `cam3.mp4@00:12:40`) and the claim is flagged `anchor: visual`. These claims can't be quote-verified, so they're reviewed in the run report (§14).

### 7.6 `reconcile`: rosters, de-identification, assertions, conflicts (CLI + agent)
1. **Role roster:** every person mention across new claims is mapped to a role label (§13). New people get labels, and known aliases ("Mr. Shaikh", "CE (P)", "the Chief Engineer") resolve to the existing label.
2. **Equipment roster:** labels plus aliases (310FE1 = 310FT01 = "meter no.1" = "Meter ID 310 FF1" [caption]). Mismatches inside a source are noted.
3. **Event alignment:** `event` claims are clustered by referent (same event, e.g. "MOV 54 closure") using roster entities and times.
4. **Conflict detection** (§10).

### 7.7 `author`: claims → evidence items (agent + CLI)
`epb author-plan` proposes item groupings: claims sharing an underlying artefact and perspective (e.g. all claims from one witness statement; one CCTV frame; one SAP notification and its history). The agent decides final grouping and writes each item YAML (§8.3) through `epb items add`, which validates it immediately. Items reference claims. They don't restate anchors by hand.

### 7.8 `verify` → `build` → `index`
See §14 (gates), §8.4–8.5 (workbook), §6.1 (INDEX).

### 7.9 Optional `web-snapshot`
Invoked only when the user asks (e.g. "find public coverage of this incident"). The agent searches the web, proposes candidate URLs, and **the user confirms which to keep**. For each kept URL, `epb snapshot <url>` saves to `inputs/web/<YYYY-MM-DD>-<domain>-<slug>/`: raw HTML, a PDF print if a headless browser is available, extracted Markdown, and `meta.yaml` (URL, retrieved-at, HTTP status, title, author/byline *de-identified*, publication date if stated). From then on it's an ordinary input. PDFs found online (e.g. a regulator's report) are downloaded as-is. Paywalled or failed fetches are recorded and never paraphrased from memory. **The agent must never add a web claim it didn't read in a saved snapshot.**

## 8. Data model

### 8.1 Source record (`.epb/sources/S001.json`)
`src_id, version, paths[], sha256, size, mime, first_seen_run, last_processed_run, parent (for attachments/archive members), modality, converter{tool, version, options}, pages|duration, ocr{pages, mean_conf, low_conf_pages[]}, transcript{model, language, mean_conf}, source_kind (official_report | witness_statement | interview_recording | cctv | photo | system_export | procedure | permit | email | press | regulator_notice | operator_statement | sidecar | other), title, author_body (de-identified), date (with precision), citation_short ("PNGRB Enquiry Committee Report, 15-Jan-2021"), status`.

`source_kind` and `citation_short` are proposed by the agent from the first segments and confirmed in the run report.

### 8.2 Claim (`ledger/claims.jsonl`)
As listed in §7.4. Quote anchors store `{seg_ids, char_start, char_end, text}`. They're verified when added and re-verified at build.

**Quote conventions** (enforced):
- Verbatim after normalising only: whitespace, line-break hyphenation, Unicode quote/dash variants, ligatures.
- Omissions inside a quote use `…`. Each fragment between ellipses must verify, in order, within the cited segments.
- Editorial insertions only in `[square brackets]`, used for de-identification (§13.3) or a minimal clarifier. `[sic]` marks a source error kept verbatim. **Typos are never silently corrected.**
- Descriptions use typographic quotes `“ ”` for quotations, so inch marks (`6"`, `36"`) never collide with quote delimiters. The prototype's 21 unverifiable quotes included 9 that were only inch-mark collisions.

### 8.3 Evidence item (`.epb/items/EVD-<PFX>-NNN.yaml`)
```yaml
id: EVD-HAZ-031            # stable forever; also the Evidence ID column
tag: TAG-HAZ-00000031      # stable; Evidence Tag column; survives ProbeMatrix import
version_added: 1           # 1 = master, 2.. = delta number
type: log_record           # ProbeMatrix enum, from §9 rules
type_rationale: "SAP notification record (underlying artefact), reported via enquiry report"
priority: critical
priority_rationale: "Direct antecedent of loss of containment; 7 days before incident"
asserted_by: investigating_body
claims: [C0412, C0413, C0419]
description: >-
  …three-part text, generated by the agent from the claims, quotes in “ ”…
quotes:                    # every quotation in description must appear here (machine-checked)
  - claim: C0412
    text: "Notification no. 3800419840 was raised on 17/09/2020 for malfunction of meter no.1"
tags: [maintenance-trigger, notification-closure, metering]
linked_roles: []
linked_equipment: [EQ-METER-1]       # roster keys; rendered as labels
related: [EVD-HAZ-032, EVD-HAZ-035]  # rendered as Evidence Tags in Related Evidence
event_time: {value: "2020-09-17", precision: day}
artefact_date: {value: "2020-09-17", precision: day}
status: verified | disputed | visual_unverified | low_confidence_source
conflicts: []                        # conflict ids (§10)
supersedes: null                     # for correction items (§12.4)
```

### 8.4 Column mapping to `EVIDENCE_PACK_V2` (importer-exact)

The importer was read directly (ProbeMatrix `server/services/evidenceExportService.ts`, main branch, checked 2026-10-17). It imports into the incident named in the upload URL and **appends** rows: there is no duplicate check, so a delta workbook adds to an existing incident and re-importing duplicates. It keeps `Evidence Tag` values, suffixing duplicates `-IMP1`, `-IMP2`. It stores `Related Evidence` as plain strings without resolving them, so tag references across master and deltas are for human navigation only, never for the analyser. The exact header strings, sheet names, metadata rows and column widths are a file format, and the builder transcribes them into `formats/probematrix_v2.py` and `references/evidence-pack-v2.md`. No ProbeMatrix code is copied. It splits **Tags, Linked Individuals, Linked Equipment, Related Evidence and Regulatory Requirements on commas**. It maps `Collection Conditions`→collection_location, `Preservation Method`→environmental_requirements and `QA Status`→lifecycle_status (enum: collected, preserved, under_review, verified, disputed, released, destroyed, sealed). It casts `Retention Category` to an enum (regulatory, legal, internal, permanent). It **drops** `Access Restrictions`, `QA Reviewed By/At` and `Verification Notes`. `Integrity Verified = Yes` stamps the import time. The analyser prompt sees only `[Evidence ID] (Type, Priority)`, Description (cut at 2,000 characters), Tags, Linked Individuals and Linked Equipment.

| Column | Filled from | Rule |
|---|---|---|
| Evidence ID | item.id | `EVD-<PFX>-<NNN>`, stable across versions inside the workspace; numbering continues in deltas. **Discarded by ProbeMatrix on import** (it assigns a fresh `EVD-NNNN`), so it is a workspace and human-navigation key only |
| Type | item.type | §9 |
| Description | item.description | §9.4. No IDs or row numbers in prose |
| Priority | item.priority | rubric §9.3 |
| Analysis Status | constant | `pending` |
| Tags | item.tags | controlled vocabulary; lowercase-hyphenated; no commas inside a tag; joined `, ` |
| Linked Individuals | roster labels | **comma-free labels** (gate); joined `, ` |
| Linked Equipment | roster labels | **comma-free labels** (gate); joined `, `. Descriptive detail ("1986 vintage, 6 inch") goes in the Description, not the label |
| Source | generated | `<citation_short>, p.<n>[–<m>][; p.<k>]` for paged sources; `<citation_short>, <hh:mm:ss>–<hh:mm:ss>` for media; `<citation_short>, sheet <name> rows <a>–<b>` for tables; plus `[web snapshot <retrieved-date>] <url>` for web inputs. Page numbers come from the verified anchor segments, never typed |
| Collection Date | item.artefact_date | rendered to its precision: `YYYY`, `YYYY-MM` or `YYYY-MM-DD`. Blank if unknown. **Never padded** |
| Collection Method | §9 table | from controlled list |
| Collector | source.author_body | de-identified body or role, e.g. "PNGRB Enquiry Committee"; for user-collected evidence the investigating team role |
| Storage Location | segment section path + input reference | e.g. "Section 10 (Observations: Maintenance), inputs/Hazira_enquiry15012021.pdf". Name-bearing file names use role-label substitution |
| Evidence Tag | item.tag | `TAG-<PFX>-<8 digits>` |
| Hash/Checksum | source sha256 | `sha256:<hex>` of the input file (or `;`-joined if multiple sources). Real integrity value |
| Related Evidence | item.related | rendered as **Evidence Tags** (they survive import; Evidence IDs don't); joined `, ` |
| Chain of Custody (JSON) | generated | one entry per contributing input: `{timestamp: ingest time, transferred_from: "<source kind / provider>", transferred_to: "evidence-pack-builder workspace", received_by: "<investigating team role>", action_type: "duplication", condition_on_receipt: "intact", location: "<inputs relative path, de-identified>", notes: "sha256 <short>; converted by <tool> <ver>"}` plus user-supplied custody from sidecars. Valid JSON array; `[]` only if truly none |
| Integrity Verified | constant | `No` (the tool verified quotes, not physical integrity) |
| Collection Conditions | sidecar / source | real collection location or conditions if stated; else blank |
| Preservation Method | blank | unless supplied by sidecar |
| Access Restrictions | blank | dropped by importer |
| Regulatory Requirements | claims | statute or regulation explicitly cited by the source; **comma-free** entries |
| Retention Category | blank | unless the user sets a case default from the enum |
| Retention Until | blank | |
| QA Status | item.status | `verified` (all quotes verified) or `disputed` (open conflict); else blank. Uses the importer enum so it lands in lifecycle_status |
| QA Reviewed By / At / Verification Notes | blank | dropped by importer; verification detail lives in `.epb/runs/` |
| Created At / Updated At | build time | ISO 8601 |

**Pack Metadata** sheet, exact 10-row layout: `Incident Number` = case number from `case.yaml` (user-supplied, or `INC-<PFX>-<year>`), `Incident Title` = case title, `Total Evidence Items` = items *in this file*, `Total Attachments` = 0. Rows 7–9 carry the importer's standard notes. **Additional informational rows are not added** (the importer reads by position). Version and source information goes in the file name and `INDEX.md`.

**No meta-items:** the source documents themselves are never evidence items (D17).

**Importer re-check (2026-10-17).** A second, line-by-line read of the importer (`server/services/evidenceExportService.ts`, the import route in `server/routes.ts`, `shared/schema.ts`, and the analyser prompt in `server/services/analysis.ts`) corrects and extends the paragraph above. Where they disagree, this block wins. The builder's validator is **stricter** than the importer wherever the importer is lax.
1. **Evidence ID is required as a header but its value is never read.** The import route assigns a new random `EVD-NNNN` to every row (routes.ts l.67–70, 718–720), and the analyser shows that new ID. Only `Evidence Tag` survives.
2. **Collision handling lives in the route, not the service.** Nothing is deduplicated by content. A tag colliding with the incident's existing tags or another row in the file gets `-IMP1`, `-IMP2`… with a warning (routes.ts l.656–712). Re-importing a file therefore duplicates every item, and the duplicates' `Related Evidence` still points at the *original* tags. This is another reason a workbook is never re-imported (§12).
3. **Enums are not validated by the importer.** `QA Status` and `Retention Category` are stored as raw strings with no lowercasing (l.382–401). The builder must emit the exact lowercase enum values, and the validator rejects anything else.
4. **Type, Priority and Analysis Status are normalised, not rejected.** Type is lowercased with spaces turned into `_`, and the other two are lowercased. Unknown values silently become `other`, `medium` or `pending` with a warning (l.325–345). The validator treats any non-exact value as a hard error.
5. **Whole-file rejection** happens if the `Pack Metadata` sheet is missing or empty, the marker in row 1 column B is not `EVIDENCE_PACK_V2` (`V1` is accepted with a warning), the `Evidence Pack` sheet is missing, any required header is missing (l.259–307), or **any row has a blank Description** (l.330–333, 427; route l.648–653).
6. **Rows with a blank Type are skipped silently** (l.320). The validator rejects them.
7. **Headers are matched by name, not position** (l.309–312). Only metadata row 1 column B is read (l.267). The builder still writes the exact header order, widths and 10-row metadata layout, so a pack stays byte-comparable with ProbeMatrix's own exports.
8. **Every cell is read through `String(...)`.** Dates, hashes, IDs and anything numeric-looking must be written as **text cells**, or a date imports as an Excel serial number.
9. **Created At and Updated At are not read** (the database default is used). They are still written for human reference. **Retention Until maps to `disposal_date`** (l.383, 400).
10. **Malformed Chain of Custody JSON only raises a warning**, and its shape is not checked (l.367–375). The validator checks it against `ChainOfCustodyEntry` (`timestamp`, `transferred_from`, `transferred_to` and `received_by` required).
11. **The analyser line is `[ID] (type, Priority: p)`**, and a Description cut at 2,000 characters ends with `…` (analysis.ts l.65, 254–261). The 1,800-character hard limit stands.
12. **Allowed values:** Type is `witness_statement, photograph, document, log_record, recording, physical_item, lab_report, other`. Priority is `critical, high, medium, low`. Analysis Status is `analyzed, pending, requires_followup`.
13. **The `Attachments Manifest` sheet** is written by the exporter and ignored by the importer. The builder writes it with headers only, matching `Total Attachments = 0`.

Line numbers are as of the 2026-10-17 check. `references/evidence-pack-v2.md` records the check date and is re-verified against the importer whenever the format module changes.

### 8.5 Format module
`scripts/epb/formats/probematrix_v2.py` owns headers, column widths (copied from the exporter), enums, list separators and the 10-row metadata layout. The validator mirrors the importer's checks exactly. `references/evidence-pack-v2.md` documents it with the date it was last checked against the importer. A `formats/` seam allows a future V3 without touching the pipeline.

## 9. Evidence-type identification, priority, descriptions

### 9.1 Type: classify the underlying artefact, not the carrier

The question is always *"what is the original thing this evidence is?"* A report that summarises a SAP record yields a `log_record`. A report that quotes a witness yields a `witness_statement`.

| Underlying artefact | `Type` | `Collection Method` |
|---|---|---|
| Account given by a person (statement, interview record, transcript, report section summarising eyewitness accounts, user-supplied interview audio) | `witness_statement` | `Witness interview` (or `Document review` if only known via a report) |
| CCTV / video frame or clip, audio recording, radio/phone recording | `recording` | `CCTV review` / `Recording review` |
| Still photograph (site, damage, equipment), whether original image or a photo reproduced in a report | `photograph` | `Field inspection` / `Document review` |
| The physical object or its inspected condition (failed gasket, damaged meter, lamp with missing bolts) described as an inspection finding, with no specific photo as the artefact | `physical_item` | `Field inspection` |
| System-generated time-series or transactional record: DCS/SCADA alarms and trends, SAP/CMMS notifications and work orders, permit-system records, logbooks, access logs, fire-water readings | `log_record` | `System export` (if the export is in inputs) or `Document review` (if known via a report) |
| Laboratory, metallurgical, gas-analysis, calibration-certificate result | `lab_report` | `Laboratory analysis` / `Document review` |
| Written documents: procedures, SOPs, drawings, P&IDs, audit reports, training records, organisation charts, MOC records, emergency plans, contracts, regulator notices, press articles | `document` | `Document review` / `Public source` |
| An investigating body's observation that something is *absent or deficient across records* (e.g. "no MOCs since 2018", "drill records lack actions") | `document` | `Document review` |
| Anything else | `other` | `Other`, with a rationale required |

Tie-breakers: (1) a committee observation *about* records is `document` unless a specific record (ID, date, value) is the artefact; (2) photo vs physical: if the item's anchor is a specific photo (caption, figure letter, file), it's `photograph`, otherwise `physical_item`; (3) a calibration record with values is `lab_report` only if it's a test result, and a calibration *change history* is `log_record`. Every item stores `type_rationale`, and the verify step lints for the D9 patterns (e.g. `log_record` with no record identifier, date or value in its claims → warning).

`Collection Method` controlled list: `Witness interview`, `CCTV review`, `Recording review`, `Field inspection`, `System export`, `Laboratory analysis`, `Document review`, `Public source`, `Other`.

### 9.2 Tags (controlled, operational, non-HFACS)
`references/tag-vocabulary.md` ships a starter vocabulary grouped by facet: artefact (`witness`, `cctv`, `photo`, `sap`, `dcs`, `permit`, `procedure`, `drawing`, `audit`, `training-record`, `press`, `regulator`), phase (`pre-incident`, `detection`, `escalation`, `isolation`, `ignition`, `response`, `recovery`), topic (`maintenance`, `calibration`, `materials`, `inspection`, `moc`, `alarm-management`, `emergency-plan`, `communication`, `competence`, `time-sync`, `records`, …). Agents may add case-specific tags in `case.yaml` (`tags_extra`), which are linted against a **blocked list** of HFACS vocabulary (`hfacs`, `l1`–`l4`, `unsafe-act`, `precondition`, `supervision`, `supervisory`, `organisational-influence`, `violation`, `skill-based`, `decision-error`, `perceptual-error`, `latent`, `active-failure` …). 2–5 tags per item.

### 9.3 Priority rubric
- **critical:** the item directly evidences the loss event, its immediate cause, the failure of a primary barrier, or a decisive timeline anchor (onset, detection, isolation, ignition).
- **high:** it evidences a condition, practice or system weakness that plausibly contributed, or corroborates a critical item from an independent perspective.
- **medium:** context that shapes interpretation (asset description, response steps that worked, downstream impact).
- **low:** peripheral corroboration.
Each item stores `priority_rationale`. Verify warns if more than 45% of items are `critical` (the Hazira pack had 42%).

### 9.4 Description standard
Three parts, in order, 3–6 sentences:
1. **Lead-in with artefact and perspective:** what the evidence is and who asserts it ("Witness statement of `<role>` as recorded by the enquiry committee: …", "Per the operator's briefing to the committee: …", "SAP Notification 3800419840 (17 Sep 2020), as reported by the committee: …").
2. **Anchor:** at least one verbatim quotation in `“ ”` from the item's claims, and/or the specific values (times, measurements, counts, identifiers, dates).
3. **Operational significance:** in plain HSE-manager language. Every *factual* assertion here must be supported by the item's claims (another claim from the same or a related item counts). Inferences are limited to arithmetic on cited values (e.g. "46 minutes after first detection") and plain statements of what the fact means for a control ("the notification was not closed after the job, so no closure check occurred"). **No** speculation, counterfactuals ("had cooling demand been higher…"), evaluative adjectives without a number, forecasts, or opinions about consequences the source doesn't state.

Prohibited in Descriptions: Evidence IDs, row numbers, "see row", HFACS terms (blocked list), source recommendations and verdicts (§11.3), personal names and honorifics, unverified quotations.
Length: target 300–900 characters. Soft warning below 250 or above 1,200. Hard error above 1,800 (keeps a margin under the analyser's 2,000-character cut).
Date and time formats in prose: `24 Sep 2020`, `02:15`, `03:08:15`. Durations computed by the CLI on request (`epb calc`) to avoid arithmetic slips.

## 10. Assertions and conflicts

### 10.1 Perspective (`asserted_by`)
`witness` (first-hand account), `operator` (the organisation's own account or briefing), `investigating_body` (enquiry/committee/investigator's own observation), `regulator`, `record_system` (a log or record speaks for itself), `expert_lab`, `press`, `third_party` (downstream companies, mutual aid), `user_note` (sidecar). Shown in the Description lead-in so the analyser can weigh it.

### 10.2 Detection
`epb conflicts detect` compares claims that share an aligned event or entity attribute:
- **Time conflicts:** the same event with timestamps differing by more than the tolerance (default 60 s, configurable; 0 for CCTV-frame-precision claims).
- **Value conflicts:** the same measurement or identifier with different values (dates 18/09/2019 vs 18/09/2020; meter IDs FE1 vs FF1).
- **Actor/action conflicts:** the same action attributed to different roles (who closed MOV 54 / the block valve), detected from the event cluster's role entities.
- **Sequence conflicts:** ordering contradictions.
- **Outcome conflicts:** "minor environment damage" vs a regulator's compensation order (flagged as a *framing difference*, not a factual conflict).
The CLI proposes candidates. The agent confirms or dismisses each with a reason (`epb conflicts resolve`), and **may not pick a winner**. Dismissals are for false positives only (e.g. the same time in two formats).

### 10.3 Representation
- Each confirmed conflict gets a register entry: `CF-001: {attribute, versions: [{value, claim, asserted_by, citation}], kind, note}`.
- Every item touching a conflicted attribute gets `status: disputed` (→ `QA Status = disputed`), states both versions with their citations in the Description ("The committee's timeline records 02:18; the CCTV caption sequence implies 02:20 (p.13 vs p.13–14).") and is linked by `Related Evidence`.
- Unresolved conflicts are listed in INDEX "Open issues" and in the run report.

## 11. Curation and coverage

### 11.1 Coverage matrix
Every claim ends in exactly one state: `in_item`, `merged_into:<claim>`, or `omitted:<reason>` with reasons from a fixed list: `duplicate`, `out_of_scope` (e.g. production statistics), `context_only` (kept for the Description of another item), `held_back_conclusion` (§11.3), `not_de_identifiable`, `low_confidence_source`, `needs_owner_decision`. `epb coverage` reports totals per section and per source.

### 11.2 Coverage gate
For segments the agent tagged as **observation/finding sections** (e.g. "Observations/Findings of the Committee", "Site inspection", "Eyewitness statements", "CCTV analysis", annex tables), every `observation | record | measurement | condition | statement | event` claim must be `in_item` or explicitly omitted with a reason other than silence. Unaccounted claims block the build. Omissions with `needs_owner_decision` are allowed but listed. This alone would have caught D12.

There is **no fixed item-count target.** The old "40–80 items" rule pushed towards cataloguing or skimming depending on report size. Instead: items = distinct artefacts and observations after merging, with a soft warning if a source yields fewer than one item per 1.5 pages of observation sections, or more than 3 per page.

### 11.3 Conclusions, lessons and recommendations are never evidence (hard rule)

**None of the conclusions, lessons or recommendations in any source document (official investigation or enquiry reports, internal reports, audit reports, regulator analyses, press) is ever treated as a piece of evidence.** They never become claims usable by items, never appear in any evidence item, and never reach any workbook. This is checked **before anything enters the evidence bank** (the claim ledger), not just at build.

What is excluded (claim kinds `conclusion`, `lesson`, `recommendation`):
- **Conclusions:** root causes, immediate, underlying or contributing causes stated as findings, "probable cause", "it is concluded that", "attributable to", "resulted in" as a verdict, causal analyses and reconstructions that assign cause, root-cause lists, the investigating body's opinions on adequacy or blame.
- **Lessons:** "lessons learned", "learning points", "key takeaways", "what should have happened", generalised messages for other sites or industries.
- **Recommendations:** remedial measures, corrective and preventive actions proposed by the source, "shall be provided", "needs to be", "is to be", "to be introduced", "should", action plans, improvement lists.

What is still evidence (the boundary): the source's **direct observations of fact**, i.e. what was seen, measured, found in records or stated by witnesses ("No hydro test was done after replacement of the gasket", "three bolts … were missing", "Notification no. 3800419840 was raised on 17/09/2020"), and factual timelines of what happened when, without causal judgement. A sentence that mixes fact and verdict is split: the fact becomes an evidence claim, and the verdict goes to the held-back ledger. When in doubt, the sentence is held back. The run report lists borderline splits for review.

**Four layers of enforcement:**
1. **Section screening at segmentation:** headings matching conclusion, lesson or recommendation sections ("Root Cause(s)", "Conclusions", "Analysis of the incident", "Lessons learned", "Recommendations", "Improvements / Remedial measures", "Way forward", "Action plan") are tagged `held_back_section`. The chunk planner sends them only to held-back extraction. No evidence claims can be created from them.
2. **Entry gate at `claims add` (before the evidence bank):** every claim is classified. `conclusion`, `lesson` and `recommendation` claims are written **only** to `ledger/conclusions.jsonl`. A claim of an evidence kind whose anchor text matches conclusion, lesson or recommendation patterns, or that comes from a `held_back_section`, is **rejected** with a message to reclassify or split it.
3. **Item gate at `items add`:** an item may reference only evidence-kind claims from `claims.jsonl`. Any reference to a held-back claim is rejected.
4. **Build gate (§14 hard gate 7):** Description text is fuzzy-matched against every held-back claim and screened for recommendation and verdict patterns. Any hit blocks the build.

`conclusions.jsonl` exists only so that ProbeMatrix's own analysis can later be compared fairly with the official findings. It is private working state: it never enters `outputs/`, items or `INDEX.md`, which reports only its count. There is **no setting to switch this rule off.**

## 12. Incremental runs

### 12.1 Run loop
Every invocation of `evidence-pack` in a case folder:
1. `scan` → classify each input as new, changed (new version), unchanged, renamed or removed.
2. Convert, segment and extract **only** new and changed sources. Unchanged sources' segments and claims are reused.
3. Reconcile new claims against the **existing** rosters (labels stay stable forever) and against **all** existing claims for conflicts. A new witness can contradict an old CCTV item.
4. Author items only from new claims. Items in a **draft** workbook (not yet marked imported) may be revised, merged or removed freely. Items in an **imported** workbook are locked and never edited in place.
5. Build: while the master isn't marked imported, every run rewrites `evidence-pack-<case>-master.xlsx` with all items. Once the master is imported, the next run with new items writes `evidence-pack-<case>-delta-002.xlsx`. That delta stays a draft, rewritten by later runs, until it too is marked imported, after which the next delta number opens. Evidence IDs and Tags are never reused or renumbered, even in drafts: a draft item that's removed leaves a gap. A run with no new or changed items writes nothing and says so. An imported workbook is never written to again.
5a. **Marking imports:** `epb mark-imported <file>` or ticking "Imported?" in `INDEX.md` (read back on the next run) locks a workbook. The plugin warns if a draft master has been sitting un-imported for longer than `case.yaml: draft_warning_days` (default 7), and it never locks a workbook on its own.
6. Regenerate `INDEX.md`.

### 12.2 Changed inputs (new version of a known file)
Diff the new version's segments against the old. Claims whose anchors no longer verify against the new version are flagged. If they back already-shipped items, the run creates **correction items** (§12.4), never a silent rewrite. New text yields new claims as usual.

### 12.3 Reprocessing
`epb rebuild --from <stage>` recomputes intermediate state (e.g. after installing OCR) without changing shipped item IDs. A **consolidated** workbook of all items to date (`evidence-pack-<case>-consolidated-<date>.xlsx`, for importing into a *fresh* incident) is produced only on explicit request (`epb build --consolidated`). This is my call (see §18): it isn't part of the normal run, so the "master + deltas" contract stays clean.

### 12.4 Corrections
Corrections apply only to **locked** (imported) items. Draft items are simply fixed. ProbeMatrix can't un-import through a pack, so when a locked item is later found wrong (a superseded input, a newly confirmed conflict, a verification regression after a converter upgrade), the next delta includes a **correction item**: same type, Description beginning "CORRECTION to evidence tagged TAG-…: …", `Related Evidence` = the original tag, `QA Status = disputed` on the correction where applicable. INDEX lists corrections under Open issues with the instruction to review or delete the original in ProbeMatrix by hand.

### 12.5 Concurrency and safety
A lock file (`.epb/lock`) prevents two runs at once. All writes go to temp files and are renamed into place. `state.json` is written last, so a crashed run resumes from the last completed stage.

## 13. De-identification (always on)

### 13.1 Detection
Layered, so one miss doesn't leak:
1. **Pattern pass:** honorifics and titles (Mr, Mrs, Ms, Dr, Sh., Shri, Smt., Er., Capt., …) followed by capitalised tokens; signature blocks; "Name:" fields; email addresses; phone numbers; employee, badge and ID patterns.
2. **Agent pass:** during extraction, every person mention is captured as an entity with its raw string and role context.
3. **Optional NER pass** (spaCy small model if installed) over segments as a third net.
4. **Roster pass:** every raw name string, plus surname, first name and initial forms, is added to `private/name-map.yaml` and becomes part of the **scan list**.

### 13.2 Role labels
Pattern `<Designation> (<Function / Location>)`, with letter disambiguators only when needed (`CISF Constable A (Watch Tower 3)`). Never invent seniority or department. External personnel get letter codes. Committee members become the body ("PNGRB Enquiry Committee (3-member)"). Journalists' bylines are removed. Labels are **comma-free** (D14) and stable for the life of the case.

### 13.3 In quotes
A name inside a verbatim quote is replaced with the role label in square brackets, honorific included. Source: `At around 0220 hrs Mr. Shaikh heard alarm…` → Description: `“At around 0220 hrs [Chief Engineer (Production) - Gas Terminal CR] heard alarm…”`. The verifier treats a bracketed role label as matching the original name span (with or without its honorific) through the private map, so de-identified quotes still verify against the raw source.

### 13.3a Non-English sources
Quotes are always verbatim in the **original language and script**, and they are what the verifier checks. When the source isn't English, the Description carries the original quote followed by an English rendering marked `[translation]`, written by the agent. Only the original is verified. The item records `language`, and the run report lists translated items for human review. OCR language packs and the Whisper language come from `case.yaml` (`languages: [en, hi, gu]`), and `doctor` checks that the Tesseract packs are installed. De-identification patterns include honorifics in the configured scripts (e.g. श्री, श्रीमती).

### 13.4 Beyond names
GPS EXIF is stripped from anything rendered. Faces in images are never described. Voices are referred to by role. File names containing names are substituted in all shareable outputs. Signatures, and handwriting that identifies a person, are referenced generically. Equipment IDs that differ within a source (caption "310 FF1" vs text "310FE1") are recorded as roster aliases with a source-inconsistency note, never silently normalised in a quote.

### 13.5 Gates
- `epb deid-scan` runs the scan list (plus pattern pass) over `items/`, `outputs/*.xlsx`, `INDEX.md` and `runs/*/report.md`. **Zero hits is a hard gate for build.**
- Whole-word matching by default, with an allow-list for name tokens that are also common words or place or equipment names (e.g. a surname that is also a place in a valve-station name). The agent must justify each allow-list entry per case.
- Raw-text guard: the build refuses to copy any field from segments or claims into the workbook except through the item renderer, which applies the map.
- `samples/` publishing (`tools/make-sample.py`) copies only `outputs/` and `INDEX.md`, re-runs the scan, and refuses if `.epb/private` would be included.

## 14. Verification gates (`epb verify`)

**Hard gates (block build):**
1. Every quotation in every Description (`“…”`) exists in `item.quotes`, and each verifies verbatim (§8.2) in the cited segments of the current source version.
2. `Source` page or time references equal the anchor segments' labels (generated, so this is a consistency check).
3. Importer-exact format: sheets, headers, order, required fields, enums, valid JSON, 10-row metadata.
4. Comma-free list elements in Linked Individuals, Linked Equipment, Tags and Regulatory Requirements.
5. No Evidence IDs, row numbers or "row N" in Descriptions.
6. HFACS blocked-term lint on Descriptions and Tags.
7. No conclusion, lesson or recommendation in any item: no item references a held-back claim, and no Description fuzzy-matches a held-back claim or verdict/recommendation patterns (§11.3). Gates 2–3 of §11.3 also run earlier, at `claims add` and `items add`.
8. De-identification scan: zero hits.
9. Coverage gate (§11.2).
10. Description length ≤ 1,800 characters.
11. Collection Date rendered at stored precision (no padding).
12. Every item has ≥ 1 claim, and every claim's source is in a `processed` or `partial` state.

**Soft warnings (listed in the run report; the agent must review each):**
- Visual-only anchors (§7.5) or claims from low-confidence OCR or transcription segments (below the threshold in `case.yaml`). These items get `status: low_confidence_source`, and the Description says "(OCR, low confidence)" or "(transcript, low confidence)".
- Evaluative or speculative phrases in part 3 ("clearly", "significant" without a number, "had … would have", "inevitable", "demonstrably").
- Type-rule lints (§9.1), critical share > 45%, length outside the target.
- Items with no `Related Evidence` where an aligned event cluster exists.
- Lead-in missing a perspective cue.

**Spot-check:** the run report lists 5 random items (seeded, reproducible) with their claims and the raw source text around each anchor, so a human can audit in minutes. The report is de-identified like any shareable file; raw context is shown with the name map applied.

## 15. Skills and CLI

### 15.1 Skills (Agent Skills format; each SKILL.md ≤ ~150 lines)
| Skill | Purpose | Key commands |
|---|---|---|
| `evidence-pack` | **Start here.** Detects or initialises the workspace, runs `doctor`, explains what will happen, then drives the run loop through the sub-skills in order. Handles "what's the status?", "add the new evidence" and "rebuild master as consolidated". | `init`, `doctor`, `status`, `run` |
| `evidence-intake` | Scan, convert and segment, including large and scanned documents and media. Sidecar handling. | `scan`, `convert`, `segment`, `segments show` |
| `evidence-extraction` | Chunk plan, claim extraction per chunk (parallel subagents when available), completeness rules, held-back conclusions. | `plan-extract`, `claims add`, `extract-status` |
| `evidence-reconcile` | Rosters, de-identification, event alignment, conflict detection and confirmation. | `roster`, `deid-scan`, `conflicts detect/resolve` |
| `evidence-authoring` | Grouping claims into items, type/priority/tags, Description writing to §9.4. | `author-plan`, `items add`, `calc` |
| `evidence-verify-build` | All gates, coverage, spot-check, master/delta workbook, INDEX regeneration. | `verify`, `coverage`, `build`, `index` |
| `evidence-web-snapshot` | Optional. Search, user-confirmed URL list, snapshot into `inputs/web/`. | `snapshot` |

### 15.2 CLI (`python3 skills/evidence-pack/scripts/epb.py <cmd> [--case <dir>]`, defaults to cwd)
`init`, `doctor`, `status` (short INDEX summary), `mark-imported <file>`, `scan`, `convert [--src]`, `segment`, `segments show <seg-id>`, `plan-extract`, `claims add/list/show`, `extract-status`, `roster list/add/alias`, `deid-scan`, `conflicts detect/list/resolve`, `author-plan`, `items add/list/show`, `calc` (durations and date differences), `coverage`, `verify`, `build [--consolidated]`, `index`, `rebuild --from <stage>`, `snapshot <url>`. All commands support `--json` for agent consumption. Exit codes: 0 ok, 1 gate failure, 2 usage, 3 missing dependency.

### 15.3 Host specifics
- **Claude Code / Cowork:** plugin manifest with `"skills": "./skills"`. Extraction may fan out to subagents per chunk, each writing its own claims file (chunk-id-suffixed names to avoid collisions), merged by `claims add`.
- **Codex:** `AGENTS.md` describes the same flow, `.agents/skills` points to `skills/`, and `tools/install-codex.sh` installs for all projects. Extraction runs sequentially.
- Python 3.10+. All paths handled with `pathlib`. Windows supported (no symlink reliance at runtime).

## 16. Testing and evaluation

- **Unit tests (pytest):** fingerprinting and versioning; segmenters per modality (with tiny generated fixtures: a text PDF, an image-only PDF page, a DOCX with tracked changes, an .eml with an attachment, a CSV, a short wav, a short mp4 with a burned-in timestamp); quote verification (whitespace, hyphenation, cross-page, ellipsis order, `[sic]`, bracketed role label); comma gate; date precision rendering; importer-exact writer (round-trip against the format spec); de-id scan including allow-list; master/delta numbering; correction items; INDEX tick preservation; crash-resume.
- **Synthetic incident fixture:** a fully fictional incident with planted traps covering the D1–D18 classes (a contradiction, a typo, a cross-page quote, a dropped-finding bait, names with honorifics, inch marks, a recommendation sentence, a year-only date). It is the worked example in the docs, so no real-incident prose exists for an agent to copy (D1).
- **Agent evals (`evals/`):** run the skill on the synthetic incident and score: verbatim-quote rate (must be 100%), page accuracy (100%), coverage of planted observations, conflicts surfaced, conclusions leaked (must be 0), names leaked (must be 0), type accuracy against a gold key, and an incremental scenario (add 2 inputs → delta contains only new items, IDs continue, INDEX updated).
- **Public-report sample:** a published sample on an official public enquiry report, with the report included unmodified, outputs de-identified, and a zero-hit scan. It acts as a regression benchmark: re-run after converter or prompt changes and compare coverage and gate results.
- **CI:** GitHub Actions on Linux, macOS and Windows: core tests without optional tools; a media job with ffmpeg, tesseract and faster-whisper `tiny`.

## 17. Build order (for skill-creator sessions)

1. **Foundations:** repo scaffold, manifests, `AGENTS.md`, `formats/probematrix_v2.py` + validator (importer-exact), workspace `init/scan/state`, `INDEX.md` generator. Tests.
2. **Intake for text documents:** PDF (pdfplumber), DOCX, XLSX/CSV, email, HTML. Segments with page labels and section map. Quote verifier. Skill `evidence-intake` (docs only).
3. **Extraction + ledger:** chunk plan, claims schema, `claims add` with verification, held-back conclusions. Skill `evidence-extraction`.
4. **Reconcile:** rosters, de-id (pattern + agent + map), deid-scan gate, conflicts. Skill `evidence-reconcile`.
5. **Authoring + verify + build:** item schema, renderer, all gates, coverage, master workbook. Skills `evidence-authoring`, `evidence-verify-build`, and router `evidence-pack`. *Milestone: end-to-end on the synthetic text-only incident.*
6. **Incremental:** versions, deltas, corrections, INDEX ticks, crash-resume. *Milestone: incremental eval passes.*
7. **Scans + OCR** (ocrmypdf/Tesseract, confidence) and **docling** option.
8. **Media:** audio and video transcription, keyframes, CCTV overlay OCR, image handling. Sidecars.
9. **Web snapshot** (optional skill).
10. **Evals, public sample, docs** (INSTALL, USER-GUIDE), CI matrix, first release `v0.1.0`.

## 18. Calls I made (please check while reading)

- **Seven skills** (one router + five pipeline skills + one optional) rather than one large skill, to keep each SKILL.md short and let users enter mid-pipeline.
- **Python 3.10+ single CLI** (`epb.py`) with JSON-in/JSON-out. YAML for items and rosters (diff-friendly), JSONL for claims.
- **Segments and claims keep raw text with names** (confidential working files) so quotes verify exactly. De-identification is applied at rendering, and the zero-hit gate covers every shareable artefact. The alternative, de-identifying at conversion, would make verification against the original impossible.
- **No item-count target.** It's replaced by a coverage gate and density warnings.
- **Description length:** target 300–900, hard limit 1,800.
- **Related Evidence uses Evidence Tags,** not IDs, because tags survive import. Prose never cites IDs.
- **Consolidated workbook only on explicit request,** outside the normal master + delta flow.
- **Correction items** for shipped mistakes, with manual cleanup in ProbeMatrix listed in INDEX.
- **Speaker diarisation optional** (licence-gated model).
- **Marketplace name** `probematrix-evidence-pack-builder` (its own marketplace, so it can be installed alongside other plugins without a name clash).
- **Non-English sources:** verbatim original plus a marked English rendering; only the original is verified (§13.3a).
- **Public sample:** the owner chose to bundle the Hazira report unmodified as reference material (`docs/reference/hazira-2020/`). Future samples on other public reports follow the same pattern: the official report unmodified, with plugin outputs de-identified and passing a zero-hit scan. The name-scan gate (§13.5) covers plugin outputs, not `docs/reference/`.
- **`extract-msg` is GPL**, so `.msg` support moves to an optional extra (`requirements-email.txt`). Core stays permissive. `.eml` is handled by the standard library.
- **Cowork:** not verified that its sandbox can run ffmpeg, Tesseract or subagent fan-out. `doctor` decides the capability profile at runtime, and inputs it can't process are marked `unprocessed: <tool> missing`. Document text intake (pure Python) is the guaranteed baseline on every host.
- **Format transcription:** importer header strings, enums and widths are transcribed as a file-format spec; no ProbeMatrix code is copied.
- **Conflict tolerance** of 60 s by default, configurable in `case.yaml`.
- **Critical-share warning** at 45%.

## 19. Left to the builder

- Exact Python package layout inside `scripts/epb/`, internal APIs, logging format.
- Heuristics for printed-page-label detection and boilerplate removal (must be tested on the synthetic fixture and the public sample).
- Chunk token budget tuning (start at 6–8k).
- Keyframe sampling parameters and the Whisper model default (start `small`, configurable).
- Starter tag vocabulary contents beyond the facets listed.
- Wording of SKILL.md files, within the rules above.
- Whether `docling` becomes default once its install footprint is acceptable.

## 20. Amendments after project research (owner decisions, 2026-10-17)

Project research (`.planning/research/SUMMARY.md`, "Owner Decisions Needed") raised points where the design was wrong, incomplete or out of date. The owner decided each one. **This section wins over any earlier section it contradicts.** The OD numbers refer to that summary.

| # | Decision | Amends |
|---|---|---|
| A1 (OD-01) | **Locality wording.** Conversion is local. The agent's excerpts go to the AI host's model provider. `init` and `doctor` warn when the case folder is inside a known sync folder (OneDrive, Dropbox, iCloud Drive, Google Drive), because `.epb/private/` would be uploaded. README and the user manual say this in plain language. | §2 goal 10, §4 |
| A2 (OD-02) | **`.epb/.gitignore` ignores all raw-text state:** `segments/`, `ledger/`, `inbox/`, `tmp/`, `media/`, `runs/`, `private/`. Only de-identified or structural files stay trackable (`case.yaml`, `rosters/`, `items/`, `conflicts.yaml`, `coverage.json`, `state.json`). `deid-scan` also covers `runs/*/run.json`. | §6 rules, §13.5 |
| A3 | **No published samples.** The repo ships the plugin only: no `samples/` folder and no `tools/make-sample.py`. The regression benchmark on the bundled reference report runs in a scratch, git-ignored folder; results are reported in phase verification and nothing is committed. The synthetic incident remains the worked example. | §5, §13.5 (last bullet), §16, §17 step 10, §18 |
| A4 (OD-03) | **Plugin in a `plugin/` subfolder.** Everything users install (`.claude-plugin/plugin.json`, `skills/`, the CLI package, `AGENTS.md`, requirements files) lives under `plugin/`. The repo root keeps README, LICENSE, `docs/`, `tests/`, `evals/`, `tools/` and the marketplace file with `source: "./plugin"`. Install commands are unchanged. | §5 |
| A5 (OD-04) | **Python 3.11+** (3.10 reached end of life on 2026-10-01). | §15.3, §18 |
| A6 (OD-05) | **Two-week dependency rule with a security exception.** A release that fixes a published advisory in a parser of untrusted input may be adopted earlier after review, recorded in an exceptions list that CI checks. `pypdf>=6.19.0`. Every PDF is parsed in a separate process with time and memory limits; a failure marks only that input `unprocessed`. | §18; kickoff §7 |
| A7 (OD-06) | **Core dependencies add** `jsonschema`, `lxml>=6.1.0`, `defusedxml` and `charset-normalizer`. Word tracked changes are read from the XML, not from `paragraph.text`. | §5 requirements.txt, §7.2 |
| A8 (OD-07) | **Guided one-time setup.** The user installs Python once (manual, per OS). `epb.py` is a standard-library-only launcher. `epb doctor --setup` finds a suitable interpreter (`py -3` on Windows, `python3`/`python` elsewhere; never assumes `python3`), creates a private environment in the plugin's per-user data folder, installs the core packages, and reports in plain language what is ready and what is optional. Skills launch the CLI from that environment by absolute path. | §15.2, §15.3 |
| A9 (OD-08) | **CI runs Linux only for v0.1.0.** Code stays cross-platform (pathlib, no runtime symlinks, Windows-safe file replacement), but Windows and macOS CI and fresh-machine testing come **after** v0.1.0. The manual's Windows and macOS sections are marked "not yet tested on this system" until then. | §15.3, §16 CI |
| A10 (OD-09) | **Smoke import in Phase 1.** Phase 1 produces a small synthetic edge-case workbook (a Description beginning with `=`, a `0` value, a long numeric ID, a `YYYY-MM` date, multi-entry Tags and Linked Equipment, every QA Status value) that the owner imports into a test incident. | §17 step 1 |
| A11 (OD-10) | **Exit code 4** = internal or environment problem (crash, lock timeout, workspace newer than the plugin), with a stable error code in the JSON. Skills tell the agent to report it, never to edit evidence in response. | §15.2 |
| A12 (OD-11) | **Added CLI verbs:** `sources set`, `sections tag`, `coverage omit`, `items update`, `items remove`, roster and name-map input from a file or stdin (never names on the command line), and `run` (executes the due deterministic stages and returns a `next` list). | §15.2 |
| A13 (OD-12) | **Page citations:** per source, the plugin decides once which numbering applies. Reliably detected printed numbers are cited as `p.12` / `pp.16–17`; otherwise the physical page is cited as `PDF p.12`. Annexes that restart numbering use their label (`Annex B p.3`). Never mixed within one source. | §7.3, §8.4 Source |
| A14 | **Non-technical user manual.** v0.1.0 ships a detailed manual for non-technical users covering installation and use on Windows, macOS and Linux: installing Python and the optional tools, installing the plugin in Claude Code, Cowork and Codex, first setup, a first case folder, importing into ProbeMatrix, and troubleshooting, with exact on-screen text. It is started in Phase 1 and extended in each phase that adds tools. | §5 docs, §17 |

The remaining research items (OD-13 to OD-37) are decided in the discussion of the phase they affect.
