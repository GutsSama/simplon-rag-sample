# Observability: LLM Tracing with Langfuse

## Overview
Phase 3 focuses on the "black box" of LLM calls in the `/explain` endpoint. We use Langfuse to trace the internal steps of the RAG pipeline.

## Implementation Details

### 1. Tracing Architecture
We use manual instrumentation to capture high-resolution traces of our RAG process. Each request to `/explain` generates a trace containing several "Spans".

- **Helper**: [llm_observability.py](file:///Users/amaury/simplon-rag-sample/api/src/rag/api/llm_observability.py)

### 2. Instrumented Spans
According to the brief, we capture:
- **`retrieval`**: Time taken to search the vector database and the number of chunks found.
- **`prompt_build`**: Captures the final prompt sent to the LLM.
- **`llm_call`**: A "Generation" span capturing the model name, input tokens, and output content.

### 3. Privacy & Compliance (RGPD)
To protect user data:
1. **Pseudonymization**: The `user_id` provided in the request is hashed using SHA-256 before being sent to Langfuse.
2. **Content Masking**: Only a snippet of the email content is stored in the retrieval span input to allow debugging without exposing PII.

### 4. Cost Tracking
Langfuse automatically calculates the cost of each request based on the model and token count. These costs are exported daily to Prometheus via a dedicated job: [export_langfuse_cost.py](file:///Users/amaury/simplon-rag-sample/api/src/rag/jobs/export_langfuse_cost.py).

## Verification
1. Call the `/explain` endpoint.
2. Log in to Langfuse at `http://localhost:3000`.
3. Locate the `explain_email` trace. You should see the hierarchy of spans and the associated cost.
