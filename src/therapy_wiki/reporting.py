"""Report and discussion packet builders."""

from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from .constants import OUTPUT_ROOT
from .exceptions import TherapyWikiError
from .models import EvidenceSnippet, ReportBundle, SessionRecord
from .repository import collect_session_records, get_session_record, load_summary_payload, load_turns_payload
from .summarize import build_evidence_snippets
from .utils import now_iso, short_ts


def resolve_scope(root: Path, scope: str, session_id: str = None) -> List[SessionRecord]:
    records = collect_session_records(root)
    if scope == "latest":
        if not records:
            raise TherapyWikiError("No sessions are available yet.")
        return records[-1:]
    if scope == "all":
        if not records:
            raise TherapyWikiError("No sessions are available yet.")
        return records
    if scope == "session":
        if not session_id:
            raise TherapyWikiError("scope=session requires a session_id.")
        return [get_session_record(root, session_id)]
    raise TherapyWikiError(f"Unsupported scope: {scope}")


def build_report_bundle(root: Path, scope: str, persona: str, session_id: str = None) -> ReportBundle:
    sessions = resolve_scope(root, scope, session_id=session_id)
    scope_label = _scope_label(scope, session_id=session_id, sessions=sessions)
    evidence = _report_evidence(root, sessions)
    output_dir = root / OUTPUT_ROOT / "reports"
    stamp = now_iso().replace(":", "-")
    base_name = f"{stamp}_{scope_label}_{persona}".replace("/", "-")
    packet_path = output_dir / f"{base_name}.packet.md"
    output_path = output_dir / f"{base_name}.md"
    packet_path.write_text(render_report_packet(root, sessions, persona, evidence), encoding="utf-8")
    output_path.write_text(render_report_draft(sessions, persona, evidence, scope_label), encoding="utf-8")
    return ReportBundle(
        title=f"{scope_label} {persona} report",
        scope_label=scope_label,
        persona=persona,
        output_path=output_path,
        evidence=evidence,
        packet_path=packet_path,
    )


def build_discussion_packet(
    root: Path,
    scope: str,
    persona: str,
    question: str,
    session_id: str = None,
) -> Tuple[Path, str]:
    sessions = resolve_scope(root, scope, session_id=session_id)
    evidence = _discussion_evidence(root, sessions, question)
    scope_label = _scope_label(scope, session_id=session_id, sessions=sessions)
    output_dir = root / OUTPUT_ROOT / "reports"
    stamp = now_iso().replace(":", "-")
    base_name = f"{stamp}_{scope_label}_{persona}_discussion".replace("/", "-")
    packet_path = output_dir / f"{base_name}.md"
    packet_path.write_text(
        render_discussion_packet(root, sessions, persona, question, evidence),
        encoding="utf-8",
    )
    return packet_path, render_discussion_draft(persona, question, evidence)


def render_report_packet(
    root: Path,
    sessions: List[SessionRecord],
    persona: str,
    evidence: List[EvidenceSnippet],
) -> str:
    persona_card = load_persona_card(root, persona)
    lines = [
        f"# Report Packet | persona={persona}",
        "",
        "## Persona Card",
        "",
        persona_card.strip(),
        "",
        "## Sessions In Scope",
        "",
    ]
    for session in sessions:
        summary = load_summary_payload(session)
        lines.append(
            f"- {session.session_id} | keywords: {', '.join(summary.get('keywords', [])[:6]) or '暂无'}"
        )
    lines.extend(["", "## Evidence Packet", ""])
    lines.extend(_render_evidence(evidence))
    lines.extend(
        [
            "",
            "## Writing Constraints",
            "",
            "- 只写有材料支撑的内容。",
            "- 每个关键判断都附 session_id + timestamp。",
            "- 明确区分事实、解释、假设、未决问题。",
            "- 不做无证据诊断。",
        ]
    )
    return "\n".join(lines) + "\n"


def render_report_draft(
    sessions: List[SessionRecord],
    persona: str,
    evidence: List[EvidenceSnippet],
    scope_label: str,
) -> str:
    keywords = []
    themes = []
    patterns = []
    for session in sessions:
        summary = load_summary_payload(session)
        keywords.extend(summary.get("keywords", [])[:4])
        themes.extend(summary.get("candidate_themes", [])[:3])
        patterns.extend(summary.get("candidate_patterns", [])[:3])
    lines = [
        f"# {scope_label} | {persona} Draft Report",
        "",
        "## 事实",
        "",
        f"- 覆盖 sessions: {', '.join(session.session_id for session in sessions) or '暂无'}",
        f"- 高频关键词: {', '.join(keywords[:10]) or '暂无'}",
        f"- 候选主题: {', '.join(themes[:6]) or '暂无'}",
        f"- 候选模式: {', '.join(patterns[:6]) or '暂无'}",
        "",
        "## 解释",
        "",
        "- 根据 persona card 和下面的 evidence packet，在 Codex 中继续展开。",
        "",
        "## 假设",
        "",
        "- 需要继续核对 transcript.edited.md 与 speaker map，避免把错分说话人写进结论。",
        "",
        "## 未决问题",
        "",
        "- 哪些议题在跨 session 中持续重复出现？",
        "- 哪些内容只在近期 session 中新近出现？",
        "",
        "## 证据",
        "",
    ]
    lines.extend(_render_evidence(evidence[:10]))
    return "\n".join(lines) + "\n"


def render_discussion_packet(
    root: Path,
    sessions: List[SessionRecord],
    persona: str,
    question: str,
    evidence: List[EvidenceSnippet],
) -> str:
    persona_card = load_persona_card(root, persona)
    lines = [
        f"# Discussion Packet | persona={persona}",
        "",
        f"## Question\n\n{question}",
        "",
        "## Persona Card",
        "",
        persona_card.strip(),
        "",
        "## Sessions In Scope",
        "",
        *[f"- {session.session_id}" for session in sessions],
        "",
        "## Evidence Packet",
        "",
    ]
    lines.extend(_render_evidence(evidence))
    lines.extend(
        [
            "",
            "## Constraints",
            "",
            "- 回答必须 source-grounded。",
            "- 必须标出确定与不确定。",
            "- close-friend persona 可以直率，但不能把猜测写成结论。",
        ]
    )
    return "\n".join(lines) + "\n"


def render_discussion_draft(persona: str, question: str, evidence: List[EvidenceSnippet]) -> str:
    lines = [
        f"# {persona} Discussion Draft",
        "",
        f"Question: {question}",
        "",
        "## 先看到的事实",
        "",
    ]
    lines.extend(_render_evidence(evidence[:8]))
    lines.extend(
        [
            "",
            "## 可以继续追问",
            "",
            "- 这些片段之间是否属于同一个长期模式？",
            "- 是否存在只靠当前材料仍无法判断的地方？",
        ]
    )
    return "\n".join(lines) + "\n"


def load_persona_card(root: Path, persona: str) -> str:
    path = root / "schema" / "personas" / f"{persona}.md"
    return path.read_text(encoding="utf-8") if path.exists() else f"# {persona}\n\nMissing persona card.\n"


def _report_evidence(root: Path, sessions: Iterable[SessionRecord]) -> List[EvidenceSnippet]:
    evidence: List[EvidenceSnippet] = []
    for session in sessions:
        summary = load_summary_payload(session)
        for item in summary.get("highlights", [])[:4]:
            evidence.append(
                EvidenceSnippet(
                    session_id=session.session_id,
                    speaker=item["speaker"],
                    start=float(item["start"]),
                    end=float(item["end"]),
                    text=item["text"],
                )
            )
    return evidence


def _discussion_evidence(root: Path, sessions: Iterable[SessionRecord], question: str) -> List[EvidenceSnippet]:
    evidence: List[EvidenceSnippet] = []
    for session in sessions:
        turns = load_turns_payload(session)
        evidence.extend(build_evidence_snippets(session.session_id, turns, question))
    return evidence[:12]


def _render_evidence(evidence: Iterable[EvidenceSnippet]) -> List[str]:
    lines: List[str] = []
    for item in evidence:
        lines.append(
            f"- [{item.session_id} {short_ts(item.start)}-{short_ts(item.end)}] {item.speaker}: {item.text}"
        )
    if not lines:
        lines.append("- 暂无 evidence。")
    return lines


def _scope_label(scope: str, session_id: str = None, sessions: List[SessionRecord] = None) -> str:
    if scope == "session":
        return session_id or "session"
    if scope == "latest":
        return sessions[-1].session_id if sessions else "latest"
    return "all-sessions"
