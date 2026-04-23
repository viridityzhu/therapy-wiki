"""Wiki health checks."""

import re
from pathlib import Path
from typing import Dict, Iterable, List

from .constants import WIKI_ROOT
from .models import LintFinding
from .repository import collect_session_records, load_summary_payload, load_turns_payload
from .utils import now_iso


def run_lint(root: Path) -> List[LintFinding]:
    findings: List[LintFinding] = []
    findings.extend(_find_needs_review(root))
    findings.extend(_find_unknown_speakers(root))
    findings.extend(_find_missing_questions(root))
    findings.extend(_find_orphan_pages(root))
    return findings


def write_lint_report(root: Path, findings: Iterable[LintFinding]) -> Path:
    report_path = root / "outputs" / "lint" / f"{now_iso().replace(':', '-')}.md"
    lines = ["# Lint Report", ""]
    for finding in findings:
        lines.extend(
            [
                f"## [{finding.severity}] {finding.title}",
                "",
                f"- Code: `{finding.code}`",
                f"- File: `{finding.file_path}`",
                f"- Detail: {finding.detail}",
                "",
            ]
        )
    if len(lines) == 2:
        lines.append("- No findings.")
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path


def _find_needs_review(root: Path) -> List[LintFinding]:
    findings = []
    for record in collect_session_records(root):
        if record.review_status == "needs_review":
            findings.append(
                LintFinding(
                    code="needs-review",
                    title=f"{record.session_id} still needs human review",
                    severity="warning",
                    detail="speaker map or transcript edits have not been confirmed yet.",
                    file_path=record.artifact_dir / "meta.json",
                )
            )
    return findings


def _find_unknown_speakers(root: Path) -> List[LintFinding]:
    findings = []
    for record in collect_session_records(root):
        turns = load_turns_payload(record)
        if any(turn.get("speaker") == "UNKNOWN" for turn in turns):
            findings.append(
                LintFinding(
                    code="unknown-speaker",
                    title=f"{record.session_id} has unresolved speaker labels",
                    severity="warning",
                    detail="At least one turn still uses UNKNOWN and may need speaker map correction.",
                    file_path=record.artifact_dir / "transcript.turns.json",
                )
            )
    return findings


def _find_missing_questions(root: Path) -> List[LintFinding]:
    sessions = collect_session_records(root)
    questions_page = root / WIKI_ROOT / "questions" / "open.md"
    if not sessions or not questions_page.exists():
        return []
    text = questions_page.read_text(encoding="utf-8")
    if "暂无自动抽取的问题" in text:
        return [
            LintFinding(
                code="missing-questions",
                title="No open questions surfaced",
                severity="info",
                detail="The wiki has sessions but the open questions page is still empty.",
                file_path=questions_page,
            )
        ]
    return []


def _find_orphan_pages(root: Path) -> List[LintFinding]:
    wiki_root = root / WIKI_ROOT
    pages = [path for path in wiki_root.rglob("*.md") if path.name not in {"index.md", "home.md", "log.md"}]
    inbound: Dict[str, int] = {str(path.relative_to(wiki_root).with_suffix("")): 0 for path in pages}
    pattern = re.compile(r"\[\[([^\]]+)\]\]")
    for path in wiki_root.rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        for match in pattern.findall(text):
            key = match.strip()
            if key in inbound:
                inbound[key] += 1
    findings = []
    for path in pages:
        key = str(path.relative_to(wiki_root).with_suffix(""))
        if inbound.get(key, 0) == 0:
            findings.append(
                LintFinding(
                    code="orphan-page",
                    title=f"Orphan page: {key}",
                    severity="info",
                    detail="No inbound wikilinks point to this page yet.",
                    file_path=path,
                )
            )
    return findings

