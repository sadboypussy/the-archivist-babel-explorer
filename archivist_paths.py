"""Well-known paths for bundled artefacts (GGUF weights, etc.)."""

from __future__ import annotations

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent

# Default local weights (see scripts/download_model.py)
DEFAULT_GGUF_PATH: Path = _REPO_ROOT / "models" / "Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf"
