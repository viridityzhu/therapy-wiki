"""Implementation of CLI commands."""

import re
import tempfile
from pathlib import Path
from typing import Dict, List, Optional

from .audio import extract_audio_clip, get_audio_duration, prepare_audio
from .constants import (
    ACCURATE_STT_MODEL,
    ALL_PERSONAS,
    DEFAULT_PREFLIGHT_SECONDS,
    DEFAULT_DIARIZATION_MODEL,
    DEFAULT_LANGUAGE,
    DEFAULT_PROFILE,
    FAST_STT_MODEL,
    REPORTABLE_PERSONAS,
)
from .diarize import PyannoteDiarizer
from .exceptions import DuplicateSourceError, TherapyWikiError
from .linting import run_lint, write_lint_report
from .models import SessionRecord, TranscriptSegment
from .paths import discover_workspace_root, ensure_directories
from .reporting import build_discussion_packet, build_report_bundle
from .repository import (
    allocate_session,
    get_session_record,
    list_input_audio_files,
    persist_session_meta,
    persist_speaker_map,
)
from .runtime_log import cli_log
from .speaker_map import align_speakers, collapse_turns, suggest_speaker_mapping
from .stt import MLXWhisperTranscriber
from .summarize import build_session_summary
from .utils import dump_json, load_json
from .wiki import append_log, rebuild_wiki, write_persona_note, write_session_artifacts


def ingest_command(
    input_target: Optional[str] = None,
    *,
    refresh: Optional[str] = None,
    profile: str = DEFAULT_PROFILE,
    language: str = DEFAULT_LANGUAGE,
    session_date: Optional[str] = None,
    preflight_seconds: int = DEFAULT_PREFLIGHT_SECONDS,
) -> List[SessionRecord]:
    root = discover_workspace_root()
    ensure_directories(root)
    cli_log(f"workspace: {root}")

    if refresh:
        cli_log(f"refresh requested for session {refresh}")
        record = _refresh_session(root, refresh)
        cli_log("rebuilding wiki after refresh")
        rebuild_wiki(root)
        append_log(root, f"refresh | {record.session_id}", "Recompiled session artifacts and wiki pages.")
        cli_log(f"refresh complete: {record.session_id}")
        return [record]

    if not input_target:
        raise TherapyWikiError("ingest requires a file or directory unless --refresh is provided.")

    source_path = Path(input_target).expanduser().resolve()
    cli_log(f"resolving input: {source_path}")
    files = list_input_audio_files(source_path)
    if not files:
        raise TherapyWikiError(f"No supported audio files found under {source_path}")

    stt_model = _model_for_profile(profile)
    cli_log(
        f"found {len(files)} audio file(s) | profile={profile} | stt_model={stt_model} | "
        f"diarization_model={DEFAULT_DIARIZATION_MODEL} | language={language}"
    )

    diarizer = PyannoteDiarizer(DEFAULT_DIARIZATION_MODEL)
    _run_diarization_preflight(files[0], diarizer, seconds=preflight_seconds)
    transcriber = MLXWhisperTranscriber(stt_model, language=language)
    ingested: List[SessionRecord] = []

    for index, audio_file in enumerate(files, start=1):
        try:
            cli_log(f"[{index}/{len(files)}] allocating session for {audio_file.name}")
            record = allocate_session(root, audio_file, explicit_date=session_date)
        except DuplicateSourceError:
            cli_log(f"[{index}/{len(files)}] duplicate skipped: {audio_file.name}")
            continue
        cli_log(f"[{index}/{len(files)}] allocated {record.session_id}")
        ingested.append(_ingest_single(root, record, transcriber, diarizer, language=language))

    if ingested:
        cli_log("rebuilding wiki after ingest batch")
        rebuild_wiki(root)
        append_log(
            root,
            "ingest | audio batch",
            "\n".join(f"- added {record.session_id} from {record.source_filename}" for record in ingested),
        )
        cli_log(f"ingest complete: {len(ingested)} session(s) added")
    else:
        cli_log("ingest finished with no new sessions")
    return ingested


def preflight_command(
    input_target: str,
    *,
    profile: str = DEFAULT_PROFILE,
    language: str = DEFAULT_LANGUAGE,
    seconds: int = DEFAULT_PREFLIGHT_SECONDS,
) -> str:
    root = discover_workspace_root()
    ensure_directories(root)
    cli_log(f"workspace: {root}")

    source_path = Path(input_target).expanduser().resolve()
    cli_log(f"resolving input: {source_path}")
    files = list_input_audio_files(source_path)
    if not files:
        raise TherapyWikiError(f"No supported audio files found under {source_path}")

    sample = files[0]
    stt_model = _model_for_profile(profile)
    cli_log(
        f"preflight target: {sample.name} | profile={profile} | stt_model={stt_model} | "
        f"diarization_model={DEFAULT_DIARIZATION_MODEL} | language={language}"
    )

    clip_path, clip_seconds = _build_preflight_clip(sample, seconds=seconds)
    try:
        transcriber = MLXWhisperTranscriber(stt_model, language=language)
        cli_log(f"preflight | running STT smoke test with {transcriber.model_repo}")
        transcript_payload = transcriber.transcribe(clip_path)
        cli_log(
            "preflight | STT smoke test passed"
            + f" | segments={len(transcript_payload.get('segments', []))}"
        )

        diarizer = PyannoteDiarizer(DEFAULT_DIARIZATION_MODEL)
        info = diarizer.preflight(clip_path)
        cli_log("preflight | diarization smoke test passed")
    finally:
        try:
            clip_path.unlink()
        except FileNotFoundError:
            pass

    return (
        f"preflight ok\n"
        f"file: {sample}\n"
        f"clip_seconds: {clip_seconds:.1f}\n"
        f"stt_model: {transcriber.model_repo}\n"
        f"stt_segments: {len(transcript_payload.get('segments', []))}\n"
        f"diarization_model_requested: {info['requested_model']}\n"
        f"diarization_model_resolved: {info['resolved_model']}\n"
        f"pyannote_version: {info.get('pyannote_version') or 'unknown'}\n"
        f"diarization_segments: {info.get('speaker_segments', 0)}"
    )


def report_command(scope: str, *, persona: str, session_id: Optional[str] = None) -> str:
    if persona not in REPORTABLE_PERSONAS:
        raise TherapyWikiError(f"report persona must be one of: {', '.join(REPORTABLE_PERSONAS)}")
    root = discover_workspace_root()
    ensure_directories(root)
    cli_log(f"building report | scope={scope} | persona={persona}" + (f" | session_id={session_id}" if session_id else ""))
    bundle = build_report_bundle(root, scope, persona, session_id=session_id)
    append_log(root, f"report | {bundle.scope_label}", f"Generated report packet at {bundle.packet_path.name}")
    cli_log(f"report ready: {bundle.output_path.name}")
    return f"report draft: {bundle.output_path}\npacket: {bundle.packet_path}"


def discuss_command(
    scope: str,
    *,
    persona: str,
    question: str,
    session_id: Optional[str] = None,
    file_back: bool = False,
) -> str:
    if persona not in ALL_PERSONAS:
        raise TherapyWikiError(f"persona must be one of: {', '.join(ALL_PERSONAS)}")
    root = discover_workspace_root()
    ensure_directories(root)
    cli_log(
        f"building discussion | scope={scope} | persona={persona}"
        + (f" | session_id={session_id}" if session_id else "")
    )
    packet_path, draft = build_discussion_packet(root, scope, persona, question, session_id=session_id)
    message = f"discussion packet: {packet_path}\n\n{draft}"
    if file_back:
        cli_log(f"file-back enabled for persona={persona}")
        note_title = f"{persona} | {question}"
        note_body = f"# {note_title}\n\n{draft}\n"
        note_path = write_persona_note(root, persona, note_title, note_body)
        append_log(root, f"file-back | {persona}", f"Saved discussion note to {note_path}")
        cli_log("rebuilding wiki after file-back")
        rebuild_wiki(root)
        message += f"\n\nfile-backed note: {note_path}"
        cli_log(f"file-backed note saved: {note_path.name}")
    else:
        cli_log(f"discussion packet ready: {packet_path.name}")
    return message


def lint_command() -> str:
    root = discover_workspace_root()
    ensure_directories(root)
    cli_log("running wiki lint")
    findings = run_lint(root)
    report_path = write_lint_report(root, findings)
    append_log(root, "lint | wiki", f"Lint report saved to {report_path}")
    cli_log(f"lint complete: {len(findings)} finding(s)")
    return f"lint report: {report_path}\nfindings: {len(findings)}"


def _ingest_single(
    root: Path,
    record: SessionRecord,
    transcriber: MLXWhisperTranscriber,
    diarizer: PyannoteDiarizer,
    *,
    language: str,
) -> SessionRecord:
    prepared_audio = record.artifact_dir / "prepared.wav"
    cli_log(f"{record.session_id} | preparing audio")
    prepare_audio(record.source_path, prepared_audio)
    cli_log(f"{record.session_id} | probing duration")
    duration = get_audio_duration(record.source_path)
    cli_log(f"{record.session_id} | duration={duration:.1f}s")

    cli_log(f"{record.session_id} | transcribing with {transcriber.model_repo}")
    transcript_payload = transcriber.transcribe(prepared_audio)
    dump_json(record.artifact_dir / "transcript.raw.json", transcript_payload)
    cli_log(
        f"{record.session_id} | transcript saved | segments={len(transcript_payload.get('segments', []))}"
    )

    cli_log(f"{record.session_id} | running diarization with {diarizer.model_name}")
    diarization_payload = diarizer.diarize(prepared_audio)
    dump_json(record.artifact_dir / "diarization.json", diarization_payload)
    cli_log(
        f"{record.session_id} | diarization saved | speaker_segments={len(diarization_payload.get('segments', []))}"
    )

    cli_log(f"{record.session_id} | aligning transcript and diarization")
    aligned = align_speakers(transcript_payload.get("segments", []), diarization_payload.get("segments", []))
    turns = collapse_turns(aligned)
    suggestion = suggest_speaker_mapping(turns)
    mapping_payload = {
        "mapping": suggestion.mapping,
        "confidence": suggestion.confidence,
        "rationale": suggestion.rationale,
        "raw_scores": suggestion.raw_scores,
        "source": "auto",
    }
    persist_speaker_map(record, mapping_payload)
    normalized_turns = _serialize_turns(turns, suggestion.mapping)
    dump_json(record.artifact_dir / "transcript.turns.json", normalized_turns)
    cli_log(
        f"{record.session_id} | speaker map suggested | confidence={mapping_payload.get('confidence', 'unknown')}"
    )

    cli_log(f"{record.session_id} | building summary")
    summary = build_session_summary(record.session_id, _deserialize_turns(normalized_turns), duration)
    dump_json(record.artifact_dir / "summary.json", summary)

    review_lines = _review_lines(record, mapping_payload, normalized_turns)
    record.duration_s = duration
    record.stt_model = transcriber.model_repo
    record.diarization_model = diarizer.model_name
    record.language = language
    record.speaker_map = suggestion.mapping
    record.review_status = "needs_review"
    persist_session_meta(root, record)
    cli_log(f"{record.session_id} | writing markdown artifacts and session page inputs")
    write_session_artifacts(root, record, _deserialize_turns(normalized_turns), summary, review_lines)
    cli_log(f"{record.session_id} | ingest pass complete")
    return record


def _refresh_session(root: Path, session_id: str) -> SessionRecord:
    record = get_session_record(root, session_id)
    cli_log(f"{record.session_id} | loading existing artifacts for refresh")
    transcript_payload = load_json(record.artifact_dir / "transcript.raw.json", default=None)
    diarization_payload = load_json(record.artifact_dir / "diarization.json", default=None)
    if not transcript_payload or not diarization_payload:
        raise TherapyWikiError(f"Cannot refresh {session_id}: transcript.raw.json or diarization.json is missing.")

    mapping_payload = load_json(record.artifact_dir / "speaker_map.json", default={"mapping": record.speaker_map})
    edited_turns = _parse_edited_transcript(record.artifact_dir / "transcript.edited.md")
    if edited_turns:
        cli_log(f"{record.session_id} | using transcript.edited.md for refresh")
        normalized_turns = edited_turns
    else:
        cli_log(f"{record.session_id} | rebuilding turns from raw transcript + diarization")
        aligned = align_speakers(transcript_payload.get("segments", []), diarization_payload.get("segments", []))
        turns = collapse_turns(aligned)
        normalized_turns = _serialize_turns(turns, mapping_payload.get("mapping", {}))

    dump_json(record.artifact_dir / "transcript.turns.json", normalized_turns)
    cli_log(f"{record.session_id} | rebuilding summary")
    summary = build_session_summary(record.session_id, _deserialize_turns(normalized_turns), record.duration_s)
    dump_json(record.artifact_dir / "summary.json", summary)
    record.speaker_map = mapping_payload.get("mapping", {})
    record.review_status = "refreshed"
    persist_session_meta(root, record)
    review_lines = _review_lines(record, mapping_payload, normalized_turns)
    cli_log(f"{record.session_id} | writing refreshed markdown artifacts")
    write_session_artifacts(root, record, _deserialize_turns(normalized_turns), summary, review_lines)
    cli_log(f"{record.session_id} | refresh pass complete")
    return record


def _run_diarization_preflight(source_path: Path, diarizer: PyannoteDiarizer, *, seconds: int) -> None:
    clip_path, clip_seconds = _build_preflight_clip(source_path, seconds=seconds)
    try:
        cli_log(
            f"preflight | testing diarization on {source_path.name} "
            f"with a {clip_seconds:.1f}s clip"
        )
        info = diarizer.preflight(clip_path)
        cli_log(
            f"preflight | diarization ready | requested_model={info['requested_model']} "
            f"| resolved_model={info['resolved_model']} "
            f"| pyannote.audio={info.get('pyannote_version') or 'unknown'} "
            f"| speaker_segments={info.get('speaker_segments', 0)}"
        )
    finally:
        try:
            clip_path.unlink()
        except FileNotFoundError:
            pass


def _build_preflight_clip(source_path: Path, *, seconds: int) -> tuple[Path, float]:
    duration = get_audio_duration(source_path)
    clip_seconds = min(float(seconds), duration) if duration > 0 else float(seconds)
    clip_seconds = max(clip_seconds, 5.0)
    with tempfile.NamedTemporaryFile(prefix="therapy-preflight-", suffix=".wav", delete=False) as handle:
        clip_path = Path(handle.name)
    cli_log(
        f"preflight | extracting {clip_seconds:.1f}s clip from {source_path.name}"
    )
    extract_audio_clip(source_path, clip_path, duration_s=clip_seconds)
    return clip_path, clip_seconds


def _model_for_profile(profile: str) -> str:
    return ACCURATE_STT_MODEL if profile == "accurate" else FAST_STT_MODEL


def _serialize_turns(turns: List[TranscriptSegment], mapping: Dict[str, str]) -> List[Dict]:
    payload = []
    for turn in turns:
        raw_speaker = turn.speaker or "UNKNOWN"
        canonical = _canonical_speaker(mapping.get(raw_speaker, raw_speaker))
        payload.append(
            {
                "start": turn.start,
                "end": turn.end,
                "raw_speaker": raw_speaker,
                "speaker": canonical,
                "speaker_display": _display_speaker(canonical),
                "text": turn.text,
            }
        )
    return payload


def _deserialize_turns(payload: List[Dict]) -> List[TranscriptSegment]:
    turns = []
    for item in payload:
        turns.append(
            TranscriptSegment(
                start=float(item["start"]),
                end=float(item["end"]),
                text=item["text"],
                speaker=item.get("speaker", "UNKNOWN"),
            )
        )
    return turns


def _review_lines(record: SessionRecord, mapping_payload: Dict, turns: List[Dict]) -> List[str]:
    lines = [
        "# Review Notes",
        "",
        f"- Session: {record.session_id}",
        f"- Speaker map confidence: {mapping_payload.get('confidence', 'unknown')}",
        f"- Refresh command: `therapy ingest --refresh {record.session_id}`",
        "",
        "## Speaker Map Suggestion",
        "",
    ]
    for raw_speaker, canonical in mapping_payload.get("mapping", {}).items():
        lines.append(f"- {raw_speaker} -> {_display_speaker(canonical)}")
    lines.extend(["", "## Rationale", ""])
    lines.extend([f"- {item}" for item in mapping_payload.get("rationale", [])] or ["- 暂无"])
    unknown_count = sum(turn["speaker"] == "UNKNOWN" for turn in turns)
    if unknown_count:
        lines.extend(["", "## Warnings", "", f"- There are {unknown_count} UNKNOWN turns that need review."])
    return lines


def _canonical_speaker(label: str) -> str:
    normalized = label.strip().lower()
    if normalized in {"me", "client", "self"} or label.strip() in {"我", "来访者"}:
        return "me"
    if normalized in {"therapist", "counselor"} or "咨询" in label or "治疗" in label:
        return "therapist"
    if not label.strip():
        return "UNKNOWN"
    return label.strip()


def _display_speaker(label: str) -> str:
    mapping = {
        "me": "我",
        "therapist": "咨询师",
        "UNKNOWN": "UNKNOWN",
    }
    return mapping.get(label, label)


def _parse_edited_transcript(path: Path) -> List[Dict]:
    if not path.exists():
        return []
    pattern = re.compile(
        r"^- \[(?P<start>[0-9:]+)-(?P<end>[0-9:]+)\] \*\*(?P<speaker>[^*]+)\*\*: (?P<text>.+)$"
    )
    turns = []
    for line in path.read_text(encoding="utf-8").splitlines():
        match = pattern.match(line.strip())
        if not match:
            continue
        turns.append(
            {
                "start": _parse_timestamp(match.group("start")),
                "end": _parse_timestamp(match.group("end")),
                "raw_speaker": match.group("speaker").strip(),
                "speaker": _canonical_speaker(match.group("speaker").strip()),
                "speaker_display": match.group("speaker").strip(),
                "text": match.group("text").strip(),
            }
        )
    return turns


def _parse_timestamp(text: str) -> float:
    parts = [int(part) for part in text.split(":")]
    if len(parts) == 2:
        minutes, seconds = parts
        return minutes * 60 + seconds
    if len(parts) == 3:
        hours, minutes, seconds = parts
        return hours * 3600 + minutes * 60 + seconds
    raise ValueError(f"Unsupported timestamp: {text}")
