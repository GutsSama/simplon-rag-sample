#!/bin/bash
# scripts/chaos_reset.sh
# KILL SWITCH: Resets all active chaos engineering scenarios immediately

echo "🚨 ACTIVATING CHAOS KILL SWITCH 🚨"
echo "========================================="

# 1. Reset Latency
echo "- Resetting latency to 0ms..."
curl -s -X POST "http://localhost:8000/api/v1/chaos/latency?ms=0" | grep -q '"status":"ok"' && echo "  ✅ Latency reset" || echo "  ❌ Failed to reset latency"

# 2. Reset Error Codes
echo "- Resetting forced HTTP errors..."
curl -s -X POST "http://localhost:8000/api/v1/chaos/error" | grep -q '"status":"ok"' && echo "  ✅ Errors reset" || echo "  ❌ Failed to reset errors"

# 3. Reset Ollama availability
echo "- Restoring Ollama simulation state..."
curl -s -X POST "http://localhost:8000/api/v1/chaos/ollama-break?broken=false" | grep -q '"status":"ok"' && echo "  ✅ Ollama state restored" || echo "  ❌ Failed to restore Ollama state"

echo "========================================="
echo "🟢 System should now return to normal operations."
echo "   Monitor Grafana to ensure P95 and 5xx rates drop."
