from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from rag.db.session import get_db
from rag.rag.chat_service import ChatService
from rag.api.llm_observability import tracing, trace_var
import uuid
import hashlib

router = APIRouter(prefix="/explain", tags=["llm"])

def pseudonymize(user_id: str) -> str:
    return hashlib.sha256(user_id.encode()).hexdigest()

class ExplainRequest(BaseModel):
    email_content: str = Field(..., description="The content of the email to explain")
    user_id: str = Field(..., description="User ID for tracking and personalization")

class ExplainResponse(BaseModel):
    explanation: str = Field(..., description="Natural language explanation of the classification")
    request_id: str = Field(..., description="Unique ID for tracing")
    tokens_used: int = Field(0, description="Tokens consumed by the LLM (placeholder for now)")

@router.post("", response_model=ExplainResponse)
async def explain(
    request: ExplainRequest, 
    db: AsyncSession = Depends(get_db)
):
    user_id_hash = pseudonymize(request.user_id)
    
    # Start Langfuse trace
    trace = tracing.start_trace(
        name="explain_email",
        user_id=user_id_hash,
        metadata={"model": "mistral-large-latest"}
    )
    trace_var.set(trace)
    
    chat_service = ChatService()
    conv = await chat_service.create_conversation(db)
    
    # 1. Retrieval Span
    retrieval_span = tracing.span(trace, "retrieval", input=request.email_content[:100]) # Don't log full content
    
    # 2. Prompt Build Span
    prompt_span = tracing.span(trace, "prompt_build")
    prompt = f"Explain why this email might be considered spam, non-spam or phishing. Focus on its content and structure."
    prompt_span.end(output=prompt)
    
    # 3. LLM Call (Generation)
    generation = tracing.generation(
        trace, 
        "llm_call", 
        model="mistral-large-latest",
        input=prompt
    )
    
    try:
        result = await chat_service.send_message(conv.conversation_id, prompt + f": {request.email_content}", db)
        retrieval_span.end(output=f"Found {len(result.sources)} sources")
        generation.end(output=result.content)
    except Exception as e:
        retrieval_span.end(level="ERROR", status_message=str(e))
        generation.end(level="ERROR", status_message=str(e))
        trace.update(level="ERROR", status_message=str(e))
        raise HTTPException(status_code=500, detail=str(e))
    
    return ExplainResponse(
        explanation=result.content,
        request_id=trace.id,
        tokens_used=0 # Will be updated by Langfuse automatically if possible
    )
