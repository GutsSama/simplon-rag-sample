import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from rag.config.settings import get_settings
from rag.rag.ingestion.pipeline import ingest_pdf

async def ingest_all():
    settings = get_settings()
    print(f"--- Starting Bulk Ingestion ---")
    print(f"DB: {settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}")

    engine = create_async_engine(settings.database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    docs_dir = Path(__file__).parent / "data" / "docs"
    pdfs = list(docs_dir.glob("*.pdf"))
    
    if not pdfs:
        print(f"No PDFs found in {docs_dir}")
        return

    print(f"Found {len(pdfs)} PDF documents.")

    for pdf_path in pdfs:
        print(f"\nProcessing: {pdf_path.name}")
        try:
            async with async_session() as session:
                result = await ingest_pdf(pdf_path, session)
                if result.already_existed:
                    print(f"SKIPPED: {result.filename} (already in database)")
                else:
                    print(f"SUCCESS: {result.filename} - Created {result.chunks_created} chunks")
        except Exception as e:
            print(f"ERROR: Failed to ingest {pdf_path.name}: {e}")

    await engine.dispose()
    print("\n--- Bulk Ingestion Complete ---")

if __name__ == "__main__":
    asyncio.run(ingest_all())
