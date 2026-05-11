# Observability: Alerting & Incident Response

## Overview
Phase 4 ensures that the team is proactively notified when the system degrades. We use Prometheus Alertmanager to route alerts to Discord.

## Alerting Strategy

### 1. Defined Alerts
We have configured 4 primary alerts in [rules.yml](file:///Users/amaury/simplon-rag-sample/prometheus/rules.yml):

| Alert Name | Condition | Severity |
|------------|-----------|----------|
| `HighPredictLatency` | p95 latency on /predict > 0.5s | Warning |
| `HighErrorRate` | 5xx errors > 5% of traffic | Critical |
| `ModelDriftDetected` | Drift score > 0.1 | Warning |
| `LLMBudgetExceeded` | Daily cost > 15€ | Critical |

### 2. Notification Routing
Alertmanager is configured to:
1. Group similar alerts together.
2. Wait 10 seconds before sending to avoid "flapping".
3. Send notifications to a Discord webhook.

## Incident Response (Runbooks)
Each alert is linked to a dedicated runbook that provides a step-by-step guide for diagnosis and mitigation:

- [High Latency Runbook](file:///Users/amaury/simplon-rag-sample/runbooks/high-latency-predict.md)
- [High Error Rate Runbook](file:///Users/amaury/simplon-rag-sample/runbooks/high-error-rate.md)
- [Model Drift Runbook](file:///Users/amaury/simplon-rag-sample/runbooks/prediction-drift.md)
- [LLM Budget Runbook](file:///Users/amaury/simplon-rag-sample/runbooks/llm-budget-exceeded.md)

## Verification
To test the alerting pipeline:
1. Simulate a high error rate by stopping the database: `docker-compose stop postgres`.
2. Wait 2 minutes.
3. Check the Prometheus Alerts UI at `http://localhost:9090/alerts`.
4. Verify the notification in the designated Discord channel.
