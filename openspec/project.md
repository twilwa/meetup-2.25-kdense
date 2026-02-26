# Anime Studio on Stream — Project Spec

## Overview

An anime generation studio designed to be built and run live on stream/stage. Users (or Twitch/YouTube chat) submit prompts, a GPU-backed generation pipeline produces anime video clips, and results are displayed in real-time via OBS compositing.

## Current State

**Phase:** Bootstrap / Infrastructure complete, research complete, no application code yet.

**What exists:**
- Repository bootstrapped with full agent tooling: OpenSpec, beads, mise, trunk, jj, sem, sg
- k-dense-ai/claude-scientific-skills cloned into repo (147 Agent Skills including Modal)
- Two research documents compiled in `docs/` covering all four technology vectors
- No application code, no Modal deployments, no bot code, no OBS configuration

**Research findings (2026-02-25):**
- Modal is the compute platform: L4 GPUs at $0.80/hr, per-second billing, GPU memory snapshots for sub-2s cold starts, native WebSocket support, auto-scale to zero
- SeedDance 2.0 API is delayed indefinitely (Hollywood copyright dispute); model weights are closed-source and cannot be self-hosted
- Wan 2.1 (Alibaba, open-source) is the primary generation engine: full weights on HuggingFace, runs on L4/A100, ~20-40s per 5s clip
- k-dense-ai Modal skill provides 12 reference docs and production deployment templates for agents
- Streaming architecture uses pre-rendered burst pattern: generate clips async, display via OBS scene switching
- Chat integration via Streamer.bot or custom Python bot → Modal FastAPI endpoint → GPU container → OBS display
- ~30-50 seconds from chat prompt to clip on screen (acceptable for interactive content)
- Estimated cost: ~$0.60 for a 2-hour stream (~30 generations)

## Tech Stack

| Layer | Technology | Status |
|-------|-----------|--------|
| **Compute** | Modal (serverless GPU) | Selected, not deployed |
| **Generation** | Wan 2.1 (primary), SeedDance 2.0 (hero shots via web UI) | Selected, not deployed |
| **Agent Skills** | k-dense-ai/claude-scientific-skills (Modal skill) | Cloned into repo |
| **Chat Bot** | Streamer.bot or custom Python (Twitch API) | Not started |
| **Streaming** | OBS Studio + OBS WebSocket | Not started |
| **Audio** | HeadTTS (Kokoro) + Rhubarb lip-sync | Phase 2 |
| **Language** | Python 3.11+ | Available via mise |
| **Package Manager** | uv (Astral) | Available via mise |

## Architecture

```
[Twitch/YouTube Chat]
    ↓ !anime "prompt"
[Chat Bot (Python/Streamer.bot)]
    ↓ POST /generate
[Modal FastAPI Endpoint]
    ↓ JSON metadata + signed clip URL
[GPU Container (L4/A100)]
  Wan 2.1 + optional anime LoRA
  ~20-40s generation
    ↓ clip artifact
[OBS (via WebSocket)]
  Scene switching: queue → generating → result → gallery/fallback
    ↓ RTMP
[Twitch/YouTube Stream]
```

## Build Plan

### Wave 1 — MVP Sprint (Today)

Five parallelizable workstreams targeting a working end-to-end demo:

1. **Modal Endpoint** (Agent A, ~2-4 story points)
   - Modal app with Wan 2.1 serving
   - GPU memory snapshots for fast cold starts
   - FastAPI endpoint: `POST /generate`
   - Deployed to production

2. **Model Setup** (Agent B, ~2-4 story points)
   - Download Wan 2.1 weights to Modal Volume
   - Optimize inference: fp16, xformers, torch.compile
   - Benchmark generation times at various resolutions

3. **Chat Integration** (Agent C, ~1-2 story points)
   - Python Twitch bot parsing `!anime "prompt"` commands
   - Rate limiting and queue management
   - POST to Modal endpoint, download MP4 from signed URL response, write clip for OBS

4. **OBS Display Pipeline** (Agent D, ~1-2 story points)
   - OBS scenes: generating overlay, result display, gallery rotation
   - WebSocket integration for scene switching
   - Audio notification on generation complete

5. **Hero Shots** (Manual/Agent E, ~1 story point)
   - Pre-generate 5-10 clips via SeedDance 2.0 JiMeng web UI
   - Add to OBS media library for intros/transitions

**Dependency graph:**
```
[1: Modal Endpoint] ──┐
                       ├──→ [3: Chat Integration] ──→ [4: OBS Pipeline]
[2: Model Setup]   ──┘
[5: Hero Shots]    ────────────────────────────────→ [4: OBS Pipeline]
```

### Wave 2 — Polish (This Week)

- Character LoRA training and switching
- Style switching commands (`!style cyberpunk`, `!style ghibli`)
- Voting system for prompt prioritization
- Gallery of all generated clips
- Basic error handling and reconnection logic

### Wave 3 — Advanced (Next Sprint)

- Audio generation: TTS + lip-sync
- SeedDance 2.0 API integration (when available)
- Multi-character scenes
- LLM-powered prompt enhancement
- StreamDiffusion real-time img2img mode

## Key Risks

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| SeedDance 2.0 API never launches | High | Wan 2.1 is primary engine, SD2.0 is bonus |
| Wan 2.1 too slow for interactive stream | Medium | Use A100 instead of L4; pre-generate during idle |
| Modal cold starts visible to audience | Low | GPU snapshots + keep 1 warm container |
| Character inconsistency across clips | Medium | Phase 2: train LoRA per character |

## Conventions

- All Modal app code in `src/modal/`
- Chat bot code in `src/bot/`
- OBS configuration/scripts in `src/obs/`
- Shared utilities in `src/common/`
- Tests mirror source structure in `tests/`
- Pre-rendered media in `media/`
- Temporary artifacts in `scratchpad/`
- Durable documentation in `docs/`

## References

- [Modal Docs](https://modal.com/docs)
- [Wan 2.1 GitHub](https://github.com/Wan-Video/Wan2.1)
- [k-dense-ai claude-scientific-skills](https://github.com/K-Dense-AI/claude-scientific-skills)
- [SeedDance 2.0](https://seed.bytedance.com/en/seedance2_0)
- [OBS WebSocket](https://github.com/obsproject/obs-websocket)
- [Streamer.bot](https://streamer.bot/)
- [StreamDiffusion](https://github.com/cumulo-autumn/StreamDiffusion)
- Research brief: `docs/anime-studio-stream-mvp-research-2026-02-25.md`
