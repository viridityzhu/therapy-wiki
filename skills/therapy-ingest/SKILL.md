---
name: therapy-ingest
description: Ingest therapy recordings or other personal audio into the local therapy wiki workspace, run transcription and diarization, inspect review artifacts, and rebuild the long-term wiki after transcript or speaker-map corrections.
---

# Therapy Ingest

Use this skill when the user wants to:

- import one or more session audio files
- refresh a session after editing `transcript.edited.md` or `speaker_map.json`
- inspect ingest artifacts or wiki changes

## Workflow

1. Run `therapy ingest <file-or-dir>` or `therapy ingest --refresh <session-id>`.
2. Inspect the whole ingest bundle, not just whether the command succeeded:
   - `artifacts/sessions/<id>/review.md`
   - `artifacts/sessions/<id>/summary.md`
   - `artifacts/sessions/<id>/speaker_map.json`
   - `artifacts/sessions/<id>/transcript.turns.md`
   - `wiki/sessions/<id>.md`
3. Treat ingest as the first compilation pass, not the final truth.
4. Check artifact quality in this order:
   - did diarization run and produce a believable two-speaker split
   - does the speaker map look plausible for `me` vs `therapist`
   - are there transcript distortions that would poison downstream interpretation
   - does the deterministic session summary roughly match the transcript
   - did the session wiki page land on coherent themes and patterns
5. If diarization or transcription is weak, edit `speaker_map.json` or `transcript.edited.md`, then re-run refresh.
6. After refresh, summarize:
   - what changed in the session page
   - what long-term pages were updated
   - what still needs human review

## What good ingest review looks like

A good ingest review should tell the user:

- whether the speaker map looks believable
- whether there are obvious transcript distortions that will poison later reports
- what themes/patterns the deterministic pass surfaced
- whether the wiki update looks coherent or needs manual correction

## What to look for in practice

### Transcript quality

- repeated obvious homophone errors
- missing speaker turns
- emotionally important passages flattened into generic wording
- long unintelligible stretches that should be marked for manual review

### Speaker quality

- whether the “me” / “therapist” guess makes sense globally
- whether the same speaker identity suddenly flips in the middle of a stable exchange
- whether emotionally important turns were assigned to the wrong person

### Wiki quality

- whether the session page reflects the actual process rather than a random topic bag
- whether longitudinal pages were updated in a way that fits the evidence
- whether any new theme or pattern page feels overclaimed relative to one session

## Important mindset

This skill is not only for “did the command run”.

It is for turning raw recordings into a trustworthy starting point for:

- single-session review
- longitudinal comparison
- persona-based discussion
- future file-back into the personal wiki

## Guardrails

- Treat `raw/` as immutable once a session is ingested.
- Do not silently ignore diarization failures.
- Prefer artifact quality assessment over speculative interpretation during ingest review.
- If artifact quality is weak, say that clearly before producing any confident psychological read.
