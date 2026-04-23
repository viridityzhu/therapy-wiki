import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from therapy_wiki import commands  # noqa: E402


class FakeTranscriber:
    def __init__(self, model_repo, language="zh"):
        self.model_repo = model_repo
        self.language = language

    def transcribe(self, audio_path):
        return {
            "text": "dummy",
            "segments": [
                {"start": 0, "end": 5, "text": "我最近一直很焦虑，觉得自己不够好。"},
                {"start": 5, "end": 11, "text": "你觉得这种不够好的感觉最近什么时候最明显？"},
                {"start": 11, "end": 18, "text": "工作里，特别是跟老板开会的时候，我会很紧张。"},
            ],
        }


class FakeDiarizer:
    def __init__(self, model_name):
        self.model_name = model_name

    def preflight(self, audio_path):
        return {
            "requested_model": self.model_name,
            "resolved_model": self.model_name,
            "pyannote_version": "3.4.0",
            "speaker_segments": 3,
        }

    def diarize(self, audio_path):
        return {
            "segments": [
                {"start": 0, "end": 5, "speaker": "SPEAKER_00"},
                {"start": 5, "end": 11, "speaker": "SPEAKER_01"},
                {"start": 11, "end": 18, "speaker": "SPEAKER_00"},
            ]
        }


class TherapyWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "src").mkdir(exist_ok=True)
        self.audio_path = self.root / "2026-04-20-session.m4a"
        self.audio_path.write_bytes(b"fake audio")

        patchers = [
            mock.patch.object(commands, "discover_workspace_root", return_value=self.root),
            mock.patch.object(commands, "prepare_audio", side_effect=self._fake_prepare_audio),
            mock.patch.object(commands, "extract_audio_clip", side_effect=self._fake_prepare_audio),
            mock.patch.object(commands, "get_audio_duration", return_value=180.0),
            mock.patch.object(commands, "MLXWhisperTranscriber", FakeTranscriber),
            mock.patch.object(commands, "PyannoteDiarizer", FakeDiarizer),
        ]
        self.patchers = patchers
        for patcher in patchers:
            patcher.start()

    def tearDown(self):
        for patcher in reversed(self.patchers):
            patcher.stop()
        self.tmp.cleanup()

    def test_ingest_creates_raw_artifacts_and_wiki(self):
        records = commands.ingest_command(str(self.audio_path))
        self.assertEqual(len(records), 1)
        record = records[0]
        self.assertTrue((self.root / "raw" / "sessions" / record.session_id / self.audio_path.name).exists())
        self.assertTrue((self.root / "artifacts" / "sessions" / record.session_id / "meta.json").exists())
        self.assertTrue((self.root / "artifacts" / "sessions" / record.session_id / "summary.json").exists())
        self.assertTrue((self.root / "wiki" / "sessions" / f"{record.session_id}.md").exists())
        self.assertTrue((self.root / "wiki" / "index.md").exists())
        self.assertTrue((self.root / "wiki" / "log.md").exists())

        turns_json = (self.root / "artifacts" / "sessions" / record.session_id / "transcript.turns.json").read_text(
            encoding="utf-8"
        )
        self.assertIn('"speaker": "me"', turns_json)
        self.assertIn('"speaker": "therapist"', turns_json)

    def test_refresh_uses_edited_transcript(self):
        record = commands.ingest_command(str(self.audio_path))[0]
        edited_path = self.root / "artifacts" / "sessions" / record.session_id / "transcript.edited.md"
        edited_path.write_text(
            "# Edited Transcript\n\n"
            "- [00:00-00:05] **我**: 我最近一直很焦虑，也开始反复想边界问题。\n"
            "- [00:05-00:11] **咨询师**: 你觉得边界在这里具体卡在哪里？\n",
            encoding="utf-8",
        )

        refreshed = commands.ingest_command(refresh=record.session_id)[0]
        self.assertEqual(refreshed.review_status, "refreshed")
        summary_json = (self.root / "artifacts" / "sessions" / record.session_id / "summary.json").read_text(
            encoding="utf-8"
        )
        self.assertIn("边界", summary_json)

    def test_report_discuss_and_lint_outputs_exist(self):
        record = commands.ingest_command(str(self.audio_path))[0]
        report_output = commands.report_command("latest", persona="therapist")
        self.assertIn("report draft:", report_output)

        discussion_output = commands.discuss_command(
            "latest",
            persona="close-friend",
            question="我是不是在过度脑补？",
            file_back=True,
        )
        self.assertIn("file-backed note:", discussion_output)
        close_friend_dir = self.root / "wiki" / "notes" / "personas" / "close-friend"
        self.assertTrue(any(close_friend_dir.glob("*.md")))

        lint_output = commands.lint_command()
        self.assertIn("lint report:", lint_output)
        self.assertTrue(any((self.root / "outputs" / "lint").glob("*.md")))

    def test_preflight_runs_on_short_clip(self):
        output = commands.preflight_command(str(self.audio_path), seconds=30)
        self.assertIn("preflight ok", output)
        self.assertIn("clip_seconds: 30.0", output)

    @staticmethod
    def _fake_prepare_audio(input_path, output_path, **kwargs):
        output_path.write_bytes(b"wav")


if __name__ == "__main__":
    unittest.main()
