# Proposal: Wave 1 — Model Setup

## Why

The Modal endpoint needs optimized Wan 2.1 model weights available on a Modal Volume. Raw HuggingFace weights are unoptimized — we need to download, convert to fp16, configure xformers attention, and benchmark to find the quality/speed sweet spot for live streaming.

This workstream runs in parallel with the Modal endpoint workstream. The endpoint consumes whatever this workstream puts on the Volume.

## What Changes

- Wan 2.1 model weights downloaded and stored on Modal Volume `anime-models`
- Inference optimized: fp16 precision, xformers memory-efficient attention, optional torch.compile
- Benchmark data for generation times at 480p/720p at 3s/5s/10s durations (including fallback-safe presets)
- Setup script for reproducible model preparation

## Capabilities

### New Capabilities

- `model-preparation`: Script to download, optimize, and store Wan 2.1 weights on Modal Volume
- `benchmark`: Script to measure generation time across resolution/duration combinations

## Impact

- New file: `src/modal/setup_model.py` — Model download and optimization script
- New file: `src/modal/benchmark.py` — Generation benchmark runner
- New file: `docs/benchmarks.md` — Recorded benchmark results
- Writes to Modal Volume: `anime-models/wan2.1-fp16/`

## Constraints

- Must fit in L4 GPU VRAM (24 GB) — fp16 mandatory
- Model must be loadable by the endpoint workstream's Generator class
- Benchmark must test at minimum: 480p/5s and 720p/5s
- Benchmark output must identify at least one "safe preset" for degraded mode operation
