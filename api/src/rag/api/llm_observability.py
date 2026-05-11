from langfuse import Langfuse
# Removed problematic imports from langfuse.model as they are unused and cause errors in current version

import os
import uuid
import uuid
from functools import wraps
from contextvars import ContextVar
from rag.api.logging_config import request_id_var

trace_var: ContextVar[any] = ContextVar("trace", default=None)

class LangfuseTracing:
    def __init__(self):
        self.langfuse = Langfuse(
            public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
            secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
            host=os.getenv("LANGFUSE_HOST", "http://localhost:3000")
        )

    def start_trace(self, name: str, user_id: str = None, metadata: dict = None):
        request_id = request_id_var.get()
        meta = metadata or {}
        meta["request_id"] = request_id
        
        return self.langfuse.trace(
            name=name,
            user_id=user_id,
            metadata=meta
        )

    def span(self, trace, name: str, input: any = None):
        return trace.span(name=name, input=input)

    def generation(self, trace, name: str, model: str, input: any = None):
        return trace.generation(name=name, model=model, input=input)

# Global instance
tracing = LangfuseTracing()
