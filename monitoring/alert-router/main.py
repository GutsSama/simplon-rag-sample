import os
import logging
import httpx
from fastapi import FastAPI, Request, HTTPException, Query
from pydantic import BaseModel
from typing import List, Dict, Optional

# Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")

logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger("alert-router")

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

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/webhook")
async def webhook(
    payload: AlertmanagerPayload, 
    channels: str = Query("telegram,discord") # Default to both if not specified
):
    target_channels = channels.split(",")
    logger.info(f"Received alert for channels: {target_channels}")

    for alert in payload.alerts:
        # 1. Telegram
        if "telegram" in target_channels and TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
            tg_msg = format_telegram_alert(alert)
            await send_telegram_message(tg_msg)
        
        # 2. Discord
        if "discord" in target_channels and DISCORD_WEBHOOK:
            discord_payload = format_discord_alert(alert)
            await send_discord_message(discord_payload)

    return {"status": "success", "processed_channels": target_channels}

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

async def send_telegram_message(text: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "Markdown"}
    async with httpx.AsyncClient() as client:
        try:
            r = await client.post(url, json=payload)
            r.raise_for_status()
        except Exception as e:
            logger.error(f"Telegram error: {e}")

async def send_discord_message(payload: Dict):
    async with httpx.AsyncClient() as client:
        try:
            r = await client.post(DISCORD_WEBHOOK, json=payload)
            r.raise_for_status()
        except Exception as e:
            logger.error(f"Discord error: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
