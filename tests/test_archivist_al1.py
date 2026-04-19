"""Unit tests for archivist_al1 — must stay aligned with ARCHIVIST_LIBRARY_SPEC.md."""

from __future__ import annotations

import hashlib
import sys
import unittest
from pathlib import Path

# Repo root (parent of tests/)
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import archivist_al1 as al1


class TestCanonicalize(unittest.TestCase):
    def test_zero_canonical(self) -> None:
        self.assertEqual(
            al1.canonicalize_coordinate("AL1-" + "0" * 64),
            al1.reference_zero_coordinate(),
        )

    def test_normalise_case_and_whitespace(self) -> None:
        raw = "  al1-" + "A" * 64 + "  "
        self.assertEqual(al1.canonicalize_coordinate(raw), "AL1-" + "a" * 64)

    def test_invalid_prefix(self) -> None:
        with self.assertRaises(al1.CoordinateError):
            al1.canonicalize_coordinate("AL2-" + "0" * 64)

    def test_invalid_length(self) -> None:
        with self.assertRaises(al1.CoordinateError):
            al1.canonicalize_coordinate("AL1-" + "0" * 63)

    def test_invalid_hex(self) -> None:
        with self.assertRaises(al1.CoordinateError):
            al1.canonicalize_coordinate("AL1-" + "g" + "0" * 63)


class TestPageText(unittest.TestCase):
    def test_reference_zero_fingerprint(self) -> None:
        body = al1.page_text_al1(al1.reference_zero_coordinate())
        digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
        self.assertEqual(digest, al1.REFERENCE_ZERO_PAGE_SHA256)
        self.assertEqual(len(body), al1.PAGE_CHARS)
        self.assertEqual(body[:80], al1.REFERENCE_ZERO_FIRST80)
        self.assertEqual(body[-80:], al1.REFERENCE_ZERO_LAST80)

    def test_alphabet_only(self) -> None:
        body = al1.page_text_al1(al1.reference_zero_coordinate())
        for c in body:
            self.assertIn(c, al1.ALPHABET_AL1, repr(c))

    def test_deterministic_sample(self) -> None:
        coord = "AL1-" + "f" * 64
        a = al1.page_text_al1(coord)
        b = al1.page_text_al1(coord)
        self.assertEqual(a, b)


class TestPageLines(unittest.TestCase):
    def test_split(self) -> None:
        body = al1.page_text_al1(al1.reference_zero_coordinate())
        lines = al1.page_lines(body)
        self.assertEqual(len(lines), al1.LINE_COUNT)
        self.assertTrue(all(len(line) == al1.LINE_WIDTH for line in lines))
        self.assertEqual("".join(lines), body)


if __name__ == "__main__":
    unittest.main()
