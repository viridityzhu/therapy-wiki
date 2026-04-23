# Runtime Setup

This file tells an agent how to set up the Therapy Wiki runtime on any machine. Read it before running `./therapy ingest` for the first time on a fresh checkout.

## Overview

Therapy Wiki has two runtime-sensitive dependencies:

- **STT (Speech-to-Text)** — implemented today against `mlx-whisper` (see [src/therapy_wiki/stt.py](../src/therapy_wiki/stt.py)). `mlx` only ships wheels for **native Apple Silicon (`arm64`) CPython**. On Apple Silicon the code imports `mlx_whisper` directly; on x86_64 Python it spawns a subprocess into a separate arm64 interpreter via `arch -arm64`.
- **Diarization** — `pyannote.audio` (see [src/therapy_wiki/diarize.py](../src/therapy_wiki/diarize.py)). This is cross-platform (macOS, Linux, Windows/WSL) on CPU or CUDA, but the default model is gated on Hugging Face and must be accepted + authenticated.

Everything else (the CLI, wiki compilation, report/discuss flows) is pure Python and runs anywhere.

## Detect the environment first

Before creating any venv, inspect the host so the right setup branch is picked:

```bash
python3 -c "import platform, sys; print(platform.system(), platform.machine(), sys.version.split()[0])"
uname -sm
```

Key facts to extract:

- OS: `Darwin` (macOS), `Linux`, or `Windows`/WSL.
- Architecture: `arm64` / `aarch64` vs. `x86_64` / `amd64`.
- Python version: need **3.10+** for the main env.

The `therapy` launcher (see [therapy](../therapy)) auto-picks a Python interpreter in this order:

1. `./.venv310/bin/python` (preferred — the main env)
2. `./.venv/bin/python` (fallback)
3. the system `python3`

It also exports `THERAPY_MLX_PYTHON` automatically if `./.venv-mlx/bin/python` exists. You can override `THERAPY_MLX_PYTHON` in `.env` or `.env.local` at the repo root if your arm64 MLX env lives elsewhere.

## System prerequisites

`ffmpeg` is needed by both STT and any audio format conversion:

| Platform           | Install command                 |
| ------------------ | ------------------------------- |
| macOS (Homebrew)   | `brew install ffmpeg`           |
| Debian / Ubuntu    | `sudo apt install -y ffmpeg`    |
| Fedora             | `sudo dnf install -y ffmpeg`    |
| Arch               | `sudo pacman -S ffmpeg`         |
| Windows (choco)    | `choco install ffmpeg`          |
| Windows (winget)   | `winget install Gyan.FFmpeg`    |

Verify with `ffmpeg -version`.

## Per-platform setup

### macOS on Apple Silicon (arm64) — the happy path

Create two venvs:

```bash
python3.10 -m venv .venv310                   # main env (CLI + pyannote)
python3.10 -m venv .venv-mlx                  # arm64 env for mlx-whisper
```

Confirm both are native arm64:

```bash
./.venv310/bin/python -c "import platform; print(platform.machine())"   # expect: arm64
./.venv-mlx/bin/python -c "import platform; print(platform.machine())"  # expect: arm64
```

Install dependencies:

```bash
./.venv310/bin/pip install --upgrade pip
./.venv310/bin/pip install "pyannote.audio>=3.1" "numpy<2" -e .

./.venv-mlx/bin/pip install --upgrade pip
./.venv-mlx/bin/pip install mlx-whisper
```

Why `numpy<2`: `torch` wheels paired with `pyannote.audio` still have a NumPy 1.x ABI and crash-import under NumPy 2.x.

No extra env var is needed — the launcher auto-detects `./.venv-mlx/bin/python`.

### macOS on Intel (x86_64)

`mlx` has no x86_64 wheels. Two options:

1. **Install a native arm64 Python alongside Rosetta** (recommended on any Apple Silicon Mac that accidentally ended up on x86_64 Python): use `arch -arm64 brew install python@3.10` or an arm64 Python.org installer, then create `.venv-mlx` from that interpreter. The main `.venv310` can stay x86_64 — the STT layer will `arch -arm64` into `.venv-mlx` automatically.
2. **Use a non-MLX STT backend.** If the machine is genuinely Intel-only, `mlx-whisper` cannot run. [src/therapy_wiki/stt.py](../src/therapy_wiki/stt.py) only implements the MLX adapter today, so you will need to add an alternate backend (`faster-whisper`, `openai-whisper`, or `whisper.cpp`) before ingest will succeed. Treat this as an extension, not a default.

For the main env, still create `.venv310` with Python 3.10+ and install `pyannote.audio` + `numpy<2` as above.

### Linux (x86_64 or arm64)

`mlx` is macOS-only, so STT will need a non-MLX backend on Linux (same note as the macOS Intel case). Diarization works normally:

```bash
python3.10 -m venv .venv310
./.venv310/bin/pip install --upgrade pip
./.venv310/bin/pip install "pyannote.audio>=3.1" "numpy<2" -e .
```

With an NVIDIA GPU, install a CUDA-compatible `torch` first (see the PyTorch install matrix) before `pyannote.audio` to get GPU diarization.

### Windows

Use WSL2 (Ubuntu) and follow the Linux path — `pyannote.audio` is significantly smoother there than on native Windows Python.

## Hugging Face access for pyannote

The default diarization model is `pyannote/speaker-diarization-community-1` (see `DEFAULT_DIARIZATION_MODEL` in [src/therapy_wiki/constants.py](../src/therapy_wiki/constants.py)). If the installed `pyannote.audio` is 3.x, the code automatically falls back to `pyannote/speaker-diarization-3.1` (see [src/therapy_wiki/diarize.py](../src/therapy_wiki/diarize.py)).

Both models are **gated** on Hugging Face. Before the first diarize run:

1. Log in to Hugging Face and accept the model conditions for whichever model you'll use.
2. Create a read-access token at <https://huggingface.co/settings/tokens>.
3. Export the token. The code checks these variables in order: `HF_TOKEN`, `HUGGINGFACE_TOKEN`, `PYANNOTE_TOKEN`.

```bash
echo 'HF_TOKEN=hf_xxx...' >> .env.local    # picked up by ./therapy
```

`./therapy` auto-loads `.env` and `.env.local` at the repo root.

## Verifying the install

Run the built-in preflight against a short clip — it loads the pyannote pipeline end-to-end and executes STT on the first N seconds:

```bash
./therapy preflight ~/path/to/short-clip.m4a
```

Expected: a line containing `preflight ok` and a non-zero `speaker_segments` count. If either STT or diarization is misconfigured, this is where it surfaces.

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `mlx-whisper is not available in the current x86_64 Python` | Main env is x86_64 and there's no arm64 MLX env to subprocess into | Create `.venv-mlx` from a native arm64 Python, or set `THERAPY_MLX_PYTHON` to an existing arm64 interpreter |
| `ImportError: numpy.core.multiarray failed to import` under torch | `numpy>=2` ABI break | `pip install 'numpy<2'` in the main env |
| `Missing Hugging Face token for pyannote` | No token env var set | Export `HF_TOKEN` (or put it in `.env.local`) |
| `Could not download pyannote/...` / HTTP 401/403 | Token valid but model conditions not accepted | Accept the model license on its Hugging Face page |
| `pyannote/speaker-diarization-community-1 requires pyannote.audio 4.x` | `pyannote.audio` 3.x installed | Either upgrade to 4.x, or let the auto-fallback use `pyannote/speaker-diarization-3.1` (and accept *its* license) |
| `ffmpeg not found` | System binary missing | Install `ffmpeg` via the platform table above |
