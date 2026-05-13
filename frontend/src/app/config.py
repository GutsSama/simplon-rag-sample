import os

API_BASE_URL: str = os.getenv("API_BASE_URL", "http://localhost:8000")

# Read timeout for API calls in seconds. Generous default because the chat
# endpoint runs the full agent graph (guard → retrieve → generate → evaluate),
# which can take tens of seconds with a local LLM. Override via env when
# pointing at a faster backend.
API_TIMEOUT_SECONDS: float = float(os.getenv("RAG_API_TIMEOUT_SECONDS", "300"))
