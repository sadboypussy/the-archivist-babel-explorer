"""
The Archivist — couche visuelle (verre, parallaxe léger, formes géométriques).

Streamlit n’expose pas de layout HTML complet : on injecte CSS + une zone « ambiance »
et un petit script (iframe `components.html`) qui pose les variables CSS sur la page parent
pour le déplacement au curseur.
"""

from __future__ import annotations

from textwrap import dedent

import streamlit.components.v1 as components


def inject_archivist_ui() -> None:
    """À appeler une fois après `st.set_page_config`."""
    import streamlit as st

    st.markdown(_FONT_LINK, unsafe_allow_html=True)
    st.markdown(_AMBIENT_HTML, unsafe_allow_html=True)
    st.markdown(_GLOBAL_CSS, unsafe_allow_html=True)
    components.html(_PARALLAX_BRIDGE_HTML, height=0, scrolling=False)


_FONT_LINK = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=Instrument+Serif:ital@0;1&family=Manrope:wght@300;400;500;600&display=swap" rel="stylesheet">
"""

# Couche fixe sous le contenu ; les formes sont animées en CSS + variables --archivist-mx / --archivist-my.
_AMBIENT_HTML = """
<div class="archivist-ambient" aria-hidden="true">
  <div class="archivist-shape archivist-shape--1"></div>
  <div class="archivist-shape archivist-shape--2"></div>
  <div class="archivist-shape archivist-shape--3"></div>
  <div class="archivist-shape archivist-shape--4"></div>
  <div class="archivist-grid"></div>
</div>
"""

_PARALLAX_BRIDGE_HTML = dedent(
    """
    <script>
    (function () {
      try {
        var w = window.parent;
        if (!w || w.__archivistParallaxBound) return;
        w.__archivistParallaxBound = true;
        var doc = w.document;
        var root = doc.documentElement;
        function setPointer(clientX, clientY) {
          var vw = w.innerWidth || 1;
          var vh = w.innerHeight || 1;
          var nx = (clientX / vw - 0.5) * 2;
          var ny = (clientY / vh - 0.5) * 2;
          root.style.setProperty("--archivist-mx", nx.toFixed(5));
          root.style.setProperty("--archivist-my", ny.toFixed(5));
        }
        doc.addEventListener("mousemove", function (e) {
          setPointer(e.clientX, e.clientY);
        });
        doc.addEventListener("mouseleave", function () {
          root.style.setProperty("--archivist-mx", "0");
          root.style.setProperty("--archivist-my", "0");
        });
      } catch (err) {}
    })();
    </script>
    """
)

_GLOBAL_CSS = """
<style>
/* --- Variables racine (animation « respiration » + accents discrets) --- */
:root {
  --archivist-mx: 0;
  --archivist-my: 0;
  --archivist-glass: rgba(255, 252, 248, 0.045);
  --archivist-glass-edge: rgba(255, 255, 255, 0.1);
  --archivist-solid: rgba(14, 14, 18, 0.92);
  --archivist-fg: rgba(238, 235, 230, 0.95);
  --archivist-muted: rgba(160, 156, 148, 0.85);
  --archivist-gold: rgba(201, 162, 39, 0.35);
  --archivist-breathe: 14s;
}

/* Fond global : calme, pas de « néon » ; brume très légère */
.stApp {
  background:
    radial-gradient(120% 80% at 10% 0%, rgba(201, 162, 39, 0.07) 0%, transparent 55%),
    radial-gradient(90% 70% at 100% 30%, rgba(120, 140, 190, 0.06) 0%, transparent 50%),
    linear-gradient(165deg, #0a0a0d 0%, #121018 45%, #0c0c10 100%) !important;
  color: var(--archivist-fg) !important;
  font-family: "Manrope", system-ui, sans-serif !important;
}

[data-testid="stAppViewContainer"] {
  background: transparent !important;
}

/* Header Streamlit : verre léger */
[data-testid="stHeader"] {
  background: rgba(10, 10, 14, 0.55) !important;
  backdrop-filter: blur(16px) saturate(1.15) !important;
  -webkit-backdrop-filter: blur(16px) saturate(1.15) !important;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05) !important;
}

/* Contrôle du menu (⋮) toujours utilisable */
#MainMenu { visibility: visible; }

/* Titres : serif editorial + léger espacement */
h1, h2, h3 {
  font-family: "Instrument Serif", Georgia, serif !important;
  font-weight: 400 !important;
  letter-spacing: 0.02em !important;
  color: var(--archivist-fg) !important;
}

h1 {
  font-size: clamp(1.75rem, 3vw, 2.35rem) !important;
  margin-bottom: 0.25rem !important;
}

.block-container {
  padding-top: 2rem !important;
  padding-bottom: 4rem !important;
  position: relative;
  z-index: 2;
}

/* Caption sous le titre */
[data-testid="stCaptionContainer"] {
  color: var(--archivist-muted) !important;
  font-weight: 300 !important;
  letter-spacing: 0.04em !important;
  font-size: 0.82rem !important;
  text-transform: uppercase;
}

/* --- Onglets : panneau verre --- */
.stTabs [data-baseweb="tab-list"] {
  background: rgba(255, 255, 255, 0.03) !important;
  backdrop-filter: blur(18px) !important;
  -webkit-backdrop-filter: blur(18px) !important;
  border: 1px solid rgba(255, 255, 255, 0.08) !important;
  border-radius: 999px !important;
  padding: 0.35rem 0.5rem !important;
  gap: 0.25rem !important;
}

.stTabs [aria-selected="true"] {
  background: rgba(201, 162, 39, 0.18) !important;
  border-radius: 999px !important;
  color: #f5f0e8 !important;
}

.stTabs [data-baseweb="tab-panel"] {
  background: var(--archivist-glass) !important;
  backdrop-filter: blur(22px) saturate(1.2) !important;
  -webkit-backdrop-filter: blur(22px) saturate(1.2) !important;
  border: 1px solid var(--archivist-glass-edge) !important;
  border-radius: 18px !important;
  padding: 1.75rem 1.5rem 2rem !important;
  margin-top: 1rem !important;
  box-shadow:
    0 20px 50px rgba(0, 0, 0, 0.25),
    inset 0 1px 0 rgba(255, 255, 255, 0.06) !important;
}

/* Cartes / métriques / info --- verre un peu plus lisible */
[data-testid="stMetricValue"], [data-testid="stMetricLabel"] {
  color: var(--archivist-fg) !important;
}

div[data-testid="stExpander"] {
  background: rgba(255, 252, 248, 0.04) !important;
  backdrop-filter: blur(12px) !important;
  -webkit-backdrop-filter: blur(12px) !important;
  border: 1px solid rgba(255, 255, 255, 0.07) !important;
  border-radius: 14px !important;
}

/* Zones de texte et champs : pleins (lisibilité) */
.stTextInput input,
.stNumberInput input,
textarea,
[data-baseweb="textarea"] textarea,
[data-baseweb="input"] input {
  background: var(--archivist-solid) !important;
  border: 1px solid rgba(255, 255, 255, 0.14) !important;
  color: var(--archivist-fg) !important;
  border-radius: 12px !important;
  font-family: "Manrope", system-ui, sans-serif !important;
}

textarea, [data-baseweb="textarea"] textarea {
  min-height: 6rem !important;
}

.stCodeBlock, pre {
  background: rgba(8, 8, 12, 0.94) !important;
  border: 1px solid rgba(255, 255, 255, 0.1) !important;
  border-radius: 12px !important;
  font-family: "IBM Plex Mono", ui-monospace, monospace !important;
}

/* Boutons primaires : or discret, pas flashy */
.stButton > button[kind="primary"] {
  background: linear-gradient(165deg, #b8932a 0%, #8e6f1f 100%) !important;
  border: none !important;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35) !important;
  font-weight: 500 !important;
  letter-spacing: 0.03em !important;
  border-radius: 12px !important;
}

.stButton > button[kind="secondary"] {
  background: rgba(255, 255, 255, 0.08) !important;
  border: 1px solid rgba(255, 255, 255, 0.12) !important;
  color: var(--archivist-fg) !important;
  border-radius: 12px !important;
}

/* Progress : fine */
.stProgress > div > div > div > div {
  background: linear-gradient(90deg, rgba(201, 162, 39, 0.9), rgba(230, 210, 140, 0.95)) !important;
}

/* Radio horizontal */
[data-testid="stRadio"] label {
  font-weight: 400 !important;
}

/* --- Calque ambiance : géométrie + grille --- */
.archivist-ambient {
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
  overflow: hidden;
}

.archivist-grid {
  position: absolute;
  inset: -20%;
  opacity: 0.07;
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.5) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.5) 1px, transparent 1px);
  background-size: 64px 64px;
  transform:
    translate3d(calc(var(--archivist-mx, 0) * 18px), calc(var(--archivist-my, 0) * 12px), 0)
    rotate(-4deg);
  animation: archivist-grid-breathe var(--archivist-breathe) ease-in-out infinite;
}

@keyframes archivist-grid-breathe {
  0%, 100% { opacity: 0.05; }
  50% { opacity: 0.09; }
}

.archivist-shape {
  position: absolute;
  border: 1px solid rgba(255, 255, 255, 0.14);
  background: rgba(255, 255, 255, 0.02);
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
  will-change: transform, opacity;
}

.archivist-shape--1 {
  width: min(42vw, 520px);
  height: min(42vw, 520px);
  top: -12%;
  right: -8%;
  border-radius: 37% 63% 42% 58% / 45% 38% 62% 55%;
  opacity: 0.35;
  transform:
    translate3d(calc(var(--archivist-mx, 0) * 32px), calc(var(--archivist-my, 0) * -24px), 0)
    rotate(calc(12deg + var(--archivist-mx, 0) * 8deg));
  animation: archivist-morph-a 18s ease-in-out infinite, archivist-fade-a 22s ease-in-out infinite;
}

.archivist-shape--2 {
  width: 180px;
  height: 180px;
  bottom: 12%;
  left: 4%;
  clip-path: polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%);
  opacity: 0.22;
  transform:
    translate3d(calc(var(--archivist-mx, 0) * -20px), calc(var(--archivist-my, 0) * 18px), 0)
    rotate(calc(var(--archivist-my, 0) * -15deg));
  animation: archivist-spin-slow 40s linear infinite, archivist-fade-b 16s ease-in-out infinite;
}

.archivist-shape--3 {
  width: 260px;
  height: 140px;
  top: 38%;
  left: -6%;
  border-radius: 50%;
  opacity: 0.12;
  transform:
    translate3d(calc(var(--archivist-mx, 0) * 14px), calc(var(--archivist-my, 0) * 20px), 0)
    skewX(calc(var(--archivist-mx, 0) * 6deg));
  animation: archivist-shape3-pulse 24s ease-in-out infinite;
}

.archivist-shape--4 {
  width: min(55vw, 680px);
  height: min(38vh, 400px);
  bottom: -18%;
  right: 10%;
  border-radius: 60% 40% 50% 50% / 55% 45% 55% 45%;
  opacity: 0.2;
  transform:
    translate3d(calc(var(--archivist-mx, 0) * -26px), calc(var(--archivist-my, 0) * 14px), 0);
  animation: archivist-morph-c 28s ease-in-out infinite, archivist-fade-b 26s ease-in-out infinite;
}

@keyframes archivist-morph-a {
  0%, 100% { border-radius: 37% 63% 42% 58% / 45% 38% 62% 55%; }
  33% { border-radius: 63% 37% 58% 42% / 38% 62% 45% 55%; }
  66% { border-radius: 44% 56% 51% 49% / 52% 48% 53% 47%; }
}

@keyframes archivist-shape3-pulse {
  0%, 100% { opacity: 0.1; }
  50% { opacity: 0.24; }
}

@keyframes archivist-morph-c {
  0%, 100% { border-radius: 60% 40% 50% 50% / 55% 45% 55% 45%; }
  50% { border-radius: 42% 58% 48% 52% / 48% 52% 44% 56%; }
}

@keyframes archivist-spin-slow {
  from { transform: translate3d(calc(var(--archivist-mx, 0) * -20px), calc(var(--archivist-my, 0) * 18px), 0) rotate(0deg); }
  to { transform: translate3d(calc(var(--archivist-mx, 0) * -20px), calc(var(--archivist-my, 0) * 18px), 0) rotate(360deg); }
}

@keyframes archivist-fade-a {
  0%, 100% { opacity: 0.12; }
  50% { opacity: 0.38; }
}

@keyframes archivist-fade-b {
  0%, 100% { opacity: 0.08; }
  40% { opacity: 0.28; }
}

/* Main column above ambient */
section.main {
  position: relative;
  z-index: 2;
}
</style>
"""
