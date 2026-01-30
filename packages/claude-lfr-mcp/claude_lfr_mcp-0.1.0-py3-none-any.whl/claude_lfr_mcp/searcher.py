import argparse
import sys

from .indexer import (
    embed_texts,
    get_qdrant_client,
    get_collection_name,
    get_current_model_config,
    EMBEDDING_MODEL,
)
from .models import list_models


def search(query: str, top_k: int = 10):
    collection_name = get_collection_name()
    client = get_qdrant_client()
    query_vec = embed_texts([query], is_query=True)[0]

    res = client.search(
        collection_name=collection_name,
        query_vector=query_vec,
        limit=top_k,
        with_payload=True,
    )
    return res


def main():
    parser = argparse.ArgumentParser(
        prog="claude-lfr-search",
        description="Search indexed code using semantic similarity.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Environment variables:
  QDRANT_URL        Qdrant server URL (default: http://localhost:6333)
  QDRANT_API_KEY    Qdrant API key (optional)
  QDRANT_COLLECTION Override auto-generated collection name (optional)
  EMBEDDING_MODEL   Embedding model to use (default: bge-base-en-v1.5)
"""
    )
    parser.add_argument(
        "query",
        nargs="*",
        default=["authentication"],
        help="Search query (default: authentication)"
    )
    parser.add_argument(
        "-k", "--top-k",
        type=int,
        default=5,
        help="Number of results to return (default: 5)"
    )
    parser.add_argument(
        "--list-models",
        action="store_true",
        help="List available embedding models and exit"
    )
    args = parser.parse_args()

    if args.list_models:
        print(list_models())
        sys.exit(0)

    config = get_current_model_config()
    collection_name = get_collection_name()
    print(f"Model: {config.short_name} | Collection: {collection_name}")

    q = " ".join(args.query)
    hits = search(q, top_k=args.top_k)
    for h in hits:
        p = h.payload
        print(f"{p['path']}:{p['start_line']}-{p['end_line']} score={h.score:.3f}")


if __name__ == "__main__":
    main()
