# Spec: OBS Display

## ADDED Requirements

### Requirement: Scene Switching

The controller SHALL switch OBS scenes based on generation lifecycle events.

#### Scenario: Generation started

- **WHEN** `show_generating(prompt, user)` is called
- **THEN** OBS SHALL switch to the "Generating" scene
- **AND** the prompt text overlay SHALL be updated with the prompt
- **AND** the user overlay SHALL be updated with `@username`

#### Scenario: Generation complete

- **WHEN** `show_result(video_path, prompt, user)` is called
- **THEN** OBS SHALL switch to the "Result" scene
- **AND** the video source SHALL be set to the generated clip file
- **AND** the prompt and user overlays SHALL be updated

#### Scenario: Return to idle

- **WHEN** `show_idle()` is called (or 15 seconds after result display)
- **THEN** OBS SHALL switch to the "Idle" scene

#### Scenario: Enter fallback

- **WHEN** `show_fallback(status_text)` is called
- **THEN** OBS SHALL switch to the "Fallback" scene
- **AND** fallback status overlay text SHALL be updated

### Requirement: Overlay Updates

The controller SHALL update text overlays with current generation info.

#### Scenario: Queue status update

- **WHEN** `update_queue_status(depth, max_depth)` is called
- **THEN** the queue overlay text SHALL be updated to `Queue: {depth}/{max_depth}`

### Requirement: Graceful Degradation

The controller SHALL handle OBS being unavailable.

#### Scenario: OBS not running

- **WHEN** the controller attempts to connect and OBS WebSocket is not available
- **THEN** a warning SHALL be logged
- **AND** the controller SHALL retry connection every 10 seconds
- **AND** the bot MUST continue operating (commands accepted, generation happens, just no OBS display)

#### Scenario: OBS disconnects mid-stream

- **WHEN** the WebSocket connection to OBS drops during operation
- **THEN** the controller SHALL log the disconnection
- **AND** SHALL attempt to reconnect with 5-second intervals
- **AND** SHALL resume scene control once reconnected

### Requirement: Scene Switch Telemetry

Scene transitions SHALL be observable for operator debugging.

#### Scenario: Scene switch logged

- **WHEN** any scene switch call succeeds or fails
- **THEN** a log event SHALL include target scene, reason, and request id when available
