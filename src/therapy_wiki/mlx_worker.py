"""Arm64 helper process for running mlx-whisper outside the main CLI environment."""

import argparse
import json
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description="Run mlx-whisper transcription in an arm64 helper process.")
    parser.add_argument("--audio", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--language", required=True)
    args = parser.parse_args()

    import mlx_whisper

    result = mlx_whisper.transcribe(
        args.audio,
        path_or_hf_repo=args.model,
        language=args.language,
        word_timestamps=True,
    )
    payload = {
        "model": args.model,
        "language": args.language,
        "text": result.get("text", ""),
        "segments": result.get("segments", []),
    }
    json.dump(payload, sys.stdout, ensure_ascii=False)
    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
