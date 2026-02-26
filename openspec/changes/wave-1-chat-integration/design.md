# Design: Wave 1 — Chat Integration

## Context

The Modal generation endpoint will be deployed and accepting POST requests. We need a bot that bridges Twitch chat to that endpoint.

## Goals

- Parse `!anime "prompt"` from chat, forward to Modal, notify OBS when done
- Rate limit per-user and globally to prevent abuse and cost overruns
- Handle chat disconnections gracefully

## Non-Goals

- YouTube chat support (Wave 2 — different API)
- Subscriber priority queue (Wave 2)
- LLM prompt enhancement (Wave 3)
- Persistent command history (Wave 2)

## Decisions

### Decision 1: twitchio Library

Use `twitchio` (Python async Twitch IRC library) rather than raw IRC sockets or Streamer.bot. Reasons: pure Python, async-native, well-maintained, keeps everything in one codebase. Streamer.bot is great but adds a separate runtime dependency.

### Decision 2: In-Memory Queue

Use `asyncio.Queue` with a max size of 10. No need for Redis or external queue for MVP. If the queue is full, new commands get a "queue full, try again later" response in chat.

### Decision 3: Per-User Rate Limiting via Dict

Simple dict mapping `user_id → last_command_timestamp`. Check on every command. Evict stale entries periodically. No external dependencies.

### Decision 4: Fire-and-Forget Generation

The bot fires the POST to Modal and awaits the response in a background asyncio task. When the response arrives, it downloads the MP4 from the signed `output_url`, writes the clip to a known path, and sends an OBS WebSocket message to switch scenes. The bot doesn't block on generation.

### Decision 5: Degraded Mode for Backlog Protection

If generation latency/error rate causes queue health to degrade (for example queue depth above threshold or repeated timeouts), the bot enters degraded mode: it notifies OBS to show hero-shot fallback content, posts a short status message in chat, and resumes normal flow when health recovers.

## Technical Approach

```
Chat Message Flow:
  Twitch IRC → twitchio event → parse_command()
    ↓ (if valid !anime command)
  rate_limit_check(user_id)
    ↓ (if allowed)
  queue.put(GenerationRequest(prompt, user, timestamp))
    ↓
  queue_worker() picks up request
    ↓
  modal_client.generate(prompt) → awaits ~30-50s
    ↓
  modal_client.download(output_url) → writes local clip
    ↓
  obs_notify.show_result(video_path, user, prompt)
    ↓
  chat.send(f"@{user} your anime is on screen!")
```
