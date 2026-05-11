# Observability: Structured Logging & Request Tracing

## Overview
Phase 1 of the observability implementation focuses on providing a consistent and searchable logging format across all services, and establishing a way to correlate logs belonging to the same user request.

## Implementation Details

### 1. JSON Structured Logging
We replaced the standard line-based logging with a JSON format using `python-json-logger`. This allows log aggregation systems (like ELK or Grafana Loki) to parse logs as structured data.

- **Configuration**: [logging_config.py](file:///Users/amaury/simplon-rag-sample/api/src/rag/api/logging_config.py)
- **Fields included**:
  - `timestamp`: UTC ISO8601 format.
  - `level`: Log level (INFO, ERROR, etc.).
  - `name`: Logger name (usually the module name).
  - `message`: The actual log message.
  - `request_id`: The correlation ID for the current request.

### 2. Request ID Middleware
A FastAPI middleware was added to `app.py` to ensure every request is assigned a unique identifier.

- **Logic**:
  1. Check for `X-Request-ID` in incoming headers.
  2. If absent, generate a new UUID.
  3. Store the ID in a `ContextVar` for access by the logger.
  4. Inject the ID into the outgoing response headers.
  5. Log the request completion with its duration and status code.

### 3. RGPD Compliance
The logger is configured to **never** log the raw content of emails. Only metadata (email length, presence of attachments, etc.) and pseudonymized identifiers are allowed in production logs.

## Verification
To verify the logging:
1. Run the API.
2. Make a request to `/api/v1/health`.
3. Check the console output. You should see a JSON object similar to:
   ```json
   {"timestamp": "2026-05-11T14:00:00.000Z", "level": "INFO", "name": "rag.api.app", "message": "Request processed", "request_id": "550e8400-e29b-41d4-a716-446655440000", "method": "GET", "path": "/api/v1/health", "status_code": 200, "duration": 0.0012}
   ```
