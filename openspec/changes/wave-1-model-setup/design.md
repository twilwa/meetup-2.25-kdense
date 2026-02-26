# Design: Wave 1 — Model Setup

## Context

Wan 2.1 weights are available on HuggingFace (Wan-AI org). They need to be downloaded, converted to fp16, and stored on a Modal Volume so the generation endpoint can load them.

## Goals

- Wan 2.1 weights available on Modal Volume in fp16 format
- Generation time benchmarked at key resolution/duration combos
- Model loadable in <5 seconds from Volume (with GPU snapshot)

## Non-Goals

- LoRA training or fine-tuning (Wave 2)
- Multi-model support (Wave 2)
- Quantization beyond fp16 (not needed for L4 24GB)

## Decisions

### Decision 1: fp16 Only

Convert all weights to float16. Wan 2.1's base model fits comfortably in L4's 24GB VRAM at fp16. No need for int8/int4 quantization which would degrade quality.

### Decision 2: Diffusers Pipeline Format

Store weights in HuggingFace diffusers pipeline format. This is what the endpoint's Generator class expects and ensures compatibility with `from_pretrained()`.

### Decision 3: Separate Setup Script

Model preparation runs as a one-time Modal function (`modal run setup_model.py`), not as part of the serving app. This keeps the serving app clean and allows re-running setup independently.

### Decision 4: Benchmark as Separate Modal Function

Benchmarking runs its own Modal function with the same GPU config as production. Results are written to `docs/benchmarks.md` for human review and to inform resolution/duration defaults.

### Decision 5: Explicit "Safe Preset" Output

Benchmark results must nominate at least one lower-cost preset suitable for degraded mode (for example 480p/3s or 480p/5s), so queue pressure can be reduced without pausing generation entirely.

## Technical Approach

```
setup_model.py (modal run):
  1. Download Wan 2.1 from HuggingFace
  2. Convert to fp16
  3. Enable xformers attention
  4. Save to Volume /anime-models/wan2.1-fp16/
  5. Commit Volume

benchmark.py (modal run):
  1. Load model from Volume
  2. Generate test clips at [480p/3s, 480p/5s, 720p/5s, 720p/10s]
  3. Record wall-clock time, VRAM usage, output quality notes
  4. Print results table
```
