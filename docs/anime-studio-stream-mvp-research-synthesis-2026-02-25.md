# Anime Studio on Stream — Research Synthesis (MVP Sprint)

Date: 2026-02-25
Scope: Synthesis of both existing research reports, with supplemental claim checks.

## Source Inputs

- `docs/anime-studio-stream-mvp-research-2026-02-25.md`
- `docs/anime-studio-stream-mvp-research-2026-02-25-copy-2.md`

Both source files are content-identical (same SHA-256), so this synthesis consolidates one canonical view and adds confidence labeling.

## Executive Summary

- The MVP architecture is sound: chat command -> queue -> Modal generation -> OBS scene switch.
- Wan 2.1 remains the practical Wave 1 generation engine because it is open-source and self-hostable.
- SeedDance 2.0 should be treated as a quality-tier/manual pipeline for hero shots unless API entitlement is confirmed in your account.
- Wave 1 endpoint contract should be standardized as `base64` MP4 payload to reduce moving parts.
- Performance requirements should be percentile SLOs (p95/p99), not absolute "always under X seconds" guarantees.

## Architecture Snapshot (MVP)

```text
[Twitch Chat] -- !anime --> [Bot + Rate Limit + Queue]
                             |
                             v
                      [Modal /generate]
                             |
                             v
             { status, video(base64 mp4), metadata }
                             |
                             v
              [Bot decodes -> local clip path]
                             |
                             v
                    [OBS scene controller]
```

## Claim Check Matrix

### High Confidence (confirmed)

1. Modal exposes L4 pricing in official pricing docs (`$0.000222/s`, i.e. `$0.7992/h`).
2. Wan 2.1 is open-source and published in official repo/Hugging Face org.
3. OBS WebSocket is integrated directly into OBS Studio since OBS 28.

### Medium Confidence (supported but context-dependent)

1. Snapshot-style fast cold starts are a valid Modal strategy, but exact startup times vary by image/model/runtime.
2. Live generation throughput/cost claims are directionally plausible but depend strongly on prompt length, steps, resolution, and concurrency pattern.

### Low Confidence / Needs Direct Validation

1. "SeedDance 2.0 API delayed indefinitely" is not established via a clearly authoritative public status page in this synthesis pass.
2. Any exact side-by-side speed claims versus other vendors should be treated as provisional until replicated with your own benchmark harness.

## Decisions for Wave 1

1. Primary model: Wan 2.1 on Modal.
2. SeedDance 2.0 usage: manual hero-shot generation path unless API entitlement is proven in your environment.
3. Endpoint payload: base64 MP4 in response body for Wave 1.
4. Reliability/performance language: SLOs with percentiles (p95/p99) instead of absolute guarantees.

## Updated SLO Baseline (recommended)

- Generation latency (`duration=5`, `resolution=480p`):
  - p95 <= 60s
  - p99 <= 90s
- Cold start (snapshot restore):
  - p95 <= 5s
  - p99 <= 8s
- Burst concurrency behavior:
  - >= 99% success rate under defined burst test
  - <= 1% contention-related failures

## MVP Sprint Plan (pragmatic)

1. Modal endpoint first (`POST /generate`, `GET /health`).
2. Model setup + benchmark harness second (record p50/p95/p99).
3. Bot + queue + base64 decode + OBS notifier.
4. OBS scene setup and end-to-end smoke run.
5. Manual hero-shot ingestion pipeline for intro/idle/transitions.

## What To Validate Immediately (first 2 hours)

1. Real measured p95 latency for your exact model preset.
2. Base64 payload size behavior vs OBS handoff path.
3. End-to-end queue delay under at least one synthetic burst.
4. SeedDance access reality for your account/region (if needed for hero shots).

## Risks Still Worth Tracking

1. Generation latency variance during cold periods and autoscaling churn.
2. Queue pressure from chat spikes causing delayed user feedback.
3. Character consistency quality drift without LoRA strategy.
4. Payload bloat from base64 as duration/resolution increase.

## Exit Criteria for "MVP Ready"

1. Chat command produces visible clip in OBS end-to-end.
2. p95/p99 metrics are measured and recorded (not guessed).
3. Error paths are user-visible (queue full, timeout, generation failure).
4. Stream-safe fallback scenes work if generation service is degraded.

## References

- Modal pricing: https://modal.com/pricing
- Modal snapshots (guide): https://modal.com/docs/guide/memory-snapshot
- Wan 2.1 repo: https://github.com/Wan-Video/Wan2.1
- Wan Hugging Face org: https://huggingface.co/Wan-AI
- OBS WebSocket integrated in OBS 28: https://obsproject.com/blog/obs-studio-28-release
- SeedDance official page: https://seed.bytedance.com/en/seedance2_0
- SeedDance launch post: https://seed.bytedance.com/en/blog/official-launch-of-seedance-2-0

