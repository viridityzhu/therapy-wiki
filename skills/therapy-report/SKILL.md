---
name: therapy-report
description: Generate professional Chinese therapy review reports and longitudinal psychology syntheses from the local wiki, using persona-specific report frames, evidence packets, and durable file-back updates.
---

# Therapy Report

Use this skill when the user wants:

- a single-session report
- a longitudinal report across multiple sessions
- a formal therapist / supervisor / psychologist framing

## Workflow

1. Run `therapy report latest|session <id>|all --persona <persona>`.
2. Read:
   - the generated report packet
   - the corresponding persona card in `schema/personas/`
   - the matching report template in `schema/report-templates/`
3. Read the relevant session pages and formulation pages, not only the packet.
4. Reconstruct an evidence hierarchy:
   - what is directly observed
   - what is a strong interpretation
   - what remains a working hypothesis
   - what still needs more material
5. Write the final report in professional Chinese.
6. If the report produces durable insight, update:
   - `wiki/formulation/current.md`
   - relevant `wiki/themes/*.md`
   - relevant `wiki/patterns/*.md`

## What a good report should do

A good report does more than summarize content. It should:

- reconstruct the psychological process
- surface the most important working hypotheses
- show what is stable versus what is newly emerging
- make uncertainty explicit
- remain reusable when the user comes back months later

## What a strong report should feel like

- It should feel psychologically literate without sounding inflated.
- It should help the user think better, not just feel summarized.
- It should preserve contradictions instead of forcing everything into one neat story.
- It should make clear what ought to be carried into future sessions.

## Scope-specific emphasis

### Single-session report

Prioritize:

- process and turning points inside the session
- the emotional and relational live wire of the conversation
- what most deserves to be carried into the next session

### Longitudinal report

Prioritize:

- repeated themes
- recurring mechanisms
- changes over time
- what is still ambiguous despite repeated material

## Writing checklist

Before finishing, verify that the report:

- clearly distinguishes facts, interpretations, hypotheses, and open questions
- cites `session_id + timestamp` for every important claim
- includes at least one explicit uncertainty statement
- avoids generic self-help phrasing
- sounds like a reusable clinical or supervisory document, not a casual chat reply

## Writing standard

- professional Chinese
- psychologically serious, but still readable
- evidence-first
- no fake certainty
- no generic self-help filler

## Guardrails

- Distinguish facts, interpretations, hypotheses, and open questions.
- Cite `session_id + timestamp` for every important claim.
- Do not use `close-friend` or `intp-lens` as a formal report persona.
- If the evidence is weak, say so plainly instead of manufacturing coherence.
- Do not let persona style override report structure.
