# Spec: Model Optimization

## ADDED Requirements

### Requirement: Model Available on Volume

Wan 2.1 weights SHALL be stored on Modal Volume in fp16 diffusers format.

#### Scenario: Model stored successfully

- **WHEN** `modal run setup_model.py` completes
- **THEN** the Volume `anime-models` SHALL contain directory `wan2.1-fp16/`
- **AND** the model MUST be loadable via `DiffusionPipeline.from_pretrained("/models/wan2.1-fp16", torch_dtype=torch.float16)`
- **AND** the total size on Volume MUST be under 25 GB

### Requirement: Model Fits L4 VRAM

The optimized model SHALL fit within L4 GPU memory during inference.

#### Scenario: VRAM usage within bounds

- **WHEN** the model is loaded and generating a 480p/5s clip
- **THEN** peak VRAM usage SHALL NOT exceed 20 GB (leaving 4 GB headroom on 24 GB L4)

### Requirement: Benchmark Results Recorded

Generation benchmarks SHALL be run and results recorded.

#### Scenario: Benchmark completes

- **WHEN** `modal run benchmark.py` completes
- **THEN** results SHALL include generation time for at minimum: 480p/3s, 480p/5s, 720p/5s
- **AND** results MUST be written to `docs/benchmarks.md`
- **AND** each result MUST include: resolution, duration, generation_time_seconds, peak_vram_gb
- **AND** at least one tested preset SHALL be marked as degraded-mode safe
