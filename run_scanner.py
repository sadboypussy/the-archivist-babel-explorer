#!/usr/bin/env python3
"""
Phase 1–2 CLI — scan the Archivist Library (AL1), optional local Archivist LLM.

Usage (from repo root)::

    pip install -r requirements.txt
    python scripts/first_run.py
    python run_scanner.py --pages 50000 --workers 4 --log archivist_log.json

With LLM (Phase 2 — design §4, §7)::

    pip install -r requirements-llm.txt
    python run_scanner.py --pages 5000 --gguf path/to/model.gguf --pseudo You

Windows + NVIDIA (native CUDA wheel + DLL registration)::

    python scripts/install_llama_cuda_windows.py
    python run_scanner.py --pages 5000 --gguf models\\Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf

If native ``llama-cpp-python`` fails to start on your machine, keep inference on GPU by
running **llama-server** (CUDA) or LM Studio and pointing the scanner at it::

    python run_scanner.py --pages 5000 --llama-server http://127.0.0.1:8080

Dev / CI without a model::

    python run_scanner.py --pages 100 --mock-llm

Local UI (Phase 3)::

    pip install -r requirements-app.txt
    streamlit run archivist_app.py

Optional progress JSON for UIs::

    python run_scanner.py --pages 500 --mock-llm --status-file .archivist_scan_status.json

Optional pause between worker rounds (first line of the file must be ``pause``; delete file or clear to resume)::

    python run_scanner.py --pages 5000 --mock-llm --pause-flag-file .archivist_scan_pause

Workers scan in parallel; LLM enrichment runs in the **main** process after each
batch result (simple queue; a dedicated backlog worker can come later §8.1).
"""

from __future__ import annotations

import argparse
import json
import multiprocessing
import os
import secrets
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Callable

_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from archivist_log import extend_log

_SPELL = None
_PSEUDO: str | None = None


def _init_worker(pseudo: str | None) -> None:
    global _SPELL, _PSEUDO
    from spellchecker import SpellChecker

    _SPELL = SpellChecker()
    _PSEUDO = pseudo


def _scan_batch(batch_size: int) -> tuple[int, list[dict[str, Any]]]:
    """Returns (pages_scanned_in_batch, list_of_artefact_dicts)."""
    from archivist_al1 import LIBRARY_VERSION, page_text_al1
    from archivist_filters import (
        assign_rarity,
        dictionary_coverage,
        extract_fragment,
        filter1_entropy,
        filter2_dictionary,
        mission_keyword_score,
    )

    assert _SPELL is not None
    spell = _SPELL
    found: list[dict[str, Any]] = []
    scanned = 0

    for _ in range(batch_size):
        scanned += 1
        coord = "AL1-" + secrets.token_hex(32)
        page = page_text_al1(coord)

        f1_ok, f1_metrics = filter1_entropy(page)
        if not f1_ok:
            continue

        f2 = filter2_dictionary(page, spell)
        if not f2.passes:
            continue

        m_score, m_hits = mission_keyword_score(page)
        cov = dictionary_coverage(page, spell)
        rarity = assign_rarity(
            f2.max_consecutive_real_words,
            m_score,
            cov,
            page,
        )
        fragment = extract_fragment(
            page,
            f2.run_start_char_index,
            f2.run_end_char_index,
        )

        rec: dict[str, Any] = {
            "library_version": LIBRARY_VERSION,
            "coordinates": coord,
            "fragment": fragment,
            "mission_keyword_score": m_score,
            "mission_keyword_hits": m_hits,
            "dictionary_coverage": round(cov, 4),
            "filter1_metrics": {
                k: (round(v, 6) if isinstance(v, float) else v)
                for k, v in f1_metrics.items()
            },
            "filter2": {
                "max_consecutive_real_words": f2.max_consecutive_real_words,
                "tokens_checked": f2.tokens_checked,
                "longest_run_tokens": f2.longest_run_tokens,
            },
            "rarity": {"rank": rarity.rank, "display_name": rarity.display_name},
            "explorer_pseudo": _PSEUDO,
        }
        found.append(rec)

    return scanned, found


def _write_scan_status(path: Path, payload: dict[str, Any]) -> None:
    """Atomic JSON write for UI / tooling (optional ``--status-file``)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def _pause_requested(path: Path | None) -> bool:
    """True if ``pause-flag-file`` exists and its first non-empty line is ``pause`` (case-insensitive)."""
    if path is None or not path.is_file():
        return False
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            s = line.strip().lower()
            if not s:
                continue
            return s == "pause"
    except OSError:
        return False
    return False


def _wait_while_paused(path: Path | None) -> None:
    """Block between scan rounds while the pause file requests a halt (design §6 pause/resume path)."""
    while _pause_requested(path):
        time.sleep(0.25)


def _enrich_artefacts(
    arts: list[dict[str, Any]],
    enrich: Callable[[dict[str, Any]], dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    if enrich is None:
        return arts
    out: list[dict[str, Any]] = []
    for art in arts:
        try:
            out.append(enrich(art))
        except Exception as e:
            art = {**art, "llm_error": str(e), "archivist_title": "", "archivist_commentary": ""}
            art.setdefault("mission_relevance", "Unknown")
            out.append(art)
    return out


def main() -> int:
    cpu = os.cpu_count() or 2

    ap = argparse.ArgumentParser(description="Archivist Phase 1–2 — AL1 scanner + optional LLM")
    ap.add_argument("--pages", type=int, default=50_000, help="Total pages to evaluate")
    ap.add_argument("--batch", type=int, default=400, help="Pages per worker task")
    ap.add_argument(
        "--workers",
        type=int,
        default=max(1, cpu - 1),
        help="Process pool size (default: CPU count minus one)",
    )
    ap.add_argument("--log", type=Path, default=Path("archivist_log.json"))
    ap.add_argument(
        "--pseudo",
        type=str,
        default=None,
        help="Explorer name stored on each artefact",
    )
    ap.add_argument(
        "--gguf",
        type=Path,
        default=None,
        help="Path to a GGUF model (llama-cpp-python). Enables Phase 2 Archivist. "
        "If omitted, reads env ARCHIVIST_GGUF. Default weights: models/README.txt.",
    )
    ap.add_argument(
        "--llama-server",
        type=str,
        default=None,
        help="OpenAI-compatible base URL for llama-server / LM Studio (e.g. http://127.0.0.1:8080). "
        "If omitted, reads env ARCHIVIST_LLAMA_SERVER. Mutually exclusive with --gguf.",
    )
    ap.add_argument(
        "--mock-llm",
        action="store_true",
        help="Use a deterministic mock Archivist (no GGUF file). For dev / tests.",
    )
    ap.add_argument(
        "--n-gpu-layers",
        type=int,
        default=-1,
        help="llama.cpp GPU offload layer count (-1 = default try all)",
    )
    ap.add_argument(
        "--status-file",
        type=Path,
        default=None,
        help="Optional JSON file rewritten with scan progress (pages, artefacts) for UI integration.",
    )
    ap.add_argument(
        "--pause-flag-file",
        type=Path,
        default=None,
        help="Optional control file: while its first non-empty line reads 'pause', the scanner waits between worker rounds.",
    )
    args = ap.parse_args()

    if args.llama_server is None and os.environ.get("ARCHIVIST_LLAMA_SERVER"):
        args.llama_server = os.environ.get("ARCHIVIST_LLAMA_SERVER")

    if args.gguf is None and os.environ.get("ARCHIVIST_GGUF"):
        args.gguf = Path(os.environ["ARCHIVIST_GGUF"])

    if args.gguf and args.mock_llm:
        print("Use only one of --gguf or --mock-llm", file=sys.stderr)
        return 2
    if args.llama_server and args.mock_llm:
        print("Use only one of --llama-server or --mock-llm", file=sys.stderr)
        return 2
    if args.llama_server and args.gguf:
        print("Use only one of --llama-server or --gguf", file=sys.stderr)
        return 2
    if args.gguf and not args.gguf.is_file():
        print(f"GGUF not found: {args.gguf}", file=sys.stderr)
        return 2

    enrich: Callable[[dict[str, Any]], dict[str, Any]] | None = None
    if args.mock_llm:
        from archivist_llm import mock_llm_complete

        enrich = mock_llm_complete
    elif args.llama_server:
        from archivist_llm import ArchivistServerLLM

        print(f"Archivist LLM: OpenAI-compatible server {args.llama_server!r}", file=sys.stderr)
        _llm = ArchivistServerLLM(args.llama_server)
        enrich = _llm.complete
    elif args.gguf is not None:
        from archivist_llm import ArchivistLLM

        print(f"Loading LLM: {args.gguf}", file=sys.stderr)
        _llm = ArchivistLLM(str(args.gguf), n_gpu_layers=args.n_gpu_layers)
        enrich = _llm.complete

    workers = max(1, min(args.workers, cpu))
    total_target = max(1, args.pages)
    batch = max(1, args.batch)
    log_path: Path = args.log

    print(
        f"Archivist scanner AL1 — pages={total_target} batch={batch} workers={workers}",
        file=sys.stderr,
    )
    print(f"Log: {log_path.resolve()}", file=sys.stderr)
    if enrich is not None:
        print("Archivist LLM: enabled (Phase 2)", file=sys.stderr)

    total_scanned = 0
    total_artefacts = 0
    log_buffer: list[dict[str, Any]] = []
    LOG_FLUSH_EVERY = 25
    status_path = args.status_file
    pause_path = args.pause_flag_file

    def emit_status(phase: str) -> None:
        if status_path is None:
            return
        _write_scan_status(
            status_path,
            {
                "phase": phase,
                "total_target": total_target,
                "total_scanned": total_scanned,
                "total_artefacts": total_artefacts,
            },
        )

    emit_status("running")

    try:
        with ProcessPoolExecutor(
            max_workers=workers,
            initializer=_init_worker,
            initargs=(args.pseudo,),
        ) as ex:
            remaining = total_target
            while remaining > 0:
                _wait_while_paused(pause_path)
                futs = []
                for _ in range(workers):
                    if remaining <= 0:
                        break
                    c = min(batch, remaining)
                    remaining -= c
                    futs.append(ex.submit(_scan_batch, c))

                for fut in as_completed(futs):
                    scanned, arts = fut.result()
                    total_scanned += scanned
                    arts = _enrich_artefacts(arts, enrich)
                    for art in arts:
                        log_buffer.append(art)
                        total_artefacts += 1
                        if len(log_buffer) >= LOG_FLUSH_EVERY:
                            extend_log(log_path, log_buffer)
                            log_buffer.clear()
                        title = art.get("archivist_title") or "—"
                        if len(title) > 48:
                            title = title[:45] + "…"
                        print(
                            f"[+] {art['rarity']['display_name']} | "
                            f"kw={art['mission_keyword_score']} | "
                            f"LLM={art.get('mission_relevance', '—')} | "
                            f"{title} | {art['coordinates'][:16]}…",
                            file=sys.stderr,
                        )
                    emit_status("running")
                print(
                    f"… scanned {total_scanned}/{total_target} pages, "
                    f"{total_artefacts} artefacts",
                    file=sys.stderr,
                )

        if log_buffer:
            extend_log(log_path, log_buffer)

        print(
            f"Done. scanned={total_scanned} artefacts={total_artefacts}",
            file=sys.stderr,
        )
        emit_status("done")
        return 0
    except BaseException:
        emit_status("error")
        raise


if __name__ == "__main__":
    if sys.platform == "win32":
        multiprocessing.freeze_support()
    raise SystemExit(main())
