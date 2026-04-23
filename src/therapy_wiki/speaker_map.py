"""Speaker alignment and role suggestion heuristics."""

from collections import defaultdict
from typing import Dict, Iterable, List, Tuple

from .models import SpeakerSuggestion, TranscriptSegment

THERAPIST_MARKERS = (
    "你觉得",
    "听起来",
    "如果",
    "会不会",
    "我好奇",
    "你刚才",
    "我们可以",
    "想不想",
    "能不能",
    "对你来说",
)
CLIENT_MARKERS = (
    "我觉得",
    "我现在",
    "我有点",
    "我一直",
    "我小时候",
    "我妈妈",
    "我爸爸",
    "我害怕",
    "我想",
    "我不想",
)


def align_speakers(
    transcript_segments: Iterable[dict], diarization_segments: Iterable[dict]
) -> List[TranscriptSegment]:
    diarization = list(diarization_segments)
    aligned: List[TranscriptSegment] = []
    for item in transcript_segments:
        start = float(item.get("start", 0.0))
        end = float(item.get("end", start))
        speaker = _best_overlap_speaker(start, end, diarization)
        words = []
        for word in item.get("words", []) or []:
            words.append(
                {
                    "start": float(word.get("start", start)),
                    "end": float(word.get("end", end)),
                    "word": word.get("word", ""),
                    "probability": word.get("probability"),
                }
            )
        aligned.append(
            TranscriptSegment(
                start=start,
                end=end,
                text=item.get("text", "").strip(),
                speaker=speaker,
                words=[],
                confidence=item.get("avg_logprob"),
            )
        )
    return aligned


def collapse_turns(segments: Iterable[TranscriptSegment]) -> List[TranscriptSegment]:
    turns: List[TranscriptSegment] = []
    for segment in segments:
        if turns and turns[-1].speaker == segment.speaker:
            turns[-1].text = (turns[-1].text + " " + segment.text).strip()
            turns[-1].end = segment.end
            continue
        turns.append(segment)
    return turns


def suggest_speaker_mapping(turns: Iterable[TranscriptSegment]) -> SpeakerSuggestion:
    per_speaker = defaultdict(lambda: {"therapist": 0.0, "me": 0.0})
    for turn in turns:
        speaker = turn.speaker or "UNKNOWN"
        text = turn.text
        therapist_score = sum(marker in text for marker in THERAPIST_MARKERS) * 2.0
        client_score = sum(marker in text for marker in CLIENT_MARKERS) * 2.0
        therapist_score += text.count("？") + text.count("?") * 0.5
        client_score += text.count("我")
        therapist_score += 0.2 if len(text) < 25 else 0.0
        client_score += 0.2 if len(text) > 40 else 0.0
        per_speaker[speaker]["therapist"] += therapist_score
        per_speaker[speaker]["me"] += client_score

    speakers = list(per_speaker.keys())
    mapping: Dict[str, str] = {}
    rationale: List[str] = []
    for speaker in speakers:
        scores = per_speaker[speaker]
        assigned = "therapist" if scores["therapist"] >= scores["me"] else "me"
        mapping[speaker] = assigned
        rationale.append(
            f"{speaker}: therapist={scores['therapist']:.1f}, me={scores['me']:.1f}, suggested={assigned}"
        )

    if len(set(mapping.values())) == 1 and len(speakers) == 2:
        ordered = sorted(
            speakers,
            key=lambda name: per_speaker[name]["therapist"] - per_speaker[name]["me"],
            reverse=True,
        )
        mapping[ordered[0]] = "therapist"
        mapping[ordered[1]] = "me"
        rationale.append("Two-speaker fallback applied to avoid duplicate role assignment.")

    confidence = "low"
    if speakers:
        margins = []
        for speaker in speakers:
            scores = per_speaker[speaker]
            margins.append(abs(scores["therapist"] - scores["me"]))
        average_margin = sum(margins) / len(margins)
        confidence = "high" if average_margin >= 5 else "medium" if average_margin >= 2 else "low"

    return SpeakerSuggestion(
        mapping=mapping,
        confidence=confidence,
        rationale=rationale,
        raw_scores={speaker: dict(scores) for speaker, scores in per_speaker.items()},
    )


def _best_overlap_speaker(start: float, end: float, diarization_segments: List[dict]) -> str:
    best_speaker = "UNKNOWN"
    best_overlap = -1.0
    for diarization in diarization_segments:
        overlap = _segment_overlap(start, end, diarization["start"], diarization["end"])
        if overlap > best_overlap:
            best_overlap = overlap
            best_speaker = diarization["speaker"]
    return best_speaker


def _segment_overlap(start_a: float, end_a: float, start_b: float, end_b: float) -> float:
    return max(0.0, min(end_a, end_b) - max(start_a, start_b))

