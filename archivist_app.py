"""
The Archivist — interface locale (Streamlit).

Lancement depuis la racine du projet : voir Launch-Archivist-UI.bat
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
from archivist_publish import (
    fetch_gallery_artefacts,
    is_community_configured,
    public_gallery_url,
    publish_artefact_to_firestore,
    stable_document_id,
)
from archivist_ui_theme import inject_archivist_ui

_PSEUDO_FILE = _ROOT / ".explorer_pseudo.txt"
_DEFAULT_LOG = _ROOT / "archivist_log.json"
_DEFAULT_SCAN_STATUS = _ROOT / ".archivist_scan_status.json"
_DEFAULT_PAUSE_FLAG = _ROOT / ".archivist_scan_pause"

_NAV: dict[str, str] = {
    "briefing": "Seuil",
    "scan": "Balayage",
    "discoveries": "Registre",
    "gallery": "Galerie",
    "settings": "Coulisses",
}

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
    if "archivist_page" not in st.session_state:
        st.session_state.archivist_page = "briefing"


def _read_scan_status(path: Path) -> dict[str, object] | None:
    if not path.is_file():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return raw if isinstance(raw, dict) else None


def _atmosphere_glyphs(total_scanned: int) -> str:
    glyphs = "·░▒▓╱╲ωabcdefghijklmnopqrstuvwxyz"
    w = 56
    return "".join(glyphs[(total_scanned * 17 + i * 11) % len(glyphs)] for i in range(w))


def _live_scan_panel(status_path: Path) -> None:
    def paint() -> None:
        data = _read_scan_status(status_path)
        if not data:
            st.caption("Synchronisation du tableau de bord…")
            return
        ts = int(data.get("total_scanned", 0) or 0)
        ta = int(data.get("total_artefacts", 0) or 0)
        tt = max(1, int(data.get("total_target", 1) or 1))
        phase = str(data.get("phase", ""))
        c1, c2, c3 = st.columns(3)
        c1.metric("Pages visitées", f"{ts:,} / {tt:,}")
        c2.metric("Trouvailles", f"{ta:,}")
        c3.metric("Étape", phase)
        st.progress(min(1.0, ts / tt), text="Avancement")
        st.caption("Présage (pur décor)")
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


def _sidebar_nav() -> str:
    with st.sidebar:
        st.markdown("# The Archivist")
        st.caption("Babel Investigation")
        st.divider()
        st.caption("Navigation")
        page = st.radio(
            "navigation",
            options=list(_NAV.keys()),
            format_func=lambda k: _NAV[k],
            label_visibility="collapsed",
            key="archivist_page",
        )
        st.divider()
        with st.expander("Aide discrète"):
            st.caption(
                "Les données du balayage et du registre restent sur votre ordinateur. "
                "La galerie publique est une vitrine séparée : vous choisissez d’y déposer une trouvaille."
            )
        return str(page)


def _view_briefing() -> None:
    st.markdown(_BRIEFING)
    st.divider()
    name = st.text_input(
        "Votre nom dans l’histoire",
        value=st.session_state.explorer_pseudo,
        placeholder="ex. Moriarty_IX",
    )
    if st.button("Enregistrer et continuer", type="primary"):
        st.session_state.explorer_pseudo = (name or "Anonymous").strip()
        _save_pseudo_disk(st.session_state.explorer_pseudo)
        st.success(f"Signe retenu : **{st.session_state.explorer_pseudo}**")


def _view_scanner() -> None:
    if not st.session_state.explorer_pseudo:
        st.info("Indiquez d’abord votre nom au **Seuil** (menu de gauche).")
        return

    st.markdown(
        "Le balayage avance en arrière-plan. Vous pouvez suivre l’avancement ici ; "
        "pour des explorations très longues, fermez simplement cette fenêtre : le travail continue."
    )

    log_path = str(_DEFAULT_LOG)
    status_path = str(_DEFAULT_SCAN_STATUS)
    pause_path = str(_DEFAULT_PAUSE_FLAG)

    col1, col2 = st.columns(2)
    with col1:
        pages = st.number_input("Profondeur (pages)", min_value=1, value=200, step=50)
        workers = st.number_input(
            "Fils d’exécution",
            min_value=1,
            value=max(1, (os.cpu_count() or 2) - 1),
            help="Plus élevé sur une machine puissante peut accélérer le balayage.",
        )
    with col2:
        mode_labels = {
            "preview": "Aperçu — sans modèle lourd",
            "local": "Modèle sur cet ordinateur",
            "remote": "Serveur d’inférence (autre logiciel)",
        }
        mode_key = st.radio(
            "Comment l’Archiviste lit les pages retenues ?",
            list(mode_labels.keys()),
            format_func=lambda k: mode_labels[k],
        )

    gguf = str(DEFAULT_GGUF_PATH)
    server_url = ""
    if mode_key == "remote":
        server_url = st.text_input(
            "Adresse du serveur",
            placeholder="http://127.0.0.1:8080",
            help="Souvent affichée par LM Studio, llama.cpp server, etc.",
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
    if mode_key == "preview":
        cmd.append("--mock-llm")
    elif mode_key == "remote":
        if not server_url.strip():
            st.error("Indiquez l’adresse du serveur.")
            return
        cmd.extend(["--llama-server", server_url.strip()])
    else:
        if not Path(gguf).is_file():
            st.warning(
                "Le modèle attendu n’est pas encore en place dans le dossier prévu. "
                "Utilisez l’aperçu sans modèle, ou suivez les instructions du dossier **models**."
            )
            return
        cmd.extend(["--gguf", gguf])

    with st.expander("Diagnostic (copie pour support)", expanded=False):
        st.code(" ".join(cmd), language="bash")

    proc = st.session_state.scan_proc
    st_path = Path(status_path)
    pause_p = Path(pause_path)
    if proc is not None and proc.poll() is None:
        st.info("Balayage **en cours**")
        _live_scan_panel(st_path)
        c_p1, c_p2, c_p3 = st.columns(3)
        with c_p1:
            if st.button("Pause entre deux vagues", key="btn_pause_scan"):
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
            if st.button("Arrêter le balayage", type="secondary", key="kill_scan"):
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
            st.success("Le balayage s’est terminé normalement.")
        else:
            st.error("Le balayage s’est arrêté avec un incident.")
            if err.strip():
                with st.expander("Journal d’erreur (extrait)"):
                    st.text(err[-8000:])
        st.session_state.scan_proc = None
        done = _read_scan_status(st_path)
        if done and str(done.get("phase")) == "done":
            st.metric(
                "Bilan",
                f"{done.get('total_scanned', 0)} pages · {done.get('total_artefacts', 0)} trouvailles",
            )

    if st.button("Lancer le balayage", type="primary"):
        active = st.session_state.scan_proc
        if active is not None and active.poll() is None:
            st.error("Un balayage est déjà en cours.")
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
        st.caption("Exploration très profonde : prévoyez du temps ; le tableau de bord se met à jour en continu.")


def _view_discoveries() -> None:
    log_path = _DEFAULT_LOG
    sort_mode = st.selectbox(
        "Ordre d’affichage",
        ("Du plus récent au plus ancien", "Pertinence mission", "Rareté"),
    )
    if st.button("Rafraîchir"):
        st.rerun()

    rows = read_log(log_path)
    if not rows:
        st.info("Le registre est encore vide. Lancez un balayage pour laisser une trace.")
        return

    rows_view = list(rows)
    if sort_mode.startswith("Pertinence"):
        rows_view.sort(key=lambda a: int(a.get("mission_keyword_score", 0) or 0), reverse=True)
    elif sort_mode.startswith("Rareté"):
        rows_view.sort(
            key=lambda a: _RARITY_ORDER.get(str(a.get("rarity", {}).get("rank", "common")).lower(), 0),
            reverse=True,
        )
    else:
        rows_view.sort(key=lambda a: str(a.get("discovered_at", "")), reverse=True)

    st.metric("Trouvailles enregistrées", len(rows_view))
    for art in rows_view[:50]:
        r = art.get("rarity", {})
        rank = str(r.get("rank", "common")).lower()
        color = _RARITY_COLOR.get(rank, "#aaaaaa")
        title = art.get("archivist_title") or "—"
        label = f"{r.get('display_name', '?')} · {title}"
        with st.expander(label):
            st.markdown(
                f'<p style="margin:0 0 0.5rem 0"><span style="color:{color};font-weight:700">'
                f"{r.get('display_name', '?')}</span></p>",
                unsafe_allow_html=True,
            )
            c_a, c_b = st.columns(2)
            with c_a:
                st.write("**Repère**", art.get("coordinates", ""))
                st.caption(f"Bibliothèque : {art.get('library_version', '—')}")
                st.caption(f"Moment : {art.get('discovered_at', '—')} · {art.get('explorer_pseudo', '—')}")
            with c_b:
                st.write("**Mission**", art.get("mission_keyword_score", "—"))
                mh = art.get("mission_keyword_hits")
                if mh is not None:
                    st.caption(f"Indices : {mh}")
                st.write("**Langue**", art.get("dictionary_coverage", "—"))
            st.write("**Fragment**", art.get("fragment", "")[:2000])
            if art.get("archivist_title"):
                st.write("**Titre**", art.get("archivist_title"))
            if art.get("archivist_commentary"):
                st.write("**Commentaire**", art.get("archivist_commentary", "")[:4000])
            if art.get("mission_relevance"):
                st.write("**Lecture mission**", art.get("mission_relevance"))
            if art.get("llm_error"):
                st.error(art.get("llm_error"))
            with st.expander("Analyse technique (filtres)"):
                st.json(
                    {
                        "filter1_metrics": art.get("filter1_metrics"),
                        "filter2": art.get("filter2"),
                    }
                )

            st.divider()
            if is_community_configured():
                pid = stable_document_id(art)
                if st.button("Offrir à la galerie publique", key=f"pub_{pid}", type="secondary"):
                    res = publish_artefact_to_firestore(art)
                    if res.get("ok"):
                        st.success("Cette trouvaille rejoint la galerie publique.")
                    else:
                        st.error(res.get("error") or "Publication impossible pour le moment.")
            else:
                st.caption(
                    "Pour déposer une entrée dans la galerie partagée depuis ici, l’installation doit "
                    "inclure les accès côté machine (fichier de service dans **config**). "
                    "Le salon public reste visible pour tout le monde via le menu **Galerie**."
                )


def _view_gallery() -> None:
    st.markdown("**Salon public** — la même collection que sur le site, vue depuis votre poste.")
    url = public_gallery_url()
    if hasattr(st, "link_button"):
        st.link_button("Ouvrir le salon dans le navigateur", url=url, type="primary")
    else:
        st.markdown(f"[Ouvrir le salon dans le navigateur]({url})")

    st.divider()
    st.markdown("**Aperçu ici**")
    if not is_community_configured():
        st.info(
            "Pour lister les dépôts déjà visibles dans le salon, cette copie de l’application doit "
            "avoir reçu ses accès locaux (dossier **config**). Vous pouvez tout de même ouvrir le salon ci-dessus."
        )
        return

    res = fetch_gallery_artefacts(limit=120)
    if not res.get("ok"):
        st.error("La lecture du salon a échoué. Vérifiez la connexion ou les règles côté hébergement.")
        return
    rows = res.get("rows") or []
    st.caption(f"{len(rows)} pièce(s) visibles pour l’instant.")
    for r in rows:
        tier = (r.get("rarity_display_name") or r.get("rarity_rank") or "?") + ""
        title = (str(r.get("archivist_title") or "")).strip() or "—"
        with st.expander(f"{tier} — {title}", expanded=False):
            st.caption(str(r.get("coordinates") or ""))
            st.caption(f"{r.get('discovered_at', '—')} · {r.get('explorer_pseudo', '—')}")
            frag = str(r.get("fragment") or "")
            st.text(frag[:3500] + ("…" if len(frag) > 3500 else ""))


def _view_settings() -> None:
    st.markdown("**Coulisses** — à n’ouvrir que si vous devez vérifier l’installation.")
    if st.button("Vérifier l’installation"):
        from archivist_setup import gather_setup_checks

        checks = gather_setup_checks()
        errs = [c for c in checks if c.level == "error" and not c.ok]
        warns = [c for c in checks if c.level == "warn" and not c.ok]
        if not errs and not warns:
            st.success("Rien d’anormal n’a été signalé.")
        elif errs:
            st.error("Certains éléments bloquent le fonctionnement attendu.")
        else:
            st.warning("Tout tourne, mais quelques points méritent un coup d’œil.")

        for c in checks:
            sym = "✓" if c.ok else ("⚠" if c.level == "warn" else "✕")
            st.markdown(f"{sym} **{c.title}**")
            with st.expander(f"Détail — {c.title}", expanded=False):
                st.caption(c.detail)

        with st.expander("Rapport technique complet (JSON)", expanded=False):
            st.json([c.to_dict() for c in checks])


def main() -> None:
    st.set_page_config(
        page_title="The Archivist",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    inject_archivist_ui()
    _init_session()

    page = _sidebar_nav()

    st.markdown("## " + _NAV.get(page, "The Archivist"))
    st.divider()

    if page == "briefing":
        _view_briefing()
    elif page == "scan":
        _view_scanner()
    elif page == "discoveries":
        _view_discoveries()
    elif page == "gallery":
        _view_gallery()
    else:
        _view_settings()


if __name__ == "__main__":
    main()
