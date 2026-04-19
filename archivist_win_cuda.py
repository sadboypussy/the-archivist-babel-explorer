"""
Windows CUDA runtime helpers for native llama-cpp-python.

- Registers Toolkit ``bin`` folders via ``os.add_dll_directory`` (required on
  Python 3.8+ so ``llama.dll`` finds ``cublas64_*.dll``).
- Probes ``nvidia-smi`` for GPU name, driver, and compute capability.
- Maps (toolkit major.minor, compute capability) → dougeeai prebuilt wheel URL.
- ``maybe_bootstrap_cuda_and_reexec()``: if an NVIDIA GPU is present but the
  current ``llama-cpp-python`` build is CPU-only, runs ``pip install`` on the
  matching CUDA wheel and ``os.execv`` the same command line so the new binary
  loads (Windows only).

Policy (ArchivistLLM / ``--gguf``): **GPU required when ``nvidia-smi`` reports a
GPU**; CPU-only is allowed only when **no** NVIDIA GPU is detected (or
``ARCHIVIST_ALLOW_CPU=1`` for debugging). If a CUDA wheel loads but model init
still crashes on your PC, use ``ArchivistServerLLM`` (``--llama-server``).
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Final

_DOUGEE_RELEASE: Final[str] = "https://github.com/dougeeai/llama-cpp-python-wheels/releases/download"
_LCPP_VER: Final[str] = "0.3.16"

# After a successful pip CUDA install we re-exec once so ``llama.dll`` reloads.
_CUDA_REEXEC_FLAG: Final[str] = "ARCHIVIST_CUDA_REEXEC"
# Set to 1 in tests or CI to skip auto ``pip install`` / re-exec.
_SKIP_CUDA_BOOTSTRAP: Final[str] = "ARCHIVIST_SKIP_CUDA_BOOTSTRAP"


def register_cuda_dll_directories() -> int:
    """
    Register CUDA Toolkit ``bin`` directories with the Windows DLL loader.

    Returns the number of directories successfully registered.
    """
    if sys.platform != "win32":
        return 0
    seen: set[str] = set()
    n = 0
    roots: list[Path] = []

    cuda_path = os.environ.get("CUDA_PATH")
    if cuda_path:
        roots.append(Path(cuda_path) / "bin")

    base = Path(r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA")
    if base.is_dir():
        for child in sorted(base.iterdir(), reverse=True):
            if child.is_dir() and child.name.startswith("v"):
                roots.append(child / "bin")

    for b in roots:
        if not b.is_dir():
            continue
        key = str(b.resolve())
        if key in seen:
            continue
        seen.add(key)
        try:
            os.add_dll_directory(str(b))
            n += 1
        except OSError:
            continue
    return n


@dataclass(frozen=True)
class NvidiaGPUInfo:
    name: str
    compute_capability: str  # e.g. "8.9"
    driver_version: str


def query_nvidia_gpu() -> NvidiaGPUInfo | None:
    """Parse first GPU line from ``nvidia-smi --query-gpu=...``."""
    try:
        out = subprocess.check_output(
            [
                "nvidia-smi",
                "--query-gpu=name,compute_cap,driver_version",
                "--format=csv,noheader",
            ],
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=15,
        )
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return None
    line = out.strip().splitlines()[0] if out.strip() else ""
    parts = [p.strip() for p in line.split(",")]
    if len(parts) < 3:
        return None
    return NvidiaGPUInfo(name=parts[0], compute_capability=parts[1], driver_version=parts[2])


def query_cuda_driver_api_version() -> str | None:
    """Top-right ``CUDA Version: X.Y`` from plain ``nvidia-smi`` header."""
    try:
        out = subprocess.check_output(["nvidia-smi"], text=True, stderr=subprocess.DEVNULL, timeout=15)
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return None
    m = re.search(r"CUDA Version:\s*(\d+\.\d+)", out)
    return m.group(1) if m else None


def infer_toolkit_version_from_path() -> tuple[int, int] | None:
    """(major, minor) from ``CUDA_PATH`` (e.g. ``v13.0``) or newest under Program Files."""
    cuda_path = os.environ.get("CUDA_PATH")
    if cuda_path:
        m = re.search(r"v(\d+)\.(\d+)", cuda_path.replace("\\", "/"))
        if m:
            return int(m.group(1)), int(m.group(2))
    base = Path(r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA")
    best: tuple[int, int] | None = None
    if base.is_dir():
        for child in base.iterdir():
            if not child.is_dir() or not child.name.startswith("v"):
                continue
            m = re.match(r"v(\d+)\.(\d+)$", child.name)
            if not m:
                continue
            ver = (int(m.group(1)), int(m.group(2)))
            if best is None or ver > best:
                best = ver
    return best


def _compute_cap_tuple(cc: str) -> tuple[int, int]:
    parts = cc.strip().split(".")
    if len(parts) >= 2:
        return int(parts[0]), int(parts[1])
    if len(parts) == 1:
        return int(parts[0]), 0
    return 0, 0


def sm_family_for_wheel(gpu: NvidiaGPUInfo) -> str:
    """Return dougeeai SM tag: ``89``, ``86``, ``75``, ``100`` (datacenter), ``120`` consumer."""
    major, minor = _compute_cap_tuple(gpu.compute_capability)
    if (major, minor) >= (12, 0):
        return "120"  # consumer Blackwell wheel bundles sm100+sm120
    if major >= 10:
        return "100"
    if major == 8 and minor == 9:
        return "89"
    if major == 8 and minor == 6:
        return "86"
    if major == 7 and minor == 5:
        return "75"
    if major >= 8:
        return "89"
    return "75"


def cuda_wheel_tag(toolkit: tuple[int, int] | None) -> str:
    """cuda11.8 | cuda12.1 | cuda13.0 segment used in wheel filenames."""
    if toolkit is None:
        return "cuda13.0"
    major, minor = toolkit
    if major >= 13:
        return "cuda13.0"
    if major == 12:
        return "cuda12.1"
    return "cuda11.8"


def _python_abi_tag() -> str:
    vi = sys.version_info
    return f"cp{vi.major}{vi.minor}"


def dougeeai_native_wheel_url(
    *,
    sm: str,
    cuda_tag: str,
    abi_tag: str | None = None,
) -> str:
    """
    Direct HTTPS URL for the dougeeai Windows wheel (llama-cpp-python 0.3.16).

    ``sm`` is the numeric family (``89``, ``86``, ``75``) or ``120`` for consumer
    Blackwell (uses the 0.3.20 ``py3-none`` combined build).
    """
    vi = sys.version_info
    py_tag = f"py{vi.major}{vi.minor}"
    abi = abi_tag or _python_abi_tag()

    if sm == "120":
        return (
            f"{_DOUGEE_RELEASE}/v0.3.20-cuda13.0-sm100-sm120/"
            f"llama_cpp_python-0.3.20+cuda13.0.sm100.sm120.blackwell-py3-none-win_amd64.whl"
        )

    sm_token = {
        "89": "sm89.ada",
        "86": "sm86.ampere",
        "75": "sm75.turing",
        "100": "sm100.blackwell",
    }.get(sm, "sm89.ada")

    sm_dir = f"sm{sm}"

    folder = f"v{_LCPP_VER}-{cuda_tag}-{sm_dir}-{py_tag}"
    fname = f"llama_cpp_python-{_LCPP_VER}+{cuda_tag}.{sm_token}-{abi}-{abi}-win_amd64.whl"
    return f"{_DOUGEE_RELEASE}/{folder}/{fname}"


def recommended_cuda_wheel_url() -> str:
    """Wheel URL for the first detected NVIDIA GPU and inferred CUDA toolkit tag."""
    gpu = query_nvidia_gpu()
    if gpu is None:
        raise RuntimeError("recommended_cuda_wheel_url() requires a visible NVIDIA GPU (nvidia-smi).")
    tk = infer_toolkit_version_from_path()
    return dougeeai_native_wheel_url(sm=sm_family_for_wheel(gpu), cuda_tag=cuda_wheel_tag(tk))


def _llama_gpu_offload_exit_code_in_subprocess() -> int:
    """Run a fresh interpreter: 0 = ``llama_supports_gpu_offload()`` is True."""
    root = Path(__file__).resolve().parent
    snippet = (
        "import sys;"
        f"sys.path.insert(0, {str(root)!r});"
        "import archivist_win_cuda as w;"
        "w.register_cuda_dll_directories();"
        "from llama_cpp import llama_cpp as L;"
        "raise SystemExit(0 if L.llama_supports_gpu_offload() else 1)"
    )
    r = subprocess.run(
        [sys.executable, "-c", snippet],
        timeout=180,
        text=True,
        stderr=subprocess.PIPE,
        stdout=subprocess.PIPE,
    )
    return int(r.returncode)


def maybe_bootstrap_cuda_and_reexec() -> None:
    """
    Windows + NVIDIA + CPU-only ``llama-cpp-python`` → ``pip install`` CUDA wheel, then ``execv``.

    No-op if no GPU, non-Windows, offload already works, or ``ARCHIVIST_SKIP_CUDA_BOOTSTRAP=1``.
    """
    if os.environ.get(_SKIP_CUDA_BOOTSTRAP, "").lower() in ("1", "true", "yes"):
        return
    if os.environ.get(_CUDA_REEXEC_FLAG, "").lower() in ("1", "true", "yes"):
        return
    if sys.platform != "win32":
        return
    register_cuda_dll_directories()
    if query_nvidia_gpu() is None:
        return
    if _llama_gpu_offload_exit_code_in_subprocess() == 0:
        return
    url = recommended_cuda_wheel_url()
    inst = subprocess.run(
        [sys.executable, "-m", "pip", "install", "--no-cache-dir", "--force-reinstall", url],
        timeout=900,
        text=True,
    )
    if inst.returncode != 0:
        return
    if _llama_gpu_offload_exit_code_in_subprocess() != 0:
        return
    os.environ[_CUDA_REEXEC_FLAG] = "1"
    os.execv(sys.executable, [sys.executable, *sys.argv])


def describe_system_for_user() -> str:
    """Human-readable summary for install scripts / errors."""
    lines: list[str] = []
    lines.append(f"Python: {sys.version.split()[0]} ({_python_abi_tag()})")
    gpu = query_nvidia_gpu()
    if gpu:
        lines.append(f"GPU: {gpu.name}  compute_cap={gpu.compute_capability}  driver={gpu.driver_version}")
        lines.append(f"SM family for wheels: {sm_family_for_wheel(gpu)}")
    else:
        lines.append("GPU: nvidia-smi not found or failed (driver installed?)")
    tk = infer_toolkit_version_from_path()
    lines.append(f"CUDA toolkit (from CUDA_PATH / Program Files): {tk or 'unknown'}")
    drv_cuda = query_cuda_driver_api_version()
    if drv_cuda:
        lines.append(f"Driver max CUDA API: {drv_cuda}")
    lines.append(f"CUDA bin dirs registered: {register_cuda_dll_directories()}")
    return "\n".join(lines)
