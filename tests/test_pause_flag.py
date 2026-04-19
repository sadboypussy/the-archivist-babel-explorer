"""Pause flag file behaviour (run_scanner)."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from run_scanner import _pause_requested


class TestPauseRequested(unittest.TestCase):
    def test_missing_file(self) -> None:
        self.assertFalse(_pause_requested(None))
        self.assertFalse(_pause_requested(ROOT / "nonexistent_pause_flag_12345.txt"))

    def test_pause_line(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "p.txt"
            p.write_text("pause\n", encoding="utf-8")
            self.assertTrue(_pause_requested(p))

    def test_empty_means_no_pause(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "p.txt"
            p.write_text("\n\n", encoding="utf-8")
            self.assertFalse(_pause_requested(p))

    def test_other_directive_not_pause(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "p.txt"
            p.write_text("go\n", encoding="utf-8")
            self.assertFalse(_pause_requested(p))


if __name__ == "__main__":
    unittest.main()
