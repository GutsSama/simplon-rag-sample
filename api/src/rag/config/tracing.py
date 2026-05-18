import contextvars
import uuid
from langfuse import Langfuse
from rag.config.settings import get_settings

request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "request_id", default=""
)

_client = None

def get_langfuse_client():
    global _client
    if _client is None:
        settings = get_settings()
        _client = Langfuse(
            secret_key=settings.langfuse_secret_key,
            public_key=settings.langfuse_public_key,
            host=settings.langfuse_host,
        )
    return _client

def get_langfuse_handler(conversation_id: str, user_message: str):
    """Crée une trace Langfuse pour une requête."""
    request_id = uuid.uuid4().hex
    request_id_var.set(request_id)

    client = get_langfuse_client()
    trace = client.trace(
        id=request_id,
        name="rag_pipeline",
        metadata={
            "conversation_id": conversation_id,
        },
        tags=["rag", "langgraph"],
    )

    return trace, request_id
