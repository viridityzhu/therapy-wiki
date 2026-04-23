import json
import os
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from therapy_wiki.stt import MLXWhisperTranscriber  # noqa: E402


class STTFallbackTests(unittest.TestCase):
    @mock.patch("therapy_wiki.stt.platform.machine", return_value="x86_64")
    @mock.patch("therapy_wiki.stt.subprocess.run")
    @mock.patch("therapy_wiki.stt.Path.exists", return_value=True)
    def test_uses_external_arm64_runner_when_current_python_is_x86(self, _exists, run_mock, _machine):
        run_mock.return_value = mock.Mock(
            returncode=0,
            stdout=json.dumps(
                {
                    "model": "mlx-community/whisper-large-v3-turbo",
                    "language": "zh",
                    "text": "ok",
                    "segments": [{"start": 0, "end": 1, "text": "测试"}],
                }
            ),
            stderr="",
        )
        transcriber = MLXWhisperTranscriber("mlx-community/whisper-large-v3-turbo", language="zh")

        with mock.patch.dict(os.environ, {"THERAPY_MLX_PYTHON": "/tmp/fake-mlx-python"}):
            payload = transcriber.transcribe(Path("/tmp/audio.wav"))

        self.assertEqual(payload["text"], "ok")
        command = run_mock.call_args.args[0]
        self.assertEqual(command[:3], ["/usr/bin/arch", "-arm64", "/tmp/fake-mlx-python"])
        self.assertIn("therapy_wiki.mlx_worker", command)


if __name__ == "__main__":
    unittest.main()
