# Tasks: Wave 1 — OBS Display Pipeline

## 1. OBS Controller

- [ ] 1.1 Create `src/obs/controller.py` with OBS WebSocket client wrapper
- [ ] 1.2 Implement `connect()` with retry logic (10s interval)
- [ ] 1.3 Implement `show_generating(prompt, user)` — switch scene + update overlays
- [ ] 1.4 Implement `show_result(video_path, prompt, user)` — switch scene + set video source
- [ ] 1.5 Implement `show_idle()` — return to idle scene
- [ ] 1.6 Implement `show_gallery()` — rotate through previous results
- [ ] 1.7 Implement `show_fallback(status_text)` — switch to fallback hero-shot scene
- [ ] 1.8 Handle disconnection with automatic reconnect

## 2. Overlay Manager

- [ ] 2.1 Create `src/obs/overlays.py` with text source update functions
- [ ] 2.2 Implement `update_prompt_text(text)` — SetInputSettings for prompt overlay
- [ ] 2.3 Implement `update_user_text(username)` — SetInputSettings for user overlay
- [ ] 2.4 Implement `update_queue_status(depth, max_depth)` — queue depth overlay
- [ ] 2.5 Implement `update_system_status(text)` — degraded/healthy overlay indicator

## 3. OBS Scene Setup Documentation

- [ ] 3.1 Create `docs/obs-setup.md` with manual OBS scene creation instructions
- [ ] 3.2 Document required scenes: Idle, Generating, Result, Gallery, Fallback
- [ ] 3.3 Document required sources per scene (text overlays, video source, etc.)
- [ ] 3.4 Document OBS WebSocket setup (enable, port, password)
- [ ] 3.5 Export scene collection to `src/obs/scenes.json` if possible

## 4. Observability

- [ ] 4.1 Log every scene switch event with reason + request id (when available)
- [ ] 4.2 Log overlay update failures and reconnect attempts

## 5. Verify

- [ ] 5.1 Controller connects to OBS and switches scenes without error
- [ ] 5.2 Text overlays update correctly with prompt and user info
- [ ] 5.3 Video source plays a test clip on Result scene
- [ ] 5.4 Fallback scene activates on degraded-mode signal and returns to idle on recovery
- [ ] 5.5 Graceful handling when OBS is not running
