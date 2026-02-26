# Tasks: Wave 1 — Model Setup

## 1. Model Download Script

- [ ] 1.1 Create `src/modal/setup_model.py` with Modal function
- [ ] 1.2 Download Wan 2.1 weights from HuggingFace (Wan-AI org)
- [ ] 1.3 Convert to fp16 precision
- [ ] 1.4 Enable xformers memory-efficient attention config
- [ ] 1.5 Save to Modal Volume `anime-models/wan2.1-fp16/`
- [ ] 1.6 Commit Volume

## 2. Benchmark Script

- [ ] 2.1 Create `src/modal/benchmark.py` with Modal function
- [ ] 2.2 Load model from Volume
- [ ] 2.3 Generate test clips: 480p/3s, 480p/5s, 720p/5s, 720p/10s
- [ ] 2.4 Record timing, VRAM, output file size for each
- [ ] 2.5 Identify and document at least one degraded-mode safe preset
- [ ] 2.6 Write results to `docs/benchmarks.md`

## 3. Run and Validate

- [ ] 3.1 Run `modal run setup_model.py` — verify model on Volume
- [ ] 3.2 Run `modal run benchmark.py` — record benchmarks
- [ ] 3.3 Verify model loadable by endpoint Generator class pattern
- [ ] 3.4 Verify peak VRAM under 20 GB on L4
- [ ] 3.5 Verify endpoint/bot shared schema defaults align with benchmarked presets

## 4. Verify

- [ ] 4.1 Cross-check: endpoint workstream can load model from Volume
- [ ] 4.2 Benchmarks documented in `docs/benchmarks.md`
