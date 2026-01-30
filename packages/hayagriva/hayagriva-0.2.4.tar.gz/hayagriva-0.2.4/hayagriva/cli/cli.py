"""Command line interface for Hayagriva."""
from __future__ import annotations

import argparse
import sys
import os

from hayagriva.core.hayagriva import Hayagriva

from hayagriva.utils.logger import get_logger
from hayagriva.config import HayagrivaConfig

logger = get_logger(__name__)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Hayagriva RAG CLI")
    subparsers = parser.add_subparsers(dest="command")

    # Ingest command
    ingest_parser = subparsers.add_parser("ingest", help="Ingest text documents")
    ingest_parser.add_argument("paths", nargs="*", help="Paths to text files or directories")

    # Query command
    query_parser = subparsers.add_parser("query", help="Ask a question")
    query_parser.add_argument("question", help="Question to ask the index")

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)

    # Handle INGEST Command --------------------------------------
    if args.command == "ingest":
        if not args.paths:
            logger.error("No paths provided for ingestion")
            sys.exit(1)

        from hayagriva.ingestion.loaders import load_from_paths
        rag = Hayagriva()
        docs = load_from_paths(args.paths)
        rag.add_documents(docs)
        logger.info("Ingested %d documents", len(docs))
        return

    # Handle QUERY Command ---------------------------------------
    elif args.command == "query":
        rag = Hayagriva()
        answer = rag.ask(args.question)
        print(answer)
        return

    # No command given → show help
    else:
        parse_args(["-h"])