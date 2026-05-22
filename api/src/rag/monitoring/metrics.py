from prometheus_client import Counter, Histogram

# RAG specific metrics
RAG_GUARD_ROUTE_TOTAL = Counter(
    "rag_guard_route_total",
    "Total number of guard route calls",
    ["category", "in_scope", "needs_retrieval"],
)

RAG_ESCALATION_TOTAL = Counter(
    "rag_escalation_total",
    "Total number of human escalations",
)

RAG_NODE_DURATION_SECONDS = Histogram(
    "rag_node_duration_seconds",
    "Duration of RAG agent nodes in seconds",
    ["node_name"],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0, float("inf")),
)

RAG_EVAL_SCORE = Histogram(
    "rag_eval_score",
    "RAG evaluation score from 0 to 10",
    buckets=(0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10),
)
