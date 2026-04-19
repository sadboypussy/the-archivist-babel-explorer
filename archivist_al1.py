"""
Archivist Library AL1 — reference implementation.

Normative spec: ARCHIVIST_LIBRARY_SPEC.md
"""

from __future__ import annotations

import hashlib
import re
from typing import Final

LIBRARY_VERSION: Final[str] = "AL1"
COORD_PREFIX: Final[str] = "AL1-"  # 4 characters: A, L, digit 1, hyphen
PAGE_CHARS: Final[int] = 3200
_COORD_LEN: Final[int] = len(COORD_PREFIX) + 64  # 68
LINE_WIDTH: Final[int] = 80
LINE_COUNT: Final[int] = 40

ALPHABET_AL1: Final[str] = "abcdefghijklmnopqrstuvwxyz ,."

_PAGE_ID_RE = re.compile(r"^[0-9a-f]{64}$")


class CoordinateError(ValueError):
    """Raised when a coordinate string is not valid COORD_AL1."""


def canonicalize_coordinate(coord: str) -> str:
    """
    Normalise user input to canonical COORD_AL1 (§4.2).

    Raises CoordinateError if the value cannot be normalised.
    """
    s = coord.strip()
    low = s.lower()
    if not low.startswith("al1-") or len(s) < _COORD_LEN:
        raise CoordinateError("Coordinate must start with AL1- followed by 64 hex digits")
    rest = s[len(COORD_PREFIX) :].replace(" ", "")
    hexpart = rest.lower()
    if not _PAGE_ID_RE.match(hexpart):
        raise CoordinateError(
            "After AL1-, expected exactly 64 hexadecimal digits [0-9a-f]"
        )
    return COORD_PREFIX + hexpart


def page_text_al1(coord: str) -> str:
    """
    Deterministic page body: exactly PAGE_CHARS characters from ALPHABET_AL1.

    `coord` may be non-canonical; it is normalised first.
    """
    canonical = canonicalize_coordinate(coord)
    coord_bytes = canonical.encode("utf-8")
    out: list[str] = []
    counter = 0
    while len(out) < PAGE_CHARS:
        block = hashlib.sha256(coord_bytes + counter.to_bytes(8, "little")).digest()
        counter += 1
        for i in range(0, 32, 4):
            u = int.from_bytes(block[i : i + 4], "big")
            out.append(ALPHABET_AL1[u % 29])
    return "".join(out)


def page_lines(page: str) -> list[str]:
    """Split a 3200-char page into 40 lines of 80 characters (§3)."""
    if len(page) != PAGE_CHARS:
        raise ValueError(f"Expected {PAGE_CHARS} characters, got {len(page)}")
    return [page[i : i + LINE_WIDTH] for i in range(0, PAGE_CHARS, LINE_WIDTH)]


def reference_zero_coordinate() -> str:
    """Canonical minimal page id (all-zero), for tests and docs."""
    return COORD_PREFIX + "0" * 64


# SHA256 hex of UTF-8 full page at reference_zero_coordinate() — ARCHIVIST_LIBRARY_SPEC §5.2
REFERENCE_ZERO_PAGE_SHA256 = (
    "11c535f46bc509d104ef92c5414366a8554868bf85e4ac1b528bb30fe73b5d34"
)

REFERENCE_ZERO_FIRST80 = (
    "oq pzeofkxleerybcza.hmbjiclgzrsw,omjmqnhopa,ldvzpi rljoucacpbiaarxbvdghhbf,gdksr"
)

REFERENCE_ZERO_LAST80 = (
    "aqksofhylydqo,dnazptirypngaj.hujkpkrgeeoruqwzbiipkx rosjcgnzmisycwvoxvixpw,kwvfz"
)


if __name__ == "__main__":
    import hashlib as _h

    z = reference_zero_coordinate()
    body = page_text_al1(z)
    assert len(body) == PAGE_CHARS
    digest = _h.sha256(body.encode("utf-8")).hexdigest()
    assert digest == REFERENCE_ZERO_PAGE_SHA256, digest
    assert body[:80] == REFERENCE_ZERO_FIRST80
    assert body[-80:] == REFERENCE_ZERO_LAST80
    print("AL1 self-check OK:", z[:20] + "...", digest[:16] + "...")
