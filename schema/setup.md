# Runtime Setup Notes

## Current environment finding

During implementation, local Python interpreters available in this workspace resolved to `x86_64`.

That matters because `mlx-whisper` depends on `mlx`, and `mlx` is generally distributed for native Apple Silicon `arm64` Python environments, not x86_64/Rosetta Python.

## What was done

- Created a local `.venv/` with Python 3.9
- Created a local `.venv310/` with Python 3.10
- Upgraded packaging tools in `.venv/`
- Attempted to install `mlx-whisper`
- Confirmed install failure is due to `mlx` not being available for the current Python architecture
- Installed `pyannote.audio` successfully in `.venv310/`
- Pinned `numpy<2` in `.venv310/` to keep `torch` / `pyannote.audio` imports compatible

## Practical consequence

The workspace code is implemented and ready. Diarization can run from `.venv310/`, but real `mlx-whisper` transcription will only work once you run it from a native `arm64` Python environment.

## Recommended fix

Use an arm64 Python 3.10+ interpreter to create the project venv, then install:

```bash
./.venv310/bin/pip install mlx-whisper pyannote.audio
```

If your available Python interpreters remain x86_64-only, use a native arm64 Python installation first, or switch the STT backend to a non-MLX option such as WhisperKit.
