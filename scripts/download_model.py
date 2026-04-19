#!/usr/bin/env python3
"""
Download the recommended Archivist GGUF weights (design §4.1).

Default: Meta-Llama-3.1-8B-Instruct Q4_K_M from bartowski (~4.9 GB).
Ungated on Hugging Face; good instruction-following + prose for the
registry seal format in archivist_llm.py.

Usage::

    pip install "huggingface_hub>=0.20"
    python scripts/download_model.py

Override destination::

    python scripts/download_model.py --dir D:\\weights
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from archivist_setup import DEFAULT_HF_FILE, DEFAULT_HF_REPO, download_default_gguf


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=DEFAULT_HF_REPO)
    ap.add_argument("--filename", default=DEFAULT_HF_FILE)
    ap.add_argument(
        "--dir",
        type=Path,
        default=_REPO / "models",
        help="Directory to place the GGUF file",
    )
    args = ap.parse_args()

    path = download_default_gguf(dest_dir=args.dir, repo=args.repo, filename=args.filename)
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
