"""
Phase 1 detection pipeline — ARCHIVIST design §3 (calibrated heuristics, v1).

Filter thresholds are tunable constants; adjust after real-world benchmarks.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from archivist_al1 import PAGE_CHARS
from archivist_mission_keywords import MISSION_KEYWORDS

if TYPE_CHECKING:
    from spellchecker import SpellChecker

# --- Filter 1 (entropy / vowel structure) ---------------------------------

# Shannon entropy on the 29-symbol distribution; uniform random peaks ~4.85.
F1_MIN_ENTROPY: Final[float] = 2.4
F1_MAX_DOMINANCE: Final[float] = 0.42  # any single character > this share → reject
F1_MIN_VOWELS_IN_LETTERS: Final[int] = 1  # among a–z only
F1_VOWEL_RATIO_LETTERS_MIN: Final[float] = 0.08
F1_VOWEL_RATIO_LETTERS_MAX: Final[float] = 0.72

_VOWELS = frozenset("aeiou")


def shannon_entropy(s: str) -> float:
    if not s:
        return 0.0
    n = len(s)
    counts: dict[str, int] = {}
    for ch in s:
        counts[ch] = counts.get(ch, 0) + 1
    return -sum((c / n) * math.log2(c / n) for c in counts.values())


def filter1_entropy(page: str) -> tuple[bool, dict[str, float | int]]:
    """
    Speed layer. Returns (passes, metrics) for logging / UI.
    """
    if len(page) != PAGE_CHARS:
        return False, {"error": len(page)}

    h = shannon_entropy(page)
    n = len(page)
    dom = max(page.count(c) for c in set(page)) / n

    letters = [c for c in page if c.isalpha()]
    if not letters:
        return False, {"entropy": h, "dominance": dom, "vowel_ratio": 0.0}

    vowels = sum(1 for c in letters if c in _VOWELS)
    vr = vowels / len(letters)

    ok = (
        h >= F1_MIN_ENTROPY
        and dom <= F1_MAX_DOMINANCE
        and vowels >= F1_MIN_VOWELS_IN_LETTERS
        and F1_VOWEL_RATIO_LETTERS_MIN <= vr <= F1_VOWEL_RATIO_LETTERS_MAX
    )
    metrics = {"entropy": h, "dominance": dom, "vowel_ratio": vr, "letter_count": len(letters)}
    return ok, metrics


# --- Filter 2 (dictionary / consecutive real words) ------------------------
# Calibrated per design §8.1: short English tokens ("in", "at", …) appear
# constantly in random AL1 text; require meaningful tokens + longer runs.

FILTER2_MIN_TOKEN_LEN: Final[int] = 3
FILTER2_MIN_CONSECUTIVE: Final[int] = 3

_TOKEN_RE = re.compile(r"[a-z]+")


@dataclass(frozen=True)
class Filter2Result:
    passes: bool
    max_consecutive_real_words: int
    tokens_checked: int
    """Longest run of spell-known letter-tokens in left-to-right order."""
    longest_run_tokens: list[str]
    run_start_char_index: int
    run_end_char_index: int  # exclusive span in page for excerpt


def _letter_runs_with_spans(page: str) -> list[tuple[str, int, int]]:
    """[(token, start, end), ...] for lowercase a-z runs only."""
    out: list[tuple[str, int, int]] = []
    for m in _TOKEN_RE.finditer(page.lower()):
        out.append((m.group(), m.start(), m.end()))
    return out


def filter2_dictionary(page: str, spell: SpellChecker) -> Filter2Result:
    runs = _letter_runs_with_spans(page)
    if not runs:
        return Filter2Result(False, 0, 0, [], 0, 0)

    max_run = 0
    best_tokens: list[str] = []
    best_start = best_end = 0

    cur_tokens: list[str] = []
    cur_start = cur_end = 0

    for tok, start, end in runs:
        if len(tok) < FILTER2_MIN_TOKEN_LEN:
            cur_tokens = []
            continue
        unknown = spell.unknown([tok])
        known = len(unknown) == 0
        if known:
            if not cur_tokens:
                cur_start = start
            cur_tokens.append(tok)
            cur_end = end
            if len(cur_tokens) > max_run:
                max_run = len(cur_tokens)
                best_tokens = list(cur_tokens)
                best_start = cur_start
                best_end = cur_end
        else:
            cur_tokens = []

    passes = max_run >= FILTER2_MIN_CONSECUTIVE
    return Filter2Result(
        passes=passes,
        max_consecutive_real_words=max_run,
        tokens_checked=len(runs),
        longest_run_tokens=best_tokens,
        run_start_char_index=best_start,
        run_end_char_index=best_end,
    )


# --- Filter 3 (mission keyword score) -------------------------------------


def mission_keyword_score(page: str) -> tuple[int, dict[str, int]]:
    """
    Returns (0–100 score, per-keyword hit counts for transparency).
    """
    p = page.lower()
    hits: dict[str, int] = {}
    raw = 0
    for kw in MISSION_KEYWORDS:
        c = p.count(kw)
        if c:
            hits[kw] = c
        raw += min(c * 9, 27)
    return min(raw, 100), hits


# --- Dictionary coverage (for rarity, design §3.3) ------------------------


def dictionary_coverage(page: str, spell: SpellChecker) -> float:
    """Share of a–z characters that fall inside spell-known letter tokens."""
    letters = [c for c in page if c.isalpha()]
    if not letters:
        return 0.0
    covered = 0
    for m in _TOKEN_RE.finditer(page.lower()):
        w = m.group()
        if not spell.unknown([w]):
            covered += m.end() - m.start()
    return covered / len(letters)


# --- Rarity (heuristic v1 — design §3.3) -----------------------------------


@dataclass(frozen=True)
class RarityTier:
    rank: str  # machine id
    display_name: str


def assign_rarity(
    max_consecutive: int,
    mission_score: int,
    coverage: float,
    page: str,
) -> RarityTier:
    """
    Heuristic mapping; refine after corpus testing (design §8.1).

    With ``FILTER2_MIN_CONSECUTIVE == 3``, the minimum passing page already has
    three real words; tiers start from that floor (Common ≈ marginal pass).
    """
    dots = page.count(".")

    if max_consecutive >= 14 and dots >= 2 and mission_score >= 30:
        return RarityTier("mythic", "The Emissary Speaks")
    if max_consecutive >= 11 and dots >= 1 and coverage >= 0.18:
        return RarityTier("legendary", "Transmission Fragment")
    if max_consecutive >= 9 or (max_consecutive >= 7 and coverage >= 0.35):
        return RarityTier("epic", "Echo of the Emissary")
    if max_consecutive >= 5 or (max_consecutive >= 4 and coverage >= 0.22):
        return RarityTier("rare", "Buried Signal")
    if max_consecutive >= 4:
        return RarityTier("uncommon", "Lost Syllable")
    return RarityTier("common", "Shard of Static")


def extract_fragment(
    page: str,
    start: int,
    end: int,
    context: int = 120,
) -> str:
    """Verbatim slice around the flagged run for logging (design: fragment never altered)."""
    lo = max(0, start - context)
    hi = min(len(page), end + context)
    return page[lo:hi]
