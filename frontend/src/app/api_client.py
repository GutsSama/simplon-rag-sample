import json
from collections.abc import Generator

import httpx

from app.config import API_TIMEOUT_SECONDS

_META_SENTINEL = "__META__"


def _timeout() -> httpx.Timeout:
    """Generous read timeout (chat endpoint runs the LLM agent graph), short
    connect/write timeouts because those should be fast on a local network."""
    return httpx.Timeout(
        connect=10.0,
        read=API_TIMEOUT_SECONDS,
        write=30.0,
        pool=30.0,
    )


def create_conversation(base_url: str) -> str:
    """Create a new conversation and return its UUID.

    Raises:
        httpx.HTTPStatusError: if the API returns a non-2xx response.
        httpx.ConnectError: if the API is unreachable.
        httpx.ReadTimeout: if the API doesn't respond within the configured read timeout.
    """
    with httpx.Client(timeout=_timeout()) as client:
        response = client.post(f"{base_url}/conversations")
        response.raise_for_status()
        return response.json()["conversation_id"]


def stream_message(
    base_url: str, conversation_id: str, content: str
) -> tuple[Generator[str, None, None], dict]:
    """Stream tokens from the assistant response.

    Returns a (generator, metadata) pair:
      - generator yields str token chunks suitable for st.write_stream
      - metadata dict is populated after the generator is exhausted:
          {"sources": [...]}

    The generator transparently strips the backend __META__ sentinel line so
    Streamlit never renders it.
    """
    meta: dict = {"sources": []}
    url = f"{base_url}/conversations/{conversation_id}/messages/stream"

    def _gen() -> Generator[str, None, None]:
        with httpx.stream(
            "POST", url, json={"content": content}, timeout=_timeout()
        ) as response:
            response.raise_for_status()
            buffer = ""
            for chunk in response.iter_text():
                # Accumulate until we can check for the sentinel
                buffer += chunk
                if _META_SENTINEL in buffer:
                    parts = buffer.split(_META_SENTINEL, 1)
                    # Yield everything before the sentinel (strip trailing newline)
                    visible = parts[0].rstrip("\n")
                    if visible:
                        yield visible
                    # Parse metadata
                    try:
                        meta.update(json.loads(parts[1]))
                    except (json.JSONDecodeError, IndexError):
                        pass
                    buffer = ""
                else:
                    # Safe to yield everything except the last few chars
                    # (sentinel could be split across chunks)
                    safe_len = max(0, len(buffer) - len(_META_SENTINEL))
                    if safe_len:
                        yield buffer[:safe_len]
                        buffer = buffer[safe_len:]

            # Flush remaining buffer (no sentinel found)
            if buffer.strip():
                yield buffer

    return _gen(), meta


def send_message(base_url: str, conversation_id: str, content: str) -> dict:
    """Send a user message and return the assistant response (non-streaming).

    Returns:
        dict with keys: content (str), sources (list[str]).

    Raises:
        httpx.HTTPStatusError: if the API returns a non-2xx response.
        httpx.ConnectError: if the API is unreachable.
        httpx.ReadTimeout: if the API doesn't respond within the configured read timeout.
    """
    with httpx.Client(timeout=_timeout()) as client:
        response = client.post(
            f"{base_url}/conversations/{conversation_id}/messages",
            json={"content": content},
        )
        response.raise_for_status()
        data = response.json()
        return {
            "content": data.get("content", ""),
            "sources": data.get("sources", []),
        }
