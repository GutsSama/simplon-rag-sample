import os
import logging
import httpx
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional

# Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger("telegram-bridge")

app = FastAPI(title="Alertmanager Telegram Bridge")

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
async def webhook(payload: AlertmanagerPayload):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.error("Telegram credentials missing")
        raise HTTPException(status_code=500, detail="Telegram credentials missing")

    for alert in payload.alerts:
        message = format_alert(alert)
        await send_telegram_message(message)

    return {"status": "success"}

def format_alert(alert: Alert) -> str:
    status_emoji = "🚨" if alert.status == "firing" else "✅"
    severity = alert.labels.get("severity", "unknown").upper()
    alert_name = alert.labels.get("alertname", "Unknown Alert")
    summary = alert.annotations.get("summary", "No summary")
    description = alert.annotations.get("description", "No description")
    
    msg = (
        f"{status_emoji} *{alert.status.upper()}: {alert_name}*\n"
        f"━━━━━━━━━━━━━━━\n"
        f"*Sévérité*: `{severity}`\n"
        f"*Résumé*: {summary}\n"
        f"*Description*: {description}\n"
    )
    
    if alert.status == "firing":
        msg += f"\n⏳ *Début*: {alert.startsAt}"
    else:
        msg += f"\n🏁 *Fin*: {alert.endsAt}"
        
    return msg

async def send_telegram_message(text: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            logger.info(f"Successfully sent message to Telegram: {response.json()}")
        except Exception as e:
            logger.error(f"Failed to send message to Telegram: {e}")
            if hasattr(e, 'response'):
                logger.error(f"Response: {e.response.text}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
