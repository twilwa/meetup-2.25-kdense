# Anime Studio on Stream — MVP Research Brief

**Date:** 2026-02-25
**Sprint Goal:** Ship an MVP anime generation studio today, live on stream/stage
**Stack:** Modal (compute) · SeedDance 2.0 (generation) · k-dense-ai/claude-scientific-skills (Modal orchestration)
**Vibe:** Build it live, let the crowd yell prompts at it

---

## TL;DR Decision Matrix

| Component | Recommendation | Confidence | Risk |
|-----------|---------------|------------|------|
| **Compute** | Modal w/ L4 GPUs ($0.80/hr) | ★★★★★ | Low — production-proven, per-second billing |
| **Generation** | SeedDance 2.0 via JiMeng UI *or* Wan 2.1 on Modal | ★★★☆☆ | Medium — SD2.0 API delayed; Wan 2.1 is open-source fallback |
| **Orchestration** | k-dense-ai claude-scientific-skills Modal skill | ★★★★☆ | Low — 9.3k stars, 147 skills, Modal templates included |
| **Chat→Generation** | Streamer.bot + OBS WebSocket + Modal endpoints | ★★★★☆ | Low — all battle-tested |
| **Audio/Lip-sync** | HeadTTS (Kokoro) + Rhubarb | ★★★☆☆ | Medium — works but needs tuning |

---

## 1. The Stack in Plain English

You're building a system where:
1. You're live on stream (Twitch, YouTube, stage)
2. You (or chat) feed prompts into a generation pipeline
3. Modal spins up GPU containers, runs SeedDance 2.0 / Wan 2.1
4. Generated anime clips come back in ~2 minutes (SD2.0) or ~20-40 seconds (Wan 2.1 on RTX 4090 equivalent)
5. You show the results on stream, react, iterate

The k-dense-ai package gives your Claude agents pre-built Modal deployment templates so they can autonomously spin up endpoints, manage GPU containers, and orchestrate the pipeline without you hand-writing infra code.

**Real-world example:** Lemon Slice Live runs a similar architecture on Modal — thousands of concurrent video sessions, 3-6 second end-to-end latency, using L4 GPUs.

---

## 2. Modal — Your GPU Cloud

### Why Modal

Modal is the best fit here because it combines serverless auto-scaling with GPU access and per-second billing. You don't pay for idle time, and your agents can deploy functions programmatically.

### Key Numbers

| GPU | Cost/sec | Cost/hr | VRAM | Best For |
|-----|----------|---------|------|----------|
| **L4** | $0.000222 | $0.80 | 24 GB | Sweet spot — anime generation, inference |
| **A10G** | $0.000306 | $1.10 | 24 GB | Budget inference |
| **A100-40GB** | $0.000583 | $2.10 | 40 GB | Large models, training |
| **A100-80GB** | $0.000694 | $2.50 | 80 GB | Very large models |
| **H100** | $0.001097 | $3.95 | 80 GB | Maximum throughput |

**For today's sprint:** Start with L4. It's $0.80/hour, 24 GB VRAM, and can run Wan 2.1 comfortably. Upgrade to A100 if you need faster generation or SeedDance 2.0 style models.

### Critical Features for This Use Case

**GPU Memory Snapshots (Alpha):** Load your model once, snapshot the GPU state. Subsequent cold starts go from ~20 seconds to ~2 seconds. This matters when chat spams prompts and you need to scale containers fast.

```python
@app.cls(gpu="L4", enable_memory_snapshot=True)
class AnimeGenerator:
    @modal.enter(snap=True)
    def load_model(self):
        self.pipe = load_wan21_pipeline()  # Loaded once, snapshotted

    @modal.method()
    def generate(self, prompt: str):
        return self.pipe(prompt)  # Sub-second cold start on next call
```

**Concurrent Requests:** Single container handles 5-8 concurrent generation requests via `@modal.concurrent`. Means fewer containers for the same throughput.

**WebSocket Endpoints:** Native support for bidirectional streaming. Chat command → Modal WebSocket → generation → frame back. Full RFC 6455.

**Auto-scale to Zero:** Between prompts, containers spin down. You only pay during active generation. During a 2-hour stream, actual GPU time might be 30-40 minutes.

### Architecture Pattern

```
[Your Stream / Chat / Stage]
        ↓ (prompt)
[Modal FastAPI Endpoint]
        ↓
[GPU Container (L4/A100)]
  - Load model (from snapshot)
  - Generate anime clip
  - Return video/frames
        ↓
[Your Stream Display]
  - Show generated clip
  - React, iterate
```

### Cost Estimate for a 2-Hour Stream

Assuming ~30 generations, each taking ~60 seconds on L4:

```
30 generations × 60 seconds × $0.000222/sec = $0.40
Container overhead (cold starts, idle): ~$0.20
Total: ~$0.60 for 2 hours of live anime generation
```

That's basically free.

### References

- [Modal Pricing](https://modal.com/pricing)
- [Modal GPU Memory Snapshots](https://modal.com/docs/guide/memory-snapshot)
- [Modal Web Endpoints](https://modal.com/docs/guide/webhooks)
- [Modal Concurrent Inputs](https://modal.com/docs/guide/concurrent-inputs)
- [Lemon Slice Case Study (real-time video on Modal)](https://modal.com/blog/lemon-slice-case-study)

---

## 3. SeedDance 2.0 — The Generation Model

### What It Is

SeedDance 2.0 is ByteDance's flagship video generation model, launched February 12, 2026. It uses a Dual-Branch Diffusion Transformer that generates video AND audio simultaneously — no post-hoc audio sync needed.

### The Good

| Capability | Rating | Detail |
|-----------|--------|--------|
| Character consistency | 96.3% | Industry-leading identity retention across frames |
| Camera control | 9/10 | Tracking shots, dolly zooms, smooth pans |
| Resolution | Up to 2K | Native 2048x1152 |
| Duration | 15s (60s w/ extension) | Reasonable for clip-based generation |
| Audio-video sync | Millisecond-level | Joint generation, not post-hoc |
| Anime quality | ★★★★★ | Preserves 2D aesthetic, cross-hatching, sparkle effects |
| Speed | ~2 min/10s clip | Fastest in class vs Sora 2 (~50 min), Runway (~20 min) |
| Multimodal input | 4 modes | Text + images + video refs + audio refs simultaneously |
| Usable output rate | 90%+ | Only ~10% need re-rolling |

### The Bad (Critical for Today)

**The official API is DELAYED INDEFINITELY.** ByteDance postponed the REST API (originally Feb 24, 2026) due to copyright disputes with Hollywood. You cannot programmatically call SeedDance 2.0 through an official endpoint right now.

**Current access methods:**
1. **JiMeng AI web UI** (jimeng.com) — manual, not automatable for MVP
2. **Third-party API wrappers** — exist but unreliable, ToS risk
3. **Hugging Face free space** (ginigen) — watermarked, limited

**Model weights are NOT available.** You cannot download and run SeedDance 2.0 on Modal. It's closed-source.

### The Pivot: Wan 2.1 (Open-Source Alternative)

Since SeedDance 2.0 can't be self-hosted on Modal today, the pragmatic play is **Wan 2.1** by Alibaba:

| Feature | SeedDance 2.0 | Wan 2.1 |
|---------|---------------|---------|
| Open source | No | Yes — full weights on HuggingFace |
| Self-hostable on Modal | No | Yes |
| VRAM requirement | N/A (cloud only) | 8.19 GB minimum |
| Speed (5s clip, 480p) | ~1 min | ~4 min (RTX 4090) |
| Anime quality | ★★★★★ | ★★★★ |
| Character consistency | 96.3% | ~85% (improvable with LoRA) |
| Audio generation | Yes — joint | No — separate |
| Camera control | 9/10 | 5/10 |

**Recommendation:** Use **Wan 2.1 on Modal** as your primary generation engine. It's open-source, runs on L4 GPUs, and your agents can deploy it autonomously. Use SeedDance 2.0 via JiMeng web UI for hero shots when you want maximum quality.

**Hybrid approach for stream:**
- Quick generations (chat prompts, reactions): Wan 2.1 on Modal (~20-40s on A100)
- Hero shots (pre-planned, high quality): SeedDance 2.0 via web UI (pre-generate before stream)

### Competitor Comparison

| Model | Speed (10s clip) | Open Source | Anime Quality | Self-Hostable |
|-------|-----------------|-------------|---------------|---------------|
| SeedDance 2.0 | ~2 min | No | ★★★★★ | No |
| Wan 2.1 | ~4 min | Yes | ★★★★ | Yes |
| Sora 2 | ~50 min | No | ★★ | No |
| Kling 3.0 | ~3 min | No | ★★★★ | No |
| Runway Gen-4 | ~20 min | No | ★★★ | No |

### References

- [SeedDance 2.0 Official Page](https://seed.bytedance.com/en/seedance2_0)
- [SeedDance 2.0 Announcement](https://seed.bytedance.com/en/blog/official-launch-of-seedance-2-0)
- [Wan 2.1 GitHub](https://github.com/Wan-Video/Wan2.1)
- [Wan 2.1 on HuggingFace](https://huggingface.co/Wan-AI)
- [SeedDance 2.0 vs Competitors (DataCamp)](https://www.datacamp.com/blog/seedance-2-0)

---

## 4. k-dense-ai/claude-scientific-skills — Agent Orchestration for Modal

### What It Is

A collection of **147 ready-to-use Agent Skills** for Claude and compatible AI agents, maintained by K-Dense AI (9,297 GitHub stars, 100k+ users). The Modal skill specifically provides pre-built templates for deploying ML models on serverless GPU infrastructure.

### Why It Matters for Today

Your agents need to autonomously:
1. Write Modal deployment code
2. Package models into containers
3. Deploy endpoints
4. Manage GPU resources

The k-dense-ai Modal skill gives them **12 reference documentation files** covering every aspect of Modal deployment, plus production-ready code templates. Instead of your agents fumbling through Modal docs, they get structured patterns for container image building, model serving, WebSocket endpoints, volume management, concurrency configuration, and GPU selection.

### Setup (5 Minutes)

```bash
# Clone the skills
git clone https://github.com/K-Dense-AI/claude-scientific-skills.git

# Copy Modal skill to your agent's skills directory
cp -r claude-scientific-skills/scientific-skills/modal ~/.claude/skills/

# Install Modal
pip install modal
modal token new  # Browser auth
```

### What Your Agents Get

The Modal skill includes templates for:

```python
# Pattern 1: GPU-accelerated model serving
@app.cls(gpu="L4")
class ModelServer:
    @modal.enter(snap=True)
    def load(self): ...
    @modal.method()
    def generate(self, prompt): ...

# Pattern 2: WebSocket real-time endpoint
@app.function()
@modal.asgi_app()
def realtime_api(): ...

# Pattern 3: Batch generation
@app.function(gpu="L4")
def batch_generate(prompts: list[str]): ...

# Pattern 4: Scheduled pre-rendering
@app.function(schedule=modal.Cron("*/30 * * * *"))
def pre_render_scenes(): ...
```

### Key Repos

| Repo | Stars | Purpose |
|------|-------|---------|
| [claude-scientific-skills](https://github.com/K-Dense-AI/claude-scientific-skills) | 9,297 | 147 Agent Skills including Modal |
| [claude-skills-mcp](https://github.com/K-Dense-AI/claude-skills-mcp) | 325 | MCP server for semantic skill search |
| [karpathy](https://github.com/K-Dense-AI/karpathy) | 1,223 | Agentic ML Engineer |

### References

- [K-Dense-AI GitHub](https://github.com/K-Dense-AI)
- [claude-scientific-skills repo](https://github.com/K-Dense-AI/claude-scientific-skills)
- [K-Dense Web (hosted platform)](https://www.k-dense.ai)
- [Agent Skills specification](https://agentskills.io/)

---

## 5. The "Chat Yells Prompts" Architecture

Here's the architecture for a crowd-sourced anime generation stream where chat drives the content.

### How It Works

```
┌──────────────────────────────┐
│ TWITCH/YOUTUBE CHAT          │
│  !anime "girl with sword"    │
│  !anime "robot cat fight"    │
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│ CHAT BOT (Streamer.bot)      │
│  - Parse !anime commands     │
│  - Rate limit (1 per 10s)   │
│  - Queue management          │
│  - Priority for subs/bits    │
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│ MODAL ENDPOINT (FastAPI)     │
│  POST /generate              │
│  { "prompt": "...",          │
│    "style": "anime",         │
│    "duration": 5 }           │
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│ GPU CONTAINER (L4/A100)      │
│  Wan 2.1 + anime LoRA        │
│  ~20-40 seconds generation   │
│  Returns MP4 clip            │
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│ OBS (via WebSocket)          │
│  - Scene: "Generation Queue" │
│  - Shows: prompt text        │
│  - Then: plays generated clip│
│  - Overlay: who requested it │
└──────────────────────────────┘
```

### Latency Budget (Realistic)

| Phase | Time | Cumulative |
|-------|------|------------|
| Chat message → bot detection | 0.5-2s | 2s |
| Bot → Modal API call | 0.2-0.5s | 2.5s |
| Modal cold start (with snapshot) | 0.5-2s | 4.5s |
| Generation (Wan 2.1, 5s clip, A100) | 20-40s | 44.5s |
| Return + OBS scene switch | 1-2s | 46.5s |
| **Total: prompt to screen** | **~30-50 seconds** | |

That's the same generation cadence as a human artist doing speed-draws on stream. Very watchable.

### Making It Entertaining While Waiting

The ~30-50 second generation window is an opportunity:
- Show a "cooking" animation with the prompt text
- Display the generation queue (next 3-5 prompts)
- Show a progress bar (viewers love progress bars)
- React to the prompt before the result drops
- Show previous generations in a gallery rotation

### Interactive Commands (MVP Tier)

```
!anime "prompt"       → Queue a generation
!style cyberpunk      → Switch anime sub-style
!vote 1/2/3           → Chat votes on which prompt to generate next
!remix                → Re-generate the last clip with variation
!character swordgirl  → Use a specific character LoRA
```

### Scaling for Popularity

If your stream pops off and you're getting 100 prompts/minute:

```
100 prompts/min ÷ 8 concurrent per container = 13 containers
13 × $0.000222/sec (L4) = $0.17/minute = $10.32/hour

Or with A100 for faster generation:
13 × $0.000583/sec = $0.45/minute = $27/hour
```

Still cheap. Modal auto-scales, so if chat goes quiet, containers spin down.

---

## 6. Sprint Plan — MVP Today

### What "Today" Means with Agents

You said you have a bunch of agents. Here's how to parallelize this into a ~4-6 hour sprint (in agent-hours, which with parallelization = ~2-3 wall-clock hours):

### Workstream 1: Modal Infrastructure (Agent A)
**~1-2 hours (2-4 story points)**

1. Install k-dense-ai Modal skill into agent workspace
2. Write Modal app with Wan 2.1 model serving
3. Configure GPU memory snapshots for fast cold starts
4. Deploy FastAPI endpoint: `POST /generate` accepts prompt, returns video URL
5. Test with 5 sample prompts
6. Deploy to production: `modal deploy`

**Deliverable:** Live endpoint at `https://workspace--anime-gen.modal.run/generate`

### Workstream 2: Model Setup (Agent B)
**~1-2 hours (2-4 story points)**

1. Download Wan 2.1 weights to Modal Volume
2. (Optional) Train anime-style LoRA for character consistency (~1 hour GPU time)
3. Optimize inference: fp16, xformers attention, compile with torch.compile
4. Benchmark: measure generation time for 5s/10s clips at 480p/720p/1080p
5. Tune: find the sweet spot of quality vs speed for live generation

**Deliverable:** Optimized model on Modal Volume, benchmark numbers

### Workstream 3: Chat Integration (Agent C)
**~1 hour (1-2 story points)**

1. Set up Streamer.bot or custom Python Twitch bot
2. Parse `!anime "prompt"` commands
3. Queue management (rate limiting, priority)
4. POST to Modal endpoint with parsed prompt
5. Return result URL to OBS scene

**Deliverable:** Working chat bot that forwards prompts to Modal

### Workstream 4: OBS/Display Pipeline (Agent D or Manual)
**~1 hour (1-2 story points)**

1. OBS scenes: "Generating..." overlay, "Result" overlay, gallery rotation
2. OBS WebSocket integration: bot triggers scene switches
3. Audio setup: notification sound on generation complete
4. Test end-to-end: chat → generation → display

**Deliverable:** OBS configured for live anime generation display

### Workstream 5 (Bonus): SeedDance 2.0 Hero Shots
**~30 min (1 story point)**

1. Pre-generate 5-10 hero clips via JiMeng AI web UI
2. Download highest quality outputs
3. Add to OBS media library for intros/transitions/highlights

**Deliverable:** Pre-rendered SeedDance 2.0 clips ready for stream

### Dependency Graph

```
Workstream 1 (Modal Infra) ──┐
                              ├──→ Workstream 3 (Chat Integration) ──→ Workstream 4 (OBS)
Workstream 2 (Model Setup) ──┘

Workstream 5 (Hero Shots) ────→ Workstream 4 (OBS)

Parallelizable: [1, 2, 5] can run simultaneously
Sequential: 3 depends on 1+2; 4 depends on 3+5
```

---

## 7. Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| SeedDance 2.0 API never launches | High | Medium | Already pivoted to Wan 2.1 as primary |
| Wan 2.1 generation too slow for live stream | Medium | High | Pre-generate bursts during idle; use A100 instead of L4 |
| Modal cold starts cause visible delays | Low | Medium | GPU snapshots reduce to <2s; keep 1 warm container |
| Character inconsistency across clips | Medium | Medium | Train LoRA per character; use anchor frames |
| Chat spam overwhelms generation queue | Low | Low | Rate limiting, queue cap at 10, priority for subs |
| Audio/lip-sync out of sync | Medium | Medium | Phase 2 concern; MVP can be silent clips or TTS overlay |

---

## 8. What to Cut for MVP vs Phase 2

### MVP (Today)

- Modal endpoint serving Wan 2.1
- Chat command `!anime "prompt"` → generation → display
- Basic OBS scene switching (generating/result/gallery)
- Rate limiting and queue
- Pre-rendered SeedDance 2.0 hero shots for intros

### Phase 2 (This Week)

- Character LoRA training and switching
- Audio generation (TTS + lip-sync)
- Style switching (`!style cyberpunk`, `!style ghibli`)
- Voting system for prompt prioritization
- Gallery of all generated clips

### Phase 3 (Next Sprint)

- SeedDance 2.0 API integration (when it launches)
- Multi-character scenes
- Longer clip generation (30-60 seconds)
- Real-time generation (StreamDiffusion at 91 FPS for live img2img)
- LLM-powered prompt enhancement (Claude takes raw chat → cinematic prompt)

---

## 9. Contrarian Takes & Speculation

**Speculation: SeedDance API delay could last months.** Hollywood copyright disputes with AI video generators are intensifying. ByteDance may add heavy content filtering that degrades anime generation quality. Bet on Wan 2.1 as your long-term engine, with SeedDance as a quality ceiling you aspire toward.

**Contrarian: Don't optimize for real-time generation.** The *waiting* is part of the entertainment. Speed-draw streamers spend 30-60 seconds per iteration and it's compelling content. Your generation latency IS the content — show the process, build anticipation, reveal the result.

**Emerging tech to watch:** StreamDiffusion (91 FPS image generation). Within 6 months, someone will combine this with AnimateLCM for true real-time anime generation at 30+ FPS. When that happens, you can do live img2img where your webcam feed becomes anime in real-time — your movements driving character animation.

**Business model speculation:** If this takes off, the chat-driven generation model could monetize via bits/donations for priority queue, sub-only prompts at higher quality, generated clips as collectibles, and "season" compilations of best clips as YouTube content.

---

## 10. Key Links & References

### Primary Tools

- [Modal](https://modal.com) — Serverless GPU compute
- [Modal Pricing](https://modal.com/pricing) — Per-second GPU billing
- [Wan 2.1](https://github.com/Wan-Video/Wan2.1) — Open-source video generation
- [K-Dense-AI claude-scientific-skills](https://github.com/K-Dense-AI/claude-scientific-skills) — 147 Agent Skills including Modal
- [SeedDance 2.0](https://seed.bytedance.com/en/seedance2_0) — ByteDance video generation (web UI only for now)

### Streaming & Integration

- [OBS WebSocket](https://github.com/obsproject/obs-websocket) — OBS remote control (built-in since OBS 28)
- [Streamer.bot](https://streamer.bot/) — Twitch/YouTube chat automation
- [Open-LLM-VTuber](https://github.com/Open-LLM-VTuber/Open-LLM-VTuber) — Voice-interactive AI VTuber framework

### Generation & Animation

- [StreamDiffusion](https://github.com/cumulo-autumn/StreamDiffusion) — 91 FPS real-time image generation (ICCV 2025)
- [AnimateLCM](https://huggingface.co/wangfuyun/AnimateLCM) — Fast video diffusion (45-78 FPS)
- [Rhubarb Lip-Sync](https://github.com/DanielSWolf/rhubarb-lip-sync) — 2D mouth animation from audio

### Audio

- [HeadTTS / Kokoro-FastAPI](https://github.com/KoljaB/Kokoro-FastAPI) — Open-source TTS
- [XTTS / Coqui](https://github.com/coqui-ai/TTS) — Voice cloning TTS

### Research

- [SeedDance 2.0 Announcement](https://seed.bytedance.com/en/blog/official-launch-of-seedance-2-0)
- [SeedDance 2.0 vs Competitors (DataCamp)](https://www.datacamp.com/blog/seedance-2-0)
- [NVIDIA Video Storyboarding](https://research.nvidia.com/labs/par/video_storyboarding/) — Multi-shot character consistency
- [StreamDiffusion Paper (arXiv)](https://arxiv.org/abs/2312.12491) — Real-time pipeline architecture
- [Lemon Slice Live (Modal case study)](https://modal.com/blog/lemon-slice-case-study) — Production real-time video on Modal

---

*Research compiled by 4 parallel research agents. Ready to sprint.*
