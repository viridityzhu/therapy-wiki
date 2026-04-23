"""Project-wide constants."""

from pathlib import Path

APP_NAME = "therapy"
DEFAULT_LANGUAGE = "zh"
FAST_STT_MODEL = "mlx-community/whisper-large-v3-turbo"
ACCURATE_STT_MODEL = "mlx-community/whisper-large-v3-mlx"
DEFAULT_DIARIZATION_MODEL = "pyannote/speaker-diarization-community-1"
LEGACY_DIARIZATION_MODEL = "pyannote/speaker-diarization-3.1"
DEFAULT_PROFILE = "fast"
DEFAULT_PREFLIGHT_SECONDS = 60
REPORTABLE_PERSONAS = ("therapist", "supervisor", "psychologist")
ALL_PERSONAS = (
    "therapist",
    "supervisor",
    "psychologist",
    "intp-lens",
    "close-friend",
)
PERSONA_FILEBACK_ROOT = Path("wiki/notes/personas")
RAW_ROOT = Path("raw/sessions")
ARTIFACT_ROOT = Path("artifacts/sessions")
WIKI_ROOT = Path("wiki")
OUTPUT_ROOT = Path("outputs")
SCHEMA_ROOT = Path("schema")
SESSION_FILENAME_SUFFIX = ".md"
