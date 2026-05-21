# Simplon RAG - Game Day Playbook

This document outlines the scenarios to demonstrate during the technical defense.

## 1. Monitoring Stack Overview
- **Grafana**: [http://localhost:3001](http://localhost:3001)
  - Dashboard `RAG Performance & Quality`: Main business and technical KPI.
  - Dashboard `API RED`: System health (RPS, Errors, Latency).
- **Langfuse**: [http://localhost:3000](http://localhost:3000)
  - Traceability and visual debugging of the LangGraph flow.
- **Prometheus**: [http://localhost:9090](http://localhost:9090)
  - Alert status and raw metric exploration.

---

## 2. Test Scenarios

### Scenario A: Normal Business Flow
**Goal**: Show a perfect RAG response with full observability.
1. **Action**: Ask: `"Quelles sont les conditions d'admission chez Simplon ?"`
2. **Expected Observability Signals**:
   - **Grafana**: Request increase in "Guard Route Traffic" with `in_scope="True"`.
   - **Langfuse**: Detailed trace with `retrieve` -> `generate` -> `evaluate`.
   - **Loki**: Structured logs showing `guard_route_completed` and `generation_completed`.
   - **Metrics**: `rag_eval_score` should be high (>= 8).

### Scenario B: Out-of-Scope Detection
**Goal**: Demonstrate the Guardrail efficiency.
1. **Action**: Ask: `"Comment faire une pizza ?"`
2. **Expected Observability Signals**:
   - **Bot**: Replies with: *"Désolé, je ne peux répondre qu'aux questions concernant Simplon..."*
   - **Grafana**: Metric spike for `in_scope="False"`.
   - **Langfuse**: Trace stops abruptly after the `guard_route` node.
   - **Loki**: Log entry `guard_route_completed` with `in_scope=False`.

### Scenario C: Latency Spike (Stress Test)
**Goal**: Trigger the `HighP95Latency` alert.
1. **Simulation**: Run parallel requests using the dedicated traffic script:
   ```bash
   # Depuis la racine du projet, lancez le benchmark (20 requêtes, 4 en parallèle)
   uv run bench.py --messages 20 --concurrency 4
   ```
2. **Expected Observability Signals**:
   - **Grafana**: "RAG Node Latency (p95)" panel turns **RED** (threshold > 10s).
   - **Alertmanager**: [http://localhost:9093](http://localhost:9093) shows `HighP95Latency` as **FIRING**.
   - **Loki**: See logs with high `duration` values in the metadata.

### Scenario D: System Failure Recovery
**Goal**: Demonstrate resilience and error monitoring.
1. **Simulation**: Stop the Postgres container:
   ```bash
   docker stop simplon_rag_postgres
   ```
2. **Action**: Send any message.
3. **Expected Observability Signals**:
   - **Grafana (API RED)**: `5xx Error Rate` spikes above 5%.
   - **Alertmanager**: `HighErrorRate` alert triggers.
   - **Loki**: Search for `level="error"` or `SQLAlchemy` to see connection exceptions.
   - **Action**: Restart Postgres: `docker start simplon_rag_postgres`. System recovers automatically.

### Scenario E: LLM Budget Exceeded (3rd Alert Demo)
**Goal**: Demonstrate the cost monitoring system and Prometheus integration.
1. **Simulation**: Execute the Langfuse cost exporter job manually to push the day's total to the pushgateway.
   ```bash
   # Depuis la racine du projet
   uv run jobs/export_langfuse_cost.py
   ```
   *(Alternative : modifiez le script pour pousser une valeur factice de 50€ pour forcer l'alerte).*
2. **Expected Observability Signals**:
   - **Prometheus**: Metric `llm_daily_cost_euros` appears with the exact cost in €.
   - **Alertmanager**: `LLMDailyCostExceeded` triggers (if cost > 20€).
   - **Action**: Explain the mitigation process defined in `runbooks/llm-budget-exceeded.md` (e.g. switching back to local Ollama).

---

## 3. Incident Timeline (Example for Scenario C)
| Time | Event | Action/Observation |
| :--- | :--- | :--- |
| **14:00** | Traffic Burst | Manual trigger of 20 parallel requests. |
| **14:02** | Latency Spike | Grafana P95 dashboard crosses 10s threshold. |
| **14:03** | Alert Firing | Prometheus triggers `HighP95Latency`. |
| **14:05** | Trace Audit | Langfuse shows LLM nodes taking 15s+ due to CPU contention. |
| **14:08** | Recovery | Queue clears, latency returns to < 2s. |

---

## 4. Technical Defense Arguments
- **Precision Guardrails**: Use of `qwen2.5-coder:7b` for high-precision classification.
- **Data Privacy**: Automatic user ID pseudonymization in `LangfuseTracing`.
- **Performance**: GPU-accelerated Ollama on host to bypass Docker overhead.
- **Industrial Standards**: Fully instrumented with RED (Rate, Errors, Duration) and RAG-specific KPIs.
