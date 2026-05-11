from langfuse import Langfuse
# Removed problematic imports from langfuse.model as they are unused and cause errors in current version

import os
import uuid
import uuid
from functools import wraps
from contextvars import ContextVar
from rag.api.logging_config import request_id_var

trace_var: ContextVar[any] = ContextVar("trace", default=None)

import hashlib

class LangfuseTracing:
    def __init__(self):
        self.langfuse = Langfuse(
            public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
            secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
            host=os.getenv("LANGFUSE_HOST", "http://localhost:3000")
        )

    def hash_user_id(self, user_id: str) -> str:
        """Pseudonymize user_id for RGPD compliance."""
        if not user_id:
            return "anonymous"
        return hashlib.sha256(user_id.encode()).hexdigest()

    def start_trace(self, name: str, user_id: str = None, metadata: dict = None):
        request_id = request_id_var.get()
        meta = metadata or {}
        meta["request_id"] = request_id
        
        # Always hash user_id if provided
        hashed_user_id = self.hash_user_id(user_id)
        
        return self.langfuse.trace(
            name=name,
            user_id=hashed_user_id,
            metadata=meta
        )

    def span(self, trace, name: str, input: any = None):
        return trace.span(name=name, input=input)

    def generation(self, trace, name: str, model: str, input: any = None):
        return trace.generation(name=name, model=model, input=input)

    def score(self, trace_id: str, name: str, value: float, comment: str = None):
        """Send a score to Langfuse for a specific trace."""
        self.langfuse.score(
            trace_id=trace_id,
            name=name,
            value=value,
            comment=comment
        )

# Global instance
tracing = LangfuseTracing()
