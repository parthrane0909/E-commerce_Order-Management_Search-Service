"""Rebuild the Elasticsearch `orders` index from PostgreSQL.

    python -m scripts.reindex_orders                # top-up / refresh
    python -m scripts.reindex_orders --recreate     # drop + rebuild

PostgreSQL is the source of truth: this script reads every order (with
its customer and snapshot line items) and (re)indexes the corresponding
Elasticsearch document.  It never reads MongoDB.
"""

from __future__ import annotations

import argparse
import sys

from app.core.database import SessionLocal
from app.core.logging import configure_logging, get_logger
from app.repositories.elasticsearch.document import build_order_document
from app.repositories.elasticsearch.orders_repo import (
    bulk_index_orders,
    count_documents,
    ensure_index,
)
from app.repositories.postgres import order_repo

logger = get_logger(__name__)


def reindex_orders(*, recreate: bool = False) -> dict[str, int]:
    """Rebuild every order document and return a small statistics dict."""
    ensure_index(recreate=recreate)

    session = SessionLocal()
    try:
        order_count = order_repo.count_orders(session)
        documents = [build_order_document(order) for order in order_repo.iter_orders(session)]
    finally:
        session.close()

    indexed, failed = bulk_index_orders(documents)
    searchable = count_documents()

    stats = {
        "postgres_orders": order_count,
        "documents_built": len(documents),
        "indexed": indexed,
        "failed": failed,
        "elasticsearch_documents": searchable,
    }
    logger.info("reindex complete: %s", stats)
    return stats


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--recreate",
        action="store_true",
        help="Drop and recreate the index (also refreshes the mapping).",
    )
    args = parser.parse_args(argv)

    configure_logging("INFO")
    stats = reindex_orders(recreate=args.recreate)

    print("\n=== Elasticsearch reindex ====================================")
    for key, value in stats.items():
        print(f"  {key:<26} {value}")
    print("===============================================================")

    if stats["failed"]:
        print(f"ERROR: {stats['failed']} document(s) failed to index.", file=sys.stderr)
        return 1
    if stats["postgres_orders"] != stats["elasticsearch_documents"]:
        print(
            "ERROR: PostgreSQL order count "
            f"({stats['postgres_orders']}) != Elasticsearch document count "
            f"({stats['elasticsearch_documents']}).",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
