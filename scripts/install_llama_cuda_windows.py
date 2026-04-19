#!/usr/bin/env python3
"""
Install a **CUDA-enabled** ``llama-cpp-python`` wheel on Windows (NVIDIA).

Detects:
  - GPU compute capability (``nvidia-smi``)
  - Installed CUDA Toolkit version (``CUDA_PATH`` / Program Files)

Then ``pip install`` the matching **dougeeai** prebuilt wheel (see archivist_win_cuda.py).

If native import works but your machine hits rare context-init faults (e.g. WinError
0xC000001D), run **llama-server** from llama.cpp releases with full GPU offload and
point the app at ``ARCHIVIST_LLAMA_SERVER`` (see models/README.txt).
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))


def main() -> int:
    if sys.platform != "win32":
        print("This installer targets Windows only.", file=sys.stderr)
        return 2

    from archivist_win_cuda import (
        cuda_wheel_tag,
        describe_system_for_user,
        dougeeai_native_wheel_url,
        infer_toolkit_version_from_path,
        query_nvidia_gpu,
        register_cuda_dll_directories,
        sm_family_for_wheel,
    )

    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Print detection + wheel URL only; do not pip install.",
    )
    ap.add_argument(
        "--wheel-url",
        type=str,
        default=None,
        help="Override auto-selected wheel URL (advanced).",
    )
    args = ap.parse_args()

    print(describe_system_for_user(), file=sys.stderr)
    n = register_cuda_dll_directories()
    print(f"(re-)registered {n} CUDA bin path(s) for this process.", file=sys.stderr)

    gpu = query_nvidia_gpu()
    if not gpu:
        print(
            "ERROR: no NVIDIA GPU detected. Install drivers and ensure nvidia-smi works.",
            file=sys.stderr,
        )
        return 3

    tk = infer_toolkit_version_from_path()
    if tk is None:
        print(
            "ERROR: CUDA Toolkit not found under CUDA_PATH or "
            r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v*",
            file=sys.stderr,
        )
        return 4

    sm = sm_family_for_wheel(gpu)
    cuda_tag = cuda_wheel_tag(tk)
    url = args.wheel_url or dougeeai_native_wheel_url(sm=sm, cuda_tag=cuda_tag)
    print(f"Selected wheel:\n{url}", file=sys.stderr)

    if args.dry_run:
        return 0

    subprocess.check_call(
        [sys.executable, "-m", "pip", "uninstall", "llama-cpp-python", "-y"],
        stderr=sys.stderr,
        stdout=sys.stderr,
    )
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", url],
        stderr=sys.stderr,
        stdout=sys.stderr,
    )

    reg = register_cuda_dll_directories()
    print(f"After install: registered {reg} CUDA bin path(s).", file=sys.stderr)

    from llama_cpp import llama_cpp as L

    ok = bool(L.llama_supports_gpu_offload())
    print(f"llama_supports_gpu_offload() -> {ok}", file=sys.stderr)
    if not ok:
        print(
            "ERROR: installed wheel does not report GPU offload. "
            "Try --wheel-url with another CUDA/sm build, or use ARCHIVIST_LLAMA_SERVER.",
            file=sys.stderr,
        )
        return 5

    print("OK: CUDA-enabled llama-cpp-python installed.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
