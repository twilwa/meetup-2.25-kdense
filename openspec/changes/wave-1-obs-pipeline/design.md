# Design: Wave 1 — OBS Display Pipeline

## Context

OBS Studio runs locally on the streamer's machine. The bot (also local) sends WebSocket messages to OBS to switch scenes and update overlays when generation events occur.

## Goals

- 5 OBS scenes covering normal + degraded generation lifecycle
- Programmatic scene switching via WebSocket
- Dynamic text overlays showing prompt, user, queue status
- Smooth transitions between scenes

## Non-Goals

- Custom OBS plugins (too complex for MVP)
- Virtual camera output (not needed, OBS streams directly)
- Audio ducking or mixing automation (Wave 2)
- Multi-monitor dashboard (Wave 2)

## Decisions

### Decision 1: obsws-python Library

Use `obsws-python` (OBS WebSocket v5 Python client) — same library the chat bot already depends on. Single dependency, async-compatible.

### Decision 2: Five Scenes

1. **Idle** — Character art or logo with background music visualization. Shown when no generation is active.
2. **Generating** — "Cooking..." animation with the prompt text and requesting user displayed. Shown while Modal is processing.
3. **Result** — Full-screen display of the generated clip with prompt and user overlay. Shown when clip is ready.
4. **Gallery** — Rotating display of previously generated clips. Shown during extended idle periods.
5. **Fallback** — Hero-shot loop with "system busy" overlay. Shown when queue health is degraded.

### Decision 3: Text Sources for Overlays

Use OBS Text (GDI+/FreeType2) sources updated via WebSocket `SetInputSettings`. This avoids browser sources and keeps everything lightweight.

### Decision 4: Scene Export as JSON

Export the OBS scene collection as JSON for reproducibility. Include in `src/obs/scenes.json` so any machine can import the scene layout.

## Technical Approach

```
Generation Lifecycle → OBS Scenes:

  [Bot receives !anime command]
    → controller.show_generating(prompt, user)
    → OBS switches to "Generating" scene
    → Overlay shows: "🎨 Cooking: {prompt}\nRequested by @{user}\nQueue: {depth}/10"

  [Modal returns video]
    → controller.show_result(video_path, prompt, user)
    → OBS switches to "Result" scene
    → Video source plays the generated clip
    → Overlay shows: "✨ {prompt}\nby @{user}"

  [After 15 seconds]
    → controller.show_idle() or controller.show_gallery()
    → Returns to idle or gallery scene

  [Queue health degraded]
    → controller.show_fallback(status_text)
    → OBS switches to "Fallback" scene with hero-shot playback
```
