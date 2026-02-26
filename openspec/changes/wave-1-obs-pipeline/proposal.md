# Proposal: Wave 1 — OBS Display Pipeline

## Why

Generated clips need to reach the stream. OBS Studio is the compositing and encoding layer — it takes generated video, overlays information (who requested it, what prompt, queue status), and sends the final stream to Twitch/YouTube via RTMP.

The bot triggers scene switches via OBS WebSocket. This workstream defines the OBS scene layout, overlay templates, and the WebSocket control scripts.

## What Changes

- OBS scene collection configured for anime studio streaming
- Scene templates: idle, generating, result display, gallery rotation, degraded fallback
- Python OBS WebSocket controller for programmatic scene switching
- Overlay templates showing prompt text, requester name, queue depth

## Capabilities

### New Capabilities

- `obs-scene-controller`: Python module that switches OBS scenes via WebSocket based on generation lifecycle events
- `overlay-manager`: Updates text overlays (prompt, username, queue status) in OBS sources
- `fallback-display`: Dedicated scene behavior for hero-shot playback when live generation is degraded

## Impact

- New file: `src/obs/controller.py` — OBS WebSocket scene management
- New file: `src/obs/overlays.py` — Overlay text update logic
- New file: `src/obs/scenes.json` — Scene collection export/import config
- New directory: `media/overlays/` — Static overlay assets (frames, backgrounds)
- New file: `docs/obs-setup.md` — Manual OBS setup instructions for the human

## Constraints

- Depends on: Chat integration (wave-1-chat-integration) for trigger events
- Depends on: Hero shots (wave-1-hero-shots) for intro/transition media
- OBS WebSocket v5 (built-in since OBS 28)
- Must handle OBS not running / WebSocket unavailable gracefully
- Must support degraded mode trigger from bot queue health signals
