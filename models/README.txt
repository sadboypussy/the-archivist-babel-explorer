Archivist default weights (Phase 2)
====================================

**V1 (locked):** this file describes the **only** supported weight profile — **Llama 3.1 8B Instruct Q4_K_M** (no 3B or alternate GGUF in v1; see design doc §4.1 and §5.5).

Recommended file (matches design doc §4.1 — 8B instruct, Q4):

  Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf  (~4.9 GB)

Source: Hugging Face  bartowski/Meta-Llama-3.1-8B-Instruct-GGUF

Re-download or verify:

  pip install "huggingface_hub>=0.20"
  python scripts/download_model.py

First-time environment check (deps, GPU summary, GGUF path)::

  python scripts/first_run.py

Local UI (Streamlit)::

  pip install -r requirements-app.txt
  streamlit run archivist_app.py

Run the scanner with this file:

  python run_scanner.py --gguf models\Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf ...

Or set environment variable ARCHIVIST_GGUF to the full path; run_scanner.py picks it up when --gguf is omitted.

GPU inference (required for production)
---------------------------------------
The Archivist is meant to run on an **NVIDIA GPU** (design §4.1). The in-process path uses
``llama-cpp-python`` with CUDA offload.

**Policy:** if ``nvidia-smi`` sees an NVIDIA GPU, a **CUDA** build is **required** (CPU-only
``llama-cpp-python`` is rejected). If there is **no** NVIDIA GPU, a CPU build is allowed.

**Windows — first load:** loading ``ArchivistLLM`` registers CUDA ``bin`` paths, and if the
installed wheel is still CPU-only it automatically runs ``pip install`` on the matching
**dougeeai** CUDA wheel and **restarts** the process once so GPU offload activates.

You can still pre-install manually::

  python scripts/install_llama_cuda_windows.py

That script prints the same detection summary and forces a clean reinstall.

If a prebuilt wheel loads but crashes while creating the context (rare SIMD / binary
mismatches), keep **GPU** by running **llama-server** from the official llama.cpp CUDA
release (or LM Studio) with full layer offload, then::

  set ARCHIVIST_LLAMA_SERVER=http://127.0.0.1:8080
  python run_scanner.py --pages 5000

(or ``--llama-server``). Optional: ``ARCHIVIST_OPENAI_MODEL`` if your server expects a
specific model id.

Emergency CPU-only native load (not for production)::

  set ARCHIVIST_ALLOW_CPU=1

Note: *.gguf files are gitignored (too large for Git).
