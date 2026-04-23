# Therapy Atlas Workspace

This repository implements a local-first, agentic wiki workflow for therapy recordings, voice notes, and other psychologically meaningful personal archives.

## Architecture

There are three layers:

- `raw/`: immutable source recordings copied into the workspace during ingest.
- `artifacts/`: machine-generated intermediate files such as transcripts, diarization results, speaker maps, review notes, and deterministic summaries.
- `wiki/`: the persistent Markdown wiki that Codex maintains over time.

The goal is not ad-hoc retrieval from raw recordings on every query. The goal is to incrementally compile a persistent wiki that gets richer over time.

## Core Commands

- `therapy ingest <file-or-dir>`: ingest new audio into `raw/`, generate artifacts, and rebuild the wiki.
- `therapy ingest --refresh <session-id>`: recompile one session after editing `transcript.edited.md` or `speaker_map.json`.
- `therapy report latest|session <id>|all --persona therapist|supervisor|psychologist`: compile a report packet and draft under `outputs/reports/`.
- `therapy discuss --persona <persona> --scope latest|session <id>|all --question "<text>" [--file-back]`: compile a discussion packet and optional persona-specific note.
- `therapy lint`: run wiki health checks and write a lint report.

## Operating Rules

- Keep raw recordings immutable after ingest.
- Prefer editing `artifacts/sessions/<id>/transcript.edited.md` and `speaker_map.json` instead of rewriting `transcript.raw.json`.
- Rebuild the wiki after any manual artifact correction with `therapy ingest --refresh <session-id>`.
- Use persona-specific file-back only for material that should persist as a long-term note. `close-friend` notes must remain persona-scoped and must not be merged directly into `wiki/formulation/current.md`.
- Formal reports and serious interpretations must remain source-grounded and cite `session_id + timestamp`.

## Schema

- `schema/wiki-maintainer.md`: workflow and update rules for Codex.
- `schema/cli.md`: command behavior and expected outputs.
- `schema/setup.md`: runtime notes for `mlx-whisper`, `pyannote`, and local Python architecture.
- `schema/personas/`: persona cards that guide report/discussion style.
- `schema/report-templates/`: report structures for single-session and longitudinal outputs.

## Skills

Project-local skills live under `skills/`. Use `scripts/install_skills.py` to copy them into `~/.codex/skills/` when you want them available globally in Codex.
