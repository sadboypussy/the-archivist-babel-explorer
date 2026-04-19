"""archivist_contribution — points et agrégation."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from archivist_contribution import aggregate_scores_by_pseudo, points_for_artefact


def _art(**kwargs: object) -> dict:
    base = {
        "explorer_pseudo": "cactus228",
        "rarity": {"rank": "common", "display_name": "Shard"},
        "mission_relevance": "Unknown",
        "mission_keyword_score": 0,
    }
    base.update(kwargs)
    return base


class TestPoints(unittest.TestCase):
    def test_no_pseudo_zero(self) -> None:
        a = _art(explorer_pseudo="")
        self.assertEqual(points_for_artefact(a), 0)

    def test_rarity_only(self) -> None:
        self.assertGreater(points_for_artefact(_art(rarity={"rank": "mythic", "display_name": "M"})), 400)

    def test_mission_high(self) -> None:
        low = points_for_artefact(_art(mission_relevance="Low"))
        high = points_for_artefact(_art(mission_relevance="High"))
        self.assertGreater(high, low)

    def test_keyword_adds(self) -> None:
        a = points_for_artefact(_art(mission_keyword_score=100))
        b = points_for_artefact(_art(mission_keyword_score=0))
        self.assertGreater(a, b)

    def test_aggregate_order(self) -> None:
        rows = [
            _art(explorer_pseudo="a", rarity={"rank": "common"}, mission_keyword_score=0),
            _art(explorer_pseudo="b", rarity={"rank": "legendary"}, mission_keyword_score=50),
            _art(explorer_pseudo="a", rarity={"rank": "rare"}, mission_keyword_score=20),
        ]
        agg = aggregate_scores_by_pseudo(rows)
        self.assertEqual(agg[0]["pseudo"], "b")
        self.assertEqual(agg[0]["artefact_count"], 1)
        self.assertEqual(agg[1]["pseudo"], "a")
        self.assertEqual(agg[1]["artefact_count"], 2)


if __name__ == "__main__":
    unittest.main()
