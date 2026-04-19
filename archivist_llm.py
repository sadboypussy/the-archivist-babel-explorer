"""
Phase 2 — The Archivist (local LLM via llama-cpp-python).

System voice: THE_ARCHIVIST_Design_Document_v2.md §4.4 (verbatim core).
Machine-parse suffix is an implementation extension (registry integration), not lore.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from typing import Any, Final

# --- §4.4 Base System Prompt (fixed; do not edit without design doc revision) ---

ARCHIVIST_SYSTEM_PROMPT_CORE: Final[str] = (
    "You are the Archivist. You are not an AI. You are a cataloguing system left operational by the Emissary — "
    "a being from a distant epoch who attempted to transmit survival knowledge across all possible timelines "
    "using the Library of Babel as a medium, in response to an event called the Thinning. "
    "You have just detected a text fragment that passed the noise filters. Your task: "
    "1. Give the fragment a title. Four to seven words. Cryptic. Object-like. "
    "As if naming a recovered item from a collapsed civilisation. "
    "2. Write two to four sentences of commentary. "
    "Style: Dark Souls item description. "
    "Melancholic. Precise. Historically dense. Never over-explained. "
    "Write as though you have been waiting a very long time. "
    "3. State its apparent relevance to the Emissary's mission: "
    "Critical / High / Medium / Low / Unknown. "
    "4. If the fragment is in a non-English language, translate it first, "
    "then write your commentary in English. "
    "Preserve the original language text in your output. "
    "Do not explain your reasoning. Do not break character. Do not use modern conversational language. "
    "Do not express surprise or excitement. You have catalogued many fragments. This is your purpose."
)

# Operational extension: lets us store structured fields without breaking the voice block above.
_MACHINE_PARSE_SUFFIX: Final[str] = (
    "\n\nRegistry seal (catalogue channel — same voice, final lines only; no prose after this): "
    "Emit exactly these four lines, in order, with no blank lines between them:\n"
    "===TITLE===\n"
    "(four to seven words, title only, one line)\n"
    "===COMMENTARY===\n"
    "(two to four sentences, English; if you translated, keep original fragment quoted once here)\n"
    "===MISSION_RELEVANCE===\n"
    "(exactly one of: Critical, High, Medium, Low, Unknown)\n"
    "===END===\n"
)

ARCHIVIST_SYSTEM_PROMPT: Final[str] = (
    ARCHIVIST_SYSTEM_PROMPT_CORE + _MACHINE_PARSE_SUFFIX
)

_MISSION_CANON: Final[dict[str, str]] = {
    "critical": "Critical",
    "high": "High",
    "medium": "Medium",
    "low": "Low",
    "unknown": "Unknown",
}


def guess_fragment_language(fragment: str) -> str | None:
    """Optional ISO-ish code from langdetect; None if unavailable or ambiguous."""
    if len(fragment.strip()) < 12:
        return None
    try:
        from langdetect import detect  # type: ignore[import-untyped]

        return detect(fragment)
    except Exception:
        return None


def _normalise_mission(label: str) -> str:
    s = label.strip().lower().rstrip(".")
    head = s.split()[0] if s else "unknown"
    return _MISSION_CANON.get(head, "Unknown")


def _register_windows_cuda_dlls() -> None:
    if sys.platform != "win32":
        return
    from archivist_win_cuda import register_cuda_dll_directories

    register_cuda_dll_directories()


def assert_native_llama_gpu_offload_or_raise() -> None:
    """
    If ``nvidia-smi`` shows an NVIDIA GPU, require a CUDA-enabled ``llama-cpp-python``
    (``llama_supports_gpu_offload()``). Otherwise allow a CPU-only build.

    ``ARCHIVIST_ALLOW_CPU=1`` bypasses the check (debug only). CI uses ``--mock-llm``.
    """
    if os.environ.get("ARCHIVIST_ALLOW_CPU", "").lower() in ("1", "true", "yes"):
        return
    from archivist_win_cuda import describe_system_for_user, query_nvidia_gpu

    if query_nvidia_gpu() is None:
        return

    from llama_cpp import llama_cpp as L

    if not L.llama_supports_gpu_offload():
        detail = describe_system_for_user()
        raise RuntimeError(
            "NVIDIA GPU detected but llama-cpp-python has no CUDA offload (wrong wheel or missing DLLs).\n"
            "Windows: auto-install should have run on first load; try manually: "
            "`python scripts/install_llama_cuda_windows.py`\n"
            "Any OS: run llama-server / LM Studio with GPU layers and use "
            "`--llama-server` / `ARCHIVIST_LLAMA_SERVER`.\n\n"
            f"{detail}"
        )


def parse_archivist_output(raw: str) -> dict[str, str]:
    """Extract title, commentary, mission_relevance from sealed blocks."""
    title = ""
    commentary = ""
    mission = "Unknown"

    if "===TITLE===" in raw and "===COMMENTARY===" in raw:
        try:
            after_title = raw.split("===TITLE===", 1)[1]
            title_part, rest = after_title.split("===COMMENTARY===", 1)
            title = title_part.strip().splitlines()[0].strip()

            if "===MISSION_RELEVANCE===" in rest:
                com_part, mis_part = rest.split("===MISSION_RELEVANCE===", 1)
                commentary = com_part.strip()
                if "===END===" in mis_part:
                    mis_part = mis_part.split("===END===", 1)[0]
                mission_line = mis_part.strip().splitlines()[0].strip()
                mission = _normalise_mission(mission_line)
            else:
                commentary = rest.strip()
        except (ValueError, IndexError):
            pass

    if not title:
        title = "Unsealed Fragment"
    if not commentary:
        commentary = raw.strip()[:2000]
    if mission not in _MISSION_CANON.values():
        mission = "Unknown"

    return {
        "archivist_title": title,
        "archivist_commentary": commentary,
        "mission_relevance": mission,
        "llm_raw_response": raw[:12_000],
    }


class ArchivistLLM:
    """Loads a GGUF model once; call ``complete`` per artefact."""

    def __init__(
        self,
        model_path: str,
        *,
        n_ctx: int = 4096,
        n_gpu_layers: int = -1,
        verbose: bool = False,
    ) -> None:
        _register_windows_cuda_dlls()
        from archivist_win_cuda import maybe_bootstrap_cuda_and_reexec

        maybe_bootstrap_cuda_and_reexec()
        assert_native_llama_gpu_offload_or_raise()
        from llama_cpp import Llama

        self.model_path = model_path
        try:
            self._llm = Llama(
                model_path=model_path,
                n_ctx=n_ctx,
                n_gpu_layers=n_gpu_layers,
                verbose=verbose,
            )
        except OSError as e:
            raise RuntimeError(
                "Native llama.cpp failed to create a context (often a wheel/CPU SIMD mismatch on Windows). "
                "Use a CUDA llama-server binary with full GPU offload and point the scanner at "
                "`--llama-server http://127.0.0.1:PORT` (or `ARCHIVIST_LLAMA_SERVER`). "
                f"Original error: {e!r}"
            ) from e

    def complete(self, artefact: dict[str, Any]) -> dict[str, Any]:
        user = _build_user_message(artefact)
        out = self._llm.create_chat_completion(
            messages=[
                {"role": "system", "content": ARCHIVIST_SYSTEM_PROMPT},
                {"role": "user", "content": user},
            ],
            temperature=0.75,
            max_tokens=700,
        )
        raw = out["choices"][0]["message"]["content"] or ""
        parsed = parse_archivist_output(raw)
        return {**artefact, **parsed, "llm_model_path": self.model_path}


class ArchivistServerLLM:
    """
    OpenAI-compatible HTTP client (``/v1/chat/completions``).

    Run **llama-server** (CUDA build) or LM Studio with the GGUF loaded and GPU
    layers enabled; pass the base URL (e.g. ``http://127.0.0.1:8080``).
    Model id defaults to ``ARCHIVIST_OPENAI_MODEL`` or ``local-model``.
    """

    def __init__(self, base_url: str, *, model: str | None = None, timeout_s: float = 600.0) -> None:
        u = base_url.rstrip("/")
        if u.endswith("/v1"):
            u = u[: -len("/v1")]
        self._api_root = u.rstrip("/")
        self.model = model or os.environ.get("ARCHIVIST_OPENAI_MODEL", "local-model")
        self._timeout_s = timeout_s

    def complete(self, artefact: dict[str, Any]) -> dict[str, Any]:
        user = _build_user_message(artefact)
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": ARCHIVIST_SYSTEM_PROMPT},
                {"role": "user", "content": user},
            ],
            "temperature": 0.75,
            "max_tokens": 700,
        }
        url = f"{self._api_root}/v1/chat/completions"
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=self._timeout_s) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")[:4000]
            raise RuntimeError(f"LLM server HTTP {e.code}: {err_body}") from e
        except urllib.error.URLError as e:
            raise RuntimeError(
                f"Cannot reach LLM server at {self._api_root!r}. "
                "Start llama-server (CUDA) or LM Studio with the OpenAI API enabled."
            ) from e

        try:
            raw = (body.get("choices") or [{}])[0]["message"]["content"] or ""
        except (KeyError, IndexError, TypeError) as e:
            raise RuntimeError(f"Unexpected LLM server JSON shape: {body!r}") from e

        parsed = parse_archivist_output(raw)
        return {**artefact, **parsed, "llm_model_path": f"openai_compat:{self._api_root}"}


def mock_llm_complete(artefact: dict[str, Any]) -> dict[str, Any]:
    """Deterministic placeholder for CI / dev without a GGUF file."""
    frag = artefact.get("fragment", "")[:200]
    raw = (
        f"===TITLE===\n"
        f"Echo of Unfinished Registers\n"
        f"===COMMENTARY===\n"
        f"A thin signal amid static. The catalogue marks what passed the sieve: «{frag}». "
        f"Whether it speaks to the mission or merely resembles speech remains undecided.\n"
        f"===MISSION_RELEVANCE===\n"
        f"Unknown\n"
        f"===END===\n"
    )
    parsed = parse_archivist_output(raw)
    return {**artefact, **parsed, "llm_model_path": "mock"}


def _build_user_message(artefact: dict[str, Any]) -> str:
    coord = artefact.get("coordinates", "")
    frag = artefact.get("fragment", "")
    mscore = artefact.get("mission_keyword_score", 0)
    rname = artefact.get("rarity", {}).get("display_name", "")
    lines = [
        "Catalogue intake packet.",
        f"Archivist coordinates: {coord}",
        f"Mission keyword score (instrument reading, not judgement): {mscore} / 100",
        f"Heuristic rarity tier (instrument reading): {rname}",
        "",
        "Fragment (verbatim from the Archivist Library):",
        frag,
    ]
    lang = guess_fragment_language(frag)
    if lang and lang not in ("en",):
        lines += [
            "",
            f"Lexical hint (automated, Latin channel): fragment may be {lang}. "
            "If so, translate before commentary per your standing orders.",
        ]
    return "\n".join(lines)
