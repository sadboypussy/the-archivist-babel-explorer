"""Tests for archivist_setup (paths + check shape)."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from archivist_setup import gather_setup_checks, resolved_gguf_path


class TestResolvedGguf(unittest.TestCase):
    def test_default_path(self) -> None:
        os.environ.pop("ARCHIVIST_GGUF", None)
        p = resolved_gguf_path()
        self.assertTrue(str(p).endswith("Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf"))

    def test_env_override(self) -> None:
        old = os.environ.get("ARCHIVIST_GGUF")
        try:
            os.environ["ARCHIVIST_GGUF"] = r"D:\weights\model.gguf"
            self.assertEqual(resolved_gguf_path(), Path(r"D:\weights\model.gguf"))
        finally:
            if old is None:
                os.environ.pop("ARCHIVIST_GGUF", None)
            else:
                os.environ["ARCHIVIST_GGUF"] = old


class TestGatherChecks(unittest.TestCase):
    def test_has_python_and_phase1(self) -> None:
        checks = gather_setup_checks()
        ids = {c.id for c in checks}
        self.assertIn("python", ids)
        self.assertIn("phase1", ids)
        self.assertIn("phase4_firebase_sdk", ids)
        self.assertIn("phase4_firebase_json", ids)
        py = next(c for c in checks if c.id == "python")
        self.assertTrue(py.ok)


if __name__ == "__main__":
    unittest.main()
