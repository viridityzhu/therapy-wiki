"""Wiki compilation helpers."""

from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List

from .constants import PERSONA_FILEBACK_ROOT, WIKI_ROOT
from .frontmatter import write_markdown
from .models import SessionRecord, TranscriptSegment
from .repository import collect_session_records, load_summary_payload, load_turns_payload
from .runtime_log import cli_log
from .summarize import render_summary_markdown
from .utils import now_iso, short_ts, slugify, top_keywords


def write_session_artifacts(
    root: Path,
    record: SessionRecord,
    turns: List[TranscriptSegment],
    summary: Dict,
    review_lines: List[str],
) -> None:
    _write_turns_markdown(record, turns)
    (record.artifact_dir / "summary.md").write_text(
        render_summary_markdown(summary),
        encoding="utf-8",
    )
    (record.artifact_dir / "review.md").write_text("\n".join(review_lines).strip() + "\n", encoding="utf-8")
    edited_path = record.artifact_dir / "transcript.edited.md"
    if not edited_path.exists():
        edited_path.write_text(
            "# Edited Transcript\n\n"
            "请在需要时修改说话人、错字、断句。保存后运行 `therapy ingest --refresh <session-id>` 重新编译。\n\n"
            + (record.artifact_dir / "transcript.turns.md").read_text(encoding="utf-8"),
            encoding="utf-8",
        )


def rebuild_wiki(root: Path) -> None:
    records = collect_session_records(root)
    cli_log(f"Wiki | rebuilding pages from {len(records)} session(s)")
    theme_pages: Dict[str, List] = {}
    pattern_pages: Dict[str, List] = {}
    all_themes = Counter()
    all_patterns = Counter()
    open_questions: List[str] = []

    for record in records:
        summary = load_summary_payload(record)
        turns = load_turns_payload(record)
        _write_session_page(root, record, summary, turns)
        for theme in summary.get("candidate_themes", []):
            all_themes[theme] += 1
            theme_pages.setdefault(theme, []).append((record.session_id, summary))
        for pattern in summary.get("candidate_patterns", []):
            all_patterns[pattern] += 1
            pattern_pages.setdefault(pattern, []).append((record.session_id, summary))
        for question in summary.get("question_turns", [])[:3]:
            open_questions.append(
                f"- [[sessions/{record.session_id}]] [{short_ts(question['start'])}] {question['speaker']}: {question['text']}"
            )

    _write_home_page(root, records)
    _write_timeline_page(root, records)
    _write_questions_page(root, open_questions)
    _write_formulation_page(root, records, all_themes, all_patterns)
    _write_participant_pages(root, records)
    _write_theme_pages(root, theme_pages)
    _write_pattern_pages(root, pattern_pages)
    _write_index_page(root, records, theme_pages, pattern_pages)
    cli_log(
        f"Wiki | rebuild complete | themes={len(theme_pages)} | patterns={len(pattern_pages)} | sessions={len(records)}"
    )


def append_log(root: Path, title: str, detail: str) -> None:
    log_path = root / WIKI_ROOT / "log.md"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    entry = f"## [{now_iso()}] {title}\n\n{detail.strip()}\n\n"
    existing = log_path.read_text(encoding="utf-8") if log_path.exists() else "# Log\n\n"
    log_path.write_text(existing + entry, encoding="utf-8")


def write_persona_note(root: Path, persona: str, title: str, body: str) -> Path:
    note_dir = root / PERSONA_FILEBACK_ROOT / persona
    note_dir.mkdir(parents=True, exist_ok=True)
    slug = "-".join(top_keywords(title, limit=4)) or slugify(title) or "note"
    stamp = now_iso().replace(":", "-")
    path = note_dir / f"{stamp}_{slug}.md"
    write_markdown(
        path,
        {
            "type": "persona-note",
            "persona": persona,
            "created_at": now_iso(),
        },
        body,
    )
    return path


def _write_turns_markdown(record: SessionRecord, turns: Iterable[TranscriptSegment]) -> None:
    lines = ["# Transcript Turns", ""]
    for turn in turns:
        speaker = _display_speaker(turn.speaker or "UNKNOWN")
        lines.append(f"- [{short_ts(turn.start)}-{short_ts(turn.end)}] **{speaker}**: {turn.text}")
    (record.artifact_dir / "transcript.turns.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_session_page(root: Path, record: SessionRecord, summary: Dict, turns: List[Dict]) -> None:
    frontmatter = {
        "type": "session",
        "session_id": record.session_id,
        "session_date": record.session_date,
        "session_number": record.session_number,
        "review_status": record.review_status,
        "keywords": summary.get("keywords", []),
        "themes": summary.get("candidate_themes", []),
        "patterns": summary.get("candidate_patterns", []),
    }
    lines = [
        f"# Session {record.session_id}",
        "",
        "## Snapshot",
        "",
        f"- Date: {record.session_date}",
        f"- Session number: {record.session_number}",
        f"- Duration: {record.duration_s:.1f}s",
        f"- Review status: {record.review_status}",
        f"- Artifacts: [summary](../../artifacts/sessions/{record.session_id}/summary.md), [turns](../../artifacts/sessions/{record.session_id}/transcript.turns.md), [review](../../artifacts/sessions/{record.session_id}/review.md)",
        "",
        "## Deterministic Observations",
        "",
        *[f"- {item}" for item in summary.get("observations", [])],
        "",
        "## Evidence Highlights",
        "",
    ]
    for item in summary.get("highlights", []):
        lines.append(
            f"- [{short_ts(item['start'])}-{short_ts(item['end'])}] **{_display_speaker(item['speaker'])}**: {item['text']}"
        )
    if not summary.get("highlights"):
        lines.append("- 暂无 highlight。")
    lines.extend(
        [
            "",
            "## Candidate Links",
            "",
        ]
    )
    for theme in summary.get("candidate_themes", []):
        lines.append(f"- [[themes/{theme}]]")
    for pattern in summary.get("candidate_patterns", []):
        lines.append(f"- [[patterns/{pattern}]]")
    write_markdown(root / WIKI_ROOT / "sessions" / f"{record.session_id}.md", frontmatter, "\n".join(lines))


def _write_home_page(root: Path, records: List[SessionRecord]) -> None:
    body = "\n".join(
        [
            "# Therapy Wiki",
            "",
            "这是心理咨询资料库的长期 wiki 层。Raw sources 在 `raw/`，中间产物在 `artifacts/`，此处是 Codex 维护的知识层。",
            "",
            f"- Sessions: {len(records)}",
            "- Core pages: [[index]], [[timeline]], [[formulation/current]], [[questions/open]]",
            "- Use Codex skills for high-quality ingest, report, discuss, and lint passes.",
        ]
    )
    write_markdown(root / WIKI_ROOT / "home.md", {"type": "home"}, body)


def _write_timeline_page(root: Path, records: List[SessionRecord]) -> None:
    lines = ["# Timeline", ""]
    for record in sorted(records, key=lambda item: item.session_date):
        summary = load_summary_payload(record)
        lines.append(
            f"- {record.session_date} [[sessions/{record.session_id}]]"
            f" | 关键词: {', '.join(summary.get('keywords', [])[:5]) or '暂无'}"
        )
    write_markdown(root / WIKI_ROOT / "timeline.md", {"type": "timeline"}, "\n".join(lines))


def _write_questions_page(root: Path, questions: List[str]) -> None:
    body = "\n".join(["# Open Questions", "", *questions]) if questions else "# Open Questions\n\n- 暂无自动抽取的问题。\n"
    write_markdown(root / WIKI_ROOT / "questions" / "open.md", {"type": "questions"}, body)


def _write_formulation_page(
    root: Path,
    records: List[SessionRecord],
    themes: Counter,
    patterns: Counter,
) -> None:
    theme_lines = [f"- {name} ({count})" for name, count in themes.most_common(6)] or ["- 暂无"]
    pattern_lines = [f"- {name} ({count})" for name, count in patterns.most_common(6)] or ["- 暂无"]
    latest = records[-1].session_id if records else "N/A"
    body = "\n".join(
        [
            "# Current Formulation",
            "",
            f"- Latest session: [[sessions/{latest}]]" if records else "- No sessions yet.",
            "",
            "## Recurring Themes",
            "",
            *theme_lines,
            "",
            "## Recurring Patterns",
            "",
            *pattern_lines,
            "",
            "## Notes",
            "",
            "- 这是 deterministic baseline。正式的心理学 formulation 应通过 `therapy-report` 或相关 persona skill 回写强化。",
        ]
    )
    write_markdown(root / WIKI_ROOT / "formulation" / "current.md", {"type": "formulation"}, body)


def _write_participant_pages(root: Path, records: List[SessionRecord]) -> None:
    session_lines = [f"- [[sessions/{record.session_id}]]" for record in records] or ["- 暂无"]
    me_body = "\n".join(
        [
            "# Me",
            "",
            "## Sessions",
            "",
            *session_lines,
        ]
    )
    therapist_body = "\n".join(
        [
            "# Therapist",
            "",
            "## Sessions",
            "",
            *session_lines,
        ]
    )
    write_markdown(root / WIKI_ROOT / "participants" / "me.md", {"type": "participant"}, me_body)
    write_markdown(root / WIKI_ROOT / "participants" / "therapist.md", {"type": "participant"}, therapist_body)


def _write_theme_pages(root: Path, pages: Dict[str, List]) -> None:
    for title, items in pages.items():
        body = [f"# {title}", "", "## Related Sessions", ""]
        for session_id, summary in items:
            body.append(
                f"- [[sessions/{session_id}]] | 关键词: {', '.join(summary.get('keywords', [])[:4]) or '暂无'}"
            )
        write_markdown(root / WIKI_ROOT / "themes" / f"{title}.md", {"type": "theme"}, "\n".join(body))


def _write_pattern_pages(root: Path, pages: Dict[str, List]) -> None:
    for title, items in pages.items():
        body = [f"# {title}", "", "## Related Sessions", ""]
        for session_id, summary in items:
            body.append(
                f"- [[sessions/{session_id}]] | 模式证据: {', '.join(summary.get('candidate_patterns', [])[:3]) or '暂无'}"
            )
        write_markdown(root / WIKI_ROOT / "patterns" / f"{title}.md", {"type": "pattern"}, "\n".join(body))


def _write_index_page(root: Path, records: List[SessionRecord], theme_pages: Dict, pattern_pages: Dict) -> None:
    lines = [
        "# Index",
        "",
        "## Core",
        "",
        "- [[home]] | 总览",
        "- [[timeline]] | 时间线",
        "- [[formulation/current]] | 当前 formulation",
        "- [[questions/open]] | 未闭合问题",
        "",
        "## Sessions",
        "",
    ]
    for record in records:
        summary = load_summary_payload(record)
        lines.append(
            f"- [[sessions/{record.session_id}]] | {', '.join(summary.get('keywords', [])[:5]) or '暂无关键词'}"
        )
    lines.extend(["", "## Themes", ""])
    for title in sorted(theme_pages):
        lines.append(f"- [[themes/{title}]] | related sessions: {len(theme_pages[title])}")
    lines.extend(["", "## Patterns", ""])
    for title in sorted(pattern_pages):
        lines.append(f"- [[patterns/{title}]] | related sessions: {len(pattern_pages[title])}")
    lines.extend(["", "## Persona Notes", ""])
    note_root = root / WIKI_ROOT / "notes" / "personas"
    if note_root.exists():
        for note in sorted(note_root.rglob("*.md")):
            relative = note.relative_to(root / WIKI_ROOT).with_suffix("")
            lines.append(f"- [[{relative.as_posix()}]]")
    write_markdown(root / WIKI_ROOT / "index.md", {"type": "index"}, "\n".join(lines))


def _display_speaker(label: str) -> str:
    mapping = {
        "me": "我",
        "therapist": "咨询师",
        "UNKNOWN": "UNKNOWN",
    }
    return mapping.get(label, label)
