from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST
from fastapi import APIRouter, Response

# Metrics definitions
HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total", 
    "Total number of HTTP requests", 
    ["method", "endpoint", "status"]
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds", 
    "HTTP request duration in seconds", 
    ["method", "endpoint"],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0]
)

# ML Metrics for /predict
PREDICTION_DISTRIBUTION = Counter(
    "ml_prediction_total", 
    "Total number of predictions by class", 
    ["prediction_class", "model_version"]
)

PREDICTION_CONFIDENCE = Histogram(
    "ml_prediction_confidence", 
    "Distribution of prediction confidence scores", 
    ["model_version"],
    buckets=[0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 1.0]
)

MODEL_DRIFT_SCORE = Gauge(
    "ml_model_drift_score", 
    "Model drift score (e.g. KS test result)", 
    ["model_version"]
)

# LLM Metrics for /explain (Phase 3)
LLM_DAILY_COST = Gauge(
    "llm_daily_cost_euros", 
    "Total LLM cost for the current day in Euros"
)

router = APIRouter(prefix="/metrics", tags=["observability"])

@router.get("")
async def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
