"""Pyannote diarization adapter."""

import importlib
import importlib.metadata
import inspect
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .constants import DEFAULT_DIARIZATION_MODEL, LEGACY_DIARIZATION_MODEL
from .exceptions import MissingDependencyError
from .runtime_log import cli_log

HF_TOKEN_ENV_VARS = ("HF_TOKEN", "HUGGINGFACE_TOKEN", "PYANNOTE_TOKEN")


def resolve_hf_token() -> str:
    for env_var in HF_TOKEN_ENV_VARS:
        token = os.environ.get(env_var)
        if token:
            return token
    raise MissingDependencyError(
        "Missing Hugging Face token for pyannote. Set HF_TOKEN, HUGGINGFACE_TOKEN, or PYANNOTE_TOKEN."
    )


class PyannoteDiarizer:
    def __init__(self, model_name: str):
        self.requested_model_name = model_name
        self.model_name = model_name
        self._pipeline = None
        self._pyannote_version = installed_pyannote_version()

    def diarize(self, audio_path: Path) -> Dict[str, Any]:
        pipeline = self.load_pipeline()
        cli_log("Diarization | running inference")
        annotation = pipeline(str(audio_path))
        segments = _collect_segments(annotation)
        cli_log(f"Diarization | inference complete | speaker_segments={len(segments)}")
        return {
            "model": self.model_name,
            "segments": sorted(segments, key=lambda item: (item["start"], item["end"])),
        }

    def preflight(self, audio_path: Optional[Path] = None) -> Dict[str, Any]:
        pipeline = self.load_pipeline()
        payload = {
            "requested_model": self.requested_model_name,
            "resolved_model": self.model_name,
            "pyannote_version": self._pyannote_version,
        }
        if audio_path is None:
            return payload

        cli_log(f"Diarization | smoke test on clip: {audio_path.name}")
        annotation = pipeline(str(audio_path))
        segments = _collect_segments(annotation)
        cli_log(f"Diarization | smoke test passed | speaker_segments={len(segments)}")
        payload["speaker_segments"] = len(segments)
        return payload

    def load_pipeline(self):
        if self._pipeline is not None:
            return self._pipeline

        try:
            from pyannote.audio import Pipeline
        except ImportError as exc:
            raise MissingDependencyError(
                "pyannote.audio is not installed. Install it and accept the pyannote model terms first."
            ) from exc

        _patch_pyannote_hf_hub_compat()
        self.model_name, notes = resolve_compatible_diarization_model(
            self.requested_model_name,
            pyannote_version=self._pyannote_version,
        )
        for note in notes:
            cli_log(f"Diarization | {note}")

        cli_log(
            f"Diarization | loading pipeline: {self.model_name}"
            + (f" | pyannote.audio={self._pyannote_version}" if self._pyannote_version else "")
        )
        kwargs = _pipeline_auth_kwargs(Pipeline, resolve_hf_token())
        try:
            pipeline = Pipeline.from_pretrained(self.model_name, **kwargs)
        except TypeError as exc:
            message = str(exc)
            if "unexpected keyword argument 'plda'" in message:
                raise MissingDependencyError(
                    f"{self.model_name} is incompatible with installed pyannote.audio {self._pyannote_version or 'unknown'}. "
                    f"Use {LEGACY_DIARIZATION_MODEL} on pyannote.audio 3.x or upgrade to pyannote.audio 4.x."
                ) from exc
            raise
        except Exception as exc:  # pragma: no cover - network/runtime failures vary by environment
            raise _normalize_pyannote_error(exc, self.model_name) from exc

        if pipeline is None:
            raise MissingDependencyError(
                f"Could not load the pyannote pipeline {self.model_name}. Make sure your Hugging Face token is set "
                "and that you have accepted the model conditions for the diarization pipeline."
            )
        cli_log("Diarization | pipeline loaded")
        self._pipeline = pipeline
        return pipeline


def _pipeline_auth_kwargs(pipeline_cls: Any, token: str) -> Dict[str, str]:
    signature = inspect.signature(pipeline_cls.from_pretrained)
    parameters = signature.parameters
    if "token" in parameters:
        return {"token": token}
    if "use_auth_token" in parameters:
        return {"use_auth_token": token}
    return {}


def _patch_pyannote_hf_hub_compat() -> None:
    try:
        huggingface_hub = sys.modules.get("huggingface_hub") or importlib.import_module("huggingface_hub")
        model_module = sys.modules.get("pyannote.audio.core.model") or importlib.import_module(
            "pyannote.audio.core.model"
        )
        pipeline_module = sys.modules.get("pyannote.audio.core.pipeline") or importlib.import_module(
            "pyannote.audio.core.pipeline"
        )
    except ImportError:
        return

    current_download = huggingface_hub.hf_hub_download
    signature = inspect.signature(current_download)
    if "use_auth_token" in signature.parameters:
        return

    if getattr(pipeline_module.hf_hub_download, "__name__", "") == "_compat_hf_hub_download":
        return

    def _compat_hf_hub_download(*args, use_auth_token=None, token=None, **kwargs):
        if token is None and use_auth_token is not None:
            token = use_auth_token
        return current_download(*args, token=token, **kwargs)

    pipeline_module.hf_hub_download = _compat_hf_hub_download
    model_module.hf_hub_download = _compat_hf_hub_download


def installed_pyannote_version() -> Optional[str]:
    try:
        return importlib.metadata.version("pyannote.audio")
    except importlib.metadata.PackageNotFoundError:
        return None


def resolve_compatible_diarization_model(model_name: str, *, pyannote_version: Optional[str]) -> Tuple[str, List[str]]:
    if model_name != DEFAULT_DIARIZATION_MODEL:
        return model_name, []

    major = _major_version(pyannote_version)
    if major is not None and major < 4:
        return (
            LEGACY_DIARIZATION_MODEL,
            [
                f"{DEFAULT_DIARIZATION_MODEL} requires pyannote.audio 4.x, "
                f"but this environment has {pyannote_version}. Falling back to {LEGACY_DIARIZATION_MODEL}.",
                f"If {LEGACY_DIARIZATION_MODEL} has not been accepted on Hugging Face yet, accept its model conditions first.",
            ],
        )
    return model_name, []


def _major_version(version: Optional[str]) -> Optional[int]:
    if not version:
        return None
    try:
        return int(str(version).split(".", 1)[0])
    except (TypeError, ValueError):
        return None


def _collect_segments(annotation) -> List[Dict[str, Any]]:
    segments: List[Dict[str, Any]] = []
    for turn, _, speaker in annotation.itertracks(yield_label=True):
        segments.append(
            {
                "start": float(turn.start),
                "end": float(turn.end),
                "speaker": speaker,
            }
        )
    return segments


def _normalize_pyannote_error(exc: Exception, model_name: str) -> MissingDependencyError:
    message = str(exc).strip() or exc.__class__.__name__
    download_markers = (
        "could not download",
        "gated",
        "access to model",
        "401",
        "403",
        "repository not found",
    )
    if any(marker in message.lower() for marker in download_markers):
        return MissingDependencyError(
            f"Could not download {model_name}. Make sure your Hugging Face token is set and that you have "
            f"accepted the model conditions for {model_name}."
        )
    return MissingDependencyError(f"Diarization pipeline failed while loading {model_name}: {message}")
