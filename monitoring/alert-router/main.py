import os
import logging
import httpx
import time
from fastapi import FastAPI, Request, HTTPException, Query
from pydantic import BaseModel
from typing import List, Dict, Optional
from httpx import AsyncHTTPTransport

# Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")

# Setup Logging
logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("alert-router")

# HTTP Client with Retries
# Retry 3 times on connection errors or 5xx responses
transport = AsyncHTTPTransport(retries=3)
http_client = httpx.AsyncClient(transport=transport, timeout=10.0)

app = FastAPI(title="Simplon RAG Alert Router")

class Alert(BaseModel):
    status: str
    labels: Dict[str, str]
    annotations: Dict[str, str]
    startsAt: str
    endsAt: Optional[str] = None
    generatorURL: str

class AlertmanagerPayload(BaseModel):
    alerts: List[Alert]
    status: str
    receiver: str
    externalURL: str

@app.on_event("startup")
async def startup_event():
    logger.info("Initializing Alert Router...")
    logger.info(f"Telegram Config: {'ENABLED' if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID else 'DISABLED'}")
    logger.info(f"Discord Config: {'ENABLED' if DISCORD_WEBHOOK else 'DISABLED'}")

@app.on_event("shutdown")
async def shutdown_event():
    await http_client.aclose()

@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.1.0"}

@app.post("/webhook")
async def webhook(
    payload: AlertmanagerPayload, 
    channels: str = Query("telegram,discord")
):
    start_time = time.time()
    target_channels = channels.split(",")
    alert_count = len(payload.alerts)
    
    logger.info(f"Incoming request: {alert_count} alerts | Target: {target_channels}")

    results = {"telegram": "skipped", "discord": "skipped"}

    for alert in payload.alerts:
        alert_name = alert.labels.get("alertname", "Unknown")
        
        # 1. Telegram
        if "telegram" in target_channels and TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
            tg_msg = format_telegram_alert(alert)
            success = await send_telegram_message(tg_msg, alert_name)
            results["telegram"] = "success" if success else "failed"
        
        # 2. Discord
        if "discord" in target_channels and DISCORD_WEBHOOK:
            discord_payload = format_discord_alert(alert)
            success = await send_discord_message(discord_payload, alert_name)
            results["discord"] = "success" if success else "failed"

    duration = time.time() - start_time
    logger.info(f"Request processed in {duration:.3f}s | Results: {results}")

    return {
        "status": "completed", 
        "duration_sec": duration,
        "results": results
    }

def format_telegram_alert(alert: Alert) -> str:
    status_emoji = "🚨" if alert.status == "firing" else "✅"
    severity = alert.labels.get("severity", "unknown").upper()
    alert_name = alert.labels.get("alertname", "Unknown Alert")
    summary = alert.annotations.get("summary", "No summary")
    description = alert.annotations.get("description", "No description")
    
    return (
        f"{status_emoji} *{alert.status.upper()}: {alert_name}*\n"
        f"━━━━━━━━━━━━━━━\n"
        f"*Sévérité*: `{severity}`\n"
        f"*Résumé*: {summary}\n"
        f"*Description*: {description}\n"
        f"⏳ *Début*: {alert.startsAt}" if alert.status == "firing" else f"🏁 *Fin*: {alert.endsAt}"
    )

def format_discord_alert(alert: Alert) -> Dict:
    status_color = 0xFF0000 if alert.status == "firing" else 0x00FF00
    severity = alert.labels.get("severity", "unknown").upper()
    alert_name = alert.labels.get("alertname", "Unknown Alert")
    
    return {
        "username": "RAG-ALERTS-ROUTER",
        "embeds": [{
            "title": f"{alert.status.upper()}: {alert_name}",
            "color": status_color,
            "fields": [
                {"name": "Sévérité", "value": f"`{severity}`", "inline": True},
                {"name": "Status", "value": alert.status, "inline": True},
                {"name": "Résumé", "value": alert.annotations.get("summary", "No summary")},
                {"name": "Description", "value": alert.annotations.get("description", "No description")}
            ],
            "footer": {"text": f"Source: Prometheus | Start: {alert.startsAt}"}
        }]
    }

async def send_telegram_message(text: str, alert_name: str) -> bool:
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "Markdown"}
    try:
        r = await http_client.post(url, json=payload)
        r.raise_for_status()
        return True
    except Exception as e:
        logger.error(f"Telegram Delivery Failed [{alert_name}]: {e}")
        return False

async def send_discord_message(payload: Dict, alert_name: str) -> bool:
    try:
        r = await http_client.post(DISCORD_WEBHOOK, json=payload)
        r.raise_for_status()
        return True
    except Exception as e:
        logger.error(f"Discord Delivery Failed [{alert_name}]: {e}")
        return False

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
