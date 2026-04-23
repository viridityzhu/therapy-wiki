# CLI Contract

## `therapy ingest`

- Input: one audio file or a directory of audio files.
- Output:
  - copies raw audio into `raw/sessions/<session-id>/`
  - writes machine artifacts into `artifacts/sessions/<session-id>/`
  - rebuilds the wiki
- `--refresh <session-id>` rebuilds one session from existing artifacts and manual edits.

## `therapy report`

- Builds:
  - a packet file with persona instructions and evidence
  - a structured draft report
- Output directory: `outputs/reports/`
- Intended use: compile evidence first, then let Codex finish the reasoning-heavy final report.

## `therapy discuss`

- Builds a discussion packet and a deterministic draft.
- `--file-back` writes a persona-scoped wiki note when the result is worth keeping.

## `therapy lint`

- Runs lightweight structural checks over the wiki.
- Writes a report under `outputs/lint/`.

