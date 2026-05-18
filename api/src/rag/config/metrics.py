from prometheus_client import Counter, Histogram, Gauge

# Métriques agent
guard_route_counter = Counter(
    "rag_guard_route_total",
    "Nombre de passages dans guard_route",
    ["in_scope", "category"]
)

retrieve_chunks_histogram = Histogram(
    "rag_retrieve_chunks",
    "Nombre de chunks récupérés par requête",
    buckets=[0, 1, 2, 5, 10, 20]
)

evaluate_score_histogram = Histogram(
    "rag_evaluate_score",
    "Distribution des scores d'évaluation",
    buckets=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
)

evaluate_decision_counter = Counter(
    "rag_evaluate_decision_total",
    "Décisions de l'évaluateur",
    ["decision"]  # answer, rewrite, escalate
)

retry_counter = Counter(
    "rag_retry_total",
    "Nombre de retries déclenchés"
)

escalate_counter = Counter(
    "rag_escalate_total",
    "Nombre d'escalades vers un humain"
)