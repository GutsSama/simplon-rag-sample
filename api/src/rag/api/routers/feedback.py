from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from rag.api.llm_observability import tracing

router = APIRouter(prefix="/feedback", tags=["feedback"])

class FeedbackRequest(BaseModel):
    trace_id: str
    score: float  # 1.0 for 👍, 0.0 for 👎
    comment: str = None

@router.post("")
async def submit_feedback(request: FeedbackRequest):
    """
    Submit user feedback for a specific LLM trace.
    The score is written to Langfuse.
    """
    try:
        tracing.score(
            trace_id=request.trace_id,
            name="user_feedback",
            value=request.score,
            comment=request.comment
        )
        return {"status": "ok", "message": "Feedback submitted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error submitting feedback: {str(e)}")
