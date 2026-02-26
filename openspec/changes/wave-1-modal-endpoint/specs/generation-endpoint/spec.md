# Spec: Generation Endpoint

## ADDED Requirements

### Requirement: Accept Generation Request

The system SHALL accept an HTTP POST request with a text prompt and optional generation parameters, and return a generated anime video clip.

#### Scenario: Successful generation

- **WHEN** a POST request is sent to `/generate` with body `{"prompt": "anime girl with sword", "duration": 5, "resolution": "480p"}`
- **THEN** the response status is 200
- **AND** the response body contains `{"status": "success", "output_url": "<signed-url>", "expires_at": "<iso8601>", "metadata": {"prompt": "...", "duration": 5, "generation_time_seconds": <float>, "model": "wan2.1", "request_id": "<id>"}}`
- **AND** `metadata.generation_time_seconds` MUST be present for SLO tracking
- **AND** the response MUST NOT contain base64-encoded video payloads

#### Scenario: Default parameters

- **WHEN** a POST request is sent to `/generate` with body `{"prompt": "robot cat fight"}`
- **THEN** duration defaults to 5 seconds
- **AND** resolution defaults to "480p"

#### Scenario: Missing prompt

- **WHEN** a POST request is sent to `/generate` with body `{}`
- **THEN** the response status is 422
- **AND** the response body contains a validation error for the missing prompt field

### Requirement: Health Check

The system SHALL expose a health check endpoint for monitoring.

#### Scenario: Service healthy

- **WHEN** a GET request is sent to `/health`
- **THEN** the response status is 200
- **AND** the response body contains `{"status": "healthy", "model_loaded": true, "gpu": "<gpu-type>"}`

### Requirement: GPU Memory Snapshot

The system SHALL use GPU memory snapshots to minimize cold start time.

#### Scenario: Cold start performance

- **WHEN** 20 new containers start from a snapshot in a benchmark window
- **THEN** cold start ready time has p95 <= 5 seconds and p99 <= 8 seconds
- **AND** no model download SHALL occur during startup (restored from snapshot)

### Requirement: Generation Latency SLO

Generation performance SHALL be tracked using percentile-based SLOs for the MVP preset (`duration=5`, `resolution=480p`).

#### Scenario: Latency SLO measured

- **WHEN** at least 30 generation requests are executed with the MVP preset
- **THEN** p95 `generation_time_seconds` MUST be <= 60 seconds
- **AND** p99 `generation_time_seconds` MUST be <= 90 seconds
- **AND** results MUST be recorded in benchmark output

### Requirement: Concurrent Request Handling

The system SHALL handle multiple concurrent generation requests.

#### Scenario: Concurrent requests

- **WHEN** 40 requests are sent in bursts of 4 simultaneous requests
- **THEN** at least 99% MUST complete successfully (HTTP 2xx)
- **AND** contention-related failures (429/5xx/timeouts) MUST be <= 1%

### Requirement: Operational Telemetry

The endpoint SHALL emit baseline observability signals for stream operations.

#### Scenario: Structured logging

- **WHEN** any generation request is processed
- **THEN** a structured log entry SHALL include `request_id`, outcome status, and `generation_time_seconds`
- **AND** prompt content SHALL be redacted or hashed in logs
