"""
Publish artefacts to Firebase Firestore (Phase 4 — design §5.3).

Credentials (first match wins):

1. ``ARCHIVIST_FIREBASE_CREDENTIALS`` — absolute or relative path to the service account JSON.
2. Else, if present on disk: ``config/firebase-service-account.json`` next to the app
   (installateur / copie manuelle — même sans variable d'environnement).

Do **not** commit credential files. Firestore rules must constrain writes (see
``config/firestore.rules.example``).

Gallery HTML (Netlify / GitHub Pages) uses the JS SDK with a public config; this
module handles **writes** from the Python app and **reads** for the in-app gallery
feed (Admin SDK, same collection).
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Any, Final, Mapping

from archivist_contribution import points_for_artefact

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


def public_gallery_url() -> str:
    """
    Public web gallery (static HTML). Override with ``ARCHIVIST_GALLERY_PUBLIC_URL``;
    else first ``https://`` line in ``community/gallery/PUBLIC_GALLERY.txt``;
    else a safe default.
    """
    env = os.environ.get("ARCHIVIST_GALLERY_PUBLIC_URL", "").strip()
    if env:
        return env
    path = _REPO_ROOT / "community" / "gallery" / "PUBLIC_GALLERY.txt"
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            s = line.strip()
            if s.startswith("https://"):
                return s
    return "https://venerable-dango-f3a334.netlify.app/"


def _get_firestore_client() -> tuple[Any | None, str | None]:
    """Returns ``(client, None)`` or ``(None, error_message)``."""
    cp = credentials_path()
    if cp is None:
        return None, (
            "JSON compte de service absent — placez **config/firebase-service-account.json** "
            "ou définissez **ARCHIVIST_FIREBASE_CREDENTIALS**."
        )
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore
    except ImportError:
        return None, "Installez les deps galerie : pip install -r requirements-app.txt (firebase-admin)."
    try:
        if not firebase_admin._apps:
            firebase_admin.initialize_app(credentials.Certificate(str(cp)))
        return firestore.client(), None
    except Exception as e:
        return None, str(e)


def fetch_gallery_artefacts(*, limit: int = 120) -> dict[str, Any]:
    """
    Read published rows from Firestore (same collection as the public HTML gallery).

    Returns ``{"ok": bool, "error": str | None, "rows": list[dict]}``.
    """
    db, err = _get_firestore_client()
    if err:
        return {"ok": False, "error": err, "rows": []}
    try:
        col = db.collection(gallery_collection_id())
        snap = col.limit(limit).get()
        rows: list[dict[str, Any]] = []
        for doc in snap:
            rows.append({"id": doc.id, **doc.to_dict()})
        rows.sort(key=lambda r: str(r.get("discovered_at") or ""), reverse=True)
        return {"ok": True, "error": None, "rows": rows}
    except Exception as e:
        return {"ok": False, "error": str(e), "rows": []}


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
    out["archivist_points"] = int(points_for_artefact(record))
    return out


def publish_artefact_to_firestore(record: Mapping[str, Any]) -> dict[str, Any]:
    """
    Write one artefact to Firestore. Returns ``{"ok": bool, "doc_id": str|None, "error": str|None}``.
    """
    db, err = _get_firestore_client()
    if err:
        return {"ok": False, "doc_id": None, "error": err}

    payload = sanitize_for_gallery(record)
    if not payload["coordinates"]:
        return {"ok": False, "doc_id": None, "error": "Artefact sans coordonnées, publication refusée."}

    doc_id = stable_document_id(record)

    try:
        col = db.collection(gallery_collection_id())
        col.document(doc_id).set(payload, merge=True)
    except Exception as e:
        return {"ok": False, "doc_id": doc_id, "error": str(e)}

    return {"ok": True, "doc_id": doc_id, "error": None}
