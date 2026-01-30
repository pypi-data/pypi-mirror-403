"""CLI entry point for running as `python -m api.cli` or `myrag` command.

Usage:
    myrag              # REPL (search mode, default)
    myrag --rag        # REPL (RAG mode)
    myrag search "query"   # Direct search
    myrag ingest /path     # Ingest documents
    myrag rag "question"   # Direct RAG query
    myrag quality          # Quality inspection
"""

import argparse
import sys
from typing import List, Optional

from shared import __version__


def cmd_repl(args: argparse.Namespace) -> int:
    """Run interactive REPL."""
    from .repl import run_repl
    return run_repl(args)


def cmd_search(args: argparse.Namespace) -> int:
    """Run direct search query."""
    from embedding import EmbeddingProviderFactory
    from shared.config import load_config
    from ..formatters import ResponseFormatter
    from ..use_cases import SearchUseCase
    from ..validators import RequestValidator, ValidationError

    config = load_config()
    embeddings_client = EmbeddingProviderFactory.create(config)
    search_use_case = SearchUseCase(embeddings_client, config, verbose=args.verbose)

    query = args.query
    try:
        RequestValidator.validate_query(query)
        if args.view:
            RequestValidator.validate_view(args.view)
        RequestValidator.validate_top_k(args.top_k)
    except ValidationError as exc:
        print(ResponseFormatter.format_error(exc))
        return 1

    results = search_use_case.execute(
        query=query,
        view=args.view,
        language=args.language,
        top_k=args.top_k,
        expand_context=not args.no_context,
    )

    if args.json:
        output = ResponseFormatter.format_search_results_json(
            results,
            show_context=not args.no_context,
        )
    else:
        output = ResponseFormatter.format_search_results_text(
            results,
            show_context=not args.no_context,
        )
    print(output)
    return 0


def cmd_ingest(args: argparse.Namespace) -> int:
    """Ingest documents into the vector database."""
    import glob
    from shared.config import load_config
    from ..use_cases import IngestUseCase

    config = load_config()

    # Expand glob patterns
    file_paths: List[str] = []
    for pattern in args.files:
        expanded = glob.glob(pattern, recursive=True)
        if not expanded:
            print(f"[warn] No files matched pattern: {pattern}")
        file_paths.extend(expanded)

    if not file_paths:
        print("[error] No files to ingest")
        return 1

    print(f"[info] Found {len(file_paths)} file(s) to ingest")
    for fp in file_paths:
        print(f"  - {fp}")

    if args.dry_run:
        print("[dry-run] Skipping actual ingestion")
        return 0

    use_case = IngestUseCase(config, disable_cache=args.no_cache)
    result = use_case.execute(file_paths)

    print("\n[result] Ingestion complete:")
    print(f"  Documents processed: {result.documents_processed}")
    print(f"  Concepts created: {result.concepts_created}")
    print(f"  Fragments created: {result.fragments_created}")
    print(f"  Embeddings generated: {result.embeddings_generated}")
    return 0


def cmd_rag(args: argparse.Namespace) -> int:
    """Run direct RAG query."""
    from embedding import EmbeddingProviderFactory
    from shared.config import load_config, load_generation_config
    from ..use_cases import RAGUseCase
    from ..validators import RequestValidator, ValidationError
    from ..formatters import ResponseFormatter

    config = load_config()
    gen_config = load_generation_config()
    embeddings_client = EmbeddingProviderFactory.create(config)

    try:
        rag_use_case = RAGUseCase(embeddings_client, config, gen_config, verbose=args.verbose)
    except Exception as e:
        print(f"[error] Failed to initialize RAG: {e}")
        return 1

    query = args.query
    try:
        RequestValidator.validate_query(query)
        if args.view:
            RequestValidator.validate_view(args.view)
        RequestValidator.validate_top_k(args.top_k)
    except ValidationError as exc:
        print(ResponseFormatter.format_error(exc))
        return 1

    try:
        response = rag_use_case.execute(
            query=query,
            view=args.view,
            language=args.language,
            top_k=args.top_k,
            use_conversation=False,
        )
        if args.sources:
            print(response.format_with_sources())
        else:
            print(response.answer)
    except Exception as e:
        print(f"[error] RAG failed: {e}")
        return 1

    return 0


def cmd_quality(args: argparse.Namespace) -> int:
    """Run quality inspection on ingested data."""
    from shared.config import load_config
    from shared.db_pool import get_pool

    config = load_config()
    pool = get_pool(config)

    print("[quality] Running quality inspection...\n")

    with pool.connection() as conn:
        with conn.cursor() as cur:
            # Document count
            cur.execute("SELECT COUNT(*) FROM documents")
            doc_count = cur.fetchone()[0]
            print(f"Documents: {doc_count}")

            # Concept count
            cur.execute("SELECT COUNT(*) FROM concepts")
            concept_count = cur.fetchone()[0]
            print(f"Concepts: {concept_count}")

            # Fragment count
            cur.execute("SELECT COUNT(*) FROM fragments")
            fragment_count = cur.fetchone()[0]
            print(f"Fragments: {fragment_count}")

            # Embedding count (from langchain_pg_embedding)
            cur.execute("""
                SELECT COUNT(*)
                FROM langchain_pg_embedding lpe
                JOIN langchain_pg_collection lpc ON lpe.collection_id = lpc.uuid
                WHERE lpc.name = %s
            """, (config.collection_name,))
            embedding_count = cur.fetchone()[0]
            print(f"Embeddings: {embedding_count}")

            # View distribution
            print("\nView distribution:")
            cur.execute("""
                SELECT cmetadata->>'view' as view, COUNT(*) as cnt
                FROM langchain_pg_embedding lpe
                JOIN langchain_pg_collection lpc ON lpe.collection_id = lpc.uuid
                WHERE lpc.name = %s
                GROUP BY cmetadata->>'view'
                ORDER BY cnt DESC
            """, (config.collection_name,))
            for row in cur.fetchall():
                print(f"  {row[0] or 'unknown'}: {row[1]}")

            # Orphan check
            print("\nOrphan check:")
            cur.execute("""
                SELECT COUNT(*) FROM fragments f
                LEFT JOIN concepts c ON f.concept_id = c.id
                WHERE c.id IS NULL
            """)
            orphan_fragments = cur.fetchone()[0]
            print(f"  Orphan fragments: {orphan_fragments}")

            cur.execute("""
                SELECT COUNT(*) FROM concepts c
                LEFT JOIN documents d ON c.document_id = d.id
                WHERE d.id IS NULL
            """)
            orphan_concepts = cur.fetchone()[0]
            print(f"  Orphan concepts: {orphan_concepts}")

    return 0


def create_parser() -> argparse.ArgumentParser:
    """Create the main argument parser with subcommands."""
    parser = argparse.ArgumentParser(
        prog="myrag",
        description="OCR Vector DB CLI - Document parsing, embedding, and semantic search",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  myrag                        Start interactive REPL (search mode)
  myrag --rag                  Start interactive REPL (RAG mode)
  myrag search "vector db"     Search for documents
  myrag ingest docs/*.pdf      Ingest PDF files
  myrag rag "What is RAG?"     Ask a question with RAG
  myrag quality                Check data quality
        """,
    )
    parser.add_argument(
        "--version", "-V",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    # Create subcommands
    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")

    # --- search subcommand ---
    search_parser = subparsers.add_parser(
        "search",
        help="Run a search query",
        description="Search the vector database for relevant documents",
    )
    search_parser.add_argument(
        "query",
        help="Search query string",
    )
    search_parser.add_argument(
        "--view",
        choices=["text", "code", "image", "caption", "table", "figure"],
        help="Filter by view type",
    )
    search_parser.add_argument(
        "--language",
        help="Filter by language (python/javascript/etc.)",
    )
    search_parser.add_argument(
        "--top-k", "-k",
        type=int,
        default=5,
        help="Number of results (default: 5)",
    )
    search_parser.add_argument(
        "--no-context",
        action="store_true",
        help="Disable parent context expansion",
    )
    search_parser.add_argument(
        "--json",
        action="store_true",
        help="Output JSON format",
    )
    search_parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging",
    )
    search_parser.set_defaults(func=cmd_search)

    # --- ingest subcommand ---
    ingest_parser = subparsers.add_parser(
        "ingest",
        help="Ingest documents into the database",
        description="Parse and embed documents into the vector database",
    )
    ingest_parser.add_argument(
        "files",
        nargs="+",
        help="File paths or glob patterns to ingest",
    )
    ingest_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse only, no database writes",
    )
    ingest_parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable OCR cache (re-OCR all pages)",
    )
    ingest_parser.set_defaults(func=cmd_ingest)

    # --- rag subcommand ---
    rag_parser = subparsers.add_parser(
        "rag",
        help="Ask a question using RAG",
        description="Run a RAG query with LLM-generated answer",
    )
    rag_parser.add_argument(
        "query",
        help="Question to ask",
    )
    rag_parser.add_argument(
        "--view",
        choices=["text", "code", "image", "caption", "table", "figure"],
        help="Filter by view type",
    )
    rag_parser.add_argument(
        "--language",
        help="Filter by language (python/javascript/etc.)",
    )
    rag_parser.add_argument(
        "--top-k", "-k",
        type=int,
        default=5,
        help="Number of context documents (default: 5)",
    )
    rag_parser.add_argument(
        "--sources",
        action="store_true",
        help="Show source documents",
    )
    rag_parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging",
    )
    rag_parser.set_defaults(func=cmd_rag)

    # --- quality subcommand ---
    quality_parser = subparsers.add_parser(
        "quality",
        help="Inspect data quality",
        description="Run quality checks on ingested data",
    )
    quality_parser.set_defaults(func=cmd_quality)

    # --- REPL options (default when no subcommand) ---
    parser.add_argument(
        "--rag",
        action="store_true",
        help="Start REPL in RAG mode",
    )
    parser.add_argument(
        "--view",
        choices=["text", "code", "image", "caption", "table", "figure"],
        help="Default view filter",
    )
    parser.add_argument(
        "--language",
        help="Default language filter",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Default number of results (default: 5)",
    )
    parser.add_argument(
        "--no-context",
        action="store_true",
        help="Disable parent context by default",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output JSON by default",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    return parser


def main() -> int:
    """Entry point for `myrag` command."""
    parser = create_parser()
    args = parser.parse_args()

    # If a subcommand was specified, run its handler
    if args.command and hasattr(args, "func"):
        return args.func(args)

    # Default: run REPL
    return cmd_repl(args)


if __name__ == "__main__":
    sys.exit(main())
