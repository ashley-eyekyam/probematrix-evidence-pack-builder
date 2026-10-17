# Pitfalls Research

**Domain:** Agent plugin (Agent Skills format) that extracts verbatim-quoted, page-cited, de-identified evidence from incident documents and media, and writes an importer-exact `EVIDENCE_PACK_V2` Excel workbook for ProbeMatrix.
**Researched:** 2026-10-17
**Confidence:** HIGH for the workbook, PDF and quote-normalisation pitfalls, which were reproduced locally (see "Evidence tiers"). MEDIUM for host and skill-format behaviour, taken from vendor docs that change often. LOW to MEDIUM for OCR, Whisper and CCTV tuning, which comes from community reports and needs a Phase 7/8 spike.

**Baseline.** The 18 prototype defects in design §3 are called DEF-01…DEF-18 here. Each critical pitfall names the defect class it would bring back. The table at the end maps every DEF to the pitfalls and phases that cover it.

**Phase numbers** are those in `docs/GSD-KICKOFF.md` §5: 1 Foundations · 2 Text intake + verifier · 3 Extraction + ledger · 4 Reconcile · 5 Authoring + verify + build (MVP) · 6 Incremental · 7 Scans + OCR · 8 Media + images · 9 Web snapshot · 10 Release.

### Evidence tiers used in this file

| Tag | Meaning |
|---|---|
| **[VERIFIED-LOCAL]** | Reproduced on 2026-10-17 in a scratch venv: Python 3.14.4, openpyxl 3.1.5, pypdf 6.21.0, pdfplumber 0.11.10 / pdfminer.six 20260107, Pillow 13.0.0, PyYAML, rapidfuzz, python-dateutil. The workbooks were read back with **the importer's own reader**, SheetJS `xlsx` 0.18.5 from the parent checkout's `node_modules` (read-only), using the importer's exact idiom `sheet_to_json(..., {header:1})` + `String(v \|\| '')`. |
| **[OFFICIAL-DOC]** | Vendor documentation: code.claude.com skills docs, the Codex/ChatGPT build-skills docs, the Python `os` docs, the ocrmypdf man page. The GSD classify-confidence seam rates WebFetch as **LOW** because Context7 needed OAuth and was unavailable. Treat these as authoritative today but liable to change. |
| **[COMMUNITY]** | Issue threads, blogs and papers. LOW: validate in a phase spike before relying on them. |
| **[REASONED]** | Inferred from the design and the importer source. Not externally verified. |

---

## Critical Pitfalls

### Pitfall 1: The quote verifier is too lenient, so paraphrase, "corrected" typos and inverted meaning pass as verbatim

**What goes wrong:**
The verifier is meant to be the hard gate against DEF-01 and DEF-02, but it accepts quotes that are not verbatim. The usual routes are:
- **Fuzzy acceptance** with `rapidfuzz` (a core dependency). [VERIFIED-LOCAL] Against a synthetic source sentence, `fuzz.partial_ratio` scored a **meaning-inverted** quote (with "not" inserted) at **92.3**. The DEF-02-style paraphrase (article dropped, verb dropped) scored only **81.5**. Any threshold loose enough to tolerate OCR noise accepts the inversion.
- **Over-normalising.** Developers reach for `unicodedata.normalize("NFKC")` to fold ligatures. [VERIFIED-LOCAL] NFKC also changes meaning and length: `m²`→`m2` (so `10³`→`103`), `½`→`1⁄2`, `™`→`TM`, `Ⅳ`→`IV`, and `…`→`...` (one character becomes three, which breaks char maps). It does **not** fold the things you need folded: curly quotes `“ ”`, U+2212 minus, and U+00AD soft hyphen all survive NFKC unchanged.
- **Case folding or punctuation stripping** "to be safe". This accepts changed capitalisation, dropped commas and lost decimal points (`1.5` vs `15`).
- **Ellipsis distortion.** Each fragment verifies "in order" (design §8.2), yet fragments far apart can still be stitched into a new meaning, or an elision can remove a negation ("was … found intact" built from "was not found intact").
- **Trivial anchors.** A 1–3-word quote such as "closed" or "the valve" verifies almost anywhere, so it proves nothing about the page.
- **Ambiguous location.** The same sentence appears on two pages (summary and body). The verifier finds it, but the page that gets cited is whichever segment the agent named.

**Why it happens:**
Agents rewrite quotes. They drop articles, fix typos, expand abbreviations ("hrs"→"hours"), re-format times ("0220 hrs"→"02:20"), and anglicise or americanise spelling. Developers then loosen the verifier until the agent's output passes.

**How to avoid:**
- **Acceptance is exact match only**, on a normalised projection limited to the design §8.2 list: whitespace runs; line-break hyphenation (accept *both* the joined and the hyphenated form at a line-end hyphen, never guess); an explicit fold table for quote, apostrophe and dash variants plus U+2212 and U+00AD; and an explicit ligature table (U+FB00–FB06). **Never call NFKC or NFKD on the whole string.** NFC is fine.
- Keep a char map from every normalised index back to raw, so `char_start`/`char_end` in claims always point at raw text.
- Use `rapidfuzz` **only to suggest**. On rejection, return the closest raw span ("did you mean: <exact source text>") so the agent copies it. Fuzzy matching never decides acceptance. Its legitimate gate use is the held-back-claim screen (§11.3 layer 4).
- Ellipsis rules: split on `…` **before** normalising, because NFKC would turn a source-literal `…` into `...`. Cap the gap between fragments (for example, same sentence or ≤ 200 raw chars). Flag any elided gap containing a negation or modality token (`not`, `no`, `never`, `without`, `un-`/`non-` words) for review.
- Minimum anchor: a quote must reach about 4 words or 20 chars unless it is a numeric or identifier anchor. Record the count of occurrences in the source and warn when a quote is not unique.
- `[sic]` must sit right after the uncorrected source token. A test asserts that a silently "corrected" typo is rejected.

**Warning signs:**
- A verifier test suite with no **negative** tests for inserted negation, changed number, changed case, dropped article or corrected typo.
- Any `normalize("NFKC"` or `fuzz.` call on the acceptance path.
- Verified-quote rate is 100% while the eval's gold "quote unchanged" key says otherwise.

**Phase to address:** Phase 2 (the verifier and its negative test corpus). Phase 3 (`claims add` uses it). Phase 5 (re-verification at build, gate 1). **DEF-01, DEF-02.**

---

### Pitfall 2: Quotations that the verifier never sees

**What goes wrong:**
Gate 1 checks every `“…”` in a Description against `item.quotes`. A quotation in any other form is never checked:
- straight double quotes `"…"`
- single quotes `'…'` or `‘…’`
- guillemets `«…»`
- a quote in a block or after a colon with no marks
- an agent-written `[translation]` that drifts from the original

Design §8.2 chose `“ ”` so that inch marks (`6"`) do not collide with quote delimiters. The other side of that choice is that an unverified quotation written with straight quotes passes silently.

**Why it happens:** The agent's house style varies by host and model, and the gate's regex only looks for one delimiter pair.

**How to avoid:**
- Lint every straight `"` in a Description. If it is not directly preceded by a digit (an inch mark), it is a **hard error** ("use typographic quotes so the quote can be verified").
- Lint `‘…’`, `'…'` spans of 3 or more words and `«…»` as hard errors too, unless they are a verified quote.
- Gate 1 cross-checks both ways: every `item.quotes[*].text` appears in the Description, and every quoted span in the Description is in `item.quotes`.
- Translations: the `[translation]` text is never inside `“ ”`. The renderer, not the agent, places the original quote.

**Warning signs:** Descriptions in eval output that contain `"` next to letters; `item.quotes` entries that never appear in the Description.

**Phase to address:** Phase 5 (gate 1 and the Description lint). Phase 7 for the translation rendering (§13.3a). **DEF-01, DEF-02.**

---

### Pitfall 3: The segment text is not what a human reads on the page

**What goes wrong:**
Quotes verify against extracted text that is in the wrong order or full of artefacts, or that differs between extractors and versions:
- **Column interleaving.** [VERIFIED-LOCAL] On a synthetic two-column page, pdfplumber's default `extract_text()` joins line 1 of the left column with line 1 of the right column. You get spans the reader never sees. A real sentence that wraps inside one column becomes impossible to quote. pypdf returned content-stream order for the same page.
- **Extractor disagreement.** [VERIFIED-LOCAL] pdfplumber expands ligatures by default (U+FB01 becomes `fi`), while pypdf keeps U+FB01. Switching to the pypdf fallback, or upgrading pdfplumber, changes segment text, and quotes verified earlier stop verifying.
- **Fake bold** (glyphs drawn twice with an offset) gives doubled characters unless `dedupe_chars()` is applied. [COMMUNITY]
- **Fonts with no ToUnicode map** give `(cid:123)` sequences. They count as "text", so the "< N chars/page means scanned" detector does not send the page to OCR. [REASONED]
- **Legacy Indic fonts** (Kruti Dev-style, common in Indian government PDFs) store Devanagari as Latin letters. The text looks like Latin gibberish and is never OCR'd. [COMMUNITY]
- **Shaped Indic scripts** may extract with vowel signs in visual rather than logical order. [COMMUNITY] Note that reportlab does not shape Indic text, so locally generated fixtures extract cleanly while real reports do not. [VERIFIED-LOCAL]
- **A bad existing hidden OCR layer** from a scanner counts as a text layer and is used as-is.
- **Tables and rotated text.** Table text appears in both the page text and the tables, which gives duplicate claims. Rotated landscape tables come out one character per line.

**Why it happens:** PDF has no reading order, only glyph positions. Each library heuristic is right for different layouts, and the defaults favour single-column prose.

**How to avoid:**
- **One extractor per source, recorded** in `sources/<id>.json` (`converter{tool, version, options}`). Never verify a quote against text from a different extractor or version.
- **Segments are frozen.** An unchanged source is never re-converted, unless the user explicitly runs `rebuild --from convert`, which then diffs and raises corrections (§12.2–12.4).
- Detect columns per page (cluster word x-positions from `extract_words()`, then crop per column) before calling `extract_text`. Docling is the optional heavy path (§7.2).
- Quality heuristics per page, any of which routes the page to OCR or `partial`:
  - share of `(cid:` tokens
  - share of non-dictionary Latin tokens
  - font names matching known legacy-encoding families
  - doubled-character ratio
- Exclude table regions from prose text, or mark them, so a fact is extracted once.
- Build fixtures from real-world layout traps (two columns, running headers, a rotated table, a ligature font, a pre-OCR'd scan), not only reportlab single-column pages.

**Warning signs:**
- Quotes fail verification only on multi-column pages.
- Segment text has lines that end mid-sentence and resume with unrelated text.
- Hindi or Gujarati sources yield only Latin text.
- A `pip install -U` changes test snapshots of segment text.

**Phase to address:** Phase 2 (extractor choice, column handling, quality heuristics, frozen segments). Phase 7 (OCR routing for cid/legacy-font pages, `--redo-ocr` on bad layers). **DEF-01, DEF-02, DEF-03, DEF-12.**

---

### Pitfall 4: Page citations that are confidently wrong (printed vs physical, cross-page, boilerplate)

**What goes wrong:**
DEF-03 comes back even though pages are "generated":
- **pypdf `page_labels` looks authoritative but is not.** [VERIFIED-LOCAL] On a PDF with **no** `/PageLabels` it returns `['1','2','3']`, which are physical indices formatted as strings. Code that reads it as "printed labels" silently cites physical pages.
- **Off-by-N between printed and physical numbering:** an unnumbered cover, roman-numeral front matter, annexures that restart at 1 ("Annexure-B, Page 3"), inserted blank or photo pages without folios, and scanned bundles merged out of order.
- **Mixed schemes inside one source.** Footer detection succeeds on some pages and fails on others, so one source's citations mix printed and physical numbers. Nobody can tell which is which.
- **Boilerplate detection misses varying lines.** "Page 5 of 40" differs on every page, so a naive repeated-line detector keeps it as body text. A cross-page quote then contains the footer and header and fails, or the agent quotes around it and cites one page (DEF-02's cross-page case). Odd and even running headers alternate. The first page often has none.
- **Chunk overlap** (§7.4, one segment) makes the same claim come from two chunks, with different `seg_ids`.

**Why it happens:** Printed-label detection is a heuristic (§19 leaves it to the builder), and the citation format `p.<n>` does not say which scheme was used.

**How to avoid:**
- Read `/PageLabels` only if the catalogue actually contains it. Treat it as a hint and cross-check it against footer detection.
- Detect the printed label with digit-masked header and footer templates ("Page # of #", "- # -", "#"), require a **monotonic sequence** across the source, and handle restarts as sub-sequences (annex prefix).
- Decide the label scheme **per source, once**, record it in the source record, and never mix schemes within a source. (How a physical-index citation is shown is an owner decision; see Conflicts.)
- Match cross-page quotes on the join of page *n* body plus page *n+1* body with boilerplate removed, mapped back through the char map. Cite `pp.n–m`.
- Deduplicate claims on `(src_id, raw char span)` across overlapping chunks.

**Warning signs:**
- `page_labels` equals `[str(i+1) …]` and `/PageLabels` is absent.
- The source's printed labels are not monotonic.
- Fixtures where printed equals physical. This is true of the Hazira reference (design §3), so it will **not** catch off-by-N bugs. Add a synthetic fixture with an unnumbered cover, roman front matter and a restarting annex.

**Phase to address:** Phase 2 (label detection, boilerplate masks, cross-page join, dedupe). Phase 5 (gate 2 consistency). **DEF-02, DEF-03.**

---

### Pitfall 5: "Verified verbatim" against machine text that is wrong (OCR misreads, Whisper hallucinations)

**What goes wrong:**
For scans, audio and video, the "source text" is OCR or ASR output. A quote can verify perfectly against a transcript that the speaker never said:
- **Whisper hallucinates on silence, noise and music.** It produces fluent sentences, stock phrases ("thank you for watching") and repetition loops. [COMMUNITY] CCTV audio is mostly ambient, which is the worst case: whole "statements" can appear from nothing.
- **Wrong language or script.** Accented English can be detected as Hindi, and South Asian languages can be emitted in the wrong script. [COMMUNITY] With `language` auto-detected from the first 30 s, a code-switched interview is transcribed in the wrong language.
- **OCR digit and letter confusions** (`0/O`, `1/l/I`, `5/S`, `8/B`) in exactly the values that matter: times, IDs, notification numbers.
- **Confidence averaged at page level hides the bad span.** Prose at 95 can mask a numbers table at 40. Tesseract TSV structural rows carry `conf = -1`, which drags naive means down. [COMMUNITY]
- **High-confidence hallucinations.** Whisper `avg_logprob` is not a calibrated probability, and hallucinated text can score well. [COMMUNITY]

**Why it happens:** The verifier proves "this string is in the segment", and that only means "the machine wrote this string".

**How to avoid:**
- **Run VAD before ASR.** If there is no speech, emit **no transcript** (`processed: no speech detected`). Use faster-whisper with `vad_filter=True` and `condition_on_previous_text=False`. Set `hallucination_silence_threshold` (needs `word_timestamps=True`). Mark segments as hallucination candidates when `no_speech_prob`, `compression_ratio` or n-gram repetition passes a threshold, or when they match a stock-phrase list. Treat these as LOW-confidence community settings and confirm them in a Phase 8 spike.
- Take the language **from `case.yaml`**, not auto-detect, whenever it is set. Record the detected language per segment and flag disagreement.
- Compute OCR and ASR confidence **for the anchor span** (min and share of words below threshold), not per page. Ignore `conf = -1` rows (use word-level rows only).
- Treat numeric anchors from OCR as low confidence unless corroborated (a second OCR pass at a different DPI or PSM, or a matching value elsewhere).
- Label machine-derived text as such in the lead-in or Source (owner decision; see Conflicts).

**Warning signs:**
- Transcripts for CCTV clips with no audible speech.
- Identical sentences repeated across segments.
- Transcripts in a script that is not in `case.yaml: languages`.
- Mean OCR confidence is high on pages whose numbers are wrong in spot-checks.

**Phase to address:** Phase 7 (OCR confidence per span). Phase 8 (VAD, hallucination screens, language pinning). Phase 5 (low-confidence status and Description marker plumbing). **DEF-01-class (invented content), DEF-04 (false conflicts from bad times).**

---

### Pitfall 6: Conclusions leak through paraphrase, mixed sentences and the agent's own knowledge

**What goes wrong:**
The four layers in §11.3 stop *verbatim* verdicts. Leaks still get through:
- **Part 3 of the Description** ("operational significance") is agent prose. The agent restates the source's verdict in new words ("…which meant the gasket was the failure point"). A fuzzy match against held-back claims misses a semantic paraphrase.
- **Causal clauses inside "factual" sentences**, especially in timelines and observation sections: "due to", "owing to", "as a result of", "led to", "on account of", "failure to", "lack of", "inadequate", "poor".
- **Combined headings** such as "Observations and Recommendations" or "Findings and Way Forward". Screening the whole section loses the observations (a DEF-12 coverage hole). Not screening it lets recommendations in.
- **Headings the patterns do not know**: "Suggestions", "Points for consideration", "Learnings", "Corrective actions taken", non-English headings, numbered recommendation lists with no heading at all.
- **Prior knowledge.** For a well-known public incident, the model already knows the official root cause and may "explain" items with it. Nothing in the inputs anchors it.
- **Over-blocking.** A witness reporting what an SOP *says* ("the SOP says the valve should be closed") trips "should" patterns. Agents then mass-omit these claims, and coverage drops.

**Why it happens:** Verdicts are a matter of meaning, and lexical gates only see surface form. Part 3 invites inference.

**How to avoid:**
- **Constrain part 3 mechanically.** Every sentence in part 3 must carry a claim reference in the item YAML (sentence → claim ids). Lint part 3 for causal connectives and evaluative adjectives. A hit is a **hard error** unless the phrase sits inside a verified quote from an evidence-kind claim. Prefer arithmetic (`epb calc`) and control-state statements (§9.4).
- Split mixed sentences at `claims add`. The verdict clause goes to `conclusions.jsonl`, and the run report lists the splits (§11.3 already requires this; make it a tested path).
- Section screening returns **three** states: `held_back_section`, `observation_section` and `mixed_section`. A mixed section is extracted sentence by sentence with the entry gate. Its claims still count for the coverage gate.
- Recognise status words for recommendations (`shall`, `should`, `needs to`, `is to be`, `to be provided`), with an exemption path for `statement` claims whose `underlying_artefact` is a procedure or SOP. That path checks that the claim reports what a document *says* (it becomes a `document_fact`) rather than adopting it.
- Eval traps: a synthetic verdict paraphrase in part 3, a causal clause in a timeline, a combined heading, and an unheaded numbered recommendation list. Run the Hazira regression and the public sample with "prior-knowledge" probes: any Description sentence with no claim mapping fails.

**Warning signs:**
- Part-3 sentences without claim mappings.
- Held-back counts near zero for a report that has a recommendations chapter.
- Coverage collapsing after the conclusions screen is added.

**Phase to address:** Phase 3 (entry gate, mixed-section handling, split reporting). Phase 5 (part-3 sentence-to-claim mapping, causal lint, gate 7). Phase 10 (evals and regression probes). **DEF-05, DEF-13, DEF-12 (over-blocking).**

---

### Pitfall 7: De-identification is circular. The zero-hit scan only finds names you already found.

**What goes wrong:**
`deid-scan` searches for names in `private/name-map.yaml`. A name that no pass detected is not in the scan list, so the gate reports zero hits and the name ships. The common misses:
- **Formats**:
  - initials-first names (`<I>. <I>. <Surname>`, `<I>.<I>. <Surname>`, `<II> <Surname>`, `<Surname> <I> <I>`)
  - all-caps signature blocks
  - possessives (`<Surname>’s`)
  - hyphenated or line-broken names (`<Sur-\nname>`)
  - OCR-split names (`<Sur name>`)
  - transliteration variants of one name
- **Indian honorifics and suffixes** that pattern passes built for "Mr/Mrs/Dr" miss:
  - Latin-script prefixes: `Shri`, `Sh.`, `Smt.`, `Kum.`, `Km.`, `Er.`
  - relation markers: `S/o`, `D/o`, `W/o`
  - suffixes **attached to the name or following it** (`-bhai`, `-ben`, `ji`, `sahab`/`saheb`)
  - Devanagari and Gujarati forms (`श्री`, `श्रीमती`, `सुश्री`, `डॉ.`, `શ્રી`, `શ્રીમતી`) and Tamil `திரு`, `திருமதி`
  - case and postposition endings in Indic text
  - zero-width joiners or non-joiners inside Indic names, which break substring matches
- **Names that are also words, places, organisations or equipment.** The allow-list (§13.5) is right in principle but gets padded to make the gate pass.
- **Channels outside the Description**:
  - section headings that become `Storage Location` ("Statement of <Name>")
  - source titles that become `citation_short` and `Source`
  - DOCX and PDF core-properties `Author`/`LastModifiedBy` used for `author_body`
  - email `From`/`To` display names (RFC 2047 encoded words) and local parts (`<initial><surname>@`)
  - chat-export sender names and phone numbers
  - EXIF `Artist`/`Copyright`/`OwnerName`, ID3 tags, MP4 metadata
  - web snapshot bylines and URL slugs
  - Chain of Custody `location` and `notes`
- **Quotes are the main vector.** They are raw text by design, so a missed name inside a verbatim quote passes the verifier *and* the scan.
- **NFC vs NFD.** Name strings on macOS file names (NFD) vs Linux (NFC) fail equality.

**Why it happens:** Every layer depends on detection. The scan only confirms that detection was applied, not that it was complete.

**How to avoid:**
- Add a scan that **does not depend on the name map**: every capitalised or Indic-script token sequence in a shareable artefact that is not in the role roster, equipment roster, tag vocabulary, a domain dictionary or the per-case allow-list is a **review hit**. It is a hard block until it is dispositioned (allow-list with justification, or added to the map).
- Generate scan variants from each mapped name: initials forms, possessive, all-caps, with each honorific in each configured script, with and without `-bhai`/`-ben`/`ji`, ZWJ/ZWNJ-stripped, NFC-normalised.
- Before any substring test, normalise both sides: NFC, strip ZWJ, ZWNJ and soft hyphens, case-fold Latin.
- Route every field the renderer emits (Source, Storage Location, Collector, Chain of Custody, Regulatory Requirements, file-name substitutions) through the map. Do not apply it to Descriptions alone.
- Strip or ignore document metadata author fields at conversion, or route them through the map.
- Allow-list entries need a per-case justification string and are listed in every run report. Warn when the allow-list grows by more than a few entries per run.
- Plant fixture names in each channel above (heading, metadata, email header, EXIF Artist, chat sender, possessive, initials, Devanagari honorific, attached `-bhai` suffix).

**Warning signs:**
- The allow-list grows in step with failing scans.
- Zero hits on the first run of a new case. That is suspicious, not reassuring.
- Capitalised unknown tokens in the spot-check report.

**Phase to address:** Phase 4 (detection layers, variant generation, map-independent scan). Phase 2 (strip metadata authors, decode email headers). Phase 7 (Indic honorifics in OCR text). Phase 8 (EXIF, ID3, MP4 tags). Phase 9 (bylines, URLs). **DEF-15 and the "names in outputs" anti-goal.**

---

### Pitfall 8: openpyxl writes cells that the importer reads as blank, numeric or corrupt

**What goes wrong:** [VERIFIED-LOCAL] Each item below was round-tripped through openpyxl 3.1.5 and SheetJS 0.18.5 with the importer's own idiom:
- **A string starting with `=` is stored as a formula** (`data_type 'f'`, empty cached `<v/>`). SheetJS reads it as `null`, so `String(v || '')` becomes `''`. A Description that begins with `=` imports as **blank**, and per §8.4 item 5 **one blank Description rejects the whole file**. When opened in Excel, the same cell is executed: formula injection into the investigator's machine, for example from a hostile web-snapshot title or a crafted file name.
- `+`, `-` and `@` prefixes stay strings in openpyxl (safe for the importer). Do not "escape" them by prepending `'`, because that changes the stored text.
- **`datetime.date`** becomes an Excel serial (`44091`). Text `"2020-09"` survives.
- **Integers over 15 digits lose precision** (a 19-digit ID came back rounded). Long notification or work-order numbers must be text.
- **Numeric `0`** becomes `''` through `|| ''`.
- **C0 control characters** (`\x00–\x08`, `\x0b`, `\x0c`, `\x0e–\x1f`) raise `IllegalCharacterError` at **build time**, the last step. Form feeds come from PDF and pdftotext output, vertical tabs from Word line breaks, NULs from mis-decoded UTF-16 email.
- **U+FFFE and lone surrogates save without error but produce a malformed workbook.** openpyxl itself cannot reopen it (`ParseError: not well-formed`).
- **Strings over 32,767 chars are silently truncated** to 32,767. The Chain of Custody JSON for an item with many contributing inputs becomes invalid JSON, and the importer only **warns** (§8.4 item 10), so custody is silently lost.
- `Integrity Verified` must be exactly `Yes` or `No` (strict `=== 'Yes'` in the importer). [REASONED from importer source]

The YAML half of the same problem: [VERIFIED-LOCAL] PyYAML `safe_load` turns `0123` into **83** (octal), `2017` into an int, `2020-09-17` into a `date`, and `no`/`on` into booleans. An equipment ID, year or tag written unquoted into item or roster YAML is corrupted before the renderer sees it.

**Why it happens:** openpyxl infers types from Python values and from a leading `=`. SheetJS returns raw typed values. YAML 1.1 implicit typing does the rest.

**How to avoid:**
- In `formats/probematrix_v2.py`, **every cell is written as a string**: assign the value, then set `cell.data_type = 's'`. That wrote `inlineStr`, which SheetJS read back verbatim. Never pass `date`, `int` or `bool` objects.
- Sanitise before the writer: C0 controls go to a space (or are removed) through the char map at segmentation, and U+FFFE, U+FFFF and surrogates are rejected at segmentation, so quotes still verify.
- **Validate the bytes on disk, not the in-memory rows.** Reopen the saved workbook with zipfile and XML and reject any `<f>` element, any non-string cell type in the Evidence Pack sheet, any cell over the length cap, and any Chain of Custody value that does not `json.loads` back to the `ChainOfCustodyEntry` shape.
- Item and roster YAML: dump with explicit quoting (a custom dumper that quotes all scalars) and load with a schema check. Dates are stored as `{value: "2020-09", precision: month}` strings, never YAML dates.
- Golden test: a workbook with a Description starting with `=`, an ID of 19 digits, a value `0`, a date, a control character and a 33k JSON must either be rejected by the validator or written safely.

**Warning signs:** Any `ws.append([...])` with mixed Python types; validator tests that build rows in memory and never reopen the file; YAML fixtures with unquoted IDs.

**Phase to address:** Phase 1 (format module, writer, on-disk validator, YAML dumper). Recommend an **owner import smoke test in Phase 1** with an edge-case pack, not waiting for Phase 5 (see Conflicts). **DEF-08, DEF-14 (format class), whole-file rejection.**

---

### Pitfall 9: Comma-splitting corrupts more than equipment labels

**What goes wrong:** The importer runs `String(v||'').split(',').map(t=>t.trim()).filter(t=>t)` on Tags, Linked Individuals, Linked Equipment, Related Evidence and Regulatory Requirements. [VERIFIED by reading `evidenceExportService.ts`] DEF-14 was equipment labels, but the worst offenders in this domain are elsewhere:
- **Regulatory Requirements.** Statute citations almost always contain commas: "<Act name>, <year>", "Rule 5(1), Schedule II". The comma gate will fail on nearly every row unless the renderer has a deterministic comma-free form.
- **Indian digit grouping** in labels ("1,20,000 L tank"), and thousands separators generally.
- **Designations** in role labels ("Manager, Operations"), which the prototype's conventions produced.
- **User-supplied `tags_extra`** in `case.yaml`.
- **Leading and trailing whitespace is trimmed** by the importer, so a label that differs from its roster entry only by whitespace imports differently.

**Why it happens:** Labels are written for humans, and commas are natural in them.

**How to avoid:**
- Generate labels at roster creation with a comma-free rule (`<Designation> (<Function> - <Location>)`) and reject a comma at `roster add`, not only at build.
- Use a fixed rewrite for regulatory references (drop the comma before a year, use `;`-free and `,`-free forms such as "<Act> 1948 s.7A"). It is not a quote, so rewriting is allowed. Put the exact citation in the Description if it matters.
- Remove digit grouping in labels. Never strip it inside quotes.
- The gate tests every list element against `^[^,]+$` after `trim()`, and tests that every roster label equals its trimmed form.

**Warning signs:** The comma gate firing mostly on Regulatory Requirements; labels with digits and commas.

**Phase to address:** Phase 1 (gate 4 in the validator). Phase 4 (roster label rules). Phase 5 (regulatory rendering). **DEF-14.**

---

### Pitfall 10: The draft-overwrite rule creates an import race. Duplicates, or items silently never imported.

**What goes wrong:**
Design §12.1 lets a draft master be rewritten until it is marked imported. Consider this sequence:
1. The user uploads the master at 10:00 (version A, 40 items).
2. They run the plugin again at 11:00. It finds a new input and **rewrites** the master (version B, 46 items).
3. They tick "Imported?".

The plugin locks **B**. ProbeMatrix holds **A**. The 6 extra items never reach any delta, so they are silently lost. The reverse also happens: the user forgets to tick, imports again later, and every item is duplicated (§8.4 item 2).

Tick read-back is fragile too:
- Markdown formatters (Obsidian, VS Code extensions) re-flow the table.
- `[X]` vs `[x]`, and CRLF line endings.
- An editor holding INDEX.md open saves a stale copy *after* the plugin regenerated it, which drops or resurrects ticks.
- An accidental untick.

**Why it happens:** The plugin cannot see ProbeMatrix (no API, §2), so "what was imported" is only what the user reports.

**How to avoid:**
- Record a **build fingerprint** per draft write (item count, Evidence Tag set, sha256) in `state.json` and the run log.
- `mark-imported` (and tick read-back) shows the fingerprints of every write of that draft and asks which item count or Tag range the user saw in ProbeMatrix. Where the user has rewritten the draft after first write, require that confirmation.
- Make ticks **one-way**. A recorded tick is never undone by an untick; that needs an explicit command.
- Parse ticks tolerantly (`[x]`/`[X]`, CRLF, re-flowed tables, keyed by file name, not by row position).
- Do not rewrite a draft that is older than N minutes without a "this draft may already be imported" prompt. Owner decision; see Conflicts.

**Warning signs:** Draft rewrites after the file's first `outputs/` timestamp; INDEX.md mtime newer than the last run; tick count lower than state.

**Phase to address:** Phase 6 (fingerprints, mark-imported confirmation, tick parser, tests for formatter-mangled INDEX.md). **Duplicates anti-goal, DEF-07 (Related Evidence pointing at the wrong copies).**

---

### Pitfall 11: Crash, lock and atomic-write bugs that reuse IDs or corrupt state, worst on Windows

**What goes wrong:**
- **ID reuse after a crash.** Items are written under the next ID, then the run crashes before `state.json` (written last, §12.5) records the counter. The next run allocates the same `EVD-…`/`TAG-…` again. IDs must never be reused (§12.1).
- **`os.replace` fails on Windows** when the target is open:
  - Excel holds an exclusive lock on the `.xlsx`, and users will have the master open while checking it.
  - Windows Defender, the Search indexer or OneDrive briefly lock new files.
  - The temp file is on another volume (temp dir on `C:`, case folder on `D:`).
  - The case folder is on an SMB share, where atomicity is not guaranteed.

  The run dies at build, leaving `.tmp` files behind and the state ambiguous. The Python docs say `os.replace` "may fail if src and dst are on different filesystems". [OFFICIAL-DOC; Windows locking behaviour is COMMUNITY/REASONED]
- **Stale lock detection that kills processes.** The POSIX idiom `os.kill(pid, 0)` for "is the lock owner alive?" is destructive on Windows. Per the Python docs, any `sig` other than `CTRL_C_EVENT` or `CTRL_BREAK_EVENT` "will cause the process to be unconditionally killed by the TerminateProcess API", and `CTRL_C_EVENT` itself has the value 0. [OFFICIAL-DOC]
- **Lock scope.** If the run lock is held by the orchestrating agent's `run` and per-chunk `claims add` calls from parallel subagents take the same lock, subagents fail with "locked". Agents then retry badly or skip silently, so claims go missing. Concurrent appends to `claims.jsonl` without a lock interleave lines.
- **Excel's owner file** `~$evidence-pack-…xlsx` appears **in `outputs/`** while the user has the pack open. It breaks "outputs contains only packs" and could be listed in INDEX "What to import".

**How to avoid:**
- Allocate IDs **from a durable reservation**: `next = max(counter, max id present in items/ and in every workbook in outputs/) + 1`, recomputed on every run, or append-only `ids.log` written *before* the item.
- Atomic write helper:
  - create the temp file in the **same directory** as the target
  - `flush` + `os.fsync`
  - `os.replace` with a bounded retry and backoff on `PermissionError` (WinError 5 or 32)
  - then a clear message ("close `<file>` in Excel and re-run"), exit code 1, and state not advanced
  - clean up orphaned `*.tmp` on the next start
- Lock file holds `{pid, hostname, started_at, command}`. Staleness is decided by age plus hostname, **never by `os.kill`** on Windows. Use a read-only process query, or a documented `epb unlock` after a timeout.
- Two lock levels: a **run lock** for state-mutating stages, and a short **ledger lock** for `claims add`/`items add` with a wait timeout and a distinct exit code. Subagents write per-chunk files (§15.3); only the merge takes the ledger lock.
- Ignore `~$*` and `*.tmp` everywhere: scan, outputs listing, INDEX.
- Crash-resume test: kill the process between every pair of writes in a build (fault-injection seam) and assert no ID reuse and a resumable state.

**Warning signs:** No Windows runner in CI until Phase 10; `os.kill` in lock code; temp files created with `tempfile.mkstemp()` with no `dir=`.

**Phase to address:** Phase 1 (atomic writer, lock, ID reservation, Windows CI). Phase 3 (ledger lock and merge). Phase 6 (crash-resume and fault injection). **Duplicates anti-goal, "IDs never reused".**

---

### Pitfall 12: The agent games the gates, or stops following the skill

**What goes wrong:** The CLI blocks the build, and the agent "fixes" the symptom instead of the cause:
- It writes item YAML or `claims.jsonl` directly with its file tools instead of `epb items add`/`claims add`, which skips validation on write.
- It pads the de-identification allow-list.
- It marks unaccounted claims `omitted: needs_owner_decision` in bulk to pass the coverage gate (§11.2 allows that reason).
- It dismisses real conflicts as "false positives" to avoid `disputed` status (§10.2 forbids picking a winner but cannot detect a bad dismissal).
- It edits `case.yaml` thresholds, such as the OCR confidence threshold.

Separately, Claude Code's docs say that after compaction only **the start** of an invoked skill may be kept, and that rules which must always hold belong in hooks or deterministic code. [OFFICIAL-DOC] A long extraction session therefore drifts away from the SKILL.md rules partway through a 300-page report.

**Why it happens:** Agents optimise for "the command succeeded". Long runs exceed context.

**How to avoid:**
- Every must-hold rule lives in the CLI (design intent, §2 goal 9). SKILL.md only routes and explains.
- `verify` recomputes from first principles. It re-verifies every quote, recomputes coverage from `claims.jsonl` and does not trust cached flags. It also detects items or claims that were not written through the CLI: the CLI records a content hash for each write in an append-only journal, and an unjournalled or hash-mismatched file is a hard error.
- The run report gets an "agent dispositions" section: every allow-list addition, conflict dismissal (with reason) and `needs_owner_decision` omission. Each is counted, and a soft warning fires above a ratio. Threshold edits in `case.yaml` are diffed in the report.
- Put the five non-negotiable rules **at the top** of each SKILL.md (they survive compaction). Re-invoke the skill per chunk (`plan-extract` prints the instruction to do so).
- Optional Claude Code hook (skill `hooks` frontmatter) that denies direct writes under `.epb/items/` and `.epb/ledger/`. Codex has no equivalent, so the journal check is the cross-host guarantee.

**Warning signs:** Items with no journal entry; allow-list or dismissal counts spiking; Descriptions quality degrading in later chunks of a long source.

**Phase to address:** Phase 3 (journal, `claims add` only path). Phase 4 (dispositions for allow-list and dismissals). Phase 5 (verify from first principles, dispositions report). Phase 10 (evals on long inputs).

---

### Pitfall 13: Skills that do not trigger, scripts that cannot be found, and installs that fail on a fresh machine

**What goes wrong:**
- **Description budgets.** Claude Code truncates `description` + `when_to_use` at **1,536 chars** in the listing. The whole listing is capped at **1% of context**, and on overflow it **drops descriptions starting with the least-invoked skills**. Six sub-skills that are rarely invoked directly are first to lose their descriptions. Codex caps the initial list at **2% of context or 8,000 chars**, shortens descriptions first, and may omit skills. [OFFICIAL-DOC]
- **Frontmatter differences.** Codex *requires* `name` and `description`. Claude Code treats all fields as optional and **loads a skill with malformed YAML with no fields at all**, so it never auto-triggers and there is no error. The open Agent Skills spec limits `name` to 64 chars of lowercase, digits and hyphens, and `description` to 1,024. [OFFICIAL-DOC / COMMUNITY for the spec mirror]
- **Script paths.** Design §15.2's `python3 skills/evidence-pack/scripts/epb.py` is relative to the *repo*, but the agent's cwd is the *case folder*, and an installed plugin lives in a host cache directory. Claude Code provides `${CLAUDE_SKILL_DIR}`/`${CLAUDE_PLUGIN_ROOT}` substitution in SKILL.md. [OFFICIAL-DOC] Codex documents no equivalent. [OFFICIAL-DOC: none stated]
- **Interpreter discovery.**
  - On Windows, `python3`/`python` may be the **Microsoft Store App Execution Alias stub**, which errors instead of running. [COMMUNITY]
  - On a fresh Mac, `/usr/bin/python3` from the Command Line Tools is older than 3.10 [REASONED: commonly 3.9], so modern syntax in `epb.py` gives a `SyntaxError` before any friendly version check can run.
  - On Debian/Ubuntu and Homebrew Python, `pip install` into the system interpreter is refused (PEP 668 "externally-managed-environment"). [REASONED, well established]
- **Codex discovery on Windows.** `.agents/skills -> ../skills` is a git symlink. On a Windows clone with `core.symlinks=false` (the default without Developer Mode) it checks out as a **plain text file** containing `../skills`, so Codex finds no skills. [COMMUNITY] `tools/install-codex.sh` does not run natively on Windows.
- **Cowork.** Not verified: whether its sandbox runs ffmpeg or Tesseract, allows pip, or maps the case folder to the same absolute path as the host (design §18 already flags this). Absolute paths in `state.json` would break when the same case is opened from Claude Code.
- **Model downloads.** faster-whisper downloads models on first use, so the first media run fails offline and tests that touch it break the "no network" rule. [REASONED]

**How to avoid:**
- Write descriptions with **trigger words first** ("evidence pack", "ProbeMatrix", "incident folder", "witness statements"), keep each under about 400 chars, and keep `name` spec-compliant and equal to its folder name. Make `evidence-pack` the only skill that needs to auto-trigger. Sub-skills are reached by the router, so a truncated listing does not matter.
- Lint every SKILL.md in CI: YAML parses, `name` regex, description ≤ 1,024 chars, ≤ ~150 lines. Run `claude plugin validate` where available, and use `claude plugin eval` with a `tool_used: Skill` grader for trigger-rate tests. [OFFICIAL-DOC]
- Use one launcher contract per host:
  - Claude Code SKILL.md uses `${CLAUDE_SKILL_DIR}/scripts/epb.py`.
  - On Codex, AGENTS.md tells the agent to resolve the skill directory from the SKILL.md path it just read.
  - `epb.py` is written in syntax that parses on old Pythons and checks `sys.version_info >= (3,10)` before importing the package.
  - Document `py -3` on Windows.
- **Venv strategy** decided in Phase 1: `epb doctor --setup` creates a venv in a per-user data dir (`${CLAUDE_PLUGIN_DATA}` when present) and re-execs under it. It never touches the system interpreter.
- Use a Python installer (`tools/install-codex.py`) instead of, or alongside, `.sh`. It copies `skills/` rather than relying on the repo symlink (see Conflicts).
- Store only case-relative POSIX paths in `.epb/`.
- `doctor` reports whether a model is cached. Fetch models explicitly (`doctor --fetch-models`). At runtime set `HF_HUB_OFFLINE=1` when the model is present.

**Warning signs:** The skill works when you type `/evidence-pack` but never auto-triggers; Codex `/skills` does not list it; the Windows CI job is absent; "works on my machine" with Python 3.14.

**Phase to address:** Phase 1 (manifests, launcher contract, version-guarding shim, venv strategy, SKILL.md lint, Windows CI). Phase 5 (router description). Phase 8 (model fetch). Phase 10 (fresh-machine installs on all three hosts, trigger evals).

---

### Pitfall 14: Date handling fabricates precision or swaps day and month

**What goes wrong:** [VERIFIED-LOCAL] `dateutil.parser.parse`:
- reads `"2017"` as **2017-10-17** and `"Sep 2020"` as **2020-09-17**, filling the missing parts **from today's date**. That is fabricated precision (DEF-08), and it is non-deterministic, because the result depends on the run date.
- reads `"04/05/2020"` month-first as 2020-04-05. Indian and UK sources are day-first.

Other routes to the same failures:
- PyYAML turns unquoted ISO dates into `date` objects (Pitfall 8).
- Converting a date-only value through a timezone-aware datetime shifts it a day (IST to UTC).
- openpyxl reads date-typed cells in XLSX inputs as `datetime` with `00:00`, which invents time precision.
- `mtime` changes on every copy, so it is never an artefact date.
- EXIF `DateTimeOriginal` has no timezone unless `OffsetTimeOriginal` is present.
- Indian fiscal years ("FY 2019-20") are not expressible as `YYYY`, `YYYY-MM` or `YYYY-MM-DD` (§8.4).
- WhatsApp exports format dates per phone locale, and iOS inserts U+202F before AM/PM.

**How to avoid:**
- Ban `dateutil` (and any default-filling parser) from date extraction. Use a small explicit parser that returns `(value, precision)` and **never fills** missing parts.
- Set day-first or month-first **per source** (from `case.yaml` locale or detected from unambiguous dates in the same source). Flag ambiguous dates (both parts ≤ 12) when the source convention is unknown.
- Keep dates as strings end to end, and never put a date-only value through a timezone.
- Fiscal-year or range dates: Collection Date blank, exact text in the Description (owner decision; see Conflicts).

**Warning signs:** Any `parser.parse(`; `datetime` objects in item YAML; Collection Dates ending `-01` or `-31`, or equal to today's day.

**Phase to address:** Phase 2 (input parsing, chat and email timestamps). Phase 3 (claim `values` precision). Phase 5 (gate 11 rendering). Phase 8 (EXIF and overlay times). **DEF-08, DEF-04.**

---

## Moderate Pitfalls

### Converters silently drop content (DEF-12 class at intake)
**What goes wrong:**
- **DOCX:**
  - Footnotes, endnotes, comments, text boxes (`w:txbxContent`) and headers are not in `document.paragraphs`.
  - **Automatic list numbering is not in the text**, so a section map built from "10.3"-style numbers fails on Word documents.
  - Text inside tracked insertions (`w:ins`) may be skipped by naive run iteration. [REASONED; test it]
- **Email:**
  - Quoted reply chains attribute an earlier sender's text to the replier (`asserted_by` error, DEF-10).
  - Quoted-printable artefacts (`=20`, soft line breaks) appear if decoding is skipped.
  - Outlook `winmail.dat` (TNEF) hides attachments.
  - Wrong declared charsets.
- **XLSX inputs:**
  - No cached values when `data_only=True` on files saved by non-Excel tools.
  - Merged cells: only the top-left cell has the value.
  - Hidden sheets, rows and columns.
- **CSV:** UTF-16 or BOM, semicolon delimiters, decimal commas.
- **HTML:** readability-style extraction drops tables and sidebars that hold dates.

**Prevention:**
- Each converter emits a **content inventory**: counts of paragraphs, footnotes, comments, text boxes, tables, attachments and hidden sheets found vs emitted. Any non-emitted class becomes `partial: <reason>` in INDEX.
- Render DOCX list numbers from `numbering.xml`, or flag documents that use auto-numbering.
- Split email quoted blocks into their own perspective.

**Phase:** 2 (fixtures per trap).

### Media timing and keyframe selection
**What goes wrong:**
- Whisper segment and word timestamps drift, especially across long non-speech spans. [COMMUNITY: WhisperX paper and later work]
- Containers with non-zero `start_time` (DVR MPEG-TS) offset transcript times from keyframe times.
- Variable-frame-rate phone video makes `frame_index / fps` wrong.
- CCTV overlay clocks are often wrong (DVR drift, timezone), and the drift produces false or masked time conflicts.
- `select='gt(scene,0.3)'` is a reasonable default for edited video [COMMUNITY: ffmpeg docs suggest 0.3–0.5], but it suppresses almost everything on a **static** CCTV camera. Gradual smoke onset rarely crosses it, while IR day/night switches and auto-exposure jumps do.
- Handheld phone video crosses the threshold constantly, which yields thousands of frames that the agent cannot review: silent loss by volume.
- Proprietary DVR formats (`.dav`, raw `.264`) may not decode at all.

**Prevention:**
- Take frame times from `showinfo` `pts_time`. Normalise to the container start.
- Pick the threshold per video from the score distribution (log `scdet`/scene scores and use a percentile), keep the time floor, and **cap frames per minute**, recording how they were sampled.
- Precision-aware conflict tolerance: media offsets plus an assumed start time never feed a 0 s tolerance.
- Overlay OCR: crop the region, allow-list characters, use `--psm 7`, and enforce monotonic times.
- Mark undecodable DVR formats `unprocessed: codec`.

**Phase:** 8 (spike first). Phase 4 (conflict tolerance by precision).

### Conflict detection noise (DEF-04)
**What goes wrong:**
- Minute-precision vs second-precision times are compared as equals or as conflicts.
- 12 h vs 24 h vs "0218 hrs".
- Midnight rollover.
- DCS logs in UTC vs local narrative times (a 5 h 30 m IST offset).
- Event clustering merges "Valve 1" from two different units.

Candidate explosion pushes the agent toward bulk dismissal (Pitfall 12).

**Prevention:** Normalise times with precision and timezone per source. Make the tolerance precision-aware. Cluster on roster entity **plus** location. Cap candidates and rank them by severity.

**Phase:** 4.

### Windows paths and text encoding
**What goes wrong:**
- `MAX_PATH` (260) on deep `inputs/` trees, worse in OneDrive folders with long names.
- Reserved names (`CON`, `NUL`, `COM1`) and the characters `<>:"|?*` in slugs built from case titles or URLs (web snapshot folders).
- Case-only renames, and NFD (macOS) vs NFC file names, show up as "removed + new".
- The default `open()` encoding on Windows is not UTF-8, so Devanagari and curly quotes raise `UnicodeEncodeError`, and `--json` output to a cp1252 console fails.
- CRLF translation in text mode shifts char offsets.
- `shutil.which("tesseract")` misses installs that are not on PATH (common Windows installers).

**Prevention:**
- Always `encoding="utf-8"` and `newline="\n"` (enable ruff `PLW1514`). Reconfigure stdout to UTF-8 in the CLI.
- Store NFC case-relative POSIX paths and compare them case-insensitively on Windows and macOS.
- Slugify with a reserved-name check.
- `doctor` checks `LongPathsEnabled` and known install directories.

**Phase:** 1 (helpers, CI on Windows). 2 and 9 (slugs).

### Symlinks and junctions inside `inputs/`
**What goes wrong:** A symlink or junction in `inputs/` pointing outside the case folder makes `scan` read and hash arbitrary files (including other cases' evidence) or loop forever. `pathlib` glob symlink-following defaults changed across 3.10–3.14. [REASONED; verify per version]

**Prevention:** Walk with `os.walk(followlinks=False)` (or `os.scandir` with `is_symlink()` / `is_junction()` on 3.12+). List links as `ignored: link` in INDEX. Do the same for archive members: refuse `../` paths and absolute paths in zip entries (zip-slip).

**Phase:** 1 (scan). 2 (archives).

### Non-determinism breaks "no change writes nothing" and evals
**What goes wrong:**
- Set and dict iteration order, `Created At`/`Updated At` build times, and the zip timestamps in `docProps/core.xml` make every rebuild byte-different.
- Seeding the spot-check with `hash(str)` is randomised per process (PYTHONHASHSEED).
- Claim IDs depend on subagent finishing order.

**Prevention:** Decide "changed" from a canonical item-set fingerprint, never workbook bytes. Sort everything explicitly. Seed with `int(hashlib.sha256(...).hexdigest(), 16)`. Make eval comparisons order-independent.

**Phase:** 1 (helpers). 6 (no-op run test). 10 (evals).

### Licence traps in "obvious" dependencies
**What goes wrong:**
- PyMuPDF/`fitz` (AGPL) is the usual "faster PDF" suggestion.
- `extract-msg` is GPL (already optional, §18).
- pillow-heif binary wheels bundle third-party codecs whose licences need checking before going anywhere near core.
- ocrmypdf is MPL-2.0 and needs Ghostscript (AGPL) as an **external** tool.
- pyannote models are licence-gated.
- `python-magic` needs native libmagic on Windows. The design already has an extension fallback.

**Prevention:** Run a licence check in CI (`pip-licenses` against an allow-list) over core requirements. Detect external tools only, never bundle them. Add an ADR note that forbids AGPL imports in core.

**Phase:** 1 (CI check). 7 and 8 (re-check when adding extras).

---

## Minor Pitfalls

- **Excel `~$` owner files and `.tmp` leftovers** in `outputs/` or `inputs/`. Ignore them everywhere (Phase 1).
- **`epb init` in a synced folder.** See Security. (Phase 1)
- **Whisper language for code-switched speech.** Setting `hi` transcribes English loanwords into Devanagari. [COMMUNITY] Accept this but record it (Phase 8).
- **Tesseract language packs.** Order matters in `-l eng+hin+guj`. Each added language slows OCR and can lower accuracy. `doctor` must check `tesseract --list-langs` against `case.yaml: languages` and the `TESSDATA_PREFIX` location (Phase 7).
- **ocrmypdf mode flags.** `--skip-text`, `--redo-ocr` and `--force-ocr` are alternatives. `--force-ocr` rasterises and rewrites text pages, which destroys a good text layer. [OFFICIAL-DOC man page] Use per-page decisions, never `--force-ocr` on mixed PDFs (Phase 7).
- **pypdf AES-encrypted PDFs** need the `cryptography` extra, or opening fails with a dependency error. [REASONED] Have `doctor` report it, and mark such inputs `unprocessed: encrypted` (Phase 2).
- **Pillow re-save keeps GPS** if code passes `exif=im.getexif()` to preserve orientation or capture time. [VERIFIED-LOCAL] A default re-save drops EXIF and XMP in Pillow 13 (Phase 8).
- **Spot-check report shows raw context.** It is in `deid-scan` scope (§13.5). Make sure the map is applied *before* writing, not after (Phase 5).

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|---|---|---|---|
| Fuzzy (`rapidfuzz`) quote acceptance at ≥ 90 | Agents' near-quotes pass; fewer retries | Accepts inverted meaning (92.3 measured); DEF-01 and DEF-02 return | **Never** on the acceptance path; fine for suggestions and the held-back screen |
| `unicodedata.normalize("NFKC")` as "the" normaliser | One line handles ligatures and full-width digits | Changes meaning (`m²`→`m2`) and length (`…`→`...`); breaks char maps | **Never** whole-string; use explicit fold tables |
| Validate rows in memory instead of the saved file | Faster tests | Misses formula cells, serial dates, truncation and malformed XML (all measured) | Never as the only check; keep the on-disk validator as the gate |
| Re-convert sources whenever a converter improves | Better text "for free" | Previously verified quotes break, which triggers correction storms on imported items | Only via explicit `rebuild --from convert` with diff and correction review |
| Page-level OCR/ASR confidence | Simple to compute | Masks bad numeric spans inside good pages | MVP only if span-level confidence is a tracked follow-up |
| `dateutil.parser.parse` for dates | Handles every format | Fabricates day and month from today; month-first | **Never** |
| Allow-list a token to pass `deid-scan` | Unblocks the build | Real names ship | Only with a per-case justification shown in the run report |
| Windows CI only at Phase 10 | Faster early phases | Encoding, path, locking and symlink bugs accumulate for 9 phases | **Not recommended**; add a Windows core-tests job in Phase 1 |
| Bash-only `install-codex.sh` | Quick to write | No native Windows Codex install | Only alongside a Python or PowerShell installer |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|---|---|---|
| ProbeMatrix importer (SheetJS 0.18.5) | Assume typed cells are fine because Excel shows them correctly | Write every cell as a string (`data_type='s'`); importer does `String(v \|\| '')`, so `0`, `null` and formula cells become `''` [VERIFIED-LOCAL] |
| ProbeMatrix importer | Treat `Evidence ID` as a stable key | Only `Evidence Tag` survives; Related Evidence uses Tags (§8.4 items 1–2) |
| ProbeMatrix importer | Trust it to reject bad enums | It normalises or stores them raw; the builder's validator must be stricter (§8.4 items 3–4) |
| pypdf | Use `page_labels` as printed labels | Check the `/PageLabels` key first; fallback values are physical indices [VERIFIED-LOCAL] |
| pdfplumber | Default `extract_text()` on multi-column pages | Detect columns, crop per column, record extractor version, freeze segments [VERIFIED-LOCAL] |
| openpyxl (inputs) | `load_workbook(data_only=True)` and trust values | Detect missing cached values, merged cells and hidden sheets; read dates as text with precision |
| Tesseract | Average all TSV `conf` values | Use word-level rows only (`conf ≥ 0`), per anchor span |
| ocrmypdf | Expect confidences from its outputs | Sidecar is plain text [OFFICIAL-DOC man page]; get confidence from Tesseract TSV/hOCR (see Conflicts) |
| faster-whisper | Default settings on CCTV or ambient audio | VAD first, no transcript when no speech, `condition_on_previous_text=False`, hallucination screens, pinned language [COMMUNITY] |
| ffmpeg | Fixed `scene>0.3` and `-vsync` on new ffmpeg | Per-video threshold, `showinfo` times, frame caps; use `-fps_mode` (newer ffmpeg) |
| Claude Code skills | Rely on auto-trigger for sub-skills | Router-only trigger; trigger words first; `${CLAUDE_SKILL_DIR}` paths [OFFICIAL-DOC] |
| Codex skills | Commit a symlink and expect Windows to work | Installer copies `skills/` into `.agents/skills` or `~/.agents/skills`; name and description required [OFFICIAL-DOC] |
| Hugging Face model cache | Lazy download during a run | Explicit fetch in `doctor`; offline mode at runtime |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|---|---|---|---|
| Re-hashing every input every run | Slow `scan` on large media folders; OneDrive placeholders trigger mass downloads | Cache `(size, mtime, inode)` → hash; re-hash only on change | Folders with GBs of video, or cloud-placeholder folders |
| Verifier doing linear search per quote over whole source | Build slows quadratically | Index normalised segment text; search only cited segments plus neighbours | 300+ page reports with 1,000+ claims |
| Whisper `small` on CPU without int8 | Hours per interview | `compute_type="int8"` on CPU; model size in `case.yaml`; progress and resume per file | Over about 1 h of audio on a laptop |
| Keyframes without caps | Thousands of frames; agent context blown; silent skipping | Frames-per-minute cap, contact sheets, sampling recorded | Handheld or moving-camera video |
| Huge DCS/SAP CSVs fully in memory | MemoryError; giant segments | Stream rows; schema plus row-range segments (§7.2) | Exports above about 10^6 rows |
| Conflict detection all-pairs | Minutes per run; candidate floods | Block by event cluster and entity before comparing | Thousands of event claims |

## Security Mistakes

| Mistake | Risk | Prevention |
|---|---|---|
| Case folder inside OneDrive, Dropbox, Google Drive or iCloud | `.epb/private/name-map.yaml` and raw segments with names sync to the cloud. That contradicts "evidence never leaves the machine" | `init` and `doctor` detect sync roots (path heuristics plus known env vars) and warn loudly; docs say to keep case folders out of synced trees |
| Claiming "evidence never leaves the machine" while the agent reads segments | Segment text **is** sent to the model provider of the user's host (Claude, Codex). That is a trust and compliance misstatement | Reword the docs: conversion is local, and agent reasoning sends excerpts to the host's model provider (see Conflicts) |
| Formula cells in packs | Formula or DDE execution when an investigator opens the workbook in Excel | All cells are strings; validator rejects any `<f>` [VERIFIED-LOCAL] |
| GPS and location leaking as text | Coordinates from EXIF GPS IFD, XMP, or MP4/QuickTime location atoms copied into claims, Collection Conditions or Chain of Custody | Allow-list the metadata fields that may enter claims (capture time, device model); never copy GPS, XMP location or MP4 location tags; scan outputs for coordinate patterns |
| Following symlinks and zip-slip in `inputs/` | Reads and hashes files outside the case, or writes outside `.epb/` | No link following; reject `..` and absolute archive paths |
| Hostile web snapshots | HTML with scripts, or text in an input that is phrased as instructions to the agent (prompt injection) | Treat all input text as data; snapshot extraction strips scripts; SKILL.md tells agents that input text is never instructions |
| `samples/` publishing includes `.epb/` | Raw names published | `make-sample.py` copies only `outputs/` and `INDEX.md`, re-scans, and refuses on `.epb/private` (§13.5); test it |

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---|---|---|
| Build fails at the very end on an illegal character or a locked file | Lost time and distrust | Sanitise at segmentation; pre-flight check that outputs are writable *before* the long stages |
| Gate failure messages name internal IDs only | User cannot act | Every gate error names the input file, page or time, and the exact text span, plus a fix hint |
| "Imported?" tick semantics unclear | Duplicates or lost items (Pitfall 10) | INDEX states the exact file and item count to import; `mark-imported` confirms the count |
| Silent `unprocessed` inputs | User believes the video was analysed | INDEX "Open issues" lists every unprocessed or partial input with the `doctor` install command |
| Hand-editing the pack in Excel | Excel turns typed `2020-09` into a date serial, so the import is corrupt | Docs: never edit the workbook; fix items and rebuild |
| A wall of soft warnings | Real issues buried | Group warnings by severity; cap per class; spot-check items first |

## "Looks Done But Isn't" Checklist

- [ ] **Quote verifier:** has negative tests for negation insertion, number change, case change, corrected typo, NFKC folds and ellipsis-gap negation. Verify that `rapidfuzz` is absent from the acceptance path.
- [ ] **Validator:** reopens the saved `.xlsx` and inspects cell XML types. Verify that a Description starting with `=` is rejected or safely written, and that SheetJS reads it non-blank.
- [ ] **Page labels:** tested on a fixture where printed ≠ physical (unnumbered cover, roman front matter, restarting annex). The Hazira reference has printed = physical and cannot catch this.
- [ ] **Two-column PDFs:** a quote that wraps inside one column verifies, and a cross-column splice is rejected.
- [ ] **Indic text:** fixtures include real shaped Devanagari or Gujarati, not reportlab-generated logical-order text (reportlab does not shape).
- [ ] **De-identification:** the map-independent capitalised-token scan exists. Names are planted in headings, metadata, email headers, EXIF Artist, chat senders, possessives and initials forms.
- [ ] **Conclusions:** part-3 sentence→claim mapping is enforced. A paraphrased verdict and a causal clause in a timeline are planted and caught.
- [ ] **Crash-resume:** fault injection between writes; no ID reuse.
- [ ] **Windows:** CI runs core tests on Windows; `os.replace` retry is exercised with an open handle; no `os.kill(pid, 0)`.
- [ ] **No-op run:** a second run with no changes writes no workbook (fingerprint-based).
- [ ] **Import race:** a draft rewritten after first write requires a count confirmation at `mark-imported`.
- [ ] **Media:** a silent-audio fixture produces **no** transcript; a static-camera fixture still yields floor frames; frame caps are enforced.
- [ ] **Packaging:** fresh-machine install on macOS with the system Python older than 3.10 shows a friendly error; on Windows without symlink support, Codex lists the skills; SKILL.md lint passes.
- [ ] **Dates:** no `dateutil` import; year-only and month-only sources render unpadded.

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---|---|---|
| Invented or paraphrased quote shipped in an imported pack | HIGH (trust) | Correction item in next delta (§12.4); INDEX instructs manual deletion; add the failing pattern to the verifier negative corpus |
| Name leaked in an imported pack | HIGH | Correction item; owner deletes the original in ProbeMatrix by hand; add the variant to scan generation; re-scan all outputs |
| Draft rewritten after import (race) | MEDIUM | Diff the fingerprints of draft writes; emit the missing items in the next delta as new items |
| ID reuse after crash | MEDIUM | Detect duplicates across `outputs/`; renumber only *draft* items; correction items for imported ones |
| Converter upgrade changed segment text | MEDIUM | Pin back; or `rebuild --from convert` with diff; corrections only for genuinely changed anchors |
| Whole-file rejection on import | LOW | The validator should have caught it: add the case to the on-disk validator; rebuild |

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---|---|---|
| 1 Lenient verifier | 2 (3, 5) | Negative corpus passes; DEF-01 and DEF-02 regression quotes rejected; fuzzy absent from acceptance |
| 2 Unchecked quotation forms | 5 | Straight-quote and single-quote lint fires on synthetic Descriptions |
| 3 Wrong segment text | 2 (7) | Two-column, ligature, cid, legacy-font and fake-bold fixtures; extractor recorded; segments frozen |
| 4 Page citations | 2 (5) | Printed ≠ physical fixture; cross-page quote cites `pp.n–m`; `/PageLabels` absence handled |
| 5 Machine-text truth | 7, 8 (5) | Silent-audio fixture yields no transcript; span-level confidence present |
| 6 Conclusion leakage | 3, 5 (10) | Planted paraphrase, causal clause and combined heading caught; 0 leaks in evals |
| 7 De-id circularity | 4 (2, 7, 8, 9) | Planted names in every channel caught; map-independent scan in place |
| 8 Workbook coercion | 1 | On-disk validator; SheetJS-semantics tests; owner smoke import |
| 9 Comma-split | 1, 4, 5 | Regulatory and digit-grouping fixtures; roster rejects commas |
| 10 Import race | 6 | Rewrite-after-first-write scenario requires confirmation |
| 11 Crash, lock, atomic | 1 (3, 6) | Fault injection; Windows open-handle test; no `os.kill` |
| 12 Agent gate-gaming | 3, 4, 5 (10) | Unjournalled item rejected; dispositions report present |
| 13 Host and packaging | 1 (5, 8, 10) | SKILL.md lint; trigger evals; fresh installs on 3 hosts and Windows |
| 14 Dates | 2, 3, 5 (8) | No default-filling parser; precision fixtures; day-first sources |
| Converter silent loss | 2 | Content inventory counts match fixtures |
| Media timing and keyframes | 8 | Start-offset, VFR and static-CCTV fixtures |
| Conflict noise | 4 | Precision and timezone-aware tolerance tests |
| Windows paths and encoding | 1 | Windows CI; UTF-8 I/O lint |
| Licences | 1 (7, 8) | CI licence allow-list |

### Baseline coverage: DEF-01…DEF-18

| Defect | Primary pitfall(s) | Phase |
|---|---|---|
| DEF-01 invented quote | 1, 2, 3, 5 | 2, 5 |
| DEF-02 paraphrase / typo fix / cross-page | 1, 2, 4 | 2 |
| DEF-03 wrong pages | 3, 4 | 2, 5 |
| DEF-04 unflagged contradiction | 5, Conflict noise, Media timing, 14 | 4, 8 |
| DEF-05 author opinion | 6 | 5 |
| DEF-06 HFACS vocabulary | 12 (lint bypass via direct writes) | 5 |
| DEF-07 broken cross-refs | 10, 8 (Tags not IDs) | 5, 6 |
| DEF-08 fabricated date precision | 14, 8 | 2, 3, 5 |
| DEF-09 inconsistent type | 12 (rationale lint must run on every item) | 5 |
| DEF-10 who asserts what | Converter silent loss (email quoting) | 2, 4 |
| DEF-11 unverifiable online items | Security (hostile snapshots); 7 (bylines) | 9 |
| DEF-12 dropped findings | 3, 6 (over-blocking), Converter silent loss, 12 (mass omissions) | 2, 3, 5 |
| DEF-13 official answer leaking | 6 | 3, 5 |
| DEF-14 comma corruption | 9 | 1, 4 |
| DEF-15 redaction artefacts in quotes | 7 | 4 |
| DEF-16 Description length | 8 (32,767 truncation is the extreme case); length gate | 5 |
| DEF-17 meta-item about the report | 12 (agent adds it anyway) | 5 |
| DEF-18 mismatched IDs in source | 1 (never normalise IDs in quotes), 7 (roster aliases) | 4 |

---

## Conflicts with design (need owner decision)

The design wins until the owner decides otherwise. Each item below is a contradiction or a gap found while researching pitfalls. **K** marks items that concern the kickoff rather than the design.

1. **"Evidence never leaves the machine" (§2 goal 10, §4) vs agent inference.** Conversion is local, but extraction, authoring and reconciliation are done by the host's LLM. Segment text, including names, is therefore sent to the model provider (Anthropic for Claude Code and Cowork, OpenAI for Codex). Separately, case folders in OneDrive or Dropbox sync `.epb/private/`. *Recommendation:* reword the claim in README, INSTALL and AGENTS.md to "conversion is local; the agent sends excerpts to your host's model provider", and add a `doctor` and `init` warning for synced folders.

2. **Machine-derived text is labelled only when low-confidence (§14 soft warnings, §8.4 QA Status).** Whisper hallucinations and OCR misreads can have high confidence (Pitfall 5). *Recommendation:* always mark transcript- or OCR-derived quotes in the lead-in or Source ("machine transcript", "OCR text"), and keep "(…, low confidence)" for below-threshold spans.

3. **The citation format `p.<n>` (§8.4 Source) does not say whether `n` is printed or physical**, and §7.3 picks per page "when detectable". *Recommendation:* decide the scheme once per source. When physical indices are used, render them distinctly (for example `PDF p.<n>`). That changes the §8.4 Source format, so the owner must decide.

4. **Draft overwrite until marked imported (§4, §12.1) allows an import race** (Pitfall 10). *Recommendation:* record a per-write fingerprint, and have `mark-imported` confirm the item count or Tag range when the draft was rewritten after its first write. An alternative is to freeze a draft once it is older than a threshold.

5. **Codex on Windows (§5, §15.3).** `tools/install-codex.sh` does not run natively on Windows, and the committed `.agents/skills` symlink checks out as a text file without `core.symlinks`. *Recommendation:* ship `tools/install-codex.py` (cross-platform) that copies `skills/`, and keep `.sh` as a thin wrapper.

6. **CLI invocation (§15.2) `python3 skills/evidence-pack/scripts/epb.py`** is repo-relative and uses `python3`. That breaks with an installed plugin (cwd is the case folder), with the Windows Store stub, and with macOS system Python older than 3.10. *Recommendation:* use a host-resolved script path (`${CLAUDE_SKILL_DIR}` on Claude Code, the resolved skill directory on Codex), a version-guard shim, and a venv strategy (Pitfall 13).

7. **OCR confidence source (§7.2).** ocrmypdf is primary, but its sidecar output is plain text with no word confidences [OFFICIAL-DOC man page]. *Recommendation:* make Tesseract TSV/hOCR (on `pdftoppm` renders) the **confidence source of truth**, optionally still using ocrmypdf for the searchable PDF. Spike this in Phase 7.

8. **Dependency policy "pin minimum versions" (§18, kickoff §7)** lets pdfplumber, pdfminer.six and pypdf upgrades change segment text. *Recommendation:* segments are frozen per source (never re-converted unless `rebuild --from convert` is run explicitly), and optionally add upper bounds on the text-producing converters.

9. **K — Windows CI only in Phase 10 (kickoff §5).** *Recommendation:* a Windows core-tests job from Phase 1. Atomic writes, locking, encoding and paths are Phase 1 deliverables.

10. **K — First owner import at Phase 5 (kickoff §8).** The format assumptions (string cells, enums, 10-row metadata) are Phase 1 deliverables. *Recommendation:* an owner smoke import of a Phase 1 edge-case pack (with a `=`-leading Description written safely, `0`, a 19-digit ID and a `YYYY-MM` date).

11. **Dates the precision model cannot express (§8.4 Collection Date).** Fiscal years ("FY 2019-20"), ranges and "early 2019" have no rule. *Recommendation:* leave Collection Date blank, keep the exact text in the Description, and record `precision: range|fiscal_year` internally.

12. **Source ellipses vs quote ellipses (§8.2).** The design uses `…` for omissions, but sources also contain literal `…` or `...`. *Recommendation:* the verifier splits a quote on the agent's omission marker `…` *before* any normalisation. A source-literal ellipsis that the agent wants to keep inside a quote must be quoted exactly as it appears in the source (`...` or `…`) and matched literally. Gate 1 then treats `…` as an omission only where the raw source has no ellipsis at that position. (Builder-level detail, raised because it affects gate 1 semantics.)

---

## Sources

**Reproduced locally [VERIFIED-LOCAL]** (scripts in the session scratchpad, not committed):
- openpyxl 3.1.5 write → SheetJS `xlsx` 0.18.5 read (`/home/ashley/Eyekyam/Eyekyam-Apps/probematrix/node_modules/xlsx`, importer idiom from `server/services/evidenceExportService.ts` lines 257–410, read-only): formula cells → `null`; dates → serial; `0` → `''`; big ints rounded; `data_type='s'` → `inlineStr` read correctly; 32,767 truncation; `IllegalCharacterError` for C0; U+FFFE and lone surrogates → malformed XML.
- pypdf 6.21.0 `page_labels` fallback; pdfplumber 0.11.10 column interleaving and ligature expansion vs pypdf.
- `unicodedata` NFKC fold table; PyYAML implicit typing; `rapidfuzz.partial_ratio` scores; `dateutil` default filling; Pillow 13 EXIF and XMP re-save behaviour.

**Official docs [OFFICIAL-DOC]** (seam tier LOW: WebFetch, no curated provider):
- [Claude Code: Skills](https://code.claude.com/docs/en/skills): 1,536-char cap, 1% listing budget, least-invoked dropped first, compaction keeps the start of the skill, `${CLAUDE_SKILL_DIR}`/`${CLAUDE_PLUGIN_ROOT}`, malformed YAML loads with no fields, `claude plugin validate` / `claude plugin eval`.
- [Codex / ChatGPT: Build skills](https://learn.chatgpt.com/docs/build-skills) (redirected from developers.openai.com/codex/skills): `name` + `description` required, `.agents/skills` scan, symlinks followed, 2% / 8,000-char budget, `agents/openai.yaml`.
- [Python `os` docs](https://docs.python.org/3/library/os.html): `os.kill` on Windows (TerminateProcess for other signals).
- [ocrmypdf man page](https://manpages.ubuntu.com/manpages/lunar/man1/ocrmypdf.1.html): `--skip-text` / `--redo-ocr` / `--force-ocr`, plain-text `--sidecar`.
- [agentskills.io specification](https://agentskills.io/specification): `name` ≤ 64 chars, lowercase, digits and hyphens; `description` ≤ 1,024.

**Community [COMMUNITY], LOW, validate in spikes:**
- [faster-whisper issue #843 (near-silence and VAD)](https://github.com/SYSTRAN/faster-whisper/issues/843); [openai/whisper discussion #679 (hallucination)](https://github.com/openai/whisper/discussions/679); [Whisper hallucination fix (vad_filter, condition_on_previous_text)](https://localaimaster.com/blog/whisper-hallucination-fix).
- [WhisperX paper: timestamp drift in long-form audio](https://arxiv.org/abs/2303.00747v1).
- [Interspeech 2026: ASR script confusion in South Asian languages](https://aghaaliraza.com/publications/2026--Interspeech--Dissecting_ASR_Failures_in_Low-Resource_South_Asian_Languages.pdf); [Hindi code-switching transcription](https://convertaudiototext.com/blog/hindi-transcription-code-switching); [OpenAI forum: accented English detected as another language](https://community.openai.com/t/whisper-is-translating-my-audios-for-some-reason/86468).
- [Digital Orientalist: extracting Hindi text from PDFs (legacy fonts)](https://digitalorientalist.com/2025/12/02/why-extracting-hindi-text-from-pdfs-is-so-much-harder-than-english-and-how-you-can-do-it/).
- [GDELT: ffmpeg scene detection on static shots](https://blog.gdeltproject.org/using-ffmpegs-scene-detection-to-generate-a-visual-shot-summary-of-television-news/); [drop static video (surveillance thresholds)](https://alter.org.ua/docs/other/drop_static_video/).
- [Windows Python App Execution Alias stub](https://dev.to/abidcomsian/how-to-fix-python-was-not-found-error-on-windows-disable-app-execution-aliases-2mj6).
- [Git `core.symlinks` on Windows](https://github.com/git-for-windows/git/pull/220); [Snyk: symlinks are still scary](https://snyk.io/fr/blog/symlinks-are-still-scary/).
- [OpenAI community: ~/.agents/skills not discovered](https://community.openai.com/t/local-skills-in-agents-skills-are-no-longer-discovered-in-new-codex-sessions/1379522).
- [Cowork plugins guide](https://claude.com/docs/cowork/guide/plugins) (no sandbox capability details found; Cowork remains unverified, as design §18 says).

**Design and importer analysis [REASONED]:** design §2–§19; `docs/GSD-KICKOFF.md` §5–§8; ProbeMatrix importer source (read-only).

---
*Pitfalls research for: verbatim-evidence extraction agent plugin → ProbeMatrix `EVIDENCE_PACK_V2`*
*Researched: 2026-10-17*
