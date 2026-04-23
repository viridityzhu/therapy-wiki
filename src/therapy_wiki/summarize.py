"""Deterministic summaries and evidence extraction."""

from collections import Counter
from typing import Dict, Iterable, List

from .models import EvidenceSnippet, TranscriptSegment
from .taxonomy import PATTERNS, THEMES
from .utils import short_ts, top_keywords, unique_preserve_order


def build_session_summary(session_id: str, turns: Iterable[TranscriptSegment], duration_s: float) -> Dict:
    turn_list = [turn for turn in turns if turn.text.strip()]
    full_text = "\n".join(turn.text for turn in turn_list)
    keywords = top_keywords(full_text, limit=10)
    themes = score_taxonomy(full_text, THEMES)
    patterns = score_taxonomy(full_text, PATTERNS)
    questions = [
        {
            "speaker": turn.speaker or "UNKNOWN",
            "start": turn.start,
            "end": turn.end,
            "text": turn.text,
        }
        for turn in turn_list
        if "?" in turn.text or "？" in turn.text
    ][:8]
    speaker_counts = Counter((turn.speaker or "UNKNOWN") for turn in turn_list)
    speaker_word_counts = Counter()
    for turn in turn_list:
        speaker_word_counts[turn.speaker or "UNKNOWN"] += len(turn.text)

    highlights = []
    ranked = sorted(
        turn_list,
        key=lambda turn: (
            ("?" in turn.text or "？" in turn.text),
            len(turn.text),
        ),
        reverse=True,
    )
    for turn in ranked[:6]:
        highlights.append(
            {
                "speaker": turn.speaker or "UNKNOWN",
                "start": turn.start,
                "end": turn.end,
                "text": turn.text,
            }
        )

    stats = {
        "duration_s": duration_s,
        "turn_count": len(turn_list),
        "speaker_turn_counts": dict(speaker_counts),
        "speaker_text_lengths": dict(speaker_word_counts),
    }

    observations = [
        f"高频关键词：{', '.join(keywords[:6])}" if keywords else "高频关键词不足，建议人工补充主题。",
        f"候选主题：{', '.join(themes[:3])}" if themes else "候选主题暂不明确。",
        f"候选模式：{', '.join(patterns[:3])}" if patterns else "候选模式暂不明确。",
    ]
    if questions:
        observations.append(f"检测到 {len(questions)} 个带问句的关键片段，适合优先复核。")

    return {
        "session_id": session_id,
        "keywords": keywords,
        "candidate_themes": themes,
        "candidate_patterns": patterns,
        "question_turns": questions,
        "highlights": highlights,
        "stats": stats,
        "observations": observations,
    }


def build_evidence_snippets(session_id: str, turns: Iterable[Dict], query: str, limit: int = 8) -> List[EvidenceSnippet]:
    question_terms = top_keywords(query, limit=8) or [term for term in query.split() if term.strip()]
    matches: List[EvidenceSnippet] = []
    fallback: List[EvidenceSnippet] = []
    for turn in turns:
        snippet = EvidenceSnippet(
            session_id=session_id,
            speaker=turn.get("speaker", "UNKNOWN"),
            start=float(turn.get("start", 0.0)),
            end=float(turn.get("end", 0.0)),
            text=turn.get("text", ""),
        )
        if any(term and term in snippet.text for term in question_terms):
            matches.append(snippet)
        elif len(fallback) < limit:
            fallback.append(snippet)

    result = matches[:limit]
    if len(result) < limit:
        result.extend(fallback[: limit - len(result)])
    return result[:limit]


def render_summary_markdown(summary: Dict) -> str:
    theme_lines = [f"- {item}" for item in summary["candidate_themes"]] or ["- 暂无"]
    pattern_lines = [f"- {item}" for item in summary["candidate_patterns"]] or ["- 暂无"]
    lines = [
        f"# {summary['session_id']} Summary",
        "",
        "## Snapshot",
        "",
        *[f"- {item}" for item in summary["observations"]],
        "",
        "## Candidate Themes",
        "",
        *theme_lines,
        "",
        "## Candidate Patterns",
        "",
        *pattern_lines,
        "",
        "## Highlights",
        "",
    ]
    for highlight in summary["highlights"]:
        lines.append(
            f"- [{short_ts(highlight['start'])}-{short_ts(highlight['end'])}] {highlight['speaker']}: {highlight['text']}"
        )
    if not summary["highlights"]:
        lines.append("- 暂无 highlight。")
    return "\n".join(lines) + "\n"


def score_taxonomy(text: str, taxonomy: Dict[str, Dict[str, List[str]]]) -> List[str]:
    scores = []
    for key, item in taxonomy.items():
        score = sum(text.count(keyword) for keyword in item["keywords"])
        if score:
            scores.append((score, item["title"]))
    scores.sort(reverse=True)
    return unique_preserve_order([title for _, title in scores[:5]])
