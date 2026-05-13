import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from rag.db.session import get_db
from rag.rag.chat_service import ChatService, ConversationNotFoundError

router = APIRouter(prefix="/conversations", tags=["chat"])


class MessageRequest(BaseModel):
    content: str
    trace_id: str | None = None


@router.post("")
async def create_conversation(db: AsyncSession = Depends(get_db)) -> dict:
    result = await ChatService().create_conversation(db)
    return {"conversation_id": str(result.conversation_id)}


@router.post("/{conversation_id}/messages")
async def send_message(
    conversation_id: uuid.UUID,
    body: MessageRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    try:
        result = await ChatService().send_message(conversation_id, body.content, db)
    except ConversationNotFoundError:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return {
        "message_id": str(result.message_id) if result.message_id else None,
        "role": result.role,
        "content": result.content,
        "sources": result.sources,
    }


@router.post("/{conversation_id}/messages/stream")
async def stream_message(
    conversation_id: uuid.UUID,
    body: MessageRequest,
    db: AsyncSession = Depends(get_db),
):
    """Stream tokens from the generate node using LangGraph astream_events.

    Response format:
      - Plain text token chunks during generation
      - Final sentinel line: \n__META__{"sources": [...]}
    """
    import json

    from fastapi.responses import StreamingResponse
    from sqlalchemy import select

    from rag.db.models.conversation import Conversation
    from rag.rag.agent.graph import build_graph

    result = await db.execute(
        select(Conversation).where(Conversation.id == str(conversation_id))
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    graph = build_graph(db)
    initial_state = {
        "conversation_id": str(conversation_id),
        "user_message": body.content,
        "messages": [],
        "retrieved_chunks": [],
        "answer": "",
        "sources": [],
        "needs_retrieval": False,
        "in_scope": True,
        "category": "",
        "eval_score": None,
        "eval_decision": "",
        "rewrite_suggestion": "",
        "retry_count": 0,
    }

    # Configure Langfuse
    from asgi_correlation_id import correlation_id
    from langfuse.langchain import CallbackHandler

    from rag.config.settings import get_settings
    
    settings = get_settings()
    config = {}
    
    if settings.langfuse_public_key and settings.langfuse_secret_key:
        langfuse_handler = CallbackHandler(
            public_key=settings.langfuse_public_key,
        )
        config = {
            "callbacks": [langfuse_handler],
            "metadata": {
                "langfuse_user_id": str(conversation_id),
                "langfuse_tags": [settings.app_env],
                "langfuse_trace_name": "rag_chat_stream",
                "correlation_id": correlation_id.get()
            }
        }
        
    if body.trace_id:
        import uuid as _uuid
        config["run_id"] = _uuid.UUID(body.trace_id)

    async def generate():
        sources: list = []
        async for event in graph.astream_events(initial_state, config=config, version="v2"):
            kind = event["event"]
            node = event.get("metadata", {}).get("langgraph_node", "")

            # Stream tokens only from the main generation node
            if kind == "on_chat_model_stream" and node == "generate":
                chunk_content = event["data"]["chunk"].content
                if chunk_content:
                    yield chunk_content

            # Capture final state to extract sources
            elif kind == "on_chain_end" and event.get("name") == "LangGraph":
                final = event["data"].get("output", {})
                sources = final.get("sources", [])

        # Send metadata sentinel so the client can retrieve sources
        yield f"\n__META__{json.dumps({'sources': sources})}"

    return StreamingResponse(generate(), media_type="text/plain; charset=utf-8")


@router.get("/{conversation_id}/messages")
async def get_messages(
    conversation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    try:
        items = await ChatService().list_messages(conversation_id, db)
    except ConversationNotFoundError:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return [
        {
            "message_id": str(item.message_id),
            "role": item.role,
            "content": item.content,
            "sources": item.sources,
            "created_at": item.created_at.isoformat(),
        }
        for item in items
    ]
