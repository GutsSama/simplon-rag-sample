#!/usr/bin/env python3
import asyncio
import os
import sys
from pathlib import Path
from sqlalchemy import select

# Add api/src to python path
sys.path.append(str(Path(__file__).resolve().parents[1] / "api" / "src"))

from rag.config.settings import get_settings
from rag.core.storage import StorageClient
from rag.db.session import async_session_factory
from rag.db.models.document import Document
from rag.db.models.conversation import Conversation
from rag.rag.ingestion.pipeline import ingest_pdf, _compute_hash
from rag.rag.chat_service import ChatService
from rag.evaluation.ragas_pipeline import run_evaluation, EvaluationSample


async def main():
    print("=== Starting RAG migration validation ===")
    settings = get_settings()
    print(f"Environment: {settings.app_env}")
    print(f"Storage Provider: {settings.storage_provider}")
    print(f"Mistral Chat Model: {settings.mistral_chat_model}")
    print(f"Mistral Embed Model: {settings.mistral_embed_model}")

    # Ensure we have a PDF to ingest
    docs_dir = Path(__file__).resolve().parents[1] / "data" / "docs"
    pdfs = list(docs_dir.glob("*.pdf"))
    if not pdfs:
        print("ERROR: No PDF files found in data/docs to validate ingestion.")
        sys.exit(1)

    test_pdf = pdfs[0]
    print(f"Using test PDF: {test_pdf.name}")

    # Compute hash
    file_hash = _compute_hash(test_pdf)
    print(f"PDF SHA-256 hash: {file_hash}")

    async with async_session_factory() as db:
        # Clean up any existing document in the db with the same hash/name
        # to ensure we test a full new ingestion path
        result = await db.execute(select(Document).where(Document.file_hash == file_hash))
        existing = result.scalar_one_or_none()
        if existing:
            print(f"Found existing document ID {existing.id} in DB, deleting it...")
            await db.delete(existing)
            await db.commit()

        # Step 1: Upload to storage provider
        print("Uploading test PDF to storage client...")
        storage_client = StorageClient()
        storage_client.upload_file(test_pdf, test_pdf.name)
        print("Upload successful!")

        # Step 2: Download to /tmp/rag_ingest
        tmp_dir = Path("/tmp/rag_ingest")
        tmp_dir.mkdir(parents=True, exist_ok=True)
        tmp_path = tmp_dir / test_pdf.name

        print("Downloading PDF from storage to /tmp/rag_ingest...")
        storage_client.download_file(test_pdf.name, tmp_path)
        print(f"Downloaded successfully to {tmp_path}")

        try:
            # Step 3: Ingestion
            print("Ingesting PDF into vector store...")
            result = await ingest_pdf(tmp_path, db)
            print(f"Ingestion successful! Created {result.chunks_created} chunks.")
            if result.chunks_created == 0:
                raise ValueError("Ingestion created 0 chunks")
        finally:
            # Clean up local temp file
            tmp_path.unlink(missing_ok=True)

        # Step 4: Ask RAG agent a query
        print("Creating test conversation...")
        conv = Conversation()
        db.add(conv)
        await db.commit()
        await db.refresh(conv)

        print("Sending message to RAG agent...")
        chat_service = ChatService()
        response = await chat_service.send_message(
            conv.id,
            "Qu'est-ce que le Règlement spécifique IA Simplon ?",
            db
        )
        print(f"Agent response: {response.content}")
        if not response.content:
            raise ValueError("Agent returned empty response")

        # Step 5: Run Ragas Evaluation
        print("Running Ragas evaluation validation...")
        samples = [
            EvaluationSample(
                question="Qu'est-ce que le Règlement spécifique IA Simplon ?",
                ground_truth="Le règlement définit les conditions spécifiques pour la formation IA chez Simplon."
            )
        ]
        eval_result = await run_evaluation(samples, db)
        print(f"Ragas evaluation result: {eval_result.raw}")

    print("=== Validation completed successfully! ===")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        import traceback
        traceback.print_exc()
        sys.exit(1)
