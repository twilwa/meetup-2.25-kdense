# Design: Wave 1 — Modal Endpoint

## Context

No application code exists yet. The repo has agent tooling bootstrapped and k-dense-ai/claude-scientific-skills cloned. We need to go from zero to a deployed Modal endpoint serving Wan 2.1 for anime generation.

## Goals

- Deploy a Modal app that accepts text prompts and returns generated anime video clips
- Sub-2s cold starts using GPU memory snapshots
- Per-request cost under $0.02 for a 5-second clip on L4
- Endpoint callable from external services (chat bot, manual testing)

## Non-Goals

- Real-time frame streaming (Wave 3)
- Multi-model serving or LoRA switching (Wave 2)
- Authentication or rate limiting at the endpoint level (chat bot handles this)
- Audio generation (Wave 3)

## Decisions

### Decision 1: Modal Class-Based Architecture

Use `@app.cls()` with `@modal.enter(snap=True)` for model lifecycle management. This gives us GPU memory snapshots (model loaded once, snapshotted for instant restarts) and clean separation between model loading and inference.

```python
@app.cls(gpu="L4", enable_memory_snapshot=True)
class Generator:
    @modal.enter(snap=True)
    def load_model(self): ...

    @modal.method()
    def generate(self, prompt, duration, resolution): ...
```

Rationale: The k-dense-ai Modal skill documents this as the production pattern. Lemon Slice Live uses this architecture at scale.

### Decision 2: Volume-Based Model Storage

Store Wan 2.1 weights on a Modal Volume rather than baking into the container image. This decouples model updates from image rebuilds and allows the model-setup workstream to optimize weights independently.

```python
model_volume = modal.Volume.from_name("anime-models", create_if_missing=True)
```

Rationale: Wan 2.1 is ~10-20GB. Baking into image would make rebuilds slow. Volume approach allows hot-swapping models without redeployment.

### Decision 3: FastAPI ASGI App

Use `@modal.asgi_app()` wrapping a FastAPI app rather than individual `@modal.fastapi_endpoint()` decorators. This gives us multiple routes in a single deployment and WebSocket upgrade path for Wave 3.

### Decision 4: Signed URL Output Contract (Wave 1)

Generate video to Modal output storage, return clip metadata plus a short-lived signed URL in JSON. Do not return base64 video payloads in control-plane responses.

Rationale: keeps binary data off JSON responses, reduces latency/memory overhead, and stabilizes contracts between endpoint, bot, and OBS pipeline.

### Decision 5: Shared Schema + Baseline Telemetry

Define endpoint request/response models in `src/common/schemas.py` so the bot and endpoint import identical Pydantic types. Emit structured logs and minimal metrics (request id, generation latency, success/failure, queue/fallback signals from clients) for stream-night operability.

## Technical Approach

```
Modal App "anime-studio"
├── Image: debian-slim + torch + diffusers + wan2.1 deps + ffmpeg
├── Volume: "anime-models" (Wan 2.1 weights)
├── Volume: "anime-outputs" (generated clips, ephemeral)
├── Class: Generator
│   ├── enter(snap=True): Load Wan 2.1 pipeline to GPU
│   └── method generate(): Run inference, return video bytes
└── ASGI App: FastAPI
    ├── POST /generate — Accept prompt, return clip metadata + signed URL
    ├── GET /outputs/{clip_id} — Signed URL target (or equivalent temporary object URL)
    ├── GET /health — Service status
    └── (Wave 3: WS /ws/stream — Real-time streaming)
```
