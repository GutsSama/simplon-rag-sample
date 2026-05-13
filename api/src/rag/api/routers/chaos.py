import asyncio
import time
from fastapi import APIRouter, HTTPException, Query
from rag.config.settings import get_settings

router = APIRouter(prefix="/chaos", tags=["chaos"])

# Global state to simulate failures
latency_ms = 0
force_error_code = None
ollama_broken = False

@router.post("/latency")
async def set_latency(ms: int = Query(..., description="Latency in milliseconds")):
    global latency_ms
    latency_ms = ms
    return {"status": "ok", "latency_ms": latency_ms}

@router.post("/error")
async def set_error(code: int | None = Query(None, description="HTTP error code to force (None to reset)")):
    global force_error_code
    force_error_code = code
    return {"status": "ok", "force_error_code": force_error_code}

@router.post("/ollama-break")
async def toggle_ollama(broken: bool = True):
    global ollama_broken
    ollama_broken = broken
    return {"status": "ok", "ollama_broken": ollama_broken}

@router.get("/status")
async def get_chaos_status():
    return {
        "latency_ms": latency_ms,
        "force_error_code": force_error_code,
        "ollama_broken": ollama_broken
    }

async def inject_chaos():
    """Middleware-like function to inject chaos into requests."""
    global latency_ms, force_error_code, ollama_broken
    
    if latency_ms > 0:
        await asyncio.sleep(latency_ms / 1000.0)
        
    if force_error_code:
        raise HTTPException(status_code=force_error_code, detail="Chaos induced error")
    
    return ollama_broken
