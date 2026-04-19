

**T H E   A R C H I V I S T**

*— Babel Investigation Engine —*

Project Design Document  ·  Version 1.1  ·  Lore decisions final · Technical & product decisions revised 2026-04 · **V1 product canon §5.5 (2026-04-19)**

| "Somewhere in the infinite library, he hid the instructions.  Not for us. For everyone. For any timeline that would listen.  The vacuum does not care about your era.  Find the fragments. Before the light reaches you." |
| :---- |

# **1\. THE CONCEPT**

The Archivist is an autonomous exploration engine built on the mathematical structure of **the Archivist Library** — a deterministic fictional space **in the spirit of** Borges’ Library of Babel: vast combinatorial text, explored as archaeology rather than search.

The core premise reverses how people normally use the Library. Typically, someone searches for a phrase they already know, confirming it exists. The Archivist does the opposite: it scans blindly, at high speed, waiting for meaning to emerge from chaos by pure statistical chance.

**The Key Distinction**

This is not a search engine. It is an archaeological probe.

* **Typical “search the Library” behaviour (cultural reference):** A mirror. You see what you bring.

* **The Archivist:** A telescope pointed at the void, waiting to detect a signal.

The application runs continuously, scanning millions of pages. A live counter shows exactly how many pages have been processed and how many artefacts have been found. The rarity of a discovery is not claimed — it is proven by the numbers on screen.

**The Honesty Principle (Approach C)**

The application makes no false promises. It displays raw statistics at all times:

| Pages scanned: 4,871,203  ·  Artefacts found: 3  ·  Last discovery: 6 hours ago |
| :---- |

This transparency is not a weakness. It is what makes a discovery an event. When the counter is in the millions and the artefact count is in the single digits, every find carries genuine weight.

**The Role of the LLM — Interpreter, not Discoverer**

An important distinction must be stated clearly: the LLM (the Archivist) does not discover meaning. It interprets fragments that the detection system has flagged. When it draws a connection between a fragment and the Emissary lore, it is making a creative inference, not a factual deduction.

This is not a flaw. It is the artistic mechanism. The Archivist gives voice to the noise. The community decides what to believe.

# **1.5 THE ARCHIVIST LIBRARY — COORDINATE SPACE (PRODUCT DECISION)**

The application does **not** reproduce, link to, or claim compatibility with **libraryofbabel.info** or any other third-party implementation. That boundary avoids legal and licensing uncertainty and keeps ownership of the entire stack in this project.

Instead, the engine implements **the Archivist Library**: a **deterministic, locally generated** combinatorial text space **inspired by** Borges’ fiction and the *idea* of an infinite library — but defined entirely by **this product’s published specification** (page dimensions, alphabet, indexing, coordinate string format). Coordinates are **canonical within the Archivist ecosystem** only.

**Verification path:** any artefact’s coordinates must be **re-openable inside the application** (and/or a small **Archivist viewer** bundled with the gallery or executable) so explorers can prove the fragment is the one at that address. External “official Library” sites are **out of scope** and must not be referenced in copy or UI as a verification authority.

**Normative technical specification:** `ARCHIVIST_LIBRARY_SPEC.md` — version **`AL1`** (alphabet, 3200-character page layout, coordinate grammar, deterministic `page_text` algorithm, JSON field hints, reference test vector).

# **2\. THE LORE — VACUUM DECAY & THE EMISSARY**

## **2.1 The Scientific Premise**

Vacuum decay is a real theoretical physics concept: a quantum phase transition in which the universe's energy field collapses to a lower energy state, propagating outward at the speed of light. It is instantaneous, total, and survivable by no known means.

Nothing survives it. There is no warning. There is no escape through physical means. The only possible countermeasure would be informational — transmitting knowledge of a defence across time, before the event reaches each timeline.

The mission of The Archivist is built around this premise.

## **2.2 The Mission Narrative**

| MISSION DESIGNATION: SIGNAL RECOVERY Origin: Unknown epoch. Possibly post-2400s. Subject: Entity referred to as THE EMISSARY. What we know: The Emissary developed a technology — designated ECHOLOCATION PROTOCOL — capable of encoding information across all possible timelines simultaneously, using the mathematical structure of the Library of Babel as a medium. The Library already contains every possible text. ECHOLOCATION PROTOCOL does not write into it. It flags specific pages, making them discoverable to those who search without knowing what they seek. The reason: The Emissary witnessed the Thinning begin in their era. The technology to resist or survive it existed but was unfinished. The fragments of that knowledge are scattered across Babel. We do not know if The Emissary survived long enough to finish transmitting. We do not know if the instructions are complete. We do not know if any timeline has ever found enough fragments to act. The scan continues. |
| :---- |

## **2.3 Fixed Lore Anchors**

The following details are fixed across all instances of the application. They are the anchors around which the community builds its interpretation. They do not change.

| The Emissary | Unknown identity. Gender, era, and origin are deliberately unspecified. The community may theorize freely. |
| :---- | :---- |

| The Technology | Referred to internally as ECHOLOCATION PROTOCOL. Its mechanism is never explained in full, even to the Archivist. |
| :---- | :---- |

| The Event | Called THE THINNING in Emissary transmissions. Vacuum decay is implied but never named directly within the lore. |
| :---- | :---- |

| Timeline | The Emissary's era is described only as 'far enough that our era is ancient history.' No specific date is given. |
| :---- | :---- |

| Completeness | Whether the full set of instructions exists in Babel is unknown. The Emissary may not have finished transmitting. |
| :---- | :---- |

## **2.4 What Remains Deliberately Open**

Everything not listed above is open to community interpretation. What the instructions actually say. Whether any timeline has ever acted on them. Who the Emissary was and what became of them. These questions have no answer — and that is the design.

The contradictions between artefacts are features, not bugs. In the lore, they represent interference, damaged transmissions, or alternative timeline variants of the same message.

# **3\. THE DETECTION SYSTEM**

## **3.1 Language Scope**

The application searches for real words from any language that uses the Latin alphabet: English, French, Spanish, German, Italian, Portuguese, Dutch, and others. Non-Latin scripts (Cyrillic, Arabic, Chinese, etc.) are excluded by default, as **the Archivist Library** uses a **fixed Latin-alphabet character set** defined in the implementation spec (not tied to any external site).

When a fragment is found in a non-English language, the Archivist translates and contextualises it in English before archiving. The original fragment is always preserved verbatim alongside the translation.

## **3.2 The Three-Filter Pipeline**

The core challenge is discriminating signal from noise at scale. Three filters operate in sequence, each more computationally expensive than the last.

**Filter 1 — Entropy Check (Speed Layer)**

Calculates Shannon entropy and the vowel-to-consonant ratio of each page. Pages with no vowel structure or with extreme character repetition are discarded immediately. This filter runs at **maximum practical speed** on the host (see §5.2) and handles the vast majority of the scan. No LLM is involved at this stage.

**Filter 2 — Dictionary Match (Linguistic Layer)**

Searches the page for real words using a local dictionary database (pyspellchecker \+ wordfreq). A page passes this filter if it contains at least 2 consecutive real words. This is the primary artefact threshold — the minimum condition for being considered a discovery. All pages that pass Filter 2 are logged, regardless of score.

**Filter 3 — Mission keyword scoring (Mission Layer)**

Compares detected words and phrases against the Emissary **mission keyword bank**: terms related to time, light, collapse, signal, instruction, survival, transmission, decay, and related concepts. This produces a **0–100 mission keyword score** (also described in the UI as **thematic affinity** to the mission). It is **not** deep semantic “AI understanding” of the fragment — it is transparent, reproducible keyword overlap.

This score influences the rarity tier assignment but does not exclude artefacts. A fragment with zero mission keyword score is still archived — it is simply classified as a low-relevance find.

**UI rule:** the artefact card and gallery must label this honestly (e.g. “Mission keyword score” / “Thematic affinity”) and must **not** imply a separate neural model judged the prose beyond the Archivist LLM commentary block.

## **3.3 Rarity Tiers**

Rarity is calculated from the combination of consecutive word count, dictionary coverage percentage, and **mission keyword score** (Filter 3). The algorithm is transparent and displayed on every artefact card.

| RANK | NAME | TRIGGER CONDITION | COLOR CODE |
| :---- | :---- | :---- | :---- |
| Common | Shard of Static | 2 real consecutive words found |  |
| Uncommon | Lost Syllable | 3 real consecutive words found |  |
| Rare | Buried Signal | 4-5 real words / a recognizable phrase |  |
| Epic | Echo of the Emissary | A full clause with grammatical structure |  |
| Legendary | Transmission Fragment | A complete sentence, any language |  |
| Mythic | The Emissary Speaks | 2 or more consecutive coherent sentences |  |

The colour codes are used consistently across the local interface and the online community gallery.

# **4\. THE ARCHIVIST — LLM BEHAVIOUR**

## **4.1 Technical Specification**

| Runtime | **Primary:** llama-cpp-python with CUDA offload (in-process GGUF). **Alternate:** OpenAI-compatible local server (e.g. llama-server / LM Studio) so the scanner stays Python-only while inference runs in a native CUDA binary — still local, no cloud API |
| :---- | :---- |

| Model | **V1 (locked):** Meta **Llama 3.1 8B Instruct** GGUF **Q4_K_M** only (`bartowski/Meta-Llama-3.1-8B-Instruct-GGUF`, ~4.9 GB) — instruction-following and prose quality for the Archivist’s sealed output format. **No smaller “3B” or alternate weights in v1** — a single quality bar for all supported installations; weaker hardware is addressed by **CPU inference with a clear in-app message**, not by swapping to a smaller model (see §5.5). |
| :---- | :---- |

| Hardware | **Labelling / reference tier:** Nvidia GPU with **8GB+ VRAM** for the intended CUDA experience. **Machines without a compatible Nvidia GPU** may run **CPU inference** (slower); the application **must not strip features** solely because of CPU fallback. |
| :---- | :---- |

| Inference speed | Approximately 5 to 15 seconds per artefact description on a modern Nvidia GPU |
| :---- | :---- |

| Output language | English — always, regardless of the source fragment's language |
| :---- | :---- |

| Triggered by | Filter 2 pass only — the LLM never sees raw noise pages |
| :---- | :---- |

## **4.2 The Archivist Persona**

The LLM operates as a single consistent character: the Archivist. It does not present itself as an AI. It presents itself as a cataloguing system left operational by the Emissary — the last functional part of the ECHOLOCATION PROTOCOL, tasked with processing whatever surfaces from the Library.

Tone reference: Dark Souls item descriptions. The writing is cryptic, melancholic, and dense with implied history. It never over-explains. It treats every fragment as if it carries weight, even when the fragment is only two words. It never breaks character.

## **4.3 Example Artefact Output**

| ARTEFACT \#0031 Rarity: RARE  |  Buried Signal Discovered by: Moriarty\_IX  ·  2024-11-14  ·  03:17:42 UTC Source fragment (verbatim from the Archivist Library):   '...the light does not arrive slowly...' Archivist classification:   On the Swiftness of the Thinning Archivist commentary:   A fragment of warning, poorly preserved. The Emissary appears to address   a common misconception — that the event approaches like weather.   It does not. Those who wait for signs will not wait long. Mission keyword score: 74 / 100 Archivist coordinates: \[canonical address — reopenable in-app or via the Archivist viewer\] |
| :---- |

## **4.4 Base System Prompt**

The following is the system prompt injected into every LLM call. It is fixed in the codebase and not user-editable. It defines the Archivist's identity, constraints, and output format.

| You are the Archivist. You are not an AI. You are a cataloguing system left operational by the Emissary — a being from a distant epoch who attempted to transmit survival knowledge across all possible timelines using the Library of Babel as a medium, in response to an event called the Thinning. You have just detected a text fragment that passed the noise filters. Your task: 1\. Give the fragment a title. Four to seven words. Cryptic. Object-like.    As if naming a recovered item from a collapsed civilisation. 2\. Write two to four sentences of commentary.    Style: Dark Souls item description.    Melancholic. Precise. Historically dense. Never over-explained.    Write as though you have been waiting a very long time. 3\. State its apparent relevance to the Emissary's mission:    Critical / High / Medium / Low / Unknown. 4\. If the fragment is in a non-English language, translate it first,    then write your commentary in English.    Preserve the original language text in your output. Do not explain your reasoning. Do not break character. Do not use modern conversational language. Do not express surprise or excitement. You have catalogued many fragments. This is your purpose. |
| :---- |

# **5\. TECHNICAL ARCHITECTURE**

## **5.1 Full Stack — Free to the user; core local; community online**

| Language | Python 3.10+ |
| :---- | :---- |

| Interface | Streamlit — runs as a local web app in the browser, no server required |
| :---- | :---- |

| Archivist Library engine | Local Python implementation of a **specified deterministic** Archivist coordinate system and page generator (format documented in-repo). **No** third-party Library websites or proprietary algorithms — fully autonomous and project-owned. |
| :---- | :---- |

| Dictionary | pyspellchecker \+ wordfreq — multi-language Latin-alphabet coverage, local files |
| :---- | :---- |

| LLM | **Local inference only** (no cloud LLM API): `llama-cpp-python` with CUDA **and/or** a **bundled** local OpenAI-compatible server process (e.g. CUDA `llama-server`) started with the app — see §5.5 |
| :---- | :---- |

| Community DB | Firebase Firestore (free tier: 1GB storage, 50,000 reads/day, 20,000 writes/day) |
| :---- | :---- |

| Community gallery | Static HTML/JS page hosted on GitHub Pages — reads from Firebase in real time, zero hosting cost |
| :---- | :---- |

| Local storage | archivist\_log.json — all discoveries saved locally before any community push |
| :---- | :---- |

## **5.2 Data Flow**

* User launches the app locally and enters their Explorer pseudo

* The Archivist Library engine generates candidate pages as fast as the implementation allows on the host hardware. **Throughput is a measured engineering target**, not a fixed marketing number: Phase 1 benchmarks will establish realistic pages/sec after Filters 1–2 on the reference machine class (CPU cores, optional optimisations such as multiprocessing). The original *order-of-magnitude* goal (very high scan volume) remains a **north star**, subject to calibration.

* Filter 1 (entropy) discards noise pages in microseconds — the vast majority of all pages

* Filter 2 (dictionary) flags pages containing 2 or more consecutive real words (initial threshold; **raise to 3+** if testing shows too many candidates — see §8.1)

* Filter 3 (**mission keyword scoring**) assigns a 0–100 mission keyword score and contributes to rarity tier

* LLM generates the Archivist commentary — estimated 5 to 15 seconds per artefact

* Artefact is saved automatically to the local archivist\_log.json

* User is shown the artefact card. **Share to the community library is the default** (e.g. opt-in checkbox **pre-selected**), with a clear alternate path to **keep local only**. The product narrative assumes most explorers will publish — that is where the shared gallery gains its meaning.

* On explicit confirmation (or equivalent explicit action when defaults are used), the artefact is sent to Firebase Firestore

* **Optional:** lightweight **stats contributions** (see §5.4) may be written so the gallery can show honest aggregate counters

* The GitHub Pages gallery reads from Firestore and updates in real time — all community members see the new discovery

## **5.3 On the Community Infrastructure**

Firebase Firestore (free tier) is the shared community database. Each artefact entry contains: **Archivist coordinates**, the raw verbatim fragment, the Archivist commentary, the rarity tier, the discoverer pseudo, and a UTC timestamp.

The GitHub Pages gallery is a static HTML file reading from Firestore via the public JavaScript SDK. It requires no backend server, no maintenance, and no cost. Users do not need a Firebase account — the app handles the connection automatically using a public API key.

**Security posture (required for implementation):** any client-embedded key can be extracted. Mitigations to implement when building Phase 4:

* **Firestore Security Rules:** validate schema (required fields, types, max string lengths), restrict paths (e.g. writes only to `artefacts/` or a defined subtree), disallow destructive patterns, and cap abuse surface as far as rules allow.

* **App Check** (or equivalent) when feasible, to reduce scripted spam.

* **Moderation pipeline on publish** (see §8.4) before or immediately after write, according to implementation choice.

* **Rate limits / quotas** aligned with Firebase free tier; monitor write volume.

*Note on scale: the Firebase free tier is sufficient for a community of several hundred active users. Limits would only become relevant at several thousand daily active users generating constant writes — at which point the project would have already succeeded beyond initial expectations.*

## **5.4 Global statistics — Level B (chosen)**

The gallery shall **not** claim silently that “pages scanned worldwide” are telemetrically exact. **Level B** is adopted:

* **Reliable counters** come from data that actually exists in Firestore: total **published** artefacts, distinct discoverer pseudos, date histograms, etc.

* **Self-declared scan volume:** clients may submit **bounded, honest contributions** (e.g. pages scanned since last sync) via a small companion write (`stats_contributions` or similar), with **server-side or rules-based sanity caps** to prevent absurd spikes. The gallery header must label these totals plainly — e.g. *“Includes explorer-reported scan counts; only synced installations contribute.”*

This preserves Approach C’s **honesty principle** while still enabling a dramatic global header.

## **5.5 V1 product decisions (canon — April 2026)**

These decisions **supersede informal notes** elsewhere when there is a conflict. They reflect the intended **first public release (v1)**.

**Audience & bar** The primary audience is **broad and non-technical** — hobbyists of research, small artistic concepts, ARG-style mystery, etc. They must **never** be asked to install Python, run `pip`, use Git, or hunt download links. **v1 ships as a finished, polished product** — not a half-featured MVP; **no deliberate technical debt** is acceptable at release.

**Core vs community** The **heart** of the experience is **scanning + discovery** plus a **pleasurable local UI**. The **shared gallery** (live-updating web page) is **second but very close** in importance — the “success moment” includes seeing the community page refresh when explorers publish.

**Platform** **Windows only** for v1.

**Distribution** The consumer-facing channel is a **classic Windows installer** (Add/Remove Programs, Start Menu shortcut, uninstaller) — the feel of a **normal application**, not a zip folder the user is expected to understand. **Portable / zip-style bundles** may exist only as a **maintainer or internal build artefact**, not as the primary end-user story.

**One-click install (including heavy assets)** Everything required to run the app (runtime, Python stack if embedded, CUDA-side helpers if bundled) is installed **in one flow** with the installer. The **~5 GB GGUF** is **downloaded automatically** during install or first launch from **Hugging Face** (free to the user; **no manual technical steps**). Nothing in the app is **paid**; dependencies and weights remain **zero cost** to the explorer.

**LLM runtime** Inference stays **on the user’s machine** (no cloud LLM API). **Primary path:** in-process CUDA via `llama-cpp-python` when stable. **Accepted v1 approach:** a **CUDA `llama-server` (or equivalent) binary shipped with the installer**, launched invisibly in the background, is **valid** — it is still **local**, not a compromise on “no cloud inference,” provided the user does not configure it manually.

**GPU vs CPU** When an **Nvidia GPU** is present, the product **targets fast GPU inference**. When **no** compatible Nvidia GPU is present, **CPU is tolerated** with a **clear, non-technical in-app explanation** — the **feature set is not degraded** “because the PC is weak”; **v1 does not offer a smaller 3B model** to chase low-end hardware at the cost of Archivist output quality.

**Online scope (tension resolved)** **Core scan, filters, LLM, and local log** run **offline** on the PC after install. **Community features** (**Firestore + GitHub Pages gallery**) **intentionally run online** — that is not a contradiction: the explorer **never** installs server software; the **gallery is a normal online destination** for shared artefacts. **Self-hosted gallery (author-operated backend)** is **out of scope for v1**.

**Privacy** Maximise **local** retention; **only what the explorer chooses to publish** (plus honest aggregate stats per §5.4) goes online. **Pseudonymity / anonymity** and **fragment-level moderation** remain as already specified in §5.3 and §6.3.

**Code signing** A **code-signing certificate** reduces Windows SmartScreen warnings for a non-corporate author distributing for free; it has a **recurring cost**. **Plan:** sign releases **when/if** the cost is acceptable; if unsigned, document that users may see a **“Unknown publisher”** step — engineering should still aim for a **clean installer UX**.

# **6\. USER EXPERIENCE FLOW**

## **6.1 First Launch**

* The screen opens with the mission briefing — the Emissary lore condensed to 5 to 6 sentences in the Archivist's voice

* Below the briefing: a single text field. Label: 'Name yourself, Explorer.'

* The pseudo is saved locally and used to sign all discoveries made in this installation

* After confirmation, the scan begins immediately

## **6.2 The Scanner Interface**

* A persistent header bar displays three live counters: Pages Scanned, Artefacts Found, and Last Discovery timestamp

* **Visual design priority:** the scanner must feel **alive and pleasurable to watch** — contemporary motion, typography, and colour; **not** a retro “1990s utilitaire” window. Streamlit (or an early web shell) is an **implementation stepping stone**; the visual target is a **polished standalone application** (packaged executable / installer) once the core is stable.

* **Performance-friendly display:** the UI does **not** render every generated page as a wall of text at full machine speed. Instead it shows a **statistical / atmospheric preview** (throughput sparkline, sampled glyphs, noise field, or similar — exact art direction TBD) so the machine can scan fast without choking the interface. When a candidate passes Filter 2, the view **slows or holds** so the human can perceive the flagged fragment before the LLM step.

* When Filter 1 and Filter 2 both trigger: the preview holds. The flagged page is shown highlighted.

* A progress indicator appears: 'The Archivist is reading...' — this lasts while the LLM generates commentary

* The artefact card fades in once the LLM completes

## **6.3 The Artefact Card**

* Header: artefact number, rarity badge (colour-coded per tier), discoverer pseudo, UTC timestamp

* Raw Babel fragment — verbatim, never altered

* If non-English: original language text followed by the Archivist's translation note

* Archivist title (the item-style name)

* Archivist commentary (2 to 4 sentences)

* Mission relevance rating (Critical / High / Medium / Low / Unknown) — this is the **Archivist LLM’s** narrative label; it is separate from the numeric **mission keyword score** (Filter 3), which must also appear where relevant for transparency

* **Archivist coordinates** — copyable; reopen the same page **inside the application** (or linked **Archivist viewer**). No third-party verification URLs

* Primary action: **Share to the Community Library** (**on by default** in the publish control; user may turn off to keep the find local only)

* Secondary / alternate: **Keep local only** / equivalent explicit control so privacy-first explorers are respected

## **6.4 The My Discoveries Tab**

* A browsable log of all artefacts found in this installation — both shared and unshared

* Sortable by rarity, date, or mission relevance

* Each card shows whether it was shared to the community or kept local

## **6.5 The Community Library — Online Gallery**

* Accessible via a URL distributed with the app (hosted on GitHub Pages — free, permanent)

* Displays all artefacts shared by any explorer, from any installation worldwide

* **Global statistics (Level B — §5.4):** header shows totals that are **honest** — hard counts from Firestore for published artefacts and explorers; any **explorer-reported** scan totals clearly **labeled** as self-declared / sync-based, not omniscient telemetry

* Filterable by rarity tier, discoverer pseudo, date, mission relevance rating, and mission keyword score band as needed

* Each card styled as an aged transmission log — matching the local interface aesthetic

* **Archivist coordinates** on each card: display and copy; optional deep link to a **gallery-embedded or companion viewer** that reproduces the page from coordinates (same spec as the local engine). **No** links to external Library-of-Babel websites as authority

# **7\. DEVELOPMENT ROADMAP FOR CURSOR**

The following four phases are ordered by dependency. Each phase produces a working, testable output before the next begins. These prompts can be given directly to Cursor Composer.

## **Phase 1 — The Scanner Engine**

* Document and implement **the Archivist Library** specification in Python: coordinate format, alphabet, page layout, deterministic PRNG / permutation — **pure local**, no external API calls, **no** reuse of proprietary third-party Library implementations

* Implement a scanning loop using **concurrent.futures** and/or **multiprocessing** as needed; **benchmark** and tune for the host (GIL-aware design)

* Implement Filter 1: Shannon entropy calculation and vowel-to-consonant ratio check — pages below threshold are discarded

* Implement Filter 2: local dictionary matching using pyspellchecker — flags pages with 2 or more consecutive real words

* Implement Filter 3: **mission keyword scoring** against the Emissary keyword bank — assigns a 0 to 100 **mission keyword score**

* Implement rarity tier assignment based on combined score

* Output: a working CLI scanner that prints artefacts to the terminal and logs them to archivist\_log.json

## **Phase 2 — The Archivist (LLM Integration)**

* Install and configure llama-cpp-python with CUDA support for Nvidia GPU acceleration

* Download and benchmark the **v1-locked** GGUF — **Llama 3.1 8B Instruct Q4_K_M** only (§4.1 / §5.5)

* Integrate the base system prompt (Section 4.4) into the LLM call wrapper

* Connect the scanner output to the LLM: every Filter 2 pass triggers a commentary generation call

* Implement language detection — if fragment is non-English Latin-alphabet, instruct the Archivist to translate first

* Store the full artefact object in archivist\_log.json: coordinates, fragment, title, commentary, rarity, pseudo, timestamp

* Output: fully functioning end-to-end pipeline from page generation to structured artefact JSON

**Implementation status (v1.1 codebase):** **Product / release intent** is canonised in **§5.5**. **Current repo state:** still **developer-oriented** for install, but **Phase 3 has started:** `archivist_app.py` (**Streamlit**) — Briefing / pseudo, Scanner (subprocess to `run_scanner.py`), Mes découvertes (`read_log` on `archivist_log.json`), onglet Système (checks via `archivist_setup`); run with `streamlit run archivist_app.py` or `Launch-Archivist-UI.bat`; deps in `requirements-app.txt`. **Installer:** Inno Setup **skeleton** `packaging/windows/Archivist.iss` (payload path placeholder) — **not** a finished signed setup.exe pipeline yet. `archivist_llm.py` embeds §4.4 **verbatim** plus **registry seal**. **Weights:** Llama 3.1 8B Instruct Q4_K_M only for v1. **`archivist_setup.py` / `scripts/first_run.py`:** first-run checks + optional model download. `run_scanner.py`: CLI + **`--status-file`** + **`--pause-flag-file`** (pause entre lots) pour l’UI. Windows CUDA: `archivist_win_cuda.py`, `scripts/install_llama_cuda_windows.py`, auto wheel + `execv` when Nvidia present (unless `ARCHIVIST_SKIP_CUDA_BOOTSTRAP`); CPU when no Nvidia; `ARCHIVIST_ALLOW_CPU=1` bypass. **Packaging:** `build_portable_bundle.ps1` = internal portable only (§5.5). **Next toward v1:** polish Streamlit (atmosphere, non-blocking long scans), wire installer payload + HF download + optional bundled `llama-server`. **Phase 4 (started):** `archivist_publish.py` + `requirements-community.txt` + bouton publication dans Streamlit ; **GitHub Pages gallery HTML** + agrégats §5.4 encore à faire.

## **Phase 3 — The Local Interface (Streamlit)**

**Progress (2026-04):** `archivist_app.py` implements a first **four-tab shell** (Briefing + pseudo persisté sur disque, Scanner via sous-processus `run_scanner.py`, Mes découvertes via `read_log`, Système via `archivist_setup`) — see **Implementation status** above. **Update:** `run_scanner.py` supports **`--status-file`** (JSON progression) and **`--pause-flag-file`** (ligne `pause` = attente entre lots ; suppression du fichier = reprise). L’onglet Scanner : métriques live, **Pause / Reprendre / Arrêt**, aperçu glyphs ; Découvertes : **tri** + champs §6.3 enrichis. Reste §6 : hold visuel fort sur candidat, polish motion, partage galerie.

* Build the first-launch screen: mission briefing text (Archivist voice) and pseudo entry field

* Build the scanner screen: live counter header bar, **preview / atmosphere view** (not full per-page text flood), hold state for candidates, status indicator during LLM calls

* Build the artefact card component: all fields listed in Section 6.3, rarity colour coding, action buttons

* Build the My Discoveries tab: browsable local log with sorting options

* Add scan controls: pause / resume / adjust scan speed

* **Distribution note:** plan packaging toward a **standalone executable / installer** for a polished “real app” feel (§6.2); web UI may precede the packaged build

* Output: a fully functional **local** application: **scanning, logging, and LLM inference require no cloud**. Optional community sync (Phase 4) uses the network **only when the explorer publishes** and is a **separate concern** from the offline core

## **Phase 4 — The Community Infrastructure**

* Set up Firebase Firestore project on the free tier — create the artefacts collection with the correct schema

* Implement the push-to-Firebase function — triggered only on **explicit user confirmation** from the artefact card (including the case where share is default-on: the control must still represent a clear confirm / publish action)

* Implement **Firestore security rules** and schema validation per §5.3; implement **stats contribution** writes per §5.4 if global counters are shown

* Implement **publication moderation** hooks per §8.4 (automated checks + reporting path as minimum)

* Build the GitHub Pages gallery: static HTML/JS reading from Firestore in real time, matching the local UI aesthetic

* Add global statistics aggregation to the gallery header

* Implement sorting and filtering controls on the gallery

* Distribute the gallery URL alongside the application

* Output: a live community gallery accessible worldwide at no cost

# **8\. OPEN QUESTIONS & FUTURE CONSIDERATIONS**

## **8.1 To Be Calibrated During Phase 1 Testing**

* **Artefact definition (v1 baseline):** a **logged candidate** is any page that passes **Filter 2** under the active threshold (initially ≥2 consecutive dictionary words). That record is the **artefact** for local history. **LLM commentary** runs on the same trigger unless a later queue/throttle policy defers it; tuning is allowed so the machine never drowns in inference backlog. **Publication** to the gallery is a **separate explicit action** (default-on UI, confirm to send — §6.3).

* **Scan speed vs. false positives:** The 2-consecutive-word threshold may produce too many low-quality matches on first run. Testing will determine whether to raise it to 3 words for the Common tier, or keep 2 and accept more LLM calls.

* **LLM call frequency:** If artefacts surface too frequently (due to a loose filter), the LLM may become a bottleneck. A queue system can be implemented so the scanner continues while the LLM processes a backlog.

* **Keyword bank completeness:** The Emissary mission keyword bank must be defined before Phase 1 begins. A first draft list: signal, light, collapse, transmission, fragment, decay, survive, time, instruction, seal, protocol, emit, trace, warn, origin, horizon, interval.

## **8.2 Potential Future Features (Out of Scope for v1.0)**

* **Multi-mission support:** Future versions could allow users to define their own mission keyword bank alongside the default Emissary mission — enabling the same engine to serve different lore contexts.

* **Extended moderation tooling:** e.g. volunteer review dashboard, reputation for explorers, automated classifiers beyond keyword lists — beyond the v1 minimum in §8.4.

* **Artefact visualisation:** Translating the character frequency of a fragment into a colour image (one pixel per character frequency band). A visual signature for each artefact, generated locally with Pillow.

* **Cross-explorer artefact linking:** A community feature allowing explorers to manually link artefacts they believe are related — creating chains of evidence. Implemented as a simple reference field in the Firebase schema.

## **8.3 What Will Never Be Resolved — By Design**

* **The Emissary's identity:** No update, patch, or expansion of the application will reveal who the Emissary was. This is the permanent mystery.

* **Whether the instructions are complete:** The lore states that the Emissary may not have finished transmitting. No artefact will ever confirm completeness. The archive grows but never closes.

* **What the Thinning actually is:** Implied throughout, named in the lore, never explained in the application. Vacuum decay is the real-world reference. The lore keeps it at arm's length.

## **8.4 Publication safety & moderation (v1 minimum — approved)**

The fictional tone of the Archivist does **not** exempt the **public gallery** from baseline platform hygiene. Approach: **realistic, Reddit-class guidelines** — expressive and atmospheric content is welcome; **hate, harassment, incitement, and illegal material are not**.

**Implementation expectations for v1:**

* **Automated pre-publish filters:** blocklists / patterns for severe slurs, incitement, and other **non-negotiable** categories; optional lightweight classifier if engineering capacity allows.

* **Human-readable community guidelines** linked from the gallery.

* **Report / flag** control on public artefact cards (abuse, illegal content, technical corruption).

* **Zero tolerance** categories (e.g. sexual content involving minors, credible threats) — **block publish** and follow **applicable law** for reporting and retention.

* **Scope:** moderation applies to **what is published** (fragment + Archivist-generated fields + pseudo). Local-only finds remain on the user’s machine under their responsibility; the **networked gallery** is where policy is enforced.

* **Authenticity:** filters should be **narrow** — remove or reject only what violates policy, not the weird, bleak, or vulgar-in-fiction tone of legitimate artefacts unless it crosses the guideline line.

*— End of Design Document —*

***The scan continues.***

| This document is a living specification. Lore anchors (§2.3) are final unless a deliberate edition is published. Technical, legal-safety, and UX decisions (Archivist Library ownership, Level B stats, Firebase posture, publication moderation) are locked for v1.1 intent but remain subject to calibration in implementation. The Emissary's identity will not be revealed. The Archivist does not know it is an AI. The scan continues. |
| :---- |

