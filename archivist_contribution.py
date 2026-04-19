"""
Points « Archiviste » — gamification locale (design libre, ajustable).

Chaque trouvaille rapporte :
- une **base** selon la rareté (rang machine : common → mythic) ;
- un **bonus mission** selon la pertinence LLM (Critical / High / …) ;
- un **bonus indices** proportionnel au score mots-clés mission (0–100 → points plafonnés).

Les totaux par pseudo se déduisent du journal ``archivist_log.json`` ; le même calcul
est stocké sur Firestore (champ ``archivist_points``) pour futures vitrines / classements en ligne.
"""

from __future__ import annotations

from typing import Any, Final, Mapping

# Base par rareté (fragment « plus rare » = plus de valeur narrative)
_RARITY_BASE: Final[dict[str, int]] = {
    "common": 12,
    "uncommon": 28,
    "rare": 55,
    "epic": 110,
    "legendary": 220,
    "mythic": 450,
}

# Bonus selon la lecture « histoire / mission » (canon archivist_llm)
_MISSION_BONUS: Final[dict[str, int]] = {
    "Critical": 120,
    "High": 75,
    "Medium": 40,
    "Low": 15,
    "Unknown": 0,
}

# Score mots-clés (0–100) → points additionnels (plafonné)
_KEYWORD_MAX_EXTRA: Final[int] = 42


def points_for_artefact(record: Mapping[str, Any]) -> int:
    """
    Points entiers pour une entrée de journal (ou champs équivalents Firestore).

    Toujours ≥ 1 si l’entrée a un pseudo (sinon 0 = entrée ignorée pour agrégation par explorateur).
    """
    pseudo = str(record.get("explorer_pseudo", "")).strip()
    if not pseudo:
        return 0

    r = record.get("rarity") or {}
    rank = str(r.get("rank", "common")).lower()
    base = _RARITY_BASE.get(rank, _RARITY_BASE["common"])

    raw_rel = str(record.get("mission_relevance", "Unknown")).strip() or "Unknown"
    head = raw_rel.split()[0].lower() if raw_rel else "unknown"
    head_map = {"critical": "Critical", "high": "High", "medium": "Medium", "low": "Low", "unknown": "Unknown"}
    rel_key = head_map.get(head, "Unknown")
    bonus_rel = _MISSION_BONUS[rel_key]

    kw = int(record.get("mission_keyword_score", 0) or 0)
    kw = max(0, min(100, kw))
    bonus_kw = int(round(kw * (_KEYWORD_MAX_EXTRA / 100.0)))

    total = base + bonus_rel + bonus_kw
    return max(1, total)


def aggregate_scores_by_pseudo(rows: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """
    Agrège les points par ``explorer_pseudo``.

    Retourne une liste triée **décroissante** par ``total_points``, chaque élément :
    ``{"pseudo": str, "total_points": int, "artefact_count": int}``.
    """
    buckets: dict[str, list[int]] = {}
    for row in rows:
        pseudo = str(row.get("explorer_pseudo", "")).strip()
        if not pseudo:
            continue
        pts = points_for_artefact(row)
        if pseudo not in buckets:
            buckets[pseudo] = []
        buckets[pseudo].append(pts)

    out: list[dict[str, Any]] = []
    for pseudo, pts_list in buckets.items():
        out.append(
            {
                "pseudo": pseudo,
                "total_points": sum(pts_list),
                "artefact_count": len(pts_list),
            }
        )
    out.sort(key=lambda x: (-int(x["total_points"]), -int(x["artefact_count"]), x["pseudo"]))
    return out
