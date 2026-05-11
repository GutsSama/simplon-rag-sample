import os
import requests
import time
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway

# Configuration
LANGFUSE_HOST = os.getenv("LANGFUSE_HOST", "http://localhost:3000")
LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY")
LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY")
PROMETHEUS_PUSHGATEWAY = os.getenv("PROMETHEUS_PUSHGATEWAY", "http://pushgateway:9091")

def get_langfuse_daily_cost():
    # Langfuse API call to get cost (conceptual, as per Langfuse API docs)
    # GET /api/public/metrics/usage
    url = f"{LANGFUSE_HOST}/api/public/metrics/usage"
    try:
        response = requests.get(
            url, 
            auth=(LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY),
            params={"daily": "true"}
        )
        data = response.json()
        # Extract today's cost
        return data.get("total_cost", 0.0)
    except Exception as e:
        print(f"Error fetching Langfuse cost: {e}")
        return 0.0

def export_to_prometheus():
    registry = CollectorRegistry()
    g = Gauge("llm_daily_cost_euros", "Total LLM cost for the day", registry=registry)
    cost = get_langfuse_daily_cost()
    g.set(cost)
    
    try:
        push_to_gateway(PROMETHEUS_PUSHGATEWAY, job="langfuse_cost_export", registry=registry)
        print(f"Successfully exported cost: {cost}€")
    except Exception as e:
        print(f"Error pushing to Prometheus: {e}")

if __name__ == "__main__":
    while True:
        export_to_prometheus()
        # Export every hour
        time.sleep(3600)
