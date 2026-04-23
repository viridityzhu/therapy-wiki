---
name: therapy-discuss
description: Discuss therapy material or adjacent personal psychology archive material from the local wiki through a selected persona, compile an evidence packet, and optionally file durable insights back into persona-specific wiki notes.
---

# Therapy Discuss

Use this skill when the user wants to talk through a question using the therapy wiki as source material.

## Workflow

1. Run `therapy discuss --persona <persona> --scope <scope> --question "<text>" [--file-back]`.
2. Read the persona card in `schema/personas/<persona>.md`.
3. Read enough session pages, summaries, and evidence snippets to answer from material rather than from general vibes.
4. Answer in the requested persona voice while staying source-grounded.
5. If the result is durable and the user wants it preserved, use `--file-back` or write an equivalent persona-scoped note.

## What counts as a good discussion

A good discussion answer should:

- feel like a real perspective shift, not the same answer with a different tone
- stay anchored in concrete evidence
- separate what is clear, what is plausible, and what is still guesswork
- help the user see something that was harder to see before

## What this skill is for

This is the skill for questions like:

- “What am I missing here?”
- “What pattern keeps repeating?”
- “What would a supervisor notice that I wouldn’t?”
- “Can you map the structure here rather than just summarize it?”
- “Please give me the blunt close-friend version.”

## Recommended answer shape

1. Answer the user’s actual question first.
2. Support the answer with the most relevant evidence cluster.
3. Mark uncertainty clearly.
4. Add a short “what this changes” or “what to watch next” section when useful.

## File-back rule

Use file-back only when the discussion produced something durable:

- a pattern worth remembering
- a useful reframing
- a recurring contradiction
- a question that should stay live across sessions

## Guardrails

- Always separate what is known from what is guessed.
- Cite session/timestamp.
- `close-friend` notes must remain separate from formal formulation pages.
- Do not use persona style as an excuse to become careless with evidence.
- If the evidence packet is thin, narrow the answer rather than pretending to know more.
