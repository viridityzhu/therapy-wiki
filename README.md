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

## 🧱 Architecture

Three-layer structure, following the [LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#file-llm-wiki-md) principle:

| Layer          | Role                                                                          | Mutability             |
| -------------- | ----------------------------------------------------------------------------- | ---------------------- |
| `raw/`         | Source recordings copied in at ingest time                                    | Immutable              |
| `artifacts/`   | Transcripts, diarization, speaker maps, review notes, deterministic summaries | Machine-owned          |
| `wiki/`        | The long-term, human-curated knowledge base                                   | Incrementally compiled |

Everything is plain Markdown and JSON — easy for both humans and AI to read, edit, diff, and grep.

## 🔄 Built-in workflow

1. **Ingest** — copy audio into `raw/`, transcribe, diarize, generate review artifacts.
2. **Review** — fix transcript and speaker map by hand where it matters.
3. **Rebuild** — recompile the affected session's wiki page.
4. **Report** — generate a single-session review or a cross-session longitudinal report.
5. **Discuss** — ask a persona-scoped question; optionally file the insight back into the wiki.

All five steps are triggered from a single CLI (`./therapy`) plus a handful of Codex skills.

## 🎭 Personas

Different lenses on the same material. Each persona is backed by its own method card and skill, so the reading actually changes — structure, questions, attention, and output frame all shift.

| Persona          | Reads material through…                                                |
| ---------------- | ---------------------------------------------------------------------- |
| `therapist`      | process, affect, defense, relational stance, next-step exploration     |
| `supervisor`     | intervention choices, pacing, alliance, missed opportunities           |
| `psychologist`   | formulation, mechanism, competing explanations, longitudinal patterns  |
| `intp-lens`      | structure, loops, contradictions, hidden rules                         |
| `close-friend`   | direct reality check — kept **separate** from formal formulation       |

Need a new persona? Just ask the agent to add one.

## 📄 Reports

- **Single-session review** — one session, one structured pass.
- **Longitudinal report** — synthesis across every session in the wiki.

Reports are written in Chinese by default (tell your agent to change this behavior if needed), stay source-grounded, and cite `session_id + timestamp` for every claim.

## 🚀 Quick start

### For humans

1. `git clone` this repo.
2. Open it in Claude Code or Codex.
3. Ask the agent to set up the environment, install the skills, and run the first ingest.

That's it. The agent knows how to read the section below.

### For the agent

<details>
<summary>Click to expand: setup, skills install, usage</summary>

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

For fresh-machine STT + diarization setup (mlx-whisper, pyannote, etc.) see [`schema/setup.md`](./schema/setup.md); full CLI behavior lives in [`schema/cli.md`](./schema/cli.md); wiki maintenance rules in [`schema/wiki-maintainer.md`](./schema/wiki-maintainer.md).

</details>

## 🛠️ Typical usage

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

## 📦 What's in the repo

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
