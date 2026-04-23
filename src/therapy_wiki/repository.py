"""Session storage helpers."""

import shutil
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from .constants import ARTIFACT_ROOT, RAW_ROOT
from .exceptions import DuplicateSourceError, SessionNotFoundError
from .models import SessionRecord
from .utils import dump_json, extract_date_from_name, iso_date_from_timestamp, load_json, sha256_file


def collect_session_records(root: Path) -> List[SessionRecord]:
    records: List[SessionRecord] = []
    base = root / ARTIFACT_ROOT
    if not base.exists():
        return records
    for session_dir in sorted(path for path in base.iterdir() if path.is_dir()):
        meta_path = session_dir / "meta.json"
        if not meta_path.exists():
            continue
        payload = load_json(meta_path, default={})
        records.append(_session_record_from_payload(root, payload))
    return sorted(records, key=lambda item: (item.session_number, item.session_id))


def get_session_record(root: Path, session_id: str) -> SessionRecord:
    for record in collect_session_records(root):
        if record.session_id == session_id:
            return record
    raise SessionNotFoundError(f"Unknown session: {session_id}")


def next_session_number(root: Path) -> int:
    records = collect_session_records(root)
    return (max(record.session_number for record in records) + 1) if records else 1


def find_duplicate_session(root: Path, source_hash: str) -> Optional[SessionRecord]:
    for record in collect_session_records(root):
        if record.source_sha256 == source_hash:
            return record
    return None


def allocate_session(root: Path, source_path: Path, explicit_date: Optional[str] = None) -> SessionRecord:
    source_hash = sha256_file(source_path)
    duplicate = find_duplicate_session(root, source_hash)
    if duplicate:
        raise DuplicateSourceError(f"{source_path.name} already ingested as {duplicate.session_id}")

    session_number = next_session_number(root)
    session_date = explicit_date or extract_date_from_name(source_path) or iso_date_from_timestamp(source_path.stat().st_mtime)
    session_id = f"{session_date}_s{session_number:03d}"
    raw_dir = root / RAW_ROOT / session_id
    artifact_dir = root / ARTIFACT_ROOT / session_id
    raw_dir.mkdir(parents=True, exist_ok=True)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    copied_source = raw_dir / source_path.name
    shutil.copy2(source_path, copied_source)

    return SessionRecord(
        session_id=session_id,
        session_number=session_number,
        session_date=session_date,
        source_sha256=source_hash,
        source_filename=source_path.name,
        source_path=copied_source,
        artifact_dir=artifact_dir,
        raw_dir=raw_dir,
        duration_s=0.0,
        stt_model="",
        diarization_model="",
        language="zh",
        speaker_map={},
    )


def persist_session_meta(root: Path, record: SessionRecord, extra: Optional[Dict] = None) -> None:
    payload = {
        "session_id": record.session_id,
        "session_number": record.session_number,
        "session_date": record.session_date,
        "source_sha256": record.source_sha256,
        "source_filename": record.source_filename,
        "source_path": str(record.source_path.relative_to(root)),
        "artifact_dir": str(record.artifact_dir.relative_to(root)),
        "raw_dir": str(record.raw_dir.relative_to(root)),
        "duration_s": record.duration_s,
        "stt_model": record.stt_model,
        "diarization_model": record.diarization_model,
        "language": record.language,
        "speaker_map": record.speaker_map,
        "review_status": record.review_status,
    }
    if extra:
        payload.update(extra)
    dump_json(record.artifact_dir / "meta.json", payload)


def list_input_audio_files(input_path: Path) -> List[Path]:
    if input_path.is_file():
        return [input_path]
    supported = {".m4a", ".wav", ".mp3", ".flac", ".aac"}
    files = [
        path
        for path in sorted(input_path.iterdir())
        if path.is_file() and path.suffix.lower() in supported
    ]
    return files


def load_turns_payload(record: SessionRecord) -> List[Dict]:
    return load_json(record.artifact_dir / "transcript.turns.json", default=[])


def load_summary_payload(record: SessionRecord) -> Dict:
    return load_json(record.artifact_dir / "summary.json", default={})


def load_speaker_map(record: SessionRecord) -> Dict[str, str]:
    payload = load_json(record.artifact_dir / "speaker_map.json", default=None)
    if payload and "mapping" in payload:
        return payload["mapping"]
    return dict(record.speaker_map)


def persist_speaker_map(record: SessionRecord, mapping_payload: Dict) -> None:
    dump_json(record.artifact_dir / "speaker_map.json", mapping_payload)


def _session_record_from_payload(root: Path, payload: Dict) -> SessionRecord:
    return SessionRecord(
        session_id=payload["session_id"],
        session_number=int(payload["session_number"]),
        session_date=payload["session_date"],
        source_sha256=payload["source_sha256"],
        source_filename=payload["source_filename"],
        source_path=root / payload["source_path"],
        artifact_dir=root / payload["artifact_dir"],
        raw_dir=root / payload["raw_dir"],
        duration_s=float(payload.get("duration_s", 0.0)),
        stt_model=payload.get("stt_model", ""),
        diarization_model=payload.get("diarization_model", ""),
        language=payload.get("language", "zh"),
        speaker_map=payload.get("speaker_map", {}),
        review_status=payload.get("review_status", "needs_review"),
    )

