# Spec: Chat Bot

## ADDED Requirements

### Requirement: Parse Anime Command

The bot SHALL parse `!anime "prompt text"` from Twitch chat messages.

#### Scenario: Valid command with quotes

- **WHEN** a chat message `!anime "girl with fire sword"` is received
- **THEN** the command is recognized as an anime generation request
- **AND** the extracted prompt is `girl with fire sword`

#### Scenario: Valid command without quotes

- **WHEN** a chat message `!anime robot cat doing ballet` is received
- **THEN** the extracted prompt is `robot cat doing ballet`

#### Scenario: Non-command message

- **WHEN** a chat message `hey everyone!` is received
- **THEN** no generation request SHALL be created

#### Scenario: Empty prompt

- **WHEN** a chat message `!anime` (no prompt text) is received
- **THEN** the bot SHALL reply with usage instructions
- **AND** no generation request SHALL be created

### Requirement: Rate Limiting

The bot SHALL enforce per-user rate limits to prevent spam.

#### Scenario: First command from user

- **WHEN** user `viewer123` sends `!anime "prompt"` for the first time
- **THEN** the command SHALL be accepted and queued

#### Scenario: Rapid repeat command

- **WHEN** user `viewer123` sends a second `!anime` within 30 seconds of their last accepted command
- **THEN** the command SHALL be rejected
- **AND** the bot SHALL reply with time remaining until they can submit again

### Requirement: Queue Management

The bot SHALL maintain a bounded generation queue.

#### Scenario: Queue not full

- **WHEN** a valid, rate-limited command is received and the queue has fewer than 10 items
- **THEN** the request SHALL be added to the queue

#### Scenario: Queue full

- **WHEN** a valid command is received but the queue already has 10 items
- **THEN** the command SHALL be rejected
- **AND** the bot SHALL reply "Queue is full (10/10). Try again in a minute!"

### Requirement: Forward to Modal

The bot SHALL forward queued prompts to the Modal generation endpoint.

#### Scenario: Successful generation

- **WHEN** a queued request is processed
- **THEN** the bot SHALL send POST to the Modal `/generate` endpoint with the prompt
- **AND** on success, SHALL download the video from the returned signed `output_url`
- **AND** SHALL trigger OBS scene switch to display the result
- **AND** SHALL reply in chat `@user your anime is on screen!`

#### Scenario: Generation failure

- **WHEN** the Modal endpoint returns an error or times out
- **THEN** the bot SHALL reply in chat `@user generation failed, try again later`
- **AND** the request SHALL be removed from the queue
- **AND** the failure MUST be logged

### Requirement: Graceful Reconnection

The bot SHALL handle Twitch IRC disconnections.

#### Scenario: Connection lost

- **WHEN** the Twitch IRC connection drops
- **THEN** the bot SHALL attempt to reconnect with exponential backoff (1s, 2s, 4s, max 30s)
- **AND** queued requests MUST be preserved during reconnection

### Requirement: Degraded Mode Behavior

The bot SHALL enter degraded mode when generation health is poor.

#### Scenario: Queue health degraded

- **WHEN** queue depth exceeds configured threshold or repeated generation timeouts occur
- **THEN** the bot SHALL trigger OBS fallback scene behavior
- **AND** SHALL notify chat that the system is temporarily degraded
- **AND** SHALL resume normal flow when queue health recovers

### Requirement: Bot Observability

The bot SHALL emit operational logs/counters for stream-night debugging.

#### Scenario: Queue event logging

- **WHEN** requests are enqueued, rejected, completed, or failed
- **THEN** structured logs SHALL include request id (when available), queue depth, and outcome
