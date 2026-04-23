"""Dataclasses shared by commands and wiki compilation."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class TranscriptWord:
    start: float
    end: float
    word: str
    probability: Optional[float] = None


@dataclass
class TranscriptSegment:
    start: float
    end: float
    text: str
    speaker: Optional[str] = None
    words: List[TranscriptWord] = field(default_factory=list)
    confidence: Optional[float] = None


@dataclass
class DiarizationSegment:
    start: float
    end: float
    speaker: str


@dataclass
class SpeakerSuggestion:
    mapping: Dict[str, str]
    confidence: str
    rationale: List[str]
    raw_scores: Dict[str, Dict[str, float]]


@dataclass
class SessionRecord:
    session_id: str
    session_number: int
    session_date: str
    source_sha256: str
    source_filename: str
    source_path: Path
    artifact_dir: Path
    raw_dir: Path
    duration_s: float
    stt_model: str
    diarization_model: str
    language: str
    speaker_map: Dict[str, str]
    review_status: str = "needs_review"


@dataclass
class EvidenceSnippet:
    session_id: str
    speaker: str
    start: float
    end: float
    text: str


@dataclass
class LintFinding:
    code: str
    title: str
    severity: str
    detail: str
    file_path: Path


@dataclass
class ReportBundle:
    title: str
    scope_label: str
    persona: str
    output_path: Path
    evidence: List[EvidenceSnippet]
    packet_path: Path

