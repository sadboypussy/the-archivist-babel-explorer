"""
Publish artefacts to Firebase Firestore (Phase 4 — design §5.3).

Credentials (first match wins):

1. ``ARCHIVIST_FIREBASE_CREDENTIALS`` — absolute or relative path to the service account JSON.
2. Else, if present on disk: ``config/firebase-service-account.json`` next to the app
   (installateur / copie manuelle — même sans variable d'environnement).

Do **not** commit credential files. Firestore rules must constrain writes (see
``config/firestore.rules.example``).

Gallery HTML (GitHub Pages) can keep using the JS SDK with a public config; this
module is for **writes** from the Python / Streamlit app only.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Any, Final, Mapping

_REPO_ROOT = Path(__file__).resolve().parent
_DEFAULT_SERVICE_ACCOUNT_JSON = _REPO_ROOT / "config" / "firebase-service-account.json"

_MAX_FRAGMENT: Final[int] = 12_000
_MAX_COMMENTARY: Final[int] = 8_000
_MAX_TITLE: Final[int] = 500
_MAX_COORD: Final[int] = 256
_MAX_PSEUDO: Final[int] = 120


def credentials_path() -> Path | None:
    raw = os.environ.get("ARCHIVIST_FIREBASE_CREDENTIALS", "").strip()
    if raw:
        p = Path(raw)
        if not p.is_absolute():
            p = (_REPO_ROOT / p).resolve()
        return p if p.is_file() else None
    if _DEFAULT_SERVICE_ACCOUNT_JSON.is_file():
        return _DEFAULT_SERVICE_ACCOUNT_JSON
    return None


def is_community_configured() -> bool:
    return credentials_path() is not None


def gallery_collection_id() -> str:
    return os.environ.get("ARCHIVIST_FIRESTORE_COLLECTION", "artefacts").strip() or "artefacts"


def stable_document_id(record: Mapping[str, Any]) -> str:
    """Deterministic id from coordinates + discovery time (idempotent re-publish)."""
    coord = str(record.get("coordinates", ""))[: _MAX_COORD]
    when = str(record.get("discovered_at", ""))[:80]
    h = hashlib.sha256(f"{coord}|{when}".encode("utf-8")).hexdigest()
    return h[:40]


def sanitize_for_gallery(record: Mapping[str, Any]) -> dict[str, Any]:
    """Subset and size caps for Firestore (design §5.3)."""
    r = record.get("rarity") or {}
    if not isinstance(r, dict):
        r = {}
    out: dict[str, Any] = {
        "library_version": str(record.get("library_version", ""))[:32],
        "coordinates": str(record.get("coordinates", ""))[:_MAX_COORD],
        "fragment": str(record.get("fragment", ""))[:_MAX_FRAGMENT],
        "rarity_rank": str(r.get("rank", ""))[:32],
        "rarity_display_name": str(r.get("display_name", ""))[:120],
        "archivist_title": str(record.get("archivist_title", ""))[:_MAX_TITLE],
        "archivist_commentary": str(record.get("archivist_commentary", ""))[:_MAX_COMMENTARY],
        "mission_relevance": str(record.get("mission_relevance", ""))[:40],
        "mission_keyword_score": int(record.get("mission_keyword_score", 0) or 0),
        "explorer_pseudo": str(record.get("explorer_pseudo", ""))[:_MAX_PSEUDO],
        "discovered_at": str(record.get("discovered_at", ""))[:80],
    }
    if record.get("mission_keyword_hits") is not None:
        out["mission_keyword_hits"] = record.get("mission_keyword_hits")
    return out


def publish_artefact_to_firestore(record: Mapping[str, Any]) -> dict[str, Any]:
    """
    Write one artefact to Firestore. Returns ``{"ok": bool, "doc_id": str|None, "error": str|None}``.
    """
    cp = credentials_path()
    if cp is None:
        return {
            "ok": False,
            "doc_id": None,
            "error": "Définissez ARCHIVIST_FIREBASE_CREDENTIALS (chemin vers JSON compte de service).",
        }

    try:
        import firebase_admin
        from firebase_admin import credentials, firestore
    except ImportError:
        return {
            "ok": False,
            "doc_id": None,
            "error": "Installez les deps galerie : pip install -r requirements-app.txt (firebase-admin).",
        }

    payload = sanitize_for_gallery(record)
    if not payload["coordinates"]:
        return {"ok": False, "doc_id": None, "error": "Artefact sans coordonnées, publication refusée."}

    doc_id = stable_document_id(record)

    try:
        if not firebase_admin._apps:
            cred = credentials.Certificate(str(cp))
            firebase_admin.initialize_app(cred)
        db = firestore.client()
        col = db.collection(gallery_collection_id())
        col.document(doc_id).set(payload, merge=True)
    except Exception as e:
        return {"ok": False, "doc_id": doc_id, "error": str(e)}

    return {"ok": True, "doc_id": doc_id, "error": None}
