"""Tests for archivist_llm (Phase 2 parsing + mock)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from archivist_llm import mock_llm_complete, parse_archivist_output


class TestParse(unittest.TestCase):
    def test_parse_blocks(self) -> None:
        raw = """Some preamble in voice.

===TITLE===
Cold Iron Ledger of Fading Stars
===COMMENTARY===
A thin inscription. The void remembers names longer than cities.
The Emissary would have filed it without comment.
===MISSION_RELEVANCE===
Medium
===END===
"""
        d = parse_archivist_output(raw)
        self.assertIn("Cold Iron", d["archivist_title"])
        self.assertIn("thin inscription", d["archivist_commentary"])
        self.assertEqual(d["mission_relevance"], "Medium")

    def test_parse_unknown_fallback(self) -> None:
        d = parse_archivist_output("no structure here")
        self.assertEqual(d["mission_relevance"], "Unknown")


class TestMock(unittest.TestCase):
    def test_mock_merges(self) -> None:
        base = {
            "coordinates": "AL1-" + "a" * 64,
            "fragment": "the signal remains",
            "mission_keyword_score": 5,
            "rarity": {"rank": "common", "display_name": "Shard of Static"},
        }
        out = mock_llm_complete(base)
        self.assertIn("archivist_title", out)
        self.assertIn("archivist_commentary", out)
        self.assertEqual(out["llm_model_path"], "mock")
        self.assertIn("the signal remains", out["archivist_commentary"])


if __name__ == "__main__":
    unittest.main()
