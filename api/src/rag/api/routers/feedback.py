import structlog
from fastapi import APIRouter, HTTPException
from langfuse import Langfuse
from pydantic import BaseModel

from rag.config.settings import get_settings

logger = structlog.get_logger()

router = APIRouter(prefix="/feedback", tags=["feedback"])


class FeedbackRequest(BaseModel):
    trace_id: str
    score: int  # 1 for 👍, 0 for 👎


@router.post("")
async def submit_feedback(body: FeedbackRequest):
    settings = get_settings()

    if not settings.langfuse_public_key or not settings.langfuse_secret_key:
        logger.warning("langfuse_not_configured_for_feedback")
        raise HTTPException(status_code=503, detail="Langfuse not configured")

    try:
        langfuse = Langfuse(
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key,
            host=settings.langfuse_host,
        )

        langfuse.create_score(
            trace_id=body.trace_id,
            name="user-feedback",
            value=body.score,
        )
        # Flush to ensure the event is dispatched immediately
        langfuse.flush()
        
        logger.info("feedback_submitted", trace_id=body.trace_id, score=body.score)

    except Exception as e:
        logger.error("langfuse_feedback_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to submit feedback to Langfuse")

    return {"status": "ok", "trace_id": body.trace_id, "score": body.score}
