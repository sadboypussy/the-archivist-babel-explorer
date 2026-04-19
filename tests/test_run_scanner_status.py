"""Integration smoke: run_scanner --status-file JSON."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class TestRunScannerStatusFile(unittest.TestCase):
    def test_status_file_done(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            log = Path(d) / "log.json"
            st = Path(d) / "status.json"
            cmd = [
                sys.executable,
                str(ROOT / "run_scanner.py"),
                "--pages",
                "8",
                "--batch",
                "2",
                "--workers",
                "1",
                "--mock-llm",
                "--log",
                str(log),
                "--status-file",
                str(st),
            ]
            r = subprocess.run(cmd, cwd=str(ROOT), timeout=120, capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, msg=r.stderr[-2000:] if r.stderr else "")
            self.assertTrue(st.is_file(), msg="status file missing")
            data = json.loads(st.read_text(encoding="utf-8"))
            self.assertEqual(data.get("phase"), "done")
            self.assertEqual(data.get("total_target"), 8)
            self.assertEqual(data.get("total_scanned"), 8)


class TestWriteScanStatus(unittest.TestCase):
    def test_atomic_write_roundtrip(self) -> None:
        from run_scanner import _write_scan_status

        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "s.json"
            _write_scan_status(p, {"phase": "running", "x": 1})
            self.assertEqual(json.loads(p.read_text(encoding="utf-8"))["x"], 1)


if __name__ == "__main__":
    unittest.main()
