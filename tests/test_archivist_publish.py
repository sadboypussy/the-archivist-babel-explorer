"""archivist_publish — sanitisation & ids (no Firebase in CI)."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from archivist_publish import (
    credentials_path,
    gallery_collection_id,
    public_gallery_url,
    sanitize_for_gallery,
    stable_document_id,
)


class TestSanitize(unittest.TestCase):
    def test_stable_id(self) -> None:
        a = {"coordinates": "AL1-" + "a" * 64, "discovered_at": "2026-01-01T00:00:00+00:00"}
        b = {"coordinates": "AL1-" + "b" * 64, "discovered_at": "2026-01-01T00:00:00+00:00"}
        self.assertNotEqual(stable_document_id(a), stable_document_id(b))
        self.assertEqual(stable_document_id(a), stable_document_id(dict(a)))

    def test_sanitize_truncates(self) -> None:
        long_frag = "x" * 20_000
        row = {
            "coordinates": "AL1-abc",
            "fragment": long_frag,
            "rarity": {"rank": "common", "display_name": "Shard"},
            "archivist_title": "t" * 600,
            "mission_keyword_score": 42,
            "explorer_pseudo": "me",
            "discovered_at": "2026-04-19",
        }
        out = sanitize_for_gallery(row)
        self.assertLessEqual(len(out["fragment"]), 12_000)
        self.assertLessEqual(len(out["archivist_title"]), 500)
        self.assertEqual(out["mission_keyword_score"], 42)
        self.assertIn("archivist_points", out)
        self.assertGreater(int(out["archivist_points"]), 0)


class TestCredentialsPath(unittest.TestCase):
    def test_env_absolute_file(self) -> None:
        old = os.environ.pop("ARCHIVIST_FIREBASE_CREDENTIALS", None)
        try:
            p = Path(__file__).resolve().parent.parent / "tests" / "test_archivist_publish.py"
            os.environ["ARCHIVIST_FIREBASE_CREDENTIALS"] = str(p)
            self.assertEqual(credentials_path(), p.resolve())
        finally:
            if old is None:
                os.environ.pop("ARCHIVIST_FIREBASE_CREDENTIALS", None)
            else:
                os.environ["ARCHIVIST_FIREBASE_CREDENTIALS"] = old


class TestPublicGalleryUrl(unittest.TestCase):
    def test_env_overrides_file(self) -> None:
        old = os.environ.pop("ARCHIVIST_GALLERY_PUBLIC_URL", None)
        try:
            os.environ["ARCHIVIST_GALLERY_PUBLIC_URL"] = "https://example.test/gallery/"
            self.assertEqual(public_gallery_url(), "https://example.test/gallery/")
        finally:
            if old is None:
                os.environ.pop("ARCHIVIST_GALLERY_PUBLIC_URL", None)
            else:
                os.environ["ARCHIVIST_GALLERY_PUBLIC_URL"] = old


class TestCollectionEnv(unittest.TestCase):
    def test_default_collection(self) -> None:
        old = os.environ.pop("ARCHIVIST_FIRESTORE_COLLECTION", None)
        try:
            self.assertEqual(gallery_collection_id(), "artefacts")
        finally:
            if old is not None:
                os.environ["ARCHIVIST_FIRESTORE_COLLECTION"] = old


if __name__ == "__main__":
    unittest.main()
