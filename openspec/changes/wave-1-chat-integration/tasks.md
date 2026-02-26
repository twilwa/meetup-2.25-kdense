# Tasks: Wave 1 — Chat Integration

## 1. Bot Scaffold

- [ ] 1.1 Create `src/bot/` directory structure
- [ ] 1.2 Add `twitchio` and `obsws-python` to project dependencies
- [ ] 1.3 Create `src/bot/main.py` with twitchio bot setup and event loop
- [ ] 1.4 Create `.env.example` with required Twitch OAuth token and channel config
- [ ] 1.5 Import shared request/response models from `src/common/schemas.py`

## 2. Command Parser

- [ ] 2.1 Create `src/bot/commands.py` with `parse_anime_command(message)` function
- [ ] 2.2 Handle quoted and unquoted prompt text
- [ ] 2.3 Handle empty/missing prompt with usage reply
- [ ] 2.4 Write tests: `tests/test_commands.py`

## 3. Rate Limiter and Queue

- [ ] 3.1 Create `src/bot/queue.py` with `GenerationQueue` class
- [ ] 3.2 Implement per-user rate limiting (30s cooldown)
- [ ] 3.3 Implement bounded asyncio.Queue (max 10)
- [ ] 3.4 Implement queue worker that processes requests sequentially
- [ ] 3.5 Write tests: `tests/test_queue.py`

## 4. Modal Client

- [ ] 4.1 Create `src/bot/modal_client.py` with async HTTP client
- [ ] 4.2 POST to Modal `/generate` endpoint with prompt
- [ ] 4.3 Handle timeout (60s) and error responses
- [ ] 4.4 Download MP4 from signed `output_url` and persist clip locally
- [ ] 4.5 Validate signed URL expiry handling and retry behavior

## 5. OBS Notification

- [ ] 5.1 Create `src/bot/obs_notify.py` with OBS WebSocket client
- [ ] 5.2 Implement `show_result()` — switch OBS scene, update source with video
- [ ] 5.3 Implement `show_generating()` — switch to "generating" scene with prompt text

## 6. Integration

- [ ] 6.1 Wire command parser → queue → modal client → obs notify in main.py
- [ ] 6.2 Add graceful reconnection logic with exponential backoff
- [ ] 6.3 Add chat reply messages for queue status, errors, completions
- [ ] 6.4 Implement degraded mode: on queue/timeout threshold, trigger OBS hero-shot fallback + chat status

## 7. Observability

- [ ] 7.1 Emit structured logs for request id, user, queue depth, generation duration, outcome
- [ ] 7.2 Track counters for rate-limit rejects, queue overflows, and degraded-mode activations
- [ ] 7.3 Add periodic queue health log output for streamer/operator visibility

## 8. Verify

- [ ] 8.1 End-to-end: send `!anime "test"` in chat → verify generation → verify OBS switch
- [ ] 8.2 Verify rate limiting works (rapid commands rejected)
- [ ] 8.3 Verify queue overflow handling (11th command rejected)
- [ ] 8.4 Verify reconnection on simulated disconnect
- [ ] 8.5 Verify degraded mode enters/exits correctly under simulated Modal timeouts
