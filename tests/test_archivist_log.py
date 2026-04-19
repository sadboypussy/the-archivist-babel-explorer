"""Tests for archivist_log."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from archivist_log import extend_log, read_log


class TestExtendLog(unittest.TestCase):
    def test_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "log.json"
            extend_log(p, [{"a": 1}])
            extend_log(p, [{"b": 2}, {"c": 3}])
            data = json.loads(p.read_text(encoding="utf-8"))
            self.assertEqual(len(data), 3)
            self.assertEqual(data[0]["a"], 1)
            self.assertIn("discovered_at", data[1])


class TestReadLog(unittest.TestCase):
    def test_read_empty(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "empty.json"
            p.write_text("[]", encoding="utf-8")
            self.assertEqual(read_log(p), [])

    def test_read_matches_extend(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "log.json"
            extend_log(p, [{"x": 1}])
            rows = read_log(p)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["x"], 1)


if __name__ == "__main__":
    unittest.main()
