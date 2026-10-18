# ProbeMatrix Evidence Pack Builder

An open-source agent plugin (Claude Code, Cowork, OpenAI Codex) that turns a folder of raw incident material
(investigation reports, scanned documents, witness statements, audio, video, photos, system exports) into a
citation-exact, de-identified evidence pack (`EVIDENCE_PACK_V2` Excel workbook) ready to import into ProbeMatrix.
It keeps the pack current as new evidence arrives.

Status: Phase 1 (foundations) in progress: guided setup, case folders and the importer-exact workbook format. See the user manual in docs/USER-MANUAL.md.

**Privacy:** conversion runs on your computer, and the excerpts the agent reads go to your AI host's model provider.
Keep case folders out of sync folders such as OneDrive, Dropbox, iCloud Drive and Google Drive.

- User manual: [`docs/USER-MANUAL.md`](docs/USER-MANUAL.md)
- Design: [`docs/design/2026-10-17-evidence-pack-builder-design.md`](docs/design/2026-10-17-evidence-pack-builder-design.md)
- GSD kickoff prompt for development: [`docs/GSD-KICKOFF.md`](docs/GSD-KICKOFF.md)
- Study material behind the design: [`docs/reference/hazira-2020/`](docs/reference/hazira-2020/README.md)

## Licence

MIT, see [`LICENSE`](LICENSE). The bundled official report in `docs/reference/` remains the publisher's document
and is included unmodified for reference.
