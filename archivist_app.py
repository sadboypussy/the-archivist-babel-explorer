"""
The Archivist — local UI (Streamlit, Phase 3 shell).

Run from repository root::

    pip install -r requirements.txt -r requirements-llm.txt -r requirements-app.txt
    streamlit run archivist_app.py

See ``THE_ARCHIVIST_Design_Document_v2.md`` §6 and §5.5.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st

from archivist_log import read_log
from archivist_paths import DEFAULT_GGUF_PATH
from archivist_publish import is_community_configured, publish_artefact_to_firestore, stable_document_id
from archivist_ui_theme import inject_archivist_ui

_PSEUDO_FILE = _ROOT / ".explorer_pseudo.txt"
_DEFAULT_LOG = _ROOT / "archivist_log.json"
_DEFAULT_SCAN_STATUS = _ROOT / ".archivist_scan_status.json"
_DEFAULT_PAUSE_FLAG = _ROOT / ".archivist_scan_pause"

_RARITY_ORDER = {
    "mythic": 6,
    "legendary": 5,
    "epic": 4,
    "rare": 3,
    "uncommon": 2,
    "common": 1,
}

_RARITY_COLOR = {
    "common": "#8b8c9c",
    "uncommon": "#4e9c6d",
    "rare": "#4a7dc2",
    "epic": "#9b51e0",
    "legendary": "#d4a43a",
    "mythic": "#c94c59",
}

_BRIEFING = """
The vacuum does not care about your era. Somewhere in the Archivist Library — a combinatorial
space defined only by this engine — fragments of text surface by chance. Your task is not to
search for what you already know, but to **listen** while the scan runs, and to name what returns.

When the filters mark a page, the Archivist reads the fragment in the voice of the catalogue:
cryptic titles, melancholic commentary, and a seal the machine can parse.

**Name yourself, Explorer.** What follows is logged under your sign.
""".strip()


def _load_pseudo_disk() -> str:
    if _PSEUDO_FILE.is_file():
        return _PSEUDO_FILE.read_text(encoding="utf-8").strip()
    return ""


def _save_pseudo_disk(name: str) -> None:
    _PSEUDO_FILE.write_text(name.strip()[:120], encoding="utf-8")


def _init_session() -> None:
    if "explorer_pseudo" not in st.session_state:
        st.session_state.explorer_pseudo = _load_pseudo_disk()
    if "scan_proc" not in st.session_state:
        st.session_state.scan_proc = None


def _read_scan_status(path: Path) -> dict[str, object] | None:
    if not path.is_file():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return raw if isinstance(raw, dict) else None


def _atmosphere_glyphs(total_scanned: int) -> str:
    """Cheap deterministic ‘noise field’ from scan count (design §6.2 direction)."""
    glyphs = "·░▒▓╱╲ωabcdefghijklmnopqrstuvwxyz"
    w = 56
    return "".join(glyphs[(total_scanned * 17 + i * 11) % len(glyphs)] for i in range(w))


def _live_scan_panel(status_path: Path) -> None:
    """Refreshes while a subprocess scan is running (needs Streamlit ≥ 1.33 for ``fragment``)."""

    def paint() -> None:
        data = _read_scan_status(status_path)
        if not data:
            st.caption("En attente du fichier de statut…")
            return
        ts = int(data.get("total_scanned", 0) or 0)
        ta = int(data.get("total_artefacts", 0) or 0)
        tt = max(1, int(data.get("total_target", 1) or 1))
        phase = str(data.get("phase", ""))
        c1, c2, c3 = st.columns(3)
        c1.metric("Pages parcourues", f"{ts:,} / {tt:,}")
        c2.metric("Artefacts", f"{ta:,}")
        c3.metric("Phase", phase)
        st.progress(min(1.0, ts / tt), text="Progression")
        st.caption("Champ statistique (aperçu)")
        st.code(_atmosphere_glyphs(ts), language=None)

    if hasattr(st, "fragment"):
        @st.fragment(run_every=1.0)
        def _tick() -> None:
            proc = st.session_state.scan_proc
            if proc is not None and proc.poll() is None:
                paint()
            else:
                paint()

        _tick()
    else:
        paint()
        st.caption("Pour un rafraîchissement automatique, utilisez Streamlit **≥ 1.33** (``st.fragment``).")


def _tab_briefing() -> None:
    st.markdown(_BRIEFING)
    st.divider()
    name = st.text_input(
        "Nom d’explorateurice (affiché sur les découvertes)",
        value=st.session_state.explorer_pseudo,
        placeholder="ex. Moriarty_IX",
    )
    if st.button("Enregistrer et continuer", type="primary"):
        st.session_state.explorer_pseudo = (name or "Anonymous").strip()
        _save_pseudo_disk(st.session_state.explorer_pseudo)
        st.success(f"Enregistré : **{st.session_state.explorer_pseudo}**")


def _tab_scanner() -> None:
    if not st.session_state.explorer_pseudo:
        st.warning("Indiquez d’abord un nom dans l’onglet **Briefing**.")
        return

    st.caption(
        "Le scan tourne dans un processus séparé : vous pouvez **suivre la progression** ci-dessous. "
        "Pour des très longues sessions, le CLI reste le plus souple (§8.1)."
    )

    col1, col2 = st.columns(2)
    with col1:
        pages = st.number_input("Pages à parcourir", min_value=1, value=200, step=50)
        workers = st.number_input("Processus parallèles", min_value=1, value=max(1, (os.cpu_count() or 2) - 1))
    with col2:
        log_path = st.text_input("Fichier journal", value=str(_DEFAULT_LOG))
        status_path = st.text_input(
            "Fichier de statut (JSON)",
            value=str(_DEFAULT_SCAN_STATUS),
            help="Mis à jour par run_scanner.py pour l’aperçu live.",
        )
        pause_path = st.text_input(
            "Fichier pause (contrôle)",
            value=str(_DEFAULT_PAUSE_FLAG),
            help="Écrire la ligne « pause » pour suspendre entre les lots ; supprimer le fichier ou vider pour reprendre.",
        )

    mode = st.radio(
        "Mode Archiviste",
        ("mock (sans modèle)", "GGUF local", "Serveur llama (URL)"),
        horizontal=True,
    )
    gguf = st.text_input("Chemin GGUF", value=str(DEFAULT_GGUF_PATH), disabled=mode != "GGUF local")
    server_url = st.text_input(
        "URL OpenAI-compatible (ex. http://127.0.0.1:8080)",
        disabled=mode != "Serveur llama (URL)",
    )

    cmd = [
        sys.executable,
        str(_ROOT / "run_scanner.py"),
        "--pages",
        str(int(pages)),
        "--workers",
        str(int(workers)),
        "--log",
        log_path,
        "--status-file",
        status_path,
        "--pause-flag-file",
        pause_path,
        "--pseudo",
        st.session_state.explorer_pseudo,
    ]
    if mode == "mock (sans modèle)":
        cmd.append("--mock-llm")
    elif mode == "Serveur llama (URL)":
        if not server_url.strip():
            st.error("Indiquez une URL.")
            return
        cmd.extend(["--llama-server", server_url.strip()])
    else:
        if not Path(gguf).is_file():
            st.error(f"GGUF introuvable : {gguf}")
            return
        cmd.extend(["--gguf", gguf])

    st.code(" ".join(cmd), language="bash")

    proc = st.session_state.scan_proc
    st_path = Path(status_path)
    pause_p = Path(pause_path)
    if proc is not None and proc.poll() is None:
        st.info("Scan **en cours** — progression :")
        _live_scan_panel(st_path)
        c_p1, c_p2, c_p3 = st.columns(3)
        with c_p1:
            if st.button("Pause (entre les lots)", key="btn_pause_scan"):
                try:
                    pause_p.parent.mkdir(parents=True, exist_ok=True)
                    pause_p.write_text("pause\n", encoding="utf-8")
                except OSError as e:
                    st.warning(str(e))
                st.rerun()
        with c_p2:
            if st.button("Reprendre", key="btn_resume_scan"):
                try:
                    if pause_p.exists():
                        pause_p.unlink()
                except OSError as e:
                    st.warning(str(e))
                st.rerun()
        with c_p3:
            if st.button("Forcer l’arrêt (tuer le processus)", type="secondary", key="kill_scan"):
                proc.terminate()
                st.session_state.scan_proc = None
                try:
                    if pause_p.exists():
                        pause_p.unlink()
                except OSError:
                    pass
                st.rerun()
    elif proc is not None:
        code = proc.poll()
        err = (proc.stderr.read() if proc.stderr else "") or ""
        if code == 0:
            st.success(f"Processus terminé (code {code}).")
        else:
            st.error(f"Processus terminé avec le code {code}.")
            if err.strip():
                st.text(err[-8000:])
        st.session_state.scan_proc = None
        done = _read_scan_status(st_path)
        if done and str(done.get("phase")) == "done":
            st.metric("Résumé", f"{done.get('total_scanned', 0)} pages · {done.get('total_artefacts', 0)} artefacts")

    if st.button("Lancer le scan", type="primary"):
        active = st.session_state.scan_proc
        if active is not None and active.poll() is None:
            st.error("Attendez la fin du scan en cours.")
        else:
            try:
                st_path.parent.mkdir(parents=True, exist_ok=True)
                if st_path.exists():
                    st_path.unlink()
                if pause_p.exists():
                    pause_p.unlink()
            except OSError:
                pass
            st.session_state.scan_proc = subprocess.Popen(
                cmd,
                cwd=str(_ROOT),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
            )
            st.rerun()

    if int(pages) > 10_000:
        st.warning("Très grand nombre de pages : prévoir du temps ; le fichier de statut se met à jour en continu.")


def _tab_discoveries() -> None:
    log_path = Path(st.text_input("Journal à lire", value=str(_DEFAULT_LOG)))
    sort_mode = st.selectbox(
        "Trier par",
        ("Date (récent d’abord)", "Score mission (décroissant)", "Rareté (décroissant)"),
    )
    if st.button("Rafraîchir"):
        st.rerun()

    rows = read_log(log_path)
    if not rows:
        st.info("Aucun artefact dans ce journal pour l’instant.")
        return

    rows_view = list(rows)
    if sort_mode.startswith("Score"):
        rows_view.sort(key=lambda a: int(a.get("mission_keyword_score", 0) or 0), reverse=True)
    elif sort_mode.startswith("Rareté"):
        rows_view.sort(
            key=lambda a: _RARITY_ORDER.get(str(a.get("rarity", {}).get("rank", "common")).lower(), 0),
            reverse=True,
        )
    else:
        rows_view.sort(key=lambda a: str(a.get("discovered_at", "")), reverse=True)

    st.metric("Artefacts enregistrés", len(rows_view))
    for art in rows_view[:50]:
        r = art.get("rarity", {})
        rank = str(r.get("rank", "common")).lower()
        color = _RARITY_COLOR.get(rank, "#aaaaaa")
        title = art.get("archivist_title") or "—"
        label = f"{r.get('display_name', '?')} · {title}"
        with st.expander(label):
            st.markdown(
                f'<p style="margin:0 0 0.5rem 0"><span style="color:{color};font-weight:700">'
                f"{r.get('display_name', '?')}</span> · <code>{rank}</code></p>",
                unsafe_allow_html=True,
            )
            c_a, c_b = st.columns(2)
            with c_a:
                st.write("**Coordonnées**", art.get("coordinates", ""))
                st.caption(f"Bibliothèque : {art.get('library_version', '—')}")
                st.caption(f"Découvert : {art.get('discovered_at', '—')} · {art.get('explorer_pseudo', '—')}")
            with c_b:
                st.write("**Score mission (filtre 3)**", art.get("mission_keyword_score", "—"))
                mh = art.get("mission_keyword_hits")
                if mh is not None:
                    st.caption(f"Mots-clés : {mh}")
                st.write("**Couverture dictionnaire**", art.get("dictionary_coverage", "—"))
            st.write("**Fragment**", art.get("fragment", "")[:2000])
            if art.get("archivist_title"):
                st.write("**Titre (Archiviste)**", art.get("archivist_title"))
            if art.get("archivist_commentary"):
                st.write("**Commentaire (Archiviste)**", art.get("archivist_commentary", "")[:4000])
            if art.get("mission_relevance"):
                st.write("**Pertinence mission (LLM)**", art.get("mission_relevance"))
            if art.get("llm_error"):
                st.error(art.get("llm_error"))
            if art.get("llm_model_path"):
                st.caption(f"Modèle : {art.get('llm_model_path')}")
            with st.expander("Détails techniques (filtres)"):
                st.json(
                    {
                        "filter1_metrics": art.get("filter1_metrics"),
                        "filter2": art.get("filter2"),
                    }
                )

            st.divider()
            if is_community_configured():
                pid = stable_document_id(art)
                if st.button("Publier dans la galerie communautaire", key=f"pub_{pid}", type="secondary"):
                    res = publish_artefact_to_firestore(art)
                    if res.get("ok"):
                        st.success(f"Publié (document Firestore : `{res.get('doc_id')}`).")
                    else:
                        st.error(res.get("error") or "Échec de publication.")
            else:
                st.caption(
                    "Galerie : placez le JSON compte de service sous **config/firebase-service-account.json** "
                    "(voir **config/firebase-service-account.README.txt**) ou définissez **ARCHIVIST_FIREBASE_CREDENTIALS**. "
                    "Les dépendances Firebase sont incluses avec **requirements-app.txt**. Ne commitez jamais ce JSON."
                )


def _tab_system() -> None:
    st.caption("Vérifications techniques (équivalent `scripts/first_run.py`).")
    if st.button("Analyser l’environnement"):
        from archivist_setup import gather_setup_checks

        checks = gather_setup_checks()
        st.json([c.to_dict() for c in checks])


def main() -> None:
    st.set_page_config(
        page_title="The Archivist",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    inject_archivist_ui()
    _init_session()

    st.title("The Archivist")
    st.caption("Babel Investigation Engine — interface locale")

    t1, t2, t3, t4 = st.tabs(["Briefing", "Scanner", "Mes découvertes", "Système"])
    with t1:
        _tab_briefing()
    with t2:
        _tab_scanner()
    with t3:
        _tab_discoveries()
    with t4:
        _tab_system()


if __name__ == "__main__":
    main()
