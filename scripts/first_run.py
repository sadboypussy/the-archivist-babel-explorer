#!/usr/bin/env python3
"""
First-run / environment check for The Archivist.

Usage::

    python scripts/first_run.py
    python scripts/first_run.py --json --non-interactive
    python scripts/first_run.py --download-model
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from archivist_setup import main

if __name__ == "__main__":
    raise SystemExit(main())
