"""CLI entry point for local PDF ingestion.

Usage:
    uv run python -m rag.cli.ingest
    uv run python -m rag.cli.ingest --docs-dir path/to/docs/

Exit codes:
    0 — always (individual errors are reported and skipped)
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
from dataclasses import dataclass, field
from pathlib import Path

from sqlalchemy import select

from rag.cli._runner import async_session
from rag.core.storage import StorageClient
from rag.db.models.document import Document
from rag.rag.ingestion.pipeline import ingest_pdf

_PROJECT_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_DOCS_DIR = _PROJECT_ROOT / "data" / "docs"


def _compute_hash(file_path: Path) -> str:
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for block in iter(lambda: f.read(65536), b""):
            sha256.update(block)
    return sha256.hexdigest()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ingest PDF files into the vector store"
    )
    parser.add_argument(
        "--docs-dir",
        type=Path,
        required=False,
        default=DEFAULT_DOCS_DIR,
        help=f"Directory containing PDF files (default: {DEFAULT_DOCS_DIR})",
    )
    return parser.parse_args()


@dataclass
class _Summary:
    ingested: int = 0
    skipped: int = 0
    errors: int = 0
    files: list[Path] = field(default_factory=list)


async def _run(docs_dir: Path) -> None:
    if not docs_dir.exists():
        print(f"Docs directory not found: {docs_dir}")
        return

    pdfs = sorted(docs_dir.glob("*.pdf"))
    if not pdfs:
        print(f"No PDF files found in {docs_dir}")
        return

    print(f"Found {len(pdfs)} PDF file(s) in {docs_dir}")
    summary = _Summary(files=pdfs)

    storage_client = StorageClient()
    tmp_dir = Path("/tmp/rag_ingest")
    tmp_dir.mkdir(parents=True, exist_ok=True)

    async with async_session() as db:
        for pdf in pdfs:
            try:
                # 1. Compute hash and check database to prevent unnecessary work
                file_hash = _compute_hash(pdf)
                result_db = await db.execute(
                    select(Document).where(Document.file_hash == file_hash)
                )
                existing = result_db.scalar_one_or_none()

                if existing is not None:
                    print(f"[SKIP]  {pdf.name} — already ingested (DB hash match)")
                    summary.skipped += 1
                    continue

                # 2. Upload to storage client (MinIO/GCS/local)
                storage_client.upload_file(pdf, pdf.name)

                # 3. Download to /tmp/rag_ingest/ to simulate cloud pipeline
                tmp_path = tmp_dir / pdf.name
                storage_client.download_file(pdf.name, tmp_path)

                try:
                    # 4. Ingest downloaded PDF
                    result = await ingest_pdf(tmp_path, db)
                    print(f"[OK]    {pdf.name} — {result.chunks_created} chunks")
                    summary.ingested += 1
                finally:
                    # 5. Clean up temp file
                    tmp_path.unlink(missing_ok=True)

            except Exception as exc:
                print(f"[ERROR] {pdf.name} — {exc}")
                summary.errors += 1

    print(
        f"\nDone. Ingested: {summary.ingested}, Skipped: {summary.skipped}, Errors: {summary.errors}"
    )


def main() -> None:
    args = _parse_args()
    asyncio.run(_run(args.docs_dir))


if __name__ == "__main__":
    main()
