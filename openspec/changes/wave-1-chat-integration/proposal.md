# Proposal: Wave 1 — Chat Integration

## Why

The stream needs a way for viewers to submit anime generation prompts via chat. A bot monitors Twitch/YouTube chat for `!anime "prompt"` commands, manages a queue with rate limiting, and forwards prompts to the Modal generation endpoint. This is what makes the stream interactive rather than just a pre-recorded video.

## What Changes

- New Python bot that connects to Twitch chat (IRC/WebSocket)
- Command parser for `!anime "prompt"` and future commands
- Rate limiter: 1 command per user per 30 seconds, global cap of 10 queued
- Queue system that forwards prompts to Modal endpoint
- Callback mechanism to notify OBS when generation completes

## Capabilities

### New Capabilities

- `chat-command-parser`: Parse `!anime "prompt"` from chat messages, extract prompt text
- `generation-queue`: FIFO queue with rate limiting, max depth, priority support (subs)
- `modal-client`: HTTP client that POSTs to the Modal generation endpoint, receives signed clip URL, downloads MP4, and writes output clip
- `obs-notifier`: Fires OBS WebSocket event when a clip is ready for display
- `degraded-mode`: When generation backlog/timeouts cross threshold, trigger fallback hero-shot flow and inform chat

## Impact

- New file: `src/bot/main.py` — Bot entry point, chat connection
- New file: `src/bot/commands.py` — Command parsing
- New file: `src/bot/queue.py` — Generation queue with rate limiting
- New file: `src/bot/modal_client.py` — Modal endpoint HTTP client
- New file: `src/bot/obs_notify.py` — OBS WebSocket notification
- New file: `src/common/schemas.py` — Shared request/response/event schema imports used by bot + endpoint
- New file: `tests/test_commands.py` — Command parsing tests
- New file: `tests/test_queue.py` — Queue behavior tests

## Constraints

- Depends on: Modal endpoint deployed (wave-1-modal-endpoint)
- Bot must handle disconnections gracefully (Twitch IRC drops)
- Must not flood Modal with requests (rate limiting is mandatory)
- Queue depth visible to streamer (log or simple API)
- Must switch to fallback mode when queue health is degraded (thresholds defined with OBS pipeline)
