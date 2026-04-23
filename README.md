<div align="center">

# 📚 Therapy Wiki

### *A local-first agent harness for compiling therapy recordings, voice notes, chats, and journals into a maintained psychology wiki — inside [Codex](https://openai.com/codex) or [Claude Code](https://www.anthropic.com/claude-code).*

[中文说明](./README.zh-CN.md) · [Setup](./schema/setup.md) · [Wiki rules](./schema/wiki-maintainer.md) · [CLI spec](./schema/cli.md)

</div>

---

Therapy Wiki is a repository you open inside an agent runtime — the repo itself is the harness. Point it at therapy recordings, voice memos, chat logs, or journals, and it builds a durable, source-grounded psychology wiki you can keep growing for years.

> The job is to keep compiling a better wiki over time,
> so you stop re-deriving insight from scratch on every new conversation.

## ✨ Why it exists

Personal therapy material tends to rot in three ways:

- 🎙️ **Recordings pile up** and never get re-listened to.
- 💬 **Chat context evaporates** — every new session with an LLM starts from zero.
- 📝 **Insights stay disposable** — no lens, persona, or thread survives past one conversation.

Therapy Wiki fixes those three with a deliberately small workflow: a file tree plus a set of Codex / Claude AI agent skills. There's no hosted service, no web UI, no vector database, no backend to stand up (all of which have felt obsolete since the AI-agent era kicked in these past few months! 😱). If you already use Codex or Claude Code, you already have the interface.

## 👤 Who this fits

- People with a growing archive of voice memos, journals, or self-observation material.
- People doing online therapy who keep recordings or notes.
- People who want repeated analysis of the same material through different lenses.
- People who want an LLM workflow without standing up more infrastructure.
- People who want their personal archive to become a maintained knowledge base.
- People who are keen on digitalizing themselves / becoming Uploaded Intelligence.

## 🧩 What it does

### Compile recordings into a long-term wiki

Drop audio into the repo, and the pipeline transcribes, diarizes, and reviews it, then lands the result as a session page in a persistent Markdown wiki that cross-links with your existing themes and patterns. Manual corrections (transcript edits, speaker labels) are first-class; a `refresh` step recompiles just the affected session. Five operational stages — **ingest → review → rebuild → report → discuss** — are all driven by a single `./therapy` CLI plus a small set of Codex / Claude skills.

### Read the same material through different lenses

Each persona is backed by its own method card and skill, so the reading actually changes — structure, questions, attention, and output frame all shift.

| Persona          | Reads material through…                                                |
| ---------------- | ---------------------------------------------------------------------- |
| `therapist`      | process, affect, defense, relational stance, next-step exploration     |
| `supervisor`     | intervention choices, pacing, alliance, missed opportunities           |
| `psychologist`   | formulation, mechanism, competing explanations, longitudinal patterns  |
| `intp-lens`      | structure, loops, contradictions, hidden rules                         |
| `close-friend`   | direct reality check — kept **separate** from formal formulation       |

Need a new persona? Just ask the agent to add one.

### Produce reports and discussions

- **Single-session review** — one session, one structured pass.
- **Longitudinal report** — synthesis across every session in the wiki.
- **Persona-scoped discussion** — ask a focused question through one lens, optionally `--file-back` the durable conclusions into persona-specific wiki notes.

Reports are written in Chinese by default (tell your agent to change this), stay source-grounded, and cite `session_id + timestamp` for every claim.

## 🚀 Getting started

### Install

1. `git clone` this repo.
2. Open it in Claude Code or Codex.
3. Ask the agent to set up the environment, install the skills, and run the first ingest.

The agent can read the manual steps below.

<details>
<summary>Manual install steps</summary>

```bash
# 1. System prerequisites
brew install ffmpeg          # macOS; use your package manager elsewhere

# 2. Clone and enter
git clone <this-repo>
cd my-therapist

# 3. Install project-local skills into ~/.codex/skills/
python3 scripts/install_skills.py

# 4. Ingest one file or a whole folder
./therapy ingest ~/path/to/new-session.m4a
```

For fresh-machine STT + diarization setup (`mlx-whisper`, `pyannote`, etc.), see [schema/setup.md](./schema/setup.md); full CLI behavior lives in [schema/cli.md](./schema/cli.md); wiki maintenance rules in [schema/wiki-maintainer.md](./schema/wiki-maintainer.md).

</details>

### Typical usage

Day-to-day, you don't need to memorize any CLI flags. Open Codex or Claude Code inside the repo and tell the agent three things in plain language: **scope** (which material) × **persona** (which lens) × **task** (what to do). The agent picks the right skill and CLI call itself.

**Scope options**

- `latest` — the most recent session
- `session <id>` — one specific session (e.g. `session 2025-04-20`)
- `all` — every session currently in the wiki

**Persona options** — same as the table above: `therapist` / `supervisor` / `psychologist` / `intp-lens` / `close-friend`.

**Task options**

- **Ingest** — pull new audio into `raw/` + `artifacts/` + `wiki/`
- **Refresh** — after you've manually edited `transcript.edited.md` or `speaker_map.json`, recompile that session
- **Single-session review** — a structured pass on one session
- **Longitudinal report** — synthesis across sessions
- **Discuss a specific question** — ask through a chosen persona and get a structured answer
- **File back** — persist a durable conclusion from a discussion into that persona's wiki notes
- **Lint** — structural health check over the wiki

**Example chat prompts**

> "Ingest `~/voice/2025-04-20.m4a`, then write a single-session review through the `therapist` persona."

> "Looking at `all` sessions through the `psychologist` lens, produce a longitudinal report."

> "Through the `close-friend` persona, discuss the `latest` session: what am I still refusing to admit? File back anything worth keeping."

> "I just finished editing `transcript.edited.md` for session `2025-04-20`. Refresh that session."

<details>
<summary>Equivalent <code>./therapy</code> commands (for the agent)</summary>

**After a new session**

```bash
./therapy ingest ~/path/to/new-session.m4a
./therapy report latest --persona therapist
```

**Cross-session synthesis**

```bash
./therapy report all --persona psychologist
./therapy discuss --persona supervisor --scope all \
  --question "Which patterns are actually stable, and which are only recent?"
```

**A blunter read**

```bash
./therapy discuss --persona close-friend --scope latest \
  --question "What am I still refusing to admit here?" --file-back
```

**After manual transcript / speaker-map fixes**

```bash
./therapy ingest --refresh <session-id>
```

</details>

## 🔬 Under the hood

### Three-layer architecture

Following the [LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#file-llm-wiki-md) principle:

| Layer          | Role                                                                          | Mutability             |
| -------------- | ----------------------------------------------------------------------------- | ---------------------- |
| `raw/`         | Source recordings copied in at ingest time                                    | Immutable              |
| `artifacts/`   | Transcripts, diarization, speaker maps, review notes, deterministic summaries | Machine-owned          |
| `wiki/`        | The long-term, human-curated knowledge base                                   | Incrementally compiled |

Everything is plain Markdown and JSON — easy for both humans and AI to read, edit, diff, and grep.

### The ingest pipeline

The `ingest` step is a deterministic, local-first pipeline built on open-source models. No cloud STT, no cloud LLM, no per-call API spend.

```text
audio
  ├─▶ prepared.wav                             (ffmpeg: 16 kHz mono wav)
  ├─▶ transcript.raw.json                      (STT: MLX Whisper*)
  ├─▶ diarization.json                         (diarization: pyannote.audio)
  ├─▶ speaker_map.json + transcript.turns.json (deterministic alignment + labeling)
  ├─▶ summary.json + review.md                 (deterministic theme / pattern pass)
  └─▶ wiki/sessions/<id>.md                    (deterministic wiki compiler)
```

Stages and the open-source models they use:

| Stage | Artifact | Backend | License |
| --- | --- | --- | --- |
| Audio prep | `prepared.wav` | [`ffmpeg`](https://ffmpeg.org/) | LGPL |
| Speech-to-text | `transcript.raw.json` | [`mlx-whisper`](https://github.com/ml-explore/mlx-examples/tree/main/whisper) running `whisper-large-v3-turbo` (fast) or `whisper-large-v3` (accurate) | MIT (OpenAI Whisper weights) |
| Speaker diarization | `diarization.json` | [`pyannote.audio`](https://github.com/pyannote/pyannote-audio) with `speaker-diarization-community-1` (fallback `speaker-diarization-3.1`) | MIT code, gated weights on Hugging Face |
| Speaker alignment + labeling | `speaker_map.json`, `transcript.turns.json` | pure-Python heuristics — see [src/therapy_wiki/speaker_map.py](src/therapy_wiki/speaker_map.py) | — |
| Session summary + review notes | `summary.json`, `review.md` | pure-Python theme / pattern extractor — see [src/therapy_wiki/summarize.py](src/therapy_wiki/summarize.py) | — |
| Wiki compilation | `wiki/sessions/<id>.md`, `wiki/index.md`, `wiki/log.md` | [src/therapy_wiki/wiki.py](src/therapy_wiki/wiki.py) | — |

\*On macOS Intel / Linux, `mlx-whisper` isn't available; see [schema/setup.md](./schema/setup.md) for STT fallbacks.

The only place where a frontier LLM does heavy lifting is **Report** and **Discuss**, and even there it only ever reads the already-compiled wiki — not the raw audio. Everything above is local, reproducible, and runs offline once model weights are cached.

### Repo layout

```text
src/therapy_wiki/      Python CLI and workflow logic
skills/                Codex skills: ingest, report, discuss, personas
schema/                Persona cards, report templates, wiki rules, runtime notes
tests/                 Workflow tests with fake backends
therapy                Repo-local CLI launcher
```

Created at runtime and git-ignored:

```text
raw/                   Immutable source recordings
artifacts/             Transcripts, diarization, summaries, review files
wiki/                  Persistent Markdown knowledge base
outputs/               Generated reports and lint reports
```

Bundled skills: `therapy-ingest` · `therapy-report` · `therapy-discuss` · `therapy-therapist` · `therapy-supervisor` · `therapy-psychologist` · `therapy-intp-lens` · `therapy-close-friend`

The current ingest path is audio-first, but the structure is deliberately broader than therapy alone.
