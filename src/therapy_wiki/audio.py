"""Audio preparation utilities backed by ffmpeg/ffprobe."""

import json
import shutil
import subprocess
from pathlib import Path

from .exceptions import MissingDependencyError


def ensure_binary(name: str) -> str:
    resolved = shutil.which(name)
    if not resolved:
        raise MissingDependencyError(f"Missing required binary: {name}")
    return resolved


def prepare_audio(input_path: Path, output_path: Path) -> None:
    ffmpeg = ensure_binary("ffmpeg")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        ffmpeg,
        "-y",
        "-i",
        str(input_path),
        "-ac",
        "1",
        "-ar",
        "16000",
        str(output_path),
    ]
    subprocess.run(command, check=True, capture_output=True, text=True)


def extract_audio_clip(input_path: Path, output_path: Path, *, start_s: float = 0.0, duration_s: float = 60.0) -> None:
    ffmpeg = ensure_binary("ffmpeg")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        ffmpeg,
        "-y",
        "-ss",
        f"{max(start_s, 0.0):.3f}",
        "-i",
        str(input_path),
        "-t",
        f"{max(duration_s, 0.1):.3f}",
        "-ac",
        "1",
        "-ar",
        "16000",
        str(output_path),
    ]
    subprocess.run(command, check=True, capture_output=True, text=True)


def get_audio_duration(path: Path) -> float:
    ffprobe = ensure_binary("ffprobe")
    command = [
        ffprobe,
        "-v",
        "quiet",
        "-print_format",
        "json",
        "-show_format",
        str(path),
    ]
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    payload = json.loads(result.stdout)
    return float(payload["format"]["duration"])
