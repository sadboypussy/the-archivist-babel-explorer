# Distribution — vision v1 et état du dépôt

La **vérité produit** pour la première release publique est dans **`THE_ARCHIVIST_Design_Document_v2.md` §5.5** (canon avril 2026). Ce fichier résume l’alignement technique du dépôt **à l’instant T**.

---

## Ce que la v1 doit être (rappel)

- **Public** : grand public **non technique** — jamais Python, `pip`, Git ni liens à chercher.
- **Canal grand public** : **installateur Windows classique** (comme une application normale) — **pas** une zip « bricolage » comme **seule** offre utilisateur.
- **Contenu lourd** : modèle **~5 Go** téléchargé **automatiquement** depuis **Hugging Face** (gratuit pour l’utilisateur), **sans étape technique**, dans le même flux que l’installation / premier lancement.
- **Plateforme** : **Windows uniquement** pour la v1.
- **Inférence** : **locale** uniquement ; un **binaire CUDA** embarqué et lancé en tâche de fond (ex. `llama-server`) est **validé** s’il est installé **avec** l’app et **invisible** pour l’utilisateur (cf. design §5.5).
- **Qualité** : **8B Q4_K_M seul** pour la v1 — **pas de variante 3B** ; CPU toléré **avec message clair** si pas de NVIDIA, **sans** dégrader les fonctionnalités.
- **Communauté** : galerie **en ligne** (Firebase + page statique hébergée) — **normal** et **hors du disque local** ; le cœur scan + Archiviste reste **local**. **URL canonique à partager** (Netlify) + miroir Pages : voir **`community/gallery/PUBLIC_GALLERY.txt`**.
- **Signature de code** : **souhaitable** pour limiter SmartScreen ; **coût** à la charge de l’auteur si / quand c’est acceptable — sinon prévoir l’étape « éditeur inconnu » dans le support utilisateur.

---

## Où en est le dépôt **maintenant**

| Élément | État |
|--------|------|
| Moteur AL1, filtres, journal, CLI `run_scanner.py` | **Présent** |
| Archiviste LLM (GGUF, CUDA Windows, serveur local optionnel) | **Présent** (parcours dev / power user) |
| `archivist_setup` / `scripts/first_run.py` | **Présent** (vérifications + téléchargement poids, utile dev / QA) |
| Bundle **portable** `packaging/windows/build_portable_bundle.ps1` | **Artefact interne / bêta** — **ne remplace pas** l’installateur v1 (§5.5) |
| **UI locale** (`archivist_app.py` + `requirements-app.txt` + `Launch-Archivist-UI.bat`) | **Première version** (Briefing, Scanner, Découvertes, Système) — à polir §6 |
| **Installateur Windows** | Squelette **Inno Setup** `packaging/windows/Archivist.iss` — **pas** le flux build/payload final |
| Téléchargement modèle **intégré au setup graphique** | **Pas encore** (aujourd’hui : script / first_run) |
| Galerie Firebase + Pages | **HTML + Firestore** prêts ; déploiement : **`community/gallery/DEPLOY.txt`** ; **lien public canon** : **`community/gallery/PUBLIC_GALLERY.txt`** |

---

## Feuille de route technique (alignée §5.5)

1. **Installateur Windows** + runtime embarqué + flux **téléchargement HF** sans action technique.
2. **Application locale** (Streamlit packagé ou équivalent) comme **seul** point d’entrée utilisateur — le CLI reste outil **interne** si besoin.
3. **Robustesse LLM** : stratégie unique « grand public » (wheel CUDA et/ou **binaire bundlé** invisible).
4. **Phase 4 communauté** : push Firestore, règles, galerie HTML.
5. **Signature** quand le budget le permet ; polish et **zéro dette** avant release publique.

---

## CI

Workflow GitHub **`.github/workflows/ci.yml`** : Windows, Python 3.11, `pip install -r requirements.txt -r requirements-llm.txt`, puis `unittest` sur `tests/`.

## Communauté (Firestore) — bêta

1. Créer un projet **Firebase**, activer **Firestore** (mode natif).
2. Télécharger une **clé compte de service** (JSON) — **ne pas** la versionner.
3. **`pip install -r requirements-app.txt`** inclut déjà **firebase-admin** (plus besoin d’installer `requirements-community.txt` seul pour l’UI).
4. Placer le JSON sous **`config/firebase-service-account.json`** (voir `config/firebase-service-account.README.txt`) **ou** définir **`ARCHIVIST_FIREBASE_CREDENTIALS`** (chemin vers le JSON). `Launch-Archivist-UI.bat` fixe la variable si ce fichier existe.
5. Optionnel : **`ARCHIVIST_FIRESTORE_COLLECTION`** (défaut `artefacts`).
6. Règles Firestore d’exemple pour la **lecture galerie** : `config/firestore.rules.example` (les écritures Admin SDK contournent les règles ; la validation se fait côté Python dans `archivist_publish.py`).
7. Dans **Streamlit → Mes découvertes**, bouton **Publier dans la galerie communautaire** par artefact.

## Pour les contributeurs (aujourd’hui)

Clone + `python -m venv .venv` (recommandé, évite les conflits pip avec d’autres apps sur la machine) + activer le venv + `pip install -r requirements.txt -r requirements-llm.txt -r requirements-app.txt` + `python scripts/first_run.py` + double-clic **`Launch-Archivist-UI.bat`** (ou `streamlit run archivist_app.py` si Python est sur le PATH) = flux **développeur / bêta**. Le public cible **ne verra pas** ce flux en v1 (installeur unique).
