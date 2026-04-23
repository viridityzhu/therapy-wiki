# Wiki Maintainer Schema

This file tells Codex how to act as the maintainer of the therapy wiki and adjacent personal psychology archive.

## Core idea

Do not treat `raw/` as a retrieval pool that gets re-read from scratch every time.

Treat the wiki as a persistent, compounding artifact:

- new sessions should update existing pages, not only create new files
- useful answers should be filed back into the wiki when they add durable value
- contradictions, stale assumptions, and missing cross-links should be surfaced during linting

The clearest built-in workflow is therapy-session review, but the same maintenance logic also applies to voice notes and other psychologically meaningful personal material.

## Source of truth

- `raw/` is immutable after ingest
- `artifacts/` is the machine-readable working layer
- `wiki/` is the human-readable long-term layer

If a transcript is manually corrected, prefer `transcript.edited.md` over `transcript.turns.md` in downstream reasoning.

## Ingest workflow

1. Run `therapy ingest <file-or-dir>`.
2. Inspect `artifacts/sessions/<id>/review.md`, `summary.md`, `speaker_map.json`, and `transcript.turns.md`.
3. If speaker labels or obvious transcription errors are wrong, edit `speaker_map.json` and/or `transcript.edited.md`.
4. Run `therapy ingest --refresh <session-id>`.
5. Read the updated `wiki/sessions/<id>.md` and any touched long-term pages.

## Report workflow

1. Run `therapy report ...` to generate a report packet and draft.
2. Read the relevant persona card.
3. Use the generated packet plus the underlying wiki pages to write the final report.
4. If the report produces durable insights, update:
   - `wiki/formulation/current.md`
   - relevant `wiki/themes/*.md`
   - relevant `wiki/patterns/*.md`

## Discussion workflow

1. Run `therapy discuss ...`.
2. Keep the answer source-grounded and cite session/timestamp.
3. Only use `--file-back` for durable notes worth keeping in the wiki.
4. `close-friend` notes must stay under `wiki/notes/personas/close-friend/` or clearly carry `persona: close-friend`.

## Lint workflow

Periodically run `therapy lint` and inspect:

- orphan pages
- sessions still marked `needs_review`
- unresolved `UNKNOWN` speakers
- weak or missing open questions
- pages that should receive new cross-links

## Writing constraints

- Distinguish facts, interpretations, hypotheses, and open questions.
- Do not make unsupported diagnoses.
- Do not let a single session outweigh longitudinal evidence without saying so.
- Prefer linking to existing pages over creating new ones unless the concept truly needs its own page.
