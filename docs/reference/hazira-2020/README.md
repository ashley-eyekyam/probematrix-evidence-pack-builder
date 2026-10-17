# Reference material: ONGC Hazira gas terminal fire, 24 Sep 2020

These two files are the study material behind §3 of
[`docs/design/2026-10-17-evidence-pack-builder-design.md`](../../design/2026-10-17-evidence-pack-builder-design.md).
They are here for reference and regression comparison only. They are **not** worked examples for agents to copy:
the plugin's worked examples are synthetic (design §16).

| File | What it is | SHA-256 |
|---|---|---|
| `PNGRB-Hazira-enquiry-report-2021-01-15.pdf` | PNGRB Enquiry Committee Report on the fire at ONGC Hazira Plant, dated 15 Jan 2021 (36 pages, text PDF). Published public record, included **unmodified**. Original source: https://www.pngrb.gov.in/pdf/ERDMP/Hazira_enquiry15012021.pdf | `59afa1d42bf4118add25c512c207cbec1e77f5c12d11bc439adb06000751d2ba` |
| `prototype-evidence-pack-hazira-2020.xlsx` | The 60-item `EVIDENCE_PACK_V2` workbook made from that report with the earlier internal prototype tool, as re-exported from ProbeMatrix on 17 Oct 2026. Personal names are de-identified to role labels (a zero-hit name scan was run before publishing). | `86267e4f2239baa417ddd3c7b82d95e9fc481f25bf24440419a3d7b21e74771e` |

## Notes

- The report is an official public document and names the individuals involved. It is reproduced as published. The
  plugin's "no personal names in shareable files" rule applies to what the plugin *produces*, not to unmodified
  public source records kept as reference.
- The prototype pack contains the defects catalogued in design §3 (D1–D18), including one quote not found in the
  report, off-by-one page citations and comma-bearing labels that the ProbeMatrix importer splits. It is kept
  as-is so those findings can be reproduced.
