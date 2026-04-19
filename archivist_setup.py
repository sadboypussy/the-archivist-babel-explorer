"""
First-run / environment checks for The Archivist (Phase 1–2).

Used by ``scripts/first_run.py`` and callable from a future Streamlit UI.
Keeps scope small: verify Python, deps, optional NVIDIA + GGUF, suggest commands.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Final

DEFAULT_HF_REPO: Final[str] = "bartowski/Meta-Llama-3.1-8B-Instruct-GGUF"
DEFAULT_HF_FILE: Final[str] = "Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf"

_REPO_ROOT = Path(__file__).resolve().parent


def resolved_gguf_path() -> Path:
    """``ARCHIVIST_GGUF`` if set, else default under ``models/``."""
    env = os.environ.get("ARCHIVIST_GGUF", "").strip()
    if env:
        return Path(env)
    from archivist_paths import DEFAULT_GGUF_PATH

    return DEFAULT_GGUF_PATH


def download_default_gguf(
    *,
    dest_dir: Path | None = None,
    repo: str = DEFAULT_HF_REPO,
    filename: str = DEFAULT_HF_FILE,
) -> Path:
    """Download recommended weights; returns path to the GGUF file."""
    from huggingface_hub import hf_hub_download

    out = dest_dir or (_REPO_ROOT / "models")
    out.mkdir(parents=True, exist_ok=True)
    path = hf_hub_download(repo_id=repo, filename=filename, local_dir=str(out))
    return Path(path)


@dataclass(frozen=True)
class SetupCheck:
    id: str
    ok: bool
    level: str  # "ok" | "warn" | "error"
    title: str
    detail: str

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        return d


def gather_setup_checks() -> list[SetupCheck]:
    out: list[SetupCheck] = []

    vi = sys.version_info
    py_ok = vi >= (3, 10)
    out.append(
        SetupCheck(
            id="python",
            ok=py_ok,
            level="ok" if py_ok else "error",
            title="Python 3.10+",
            detail=f"{sys.version.split()[0]} ({vi.major}.{vi.minor}.{vi.micro})",
        )
    )

    try:
        import pyspellchecker  # noqa: F401

        out.append(
            SetupCheck(
                id="phase1",
                ok=True,
                level="ok",
                title="Phase 1 deps (pyspellchecker)",
                detail="OK",
            )
        )
    except ImportError as e:
        out.append(
            SetupCheck(
                id="phase1",
                ok=False,
                level="error",
                title="Phase 1 deps (pyspellchecker)",
                detail=f"Missing: {e}",
            )
        )

    llama_ok = False
    llama_detail = "not imported"
    offload = False
    try:
        if sys.platform == "win32":
            from archivist_win_cuda import register_cuda_dll_directories

            register_cuda_dll_directories()
        from llama_cpp import llama_cpp as L

        llama_ok = True
        offload = bool(L.llama_supports_gpu_offload())
        llama_detail = f"llama_cpp OK; llama_supports_gpu_offload()={offload}"
    except Exception as e:
        llama_detail = str(e)

    out.append(
        SetupCheck(
            id="phase2_llama",
            ok=llama_ok,
            level="ok" if llama_ok else "error",
            title="Phase 2 (llama-cpp-python)",
            detail=llama_detail,
        )
    )

    try:
        import firebase_admin  # noqa: F401

        out.append(
            SetupCheck(
                id="phase4_firebase_sdk",
                ok=True,
                level="ok",
                title="Galerie (firebase-admin)",
                detail="OK",
            )
        )
    except ImportError as e:
        out.append(
            SetupCheck(
                id="phase4_firebase_sdk",
                ok=False,
                level="warn",
                title="Galerie (firebase-admin)",
                detail=f"Optionnel pour la publication : {e} — pip install -r requirements-app.txt",
            )
        )

    try:
        from archivist_publish import credentials_path

        cp = credentials_path()
        if cp is not None:
            out.append(
                SetupCheck(
                    id="phase4_firebase_json",
                    ok=True,
                    level="ok",
                    title="Galerie (JSON compte de service)",
                    detail=str(cp.resolve()),
                )
            )
        else:
            out.append(
                SetupCheck(
                    id="phase4_firebase_json",
                    ok=True,
                    level="warn",
                    title="Galerie (JSON compte de service)",
                    detail="Absent — publication désactivée. Placez config/firebase-service-account.json ou ARCHIVIST_FIREBASE_CREDENTIALS.",
                )
            )
    except Exception as e:
        out.append(
            SetupCheck(
                id="phase4_firebase_json",
                ok=False,
                level="warn",
                title="Galerie (JSON compte de service)",
                detail=str(e),
            )
        )

    for mod, label in (("langdetect", "langdetect"), ("huggingface_hub", "huggingface_hub")):
        try:
            __import__(mod)
            out.append(SetupCheck(id=f"dep_{mod}", ok=True, level="ok", title=label, detail="OK"))
        except ImportError as e:
            out.append(
                SetupCheck(
                    id=f"dep_{mod}",
                    ok=False,
                    level="error",
                    title=label,
                    detail=str(e),
                )
            )

    gpu = None
    nvidia_probe_ok = False
    try:
        from archivist_win_cuda import describe_system_for_user, query_nvidia_gpu

        gpu = query_nvidia_gpu()
        summary = describe_system_for_user()
        nvidia_probe_ok = True
        out.append(
            SetupCheck(
                id="nvidia",
                ok=True,
                level="ok",
                title="NVIDIA / CUDA (summary)",
                detail=summary.replace("\n", " | "),
            )
        )
    except Exception as e:
        gpu = None
        out.append(
            SetupCheck(
                id="nvidia",
                ok=False,
                level="warn",
                title="NVIDIA / CUDA probe",
                detail=str(e),
            )
        )

    gguf = resolved_gguf_path()
    g_ok = gguf.is_file()
    out.append(
        SetupCheck(
            id="gguf",
            ok=g_ok,
            level="ok" if g_ok else "warn",
            title="GGUF weights",
            detail=str(gguf.resolve()) if g_ok else f"Missing file: {gguf}",
        )
    )

    if not llama_ok:
        out.append(
            SetupCheck(
                id="gpu_offload",
                ok=False,
                level="warn",
                title="GPU offload",
                detail="Skipped (llama-cpp-python not importable).",
            )
        )
    elif not nvidia_probe_ok:
        out.append(
            SetupCheck(
                id="gpu_offload",
                ok=False,
                level="warn",
                title="GPU offload",
                detail="Could not run NVIDIA/CUDA summary; check drivers if you expect a GPU.",
            )
        )
    elif gpu is not None and not offload:
        out.append(
            SetupCheck(
                id="gpu_offload",
                ok=False,
                level="warn",
                title="GPU offload",
                detail=(
                    "NVIDIA detected but build is CPU-only. On first ArchivistLLM load, Windows will try "
                    "`pip install` on the matching CUDA wheel and restart once. Or run "
                    "`python scripts/install_llama_cuda_windows.py`, or use `--llama-server`."
                ),
            )
        )
    elif gpu is not None and offload:
        out.append(
            SetupCheck(
                id="gpu_offload",
                ok=True,
                level="ok",
                title="GPU offload",
                detail="CUDA offload reported by llama-cpp-python.",
            )
        )
    else:
        out.append(
            SetupCheck(
                id="gpu_offload",
                ok=True,
                level="ok",
                title="GPU offload",
                detail="No NVIDIA GPU from nvidia-smi: CPU inference is expected.",
            )
        )

    return out


def _has_errors(checks: list[SetupCheck]) -> bool:
    return any(c.level == "error" and not c.ok for c in checks)


def _print_report(checks: list[SetupCheck]) -> None:
    for c in checks:
        if c.level == "error" and not c.ok:
            sym = "ERR"
        elif c.level == "warn" and not c.ok:
            sym = "WARN"
        else:
            sym = "OK"
        print(f"[{sym}] {c.title}")
        print(f"      {c.detail}")
    print()
    print("Examples:")
    print(f"  {sys.executable} run_scanner.py --pages 500 --mock-llm")
    gguf = resolved_gguf_path()
    if gguf.is_file():
        print(f"  {sys.executable} run_scanner.py --pages 500 --gguf \"{gguf}\" --pseudo You")
    else:
        print(
            f"  {sys.executable} run_scanner.py --pages 500 --gguf \"{gguf}\" --pseudo You   "
            "(after placing the GGUF or running with --download-model)"
        )
    print(f"  {sys.executable} run_scanner.py --pages 500 --llama-server http://127.0.0.1:8080")


def main(argv: list[str] | None = None) -> int:
    import argparse

    ap = argparse.ArgumentParser(description="Archivist environment check / first-run helper")
    ap.add_argument("--json", action="store_true", help="Print checks as JSON")
    ap.add_argument(
        "--non-interactive",
        action="store_true",
        help="Do not prompt (for CI / portable)",
    )
    ap.add_argument(
        "--download-model",
        action="store_true",
        help="Download the default GGUF into models/ (needs huggingface_hub)",
    )
    ns = ap.parse_args(argv)

    if ns.download_model:
        try:
            path = download_default_gguf()
            print(f"Downloaded: {path}")
        except Exception as e:
            print(f"Download failed: {e}", file=sys.stderr)
            return 3

    checks = gather_setup_checks()

    if ns.json:
        print(json.dumps([c.to_dict() for c in checks], indent=2))
    else:
        _print_report(checks)

    if not ns.non_interactive and not ns.json and sys.stdin.isatty() and not ns.download_model:
        gguf = resolved_gguf_path()
        if not gguf.is_file():
            try:
                ans = input(f"\nDownload ~5 GB model into {gguf.parent}? [y/N] ").strip().lower()
            except EOFError:
                ans = ""
            if ans in ("y", "yes", "o", "oui"):
                try:
                    path = download_default_gguf()
                    print(f"Downloaded: {path}")
                    checks = gather_setup_checks()
                    if not ns.json:
                        print()
                        _print_report(checks)
                except Exception as e:
                    print(f"Download failed: {e}", file=sys.stderr)
                    return 3

    return 1 if _has_errors(checks) else 0


if __name__ == "__main__":
    raise SystemExit(main())
