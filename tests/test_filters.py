"""Tests for archivist_filters (Phase 1 pipeline)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from archivist_al1 import PAGE_CHARS
from archivist_filters import (
    assign_rarity,
    dictionary_coverage,
    extract_fragment,
    filter1_entropy,
    filter2_dictionary,
    mission_keyword_score,
    shannon_entropy,
)


def _pad_al1(s: str) -> str:
    s = s.lower()
    if len(s) >= PAGE_CHARS:
        return s[:PAGE_CHARS]
    pad = " .," * 2000
    return (s + pad)[:PAGE_CHARS]


class TestFilter1(unittest.TestCase):
    def test_rejects_all_same_char(self) -> None:
        page = "a" * PAGE_CHARS
        ok, m = filter1_entropy(page)
        self.assertFalse(ok)
        self.assertLess(m["entropy"], 1.0)

    def test_accepts_diverse_page(self) -> None:
        from archivist_al1 import page_text_al1, reference_zero_coordinate

        page = page_text_al1(reference_zero_coordinate())
        ok, m = filter1_entropy(page)
        self.assertTrue(ok)
        self.assertGreater(m["entropy"], 3.0)


class TestFilter2(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        from spellchecker import SpellChecker

        cls.spell = SpellChecker()

    def test_finds_consecutive_real_words(self) -> None:
        page = _pad_al1("the cat sat on the mat ")
        r = filter2_dictionary(page, self.spell)
        self.assertTrue(r.passes)
        self.assertGreaterEqual(r.max_consecutive_real_words, 2)
        self.assertGreater(len(r.longest_run_tokens), 0)

    def test_rejects_random_letters(self) -> None:
        page = _pad_al1("qxzk qwvm zyxw ")
        r = filter2_dictionary(page, self.spell)
        self.assertFalse(r.passes)


class TestMissionAndRarity(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        from spellchecker import SpellChecker

        cls.spell = SpellChecker()

    def test_mission_hits_light(self) -> None:
        page = _pad_al1("the light signal here ")
        score, hits = mission_keyword_score(page)
        self.assertGreater(score, 0)
        self.assertIn("light", hits)

    def test_rarity_common(self) -> None:
        page = _pad_al1("the cat sat ")
        r = assign_rarity(3, 0, 0.1, page)
        self.assertEqual(r.rank, "common")

    def test_coverage(self) -> None:
        page = _pad_al1("the cat sat ")
        c = dictionary_coverage(page, self.spell)
        self.assertGreater(c, 0.1)


class TestExtractFragment(unittest.TestCase):
    def test_span(self) -> None:
        page = _pad_al1("aaa the cat bbb")
        frag = extract_fragment(page, 4, 11, context=5)
        self.assertIn("the cat", frag)


class TestEntropy(unittest.TestCase):
    def test_uniform(self) -> None:
        h = shannon_entropy("abcd")
        self.assertAlmostEqual(h, 2.0, places=3)


if __name__ == "__main__":
    unittest.main()
