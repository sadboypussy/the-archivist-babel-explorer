# Windows portable bundle (maintainer)

Builds a **self-contained folder** (embeddable CPython + `pip` deps + app copy) under `dist/ArchivistPortable/`. Intended for **developers / QA / internal beta**, not the **v1 consumer channel** — see **`THE_ARCHIVIST_Design_Document_v2.md` §5.5** (public release = classic Windows installer).

## Prerequisites (build machine only)

- Windows x64, PowerShell 5.1+
- Internet access (downloads Python embeddable + wheels on first build)
- `python` on PATH is optional; the script downloads **embeddable** Python into the bundle

## Command

From repo root:

```powershell
powershell -ExecutionPolicy Bypass -File packaging\windows\build_portable_bundle.ps1
```

Options:

| Flag | Meaning |
|------|--------|
| `-PythonVersion 3.11.9` | Embeddable patch version (must exist on python.org) |
| `-OutputName ArchivistPortable` | Folder name under `dist/` |
| `-SkipPipInstall` | Only layout / copy; skip `pip install` (debug) |
| `-DryRun` | Print planned paths and exit |

## After build

1. Zip `dist/ArchivistPortable/` and ship the archive.
2. Tell users to place a GGUF under `app\models\` (see `app\models\README.txt`) or pass `--llama-server` for a local CUDA server.
3. For NVIDIA + native CUDA wheel inside the bundle, run **`python scripts\install_llama_cuda_windows.py`** once **inside** the portable `app` tree using the bundle’s `python\python.exe`, then re-zip — or document GPU users to use `--llama-server`.

## Size

Expect **hundreds of MB** (Python + llama-cpp-python CPU wheel + deps). GGUF is **not** included.

## Inno Setup (consumer installer skeleton)

See **`Archivist.iss`** in this folder. Compile with [Inno Setup](https://jrsoftware.org/isinfo.php) after preparing `#define MyAppSource` (payload with `Launch-Archivist-UI.bat` or equivalent calling `streamlit run …`). §5.5 of the design doc defines the target product channel.

**Payload Streamlit / galerie :** inclure un `pip install` couvrant **`requirements-app.txt`** (contient `streamlit` et `firebase-admin`). Pour la publication Firestore, l’utilisateur (ou l’installeur) place le JSON sous **`config/firebase-service-account.json`** — voir `config/firebase-service-account.README.txt` à la racine du dépôt (fichier sensible, non versionné).
