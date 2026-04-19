"""Regression tests for Windows CUDA wheel URL resolution."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from archivist_win_cuda import dougeeai_native_wheel_url


class TestDougeeaiWheelUrls(unittest.TestCase):
    def test_sm89_cuda130_cp311_shape(self) -> None:
        u = dougeeai_native_wheel_url(sm="89", cuda_tag="cuda13.0", abi_tag="cp311")
        self.assertIn("v0.3.16-cuda13.0-sm89-py311", u)
        self.assertIn("llama_cpp_python-0.3.16+cuda13.0.sm89.ada-cp311-cp311-win_amd64.whl", u)

    def test_blackwell_sm120_py3_none(self) -> None:
        u = dougeeai_native_wheel_url(sm="120", cuda_tag="cuda13.0")
        self.assertIn("v0.3.20-cuda13.0-sm100-sm120", u)
        self.assertIn("llama_cpp_python-0.3.20+cuda13.0.sm100.sm120.blackwell-py3-none-win_amd64.whl", u)


if __name__ == "__main__":
    unittest.main()
