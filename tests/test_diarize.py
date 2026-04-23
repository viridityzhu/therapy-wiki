import sys
import types
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from therapy_wiki.diarize import (  # noqa: E402
    PyannoteDiarizer,
    _patch_pyannote_hf_hub_compat,
    _pipeline_auth_kwargs,
    resolve_compatible_diarization_model,
)
from therapy_wiki.exceptions import MissingDependencyError  # noqa: E402


class _FakeAnnotation:
    def itertracks(self, yield_label=False):
        yield (types.SimpleNamespace(start=0.0, end=1.0), None, "SPEAKER_00")


class _FakePipelineUseAuthToken:
    @classmethod
    def from_pretrained(cls, checkpoint_path, use_auth_token=None, cache_dir=None):
        cls.last_call = {
            "checkpoint_path": checkpoint_path,
            "use_auth_token": use_auth_token,
            "cache_dir": cache_dir,
        }
        return cls()

    def __call__(self, audio_path):
        return _FakeAnnotation()


class _FakePipelineToken:
    @classmethod
    def from_pretrained(cls, checkpoint_path, token=None):
        cls.last_call = {
            "checkpoint_path": checkpoint_path,
            "token": token,
        }
        return cls()

    def __call__(self, audio_path):
        return _FakeAnnotation()


class DiarizeCompatibilityTests(unittest.TestCase):
    def test_resolve_compatible_diarization_model_falls_back_for_pyannote_3(self):
        resolved, notes = resolve_compatible_diarization_model(
            "pyannote/speaker-diarization-community-1",
            pyannote_version="3.4.0",
        )
        self.assertEqual(resolved, "pyannote/speaker-diarization-3.1")
        self.assertTrue(notes)

    def test_pipeline_auth_kwargs_supports_use_auth_token(self):
        kwargs = _pipeline_auth_kwargs(_FakePipelineUseAuthToken, "abc")
        self.assertEqual(kwargs, {"use_auth_token": "abc"})

    def test_pipeline_auth_kwargs_supports_token(self):
        kwargs = _pipeline_auth_kwargs(_FakePipelineToken, "abc")
        self.assertEqual(kwargs, {"token": "abc"})

    def test_diarize_uses_compatible_auth_kwarg(self):
        fake_module = types.ModuleType("pyannote.audio")
        fake_module.Pipeline = _FakePipelineUseAuthToken
        diarizer = PyannoteDiarizer("pyannote/example")

        with mock.patch.dict(sys.modules, {"pyannote.audio": fake_module}):
            with mock.patch("therapy_wiki.diarize.resolve_hf_token", return_value="secret"):
                payload = diarizer.diarize(Path("/tmp/audio.wav"))

        self.assertEqual(_FakePipelineUseAuthToken.last_call["use_auth_token"], "secret")
        self.assertEqual(payload["segments"][0]["speaker"], "SPEAKER_00")

    def test_diarize_raises_if_pipeline_could_not_be_loaded(self):
        class _NonePipeline:
            @classmethod
            def from_pretrained(cls, checkpoint_path, use_auth_token=None):
                return None

        fake_module = types.ModuleType("pyannote.audio")
        fake_module.Pipeline = _NonePipeline
        diarizer = PyannoteDiarizer("pyannote/example")

        with mock.patch.dict(sys.modules, {"pyannote.audio": fake_module}):
            with mock.patch("therapy_wiki.diarize.resolve_hf_token", return_value="secret"):
                with self.assertRaises(MissingDependencyError):
                    diarizer.diarize(Path("/tmp/audio.wav"))

    def test_patch_pyannote_hf_hub_compat_translates_use_auth_token(self):
        def fake_hf_hub_download(repo_id, filename, *, token=None, **kwargs):
            fake_hf_hub_download.last_call = {
                "repo_id": repo_id,
                "filename": filename,
                "token": token,
                "kwargs": kwargs,
            }
            return "/tmp/fake"

        fake_hf_module = types.ModuleType("huggingface_hub")
        fake_hf_module.hf_hub_download = fake_hf_hub_download
        fake_pipeline_module = types.ModuleType("pyannote.audio.core.pipeline")
        fake_pipeline_module.hf_hub_download = lambda *args, **kwargs: None
        fake_model_module = types.ModuleType("pyannote.audio.core.model")
        fake_model_module.hf_hub_download = lambda *args, **kwargs: None

        with mock.patch.dict(
            sys.modules,
            {
                "huggingface_hub": fake_hf_module,
                "pyannote.audio.core.pipeline": fake_pipeline_module,
                "pyannote.audio.core.model": fake_model_module,
            },
            clear=False,
        ):
            _patch_pyannote_hf_hub_compat()
            fake_pipeline_module.hf_hub_download("repo", "config.yaml", use_auth_token="secret")

        self.assertEqual(fake_hf_hub_download.last_call["token"], "secret")


if __name__ == "__main__":
    unittest.main()
