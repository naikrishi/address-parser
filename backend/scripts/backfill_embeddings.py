"""Backfill embeddings for all existing parse_result rows.

Usage:
    cd backend
    python -m scripts.backfill_embeddings [--dry-run] [--force] [--batch-size N] [--limit N]
"""

from __future__ import annotations

import argparse
import logging
import sys

from sqlalchemy import select

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.llm.embeddings import embed_text
from app.models.parse_result import ParseResult
from app.models.raw_input import RawInput

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def run(dry_run: bool, force: bool, batch_size: int, limit: int | None) -> None:
    settings = get_settings()
    logger.info(
        "Starting embedding backfill | provider=%s model=%s dim=%d dry_run=%s force=%s",
        settings.embeddings_provider,
        settings.embeddings_model,
        settings.embeddings_dimension,
        dry_run,
        force,
    )

    attempted = skipped = succeeded = failed = 0

    with SessionLocal() as db:
        query = (
            select(ParseResult, RawInput.raw_address)
            .join(RawInput, ParseResult.raw_input_id == RawInput.id)
        )
        if not force:
            query = query.where(ParseResult.embedding.is_(None))
        if limit:
            query = query.limit(limit)

        rows = db.execute(query).all()
        total = len(rows)
        logger.info("Found %d rows to process", total)

        for i, (parse_result, raw_address) in enumerate(rows, start=1):
            attempted += 1
            try:
                vector = embed_text(raw_address, parse_result.parsed_components)
                if not dry_run:
                    parse_result.embedding = vector
                    if i % batch_size == 0 or i == total:
                        db.commit()
                succeeded += 1
                if i % 50 == 0 or i == total:
                    logger.info("Progress: %d/%d (succeeded=%d failed=%d)", i, total, succeeded, failed)
            except Exception as exc:
                failed += 1
                logger.error("Failed row %s: %s", parse_result.id, exc)

        if dry_run:
            db.rollback()

    logger.info(
        "Backfill complete | attempted=%d succeeded=%d skipped=%d failed=%d dry_run=%s",
        attempted,
        succeeded,
        skipped,
        failed,
        dry_run,
    )
    if failed:
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill parse_result embeddings")
    parser.add_argument("--dry-run", action="store_true", help="Show what would happen without writing")
    parser.add_argument("--force", action="store_true", help="Re-embed rows that already have embeddings")
    parser.add_argument("--batch-size", type=int, default=100, metavar="N")
    parser.add_argument("--limit", type=int, default=None, metavar="N")
    args = parser.parse_args()
    run(dry_run=args.dry_run, force=args.force, batch_size=args.batch_size, limit=args.limit)


if __name__ == "__main__":
    main()
