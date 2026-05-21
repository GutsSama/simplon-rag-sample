import asyncio
import os
import time
from datetime import datetime, timezone
import requests
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway

# Configure URLs and keys from environment
LANGFUSE_HOST = os.getenv("LANGFUSE_HOST", "http://localhost:3002")
LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY")
LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY")
PUSHGATEWAY_URL = os.getenv("PUSHGATEWAY_URL", "http://localhost:9091")

def get_daily_cost():
    if not LANGFUSE_PUBLIC_KEY or not LANGFUSE_SECRET_KEY:
        print("Langfuse keys not configured, cannot fetch metrics.")
        return 0.0

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Langfuse API - Get metrics/daily
    url = f"{LANGFUSE_HOST}/api/public/metrics/daily?page=1&limit=50"
    auth = (LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY)
    
    try:
        response = requests.get(url, auth=auth, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Find today's total cost
        # The API returns an array of daily aggregates
        for item in data.get("data", []):
            if item.get("date", "").startswith(today):
                return item.get("totalCost", 0.0)
                
    except Exception as e:
        print(f"Error fetching Langfuse cost: {e}")
        
    return 0.0

def push_metrics():
    registry = CollectorRegistry()
    cost_gauge = Gauge(
        'llm_daily_cost_euros', 
        'Total LLM cost in EUR for the current day', 
        registry=registry
    )
    
    cost = get_daily_cost()
    print(f"[{datetime.now()}] Fetched LLM Daily Cost: {cost} €")
    
    cost_gauge.set(cost)
    
    try:
        push_to_gateway(PUSHGATEWAY_URL, job='langfuse_cost', registry=registry)
        print("Successfully pushed to pushgateway.")
    except Exception as e:
        print(f"Error pushing to pushgateway: {e}")

if __name__ == "__main__":
    print("Starting Langfuse Cost Exporter Job...")
    while True:
        push_metrics()
        # Sleep for 15 minutes
        time.sleep(900)
