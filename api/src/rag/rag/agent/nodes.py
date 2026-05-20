import json
import re
import time

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_mistralai import ChatMistralAI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from rag.rag.agent.prompts import (
    ESCALATION_RESPONSE,
    EVALUATOR_PROMPT,
    GUARD_ROUTE_PROMPT,
    OUT_OF_SCOPE_RESPONSE,
    RAG_SYSTEM_PROMPT,
    RAG_USER_PROMPT,
    SYSTEM_PROMPT,
)
from rag.rag.agent.state import AgentState
from rag.config.settings import get_settings
from rag.db.models.conversation import Conversation, Message
from rag.rag.retriever import pgvector_retriever
from rag.monitoring.metrics import (
    RAG_GUARD_ROUTE_TOTAL,
    RAG_ESCALATION_TOTAL,
    RAG_NODE_DURATION_SECONDS,
    RAG_EVAL_SCORE,
)
import structlog

logger = structlog.get_logger()


def _extract_json(content: str) -> str:
    """Strip markdown code fences and extract the first JSON object from LLM output."""
    content = content.strip()
    match = re.search(r"\{.*\}", content, re.DOTALL)
    return match.group(0) if match else content


def _get_llm(settings=None, model: str | None = None, num_predict: int = 512, json_mode: bool = False) -> ChatMistralAI:
    s = settings or get_settings()
    kwargs = {
        "model": model or s.mistral_chat_model,
        "mistral_api_key": s.mistral_api_key,
        "max_tokens": num_predict,
        "temperature": 0,
    }
    if json_mode:
        kwargs["model_kwargs"] = {"response_format": {"type": "json_object"}}
    
    return ChatMistralAI(**kwargs)


async def load_history(state: AgentState, db: AsyncSession) -> dict:
    """Load previous messages for this conversation from the DB."""
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == state["conversation_id"])
        .order_by(Message.created_at, Message.id)
    )
    db_messages = result.scalars().all()

    settings = get_settings()
    lc_messages: list = [
        SystemMessage(content=SYSTEM_PROMPT.format(product_name=settings.product_name))
    ]

    for msg in db_messages:
        if msg.role == "user":
            lc_messages.append(HumanMessage(content=msg.content))
        else:
            lc_messages.append(AIMessage(content=msg.content))

    lc_messages.append(HumanMessage(content=state["user_message"]))
    return {"messages": lc_messages}


async def guard_route(state: AgentState) -> dict:
    """Single LLM call that decides scope and retrieval routing simultaneously.

    Returns:
        - in_scope=False + answer: short-circuits to save_turn (out-of-scope rejection)
        - in_scope=True + needs_retrieval=True: pipeline continues to retrieve
        - in_scope=True + needs_retrieval=False: pipeline continues to generate

    Fails open (in_scope=True, needs_retrieval=True) on any JSON parsing error
    to avoid false negatives.
    """
    start = time.perf_counter()
    settings = get_settings()
    llm = _get_llm(settings, model=settings.mistral_small_chat_model, num_predict=64, json_mode=True)
    # Explicitly disable thinking in the prompt
    instruction = "\nIMPORTANT: Do not think out loud. Do not use <thought> tags. Provide ONLY the JSON output."
    prompt = GUARD_ROUTE_PROMPT.format(
        product_name=settings.product_name,
        user_message=state["user_message"],
    ) + instruction
    response = await llm.ainvoke([HumanMessage(content=prompt)])
    duration = time.perf_counter() - start

    try:
        data = json.loads(_extract_json(response.content))
        in_scope = bool(data.get("in_scope", True))
        needs_retrieval = bool(data.get("needs_retrieval", True))
        category = str(data.get("category", ""))
    except (json.JSONDecodeError, ValueError):
        in_scope = True
        needs_retrieval = True
        category = ""

    RAG_NODE_DURATION_SECONDS.labels(node_name="guard_route").observe(duration)
    RAG_GUARD_ROUTE_TOTAL.labels(
        category=category,
        in_scope=str(in_scope),
        needs_retrieval=str(needs_retrieval)
    ).inc()

    if not in_scope:
        return {
            "in_scope": False,
            "needs_retrieval": False,
            "category": "out_of_scope",
            "answer": OUT_OF_SCOPE_RESPONSE.format(product_name=settings.product_name),
            "sources": [],
            "guard_route_duration": duration,
        }

    logger.info("guard_route_completed", category=category, in_scope=in_scope, duration=duration)

    return {
        "in_scope": True,
        "needs_retrieval": needs_retrieval,
        "category": category,
        "guard_route_duration": duration,
    }


async def retrieve(state: AgentState, db: AsyncSession) -> dict:
    """Retrieve relevant chunks from pgvector.

    Uses rewrite_suggestion as the search query when available (rewrite path),
    otherwise falls back to the original user_message.
    """
    start = time.perf_counter()
    query = state.get("rewrite_suggestion") or state["user_message"]
    chunks = await pgvector_retriever.similarity_search(query, db)
    duration = time.perf_counter() - start
    RAG_NODE_DURATION_SECONDS.labels(node_name="retrieve").observe(duration)
    logger.info("retrieval_completed", duration=duration, chunk_count=len(chunks))
    return {"retrieved_chunks": chunks, "retrieve_duration": duration}


async def generate(state: AgentState) -> dict:
    """Generate an answer using the local Ollama chat model, with optional retrieved context.

    The previous turns of the conversation are reused as structured messages
    (HumanMessage / AIMessage) rather than flattened into the system prompt,
    so the LLM keeps a clear turn-by-turn structure and prompt caching stays
    effective.

    The generated AIMessage is intentionally NOT appended to ``state["messages"]``:
    on a rewrite loop, a failed first answer would otherwise pollute the history
    fed to the second generation pass.
    """
    llm = _get_llm(num_predict=512)

    history_msgs = state["messages"][1:-1]

    if state.get("retrieved_chunks"):
        context = "\n\n---\n\n".join(
            f"[{c['filename']} chunk {c['chunk_index']}]\n{c['content']}"
            for c in state["retrieved_chunks"]
        )
        system_content = RAG_SYSTEM_PROMPT.format(
            product_name=get_settings().product_name,
            context=context,
        )
        user_content = RAG_USER_PROMPT.format(
            question=state["user_message"],
            category=state.get("category", ""),
        )
        messages_to_send = [
            SystemMessage(content=system_content),
            *history_msgs,
            HumanMessage(content=user_content),
        ]
        sources = [c["chunk_id"] for c in state["retrieved_chunks"]]
    else:
        messages_to_send = state["messages"]
        sources = []

    start = time.perf_counter()
    response = await llm.ainvoke(messages_to_send)
    duration = time.perf_counter() - start
    RAG_NODE_DURATION_SECONDS.labels(node_name="generate").observe(duration)
    logger.info("generation_completed", duration=duration, source_count=len(sources))
    return {
        "answer": response.content,
        "sources": sources,
        "generate_duration": duration,
    }


async def evaluate(state: AgentState) -> dict:
    """Evaluate the quality of the generated answer and decide routing.

    Scores 0-10 across relevance, completeness, grounding, and clarity.
    - score >= 7 → "answer": send to user
    - score 4-6  → "rewrite": retry retrieval with a reformulated query
    - score < 4  → "escalate": hand off to human support

    Increments retry_count each call. If retry_count reaches 2, forces escalation
    regardless of score to prevent infinite loops.
    Fails open ("answer") on any JSON parsing error.
    """
    settings = get_settings()
    llm = _get_llm(settings, model=settings.mistral_small_chat_model, num_predict=64, json_mode=True)

    context_summary = "\n".join(
        f"- [{c['filename']}]: {c['content'][:100]}..."
        for c in (state.get("retrieved_chunks") or [])
    ) or "Aucun contexte récupéré."

    prompt = EVALUATOR_PROMPT.format(
        question=state["user_message"],
        context_summary=context_summary,
        answer=state.get("answer", ""),
    )
    start = time.perf_counter()
    response = await llm.ainvoke([HumanMessage(content=prompt)])
    duration = time.perf_counter() - start

    try:
        data = json.loads(_extract_json(response.content))
        score = float(data.get("score", 10))
        decision = str(data.get("decision", "answer"))
        rewrite_suggestion = str(data.get("rewrite_suggestion", ""))
    except (json.JSONDecodeError, ValueError):
        score = 10.0
        decision = "answer"
        rewrite_suggestion = ""

    retry_count = state.get("retry_count", 0) + 1

    RAG_NODE_DURATION_SECONDS.labels(node_name="evaluate").observe(duration)
    RAG_EVAL_SCORE.observe(score)
    logger.info("evaluation_completed", score=score, decision=decision, duration=duration)

    return {
        "eval_score": score,
        "eval_decision": decision,
        "rewrite_suggestion": rewrite_suggestion,
        "retry_count": retry_count,
        "evaluate_duration": duration,
    }


async def escalate(state: AgentState) -> dict:
    """Set a human-escalation answer when the evaluator cannot find a satisfactory response."""
    settings = get_settings()
    RAG_ESCALATION_TOTAL.inc()
    logger.warning("request_escalated", question=state["user_message"])
    return {
        "answer": ESCALATION_RESPONSE.format(
            product_name=settings.product_name,
            question=state["user_message"],
        ),
        "sources": [],
    }


async def save_turn(state: AgentState, db: AsyncSession) -> dict:
    """Persist user message and assistant answer to the DB."""
    user_msg = Message(
        conversation_id=state["conversation_id"],
        role="user",
        content=state["user_message"],
    )
    assistant_msg = Message(
        conversation_id=state["conversation_id"],
        role="assistant",
        content=state["answer"],
        sources=state.get("sources"),
    )
    db.add_all([user_msg, assistant_msg])

    # Update conversation.updated_at
    result = await db.execute(
        select(Conversation).where(Conversation.id == state["conversation_id"])
    )
    conversation = result.scalar_one_or_none()
    if conversation:
        from sqlalchemy import func
        conversation.metadata_ = {**conversation.metadata_, "last_updated": str(func.now())}

    await db.commit()
    return {}
