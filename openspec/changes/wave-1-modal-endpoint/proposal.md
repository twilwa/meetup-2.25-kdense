# Proposal: Wave 1 — Modal Endpoint

## Why

We need a GPU-backed generation endpoint that accepts text prompts and returns anime video clips. This is the core compute layer — everything else (chat bot, OBS display) depends on this endpoint existing and being callable over HTTP.

Modal is the compute platform because it offers per-second GPU billing, sub-2s cold starts via GPU memory snapshots, native WebSocket/FastAPI support, and auto-scale to zero.

## What Changes

- New Modal app deployed to production serving Wan 2.1 for anime video generation
- FastAPI endpoint `POST /generate` accepting prompt text and returning clip metadata + short-lived signed URL for MP4 download
- GPU memory snapshots configured for fast cold starts
- Modal Volume storing Wan 2.1 model weights (shared with model-setup workstream)
- Health check endpoint for monitoring

## Capabilities

### New Capabilities

- `generation-endpoint`: HTTP endpoint that accepts a text prompt and generation parameters, runs Wan 2.1 inference on GPU, returns a video clip (MP4 or frame sequence)
- `health-check`: Simple endpoint returning service status and GPU availability

## Impact

- New file: `src/modal/app.py` — Modal app definition, image, volumes
- New file: `src/modal/generate.py` — Generation class with model loading and inference
- New file: `src/modal/endpoints.py` — FastAPI routes
- New file: `src/common/schemas.py` — Shared request/response models used by endpoint + bot
- New file: `tests/test_modal_endpoint.py` — Endpoint integration tests

## Constraints

- Must use k-dense-ai Modal skill patterns for deployment
- L4 GPU as default, A100 as configurable upgrade
- Latency SLO target: p95 generation time <= 60 seconds for MVP presets
- Response must include generation metadata (time, model, prompt used, request id)
- Signed URL expiry must be short-lived (target: <= 5 minutes)
