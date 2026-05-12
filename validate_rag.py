import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "api" / "src"))

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from rag.config.settings import get_settings
from rag.rag.embeddings import ollama_embeddings
from rag.rag.ingestion.pipeline import ingest_pdf
from rag.rag.retriever import pgvector_retriever
from rag.rag.agent.nodes import _get_llm
from langchain_core.messages import HumanMessage

async def validate_all():
    settings = get_settings()
    print(f"--- Starting RAG Validation (Branch: feature/rag-validation) ---")
    print(f"Models: Chat={settings.ollama_chat_model}, Embed={settings.ollama_embed_model}")
    print(f"DB: {settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}")

    # 1. Connectivity
    print("\n[Step 1] Checking Ollama Connectivity...")
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{settings.ollama_base_url}/api/tags")
            resp.raise_for_status()
            tags = resp.json().get("models", [])
            tag_names = [t["name"] for t in tags]
            print(f"OK: Found models: {tag_names}")
            if settings.ollama_chat_model not in tag_names and f"{settings.ollama_chat_model}:latest" not in tag_names:
                print(f"WARNING: {settings.ollama_chat_model} not found in Ollama list")
    except Exception as e:
        print(f"ERROR: Could not connect to Ollama: {e}")
        return

    # 2. Embeddings
    print("\n[Step 2] Testing Embeddings...")
    try:
        embedding = await ollama_embeddings.aembed_query("bonjour")
        print(f"OK: Embedding dimension: {len(embedding)}")
    except Exception as e:
        print(f"ERROR: Embedding failed: {e}")

    # 3. pgvector
    print("\n[Step 3] Testing pgvector...")
    engine = create_async_engine(settings.database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    try:
        async with async_session() as session:
            await session.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            result = await session.execute(text("SELECT extname FROM pg_extension WHERE extname = 'vector'"))
            if result.scalar():
                print("OK: pgvector extension active")
            else:
                print("ERROR: pgvector extension not found")
            await session.commit()
    except Exception as e:
        print(f"ERROR: pgvector test failed: {e}")

    # 4. Ingestion
    print("\n[Step 4] Testing PDF Ingestion...")
    docs_dir = Path(__file__).parent / "data" / "docs"
    pdfs = list(docs_dir.glob("*.pdf"))
    if not pdfs:
        print("SKIP: No PDFs found in data/docs")
    else:
        test_pdf = pdfs[0]
        print(f"Ingesting {test_pdf.name}...")
        try:
            async with async_session() as session:
                result = await ingest_pdf(test_pdf, session)
                print(f"OK: Ingested {result.filename}, created {result.chunks_created} chunks (already existed: {result.already_existed})")
        except Exception as e:
            print(f"ERROR: Ingestion failed: {e}")

    # 5. Retrieval
    print("\n[Step 5] Testing Retrieval...")
    try:
        async with async_session() as session:
            chunks = await pgvector_retriever.similarity_search("Simplon", session, k=2)
            print(f"OK: Retrieved {len(chunks)} chunks")
            for i, c in enumerate(chunks):
                print(f"  Chunk {i}: {c['filename']} - {c['content'][:50]}...")
    except Exception as e:
        print(f"ERROR: Retrieval failed: {e}")

    # 6. Generation
    print("\n[Step 6] Testing Generation...")
    try:
        llm = _get_llm()
        resp = await llm.ainvoke([HumanMessage(content="Bonjour, qui es-tu ?")])
        print(f"OK: LLM response: {resp.content[:100]}...")
    except Exception as e:
        print(f"ERROR: Generation failed: {e}")

    await engine.dispose()
    print("\n--- Validation Complete ---")

if __name__ == "__main__":
    # Ensure env vars are loaded for local run if not in docker
    if os.path.exists(".env"):
        from dotenv import load_dotenv
        load_dotenv()
    
    asyncio.run(validate_all())
