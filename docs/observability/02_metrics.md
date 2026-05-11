# Observability: Prometheus Metrics & Monitoring

## Overview
Phase 2 implements quantitative monitoring using Prometheus to track the health, performance, and business logic of the MailGuard API.

## Implementation Details

### 1. The RED Method
We follow the **RED** (Rate, Errors, Duration) method for HTTP monitoring:
- **Rate**: `http_requests_total` (Counter) - Number of requests per second.
- **Errors**: `http_requests_total{status=~"5.."}` - Number of failed requests.
- **Duration**: `http_request_duration_seconds` (Histogram) - Request latency distribution.

### 2. ML-Specific Metrics
For the spam classifier (`/predict`), we track:
- **Prediction Distribution**: `ml_prediction_total` (Counter) - Count of spam vs non-spam vs phishing.
- **Confidence Scores**: `ml_prediction_confidence` (Histogram) - Helps identify when the model is becoming uncertain.
- **Model Drift**: `ml_model_drift_score` (Gauge) - Quantifies the change in prediction distribution over a sliding window.

### 3. Metric Exposure
The API exposes a `/api/v1/metrics` endpoint that Prometheus scrapes every 15 seconds.

- **Source**: [metrics.py](file:///Users/amaury/simplon-rag-sample/api/src/rag/api/metrics.py)

## Infrastructure (Prometheus & Grafana)
The `docker-compose.yml` includes:
- **Prometheus**: Scrapes the API and stores historical metrics.
- **Grafana**: Visualizes the metrics. A dashboard "MailGuard Overview" is provisioned to show:
  - Global QPS and Error Rate.
  - Latency p50/p95 by endpoint.
  - ML Prediction mix.
  - Drift score over time.

## Verification
1. Access `http://localhost:8000/api/v1/metrics` to see the raw metrics.
2. Access Grafana at `http://localhost:3001` (user: `admin`, pass: `admin`).
