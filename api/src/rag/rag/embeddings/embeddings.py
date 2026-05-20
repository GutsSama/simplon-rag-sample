from functools import lru_cache

from langchain_mistralai import MistralAIEmbeddings

from rag.config.settings import get_settings


@lru_cache
def get_embeddings() -> MistralAIEmbeddings:
    settings = get_settings()
    return MistralAIEmbeddings(
        model=settings.mistral_embed_model,
        mistral_api_key=settings.mistral_api_key,
    )


import time
import structlog

logger = structlog.get_logger()

async def embed_documents(texts: list[str]) -> list[list[float]]:
    start = time.perf_counter()
    res = await get_embeddings().aembed_documents(texts)
    duration = time.perf_counter() - start
    total_chars = sum(len(t) for t in texts)
    est_tokens = total_chars // 4
    est_cost = (est_tokens / 1_000_000) * 0.1
    logger.info(
        "embeddings_generated",
        embedding_type="documents",
        count=len(texts),
        duration=duration,
        est_tokens=est_tokens,
        est_cost=est_cost,
    )
    return res


async def embed_query(text: str) -> list[float]:
    start = time.perf_counter()
    res = await get_embeddings().aembed_query(text)
    duration = time.perf_counter() - start
    est_tokens = len(text) // 4
    est_cost = (est_tokens / 1_000_000) * 0.1
    logger.info(
        "embeddings_generated",
        embedding_type="query",
        duration=duration,
        est_tokens=est_tokens,
        est_cost=est_cost,
    )
    return res
