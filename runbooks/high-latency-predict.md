# Runbook: High Latency on /predict

## Symptoms
- Alert `HighPredictLatency` is firing.
- Users report slowness when classifying emails.
- Grafana dashboard shows p95 latency > 0.5s.

## Diagnosis
1. Check the distribution of latencies on the Grafana dashboard.
2. Check API logs for any slow database queries or resource contention.
3. Verify if the scikit-learn model is being reloaded unnecessarily.
4. Check CPU usage on the `mailguard-api` container.

## Mitigation
- Restart the API container: `docker-compose restart api`.
- Scale the API if traffic is high.
- Optimize the model inference logic if needed.
