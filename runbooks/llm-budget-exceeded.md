# Runbook: LLM Daily Budget Exceeded

## Symptoms
- Alert `LLMBudgetExceeded` is firing.
- `llm_daily_cost_euros` > 15€.

## Diagnosis
1. Check Langfuse "Cost" dashboard to identify high-consumption users.
2. Verify if there is an "agent loop" (a trace with a very high number of spans/generations).
3. Check the average token count per request.

## Mitigation
- Rate-limit the top-consuming users.
- Switch to a cheaper model (e.g., Mistral Small) for non-critical requests.
- Kill any runaway processes identified in Langfuse.
- Notify the CFO and request a budget increase if the growth is legitimate.
