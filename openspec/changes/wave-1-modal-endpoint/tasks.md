# Tasks: Wave 1 — Modal Endpoint

## 1. Modal App Scaffold

- [ ] 1.1 Create `src/modal/` directory structure
- [ ] 1.2 Define Modal app with image (debian-slim + torch + diffusers + ffmpeg)
- [ ] 1.3 Create Modal Volume references for model weights and outputs
- [ ] 1.4 Configure GPU selection (L4 default, A100 via env var)

## 2. Generator Class

- [ ] 2.1 Implement `Generator` class with `@app.cls(gpu="L4", enable_memory_snapshot=True)`
- [ ] 2.2 Implement `@modal.enter(snap=True)` to load Wan 2.1 pipeline from Volume
- [ ] 2.3 Implement `generate()` method: accepts prompt/duration/resolution, writes clip artifact, returns clip metadata
- [ ] 2.4 Add `@modal.concurrent(max_inputs=4)` for concurrent request handling
- [ ] 2.5 Add warmup call in `enter()` to prime GPU before snapshot

## 3. FastAPI Endpoints

- [ ] 3.1 Create ASGI app with `@modal.asgi_app()`
- [ ] 3.2 Implement `POST /generate` with Pydantic request/response models
- [ ] 3.3 Implement signed URL output contract (no base64 video in JSON)
- [ ] 3.4 Implement `GET /outputs/{clip_id}` (or equivalent temporary object URL serving path)
- [ ] 3.5 Implement `GET /health` returning model status and GPU info
- [ ] 3.6 Add request validation and error handling
- [ ] 3.7 Add generation metadata to response (timing, model name, prompt, request id, expires_at)
- [ ] 3.8 Create `src/common/schemas.py` and use shared request/response models

## 4. Deployment

- [ ] 4.1 Test locally with `modal run`
- [ ] 4.2 Deploy to production with `modal deploy`
- [ ] 4.3 Verify endpoint URL is stable and accessible
- [ ] 4.4 Test cold start time (target: <5 seconds with snapshot)

## 5. Tests

- [ ] 5.1 Write unit tests for request validation and response serialization
- [ ] 5.2 Write integration test: POST /generate with sample prompt, verify response shape includes `output_url` and `expires_at`
- [ ] 5.3 Write integration test: GET /health, verify response
- [ ] 5.4 Write integration test: missing prompt returns 422
- [ ] 5.5 Write integration test: fetch `output_url`, verify MP4 bytes and expiry handling

## 6. Observability

- [ ] 6.1 Emit structured request logs with request id, duration, status, prompt hash (not raw prompt)
- [ ] 6.2 Emit counters/timers for generation latency and error rate
- [ ] 6.3 Expose minimal service metrics in `/health` or logs for operational triage

## 7. Verify

- [ ] 7.1 End-to-end: curl the deployed endpoint with a test prompt, fetch clip via signed URL
- [ ] 7.2 Measure and record generation time at 480p/5s
- [ ] 7.3 Verify GPU snapshot is working (second cold start <5s)
