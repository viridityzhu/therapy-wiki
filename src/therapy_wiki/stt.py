"""MLX Whisper adapter."""

import json
import os
import platform
import subprocess
from pathlib import Path
from typing import Any, Dict

from .constants import DEFAULT_LANGUAGE
from .exceptions import MissingDependencyError
from .runtime_log import cli_log

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_EXTERNAL_MLX_ENV = REPO_ROOT / ".venv-mlx" / "bin" / "python"
ALT_EXTERNAL_MLX_ENV = REPO_ROOT / ".venv-arm64" / "bin" / "python"


class MLXWhisperTranscriber:
    def __init__(self, model_repo: str, language: str = DEFAULT_LANGUAGE):
        self.model_repo = model_repo
        self.language = language

    def transcribe(self, audio_path: Path) -> Dict[str, Any]:
        if platform.machine() == "x86_64":
            return self._transcribe_via_external_arm64_python(audio_path)

        try:
            import mlx_whisper
        except ImportError as exc:
            raise self._missing_dependency_error() from exc

        result = mlx_whisper.transcribe(
            str(audio_path),
            path_or_hf_repo=self.model_repo,
            language=self.language,
            word_timestamps=True,
        )
        return {
            "model": self.model_repo,
            "language": self.language,
            "text": result.get("text", ""),
            "segments": result.get("segments", []),
        }

    def _transcribe_via_external_arm64_python(self, audio_path: Path) -> Dict[str, Any]:
        candidates = [
            os.environ.get("THERAPY_MLX_PYTHON"),
            str(DEFAULT_EXTERNAL_MLX_ENV),
            str(ALT_EXTERNAL_MLX_ENV),
        ]
        errors = []
        for candidate in candidates:
            if not candidate:
                continue
            python_path = Path(candidate).expanduser()
            if not python_path.exists():
                continue
            cli_log(f"STT | trying external arm64 MLX runner: {python_path}")
            env = os.environ.copy()
            src_path = str(REPO_ROOT / "src")
            env["PYTHONPATH"] = src_path if not env.get("PYTHONPATH") else f"{src_path}:{env['PYTHONPATH']}"
            command = [
                "/usr/bin/arch",
                "-arm64",
                str(python_path),
                "-m",
                "therapy_wiki.mlx_worker",
                "--audio",
                str(audio_path),
                "--model",
                self.model_repo,
                "--language",
                self.language,
            ]
            result = subprocess.run(command, capture_output=True, text=True, env=env)
            if result.returncode == 0:
                cli_log(f"STT | external arm64 MLX runner succeeded: {python_path}")
                return json.loads(result.stdout)
            stderr = (result.stderr or "").strip()
            stdout = (result.stdout or "").strip()
            details = stderr or stdout or f"exit code {result.returncode}"
            cli_log(f"STT | external arm64 MLX runner failed: {python_path}")
            errors.append(f"{python_path}: {details}")

        message = str(self._missing_dependency_error())
        if errors:
            message += "\nTried external arm64 MLX runners:\n- " + "\n- ".join(errors)
        raise MissingDependencyError(message)

    def _missing_dependency_error(self) -> MissingDependencyError:
        machine = platform.machine()
        if machine == "x86_64":
            return MissingDependencyError(
                "mlx-whisper is not available in the current x86_64 Python. "
                "Therapy Atlas expects an arm64 MLX env at `.venv-mlx/bin/python` "
                "or an explicit `THERAPY_MLX_PYTHON` override."
            )
        return MissingDependencyError(
            "mlx-whisper is not installed. Run `pip install mlx-whisper` in your arm64 environment."
        )
