import argparse
import os
import sys
import time
from pathlib import Path
from typing import List, Optional

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

from .models import (
    DEFAULT_MODEL,
    MODEL_REGISTRY,
    get_model_config,
    get_collection_name_for_model,
    list_models,
)
from .ignore import IgnoreHandler, get_ignore_handler

# -------- Config --------
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")  # or None
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", DEFAULT_MODEL)
MAX_FILES = int(os.getenv("MAX_FILES", "0"))  # 0 = no limit

CODE_EXTS = {
    ".py", ".ts", ".tsx", ".js", ".jsx",
    ".rs", ".go", ".java", ".cs",
    ".php", ".c", ".cpp", ".h", ".hpp",
}

# -------- Lazy model loading --------
_tokenizer = None
_model = None
_current_model_name = None


def get_current_model_config():
    """Get the configuration for the current embedding model."""
    return get_model_config(EMBEDDING_MODEL)


def get_collection_name():
    """Get the collection name for the current model."""
    override = os.getenv("QDRANT_COLLECTION")
    return get_collection_name_for_model(EMBEDDING_MODEL, override)


# For backwards compatibility
COLLECTION_NAME = get_collection_name()


def _load_model(model_name: str = None):
    global _tokenizer, _model, _current_model_name

    if model_name is None:
        model_name = EMBEDDING_MODEL

    # Reload if model changed
    if _tokenizer is not None and _current_model_name == model_name:
        return

    # Lazy import heavy dependencies
    from transformers import AutoTokenizer, AutoModel

    config = get_model_config(model_name)
    print(f"Loading tokenizer and model: {config.name}...")

    load_kwargs = {}
    if config.trust_remote_code:
        load_kwargs["trust_remote_code"] = True

    _tokenizer = AutoTokenizer.from_pretrained(config.name, **load_kwargs)
    _model = AutoModel.from_pretrained(config.name, **load_kwargs)
    _model.train(False)  # Set to evaluation mode
    _current_model_name = model_name


def embed_texts(texts: List[str], is_query: bool = False):
    import torch

    _load_model()

    config = get_current_model_config()

    # Apply model-specific prefixes
    if is_query and config.query_prefix:
        texts = [f"{config.query_prefix}{t}" for t in texts]
    elif not is_query and config.doc_prefix:
        texts = [f"{config.doc_prefix}{t}" for t in texts]

    with torch.no_grad():
        encoded = _tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors="pt",
        )
        outputs = _model(**encoded)

        # Prefer pooler_output if available, otherwise mean pool.
        if hasattr(outputs, "pooler_output") and outputs.pooler_output is not None:
            embeddings = outputs.pooler_output
        else:
            last_hidden = outputs.last_hidden_state
            attention_mask = encoded["attention_mask"].unsqueeze(-1)
            embeddings = (last_hidden * attention_mask).sum(dim=1) / attention_mask.sum(dim=1)

        embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)
        return embeddings.cpu().tolist()


def get_qdrant_client(timeout: float = 30.0, retries: int = 3) -> QdrantClient:
    """Get Qdrant client with retry logic.

    Args:
        timeout: Connection timeout in seconds.
        retries: Number of connection attempts.

    Returns:
        Connected QdrantClient instance.

    Raises:
        ConnectionError: If connection fails after all retries.
    """
    last_error = None
    for attempt in range(retries):
        try:
            client = QdrantClient(
                url=QDRANT_URL,
                api_key=QDRANT_API_KEY,
                timeout=timeout,
            )
            # Validate connection
            client.get_collections()
            return client
        except Exception as e:
            last_error = e
            if attempt < retries - 1:
                wait = 2 ** attempt  # 1s, 2s, 4s
                print(f"Qdrant connection failed, retrying in {wait}s: {e}")
                time.sleep(wait)
    raise ConnectionError(f"Failed to connect to Qdrant after {retries} attempts: {last_error}")


def ensure_collection(client: QdrantClient, dim: int = None):
    collection_name = get_collection_name()

    if dim is None:
        dim = get_current_model_config().dimension

    collections = client.get_collections().collections
    existing = next((c for c in collections if c.name == collection_name), None)

    if existing is None:
        client.recreate_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
        )
        print(f"Created collection {collection_name} with dim={dim}")
    else:
        # Validate dimension matches
        info = client.get_collection(collection_name)
        existing_dim = info.config.params.vectors.size
        if existing_dim != dim:
            raise ValueError(
                f"Collection '{collection_name}' exists with dimension {existing_dim}, "
                f"but model '{EMBEDDING_MODEL}' requires dimension {dim}.\n"
                f"Options:\n"
                f"  1. Delete collection: qdrant-client delete collection {collection_name}\n"
                f"  2. Use QDRANT_COLLECTION env var to specify a different collection name"
            )
        print(f"Using existing collection {collection_name} (dim={existing_dim})")


# -------- Code file iteration & chunking --------
def iter_code_files(
    root: Path,
    max_files: int = 0,
    ignore_handler: Optional[IgnoreHandler] = None,
):
    """Iterate over code files in a directory.

    Args:
        root: Root directory to search.
        max_files: Maximum number of files to return (0 = no limit).
        ignore_handler: IgnoreHandler instance for filtering files.
                        If None, a default handler will be created.

    Yields:
        Paths to code files.
    """
    if ignore_handler is None:
        ignore_handler = get_ignore_handler(root)

    yield from ignore_handler.iter_files(extensions=CODE_EXTS, max_files=max_files)


def chunk_file(path: Path, repo_root: Path, max_lines: int = 80):
    rel = path.relative_to(repo_root).as_posix()
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
    except OSError:
        return []

    chunks = []
    for i in range(0, len(lines), max_lines):
        chunk_lines = lines[i:i + max_lines]
        start = i + 1
        end = min(i + max_lines, len(lines))
        text = "".join(chunk_lines)
        if text.strip():
            chunks.append((rel, start, end, text))
    return chunks


# -------- Indexing --------
def index_repo(
    repo_root: Path,
    max_files: int = 0,
    ignore_handler: Optional[IgnoreHandler] = None,
):
    """Index a repository for semantic code search.

    Args:
        repo_root: Root directory of the repository.
        max_files: Maximum number of files to index (0 = no limit).
        ignore_handler: IgnoreHandler instance for filtering files.
                        If None, a default handler will be created.
    """
    collection_name = get_collection_name()
    client = get_qdrant_client()
    ensure_collection(client)
    points = []
    point_id = 0
    file_count = 0

    for path in iter_code_files(repo_root, max_files, ignore_handler):
        file_count += 1
        chunks = chunk_file(path, repo_root)
        if not chunks:
            continue

        texts = [c[3] for c in chunks]
        embeddings = embed_texts(texts, is_query=False)

        for emb, (rel, start, end, text) in zip(embeddings, chunks):
            points.append(
                PointStruct(
                    id=point_id,
                    vector=emb,
                    payload={
                        "path": rel,
                        "start_line": start,
                        "end_line": end,
                        "snippet": text,
                    },
                )
            )
            point_id += 1

        if len(points) >= 256:
            client.upsert(collection_name=collection_name, points=points)
            print(f"Indexed {file_count} files, upserted {len(points)} chunks so far...")
            points = []

    if points:
        client.upsert(collection_name=collection_name, points=points)
        print(f"Final upsert of {len(points)} chunks.")

    print(f"Indexing complete. Files processed: {file_count}")


def main():
    global EMBEDDING_MODEL

    parser = argparse.ArgumentParser(
        prog="claude-lfr-index",
        description="Index source code files for semantic search using configurable embedding models and Qdrant.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Environment variables:
  QDRANT_URL        Qdrant server URL (default: http://localhost:6333)
  QDRANT_API_KEY    Qdrant API key (optional)
  QDRANT_COLLECTION Override auto-generated collection name (optional)
  EMBEDDING_MODEL   Embedding model to use (default: bge-base-en-v1.5)
  IGNORE_PATTERNS   Additional ignore patterns (comma/newline separated)
  USE_GITIGNORE     Enable .gitignore parsing (default: true)
"""
    )
    parser.add_argument(
        "-r", "--repo-root",
        default=os.getenv("REPO_ROOT", "."),
        help="Root directory to index (default: REPO_ROOT env or .)"
    )
    parser.add_argument(
        "-m", "--max-files",
        type=int,
        default=int(os.getenv("MAX_FILES", "0")),
        help="Max files to index, 0=unlimited (default: MAX_FILES env or 0)"
    )
    parser.add_argument(
        "--model",
        default=os.getenv("EMBEDDING_MODEL", DEFAULT_MODEL),
        help=f"Embedding model to use (default: {DEFAULT_MODEL})"
    )
    parser.add_argument(
        "--list-models",
        action="store_true",
        help="List available embedding models and exit"
    )
    parser.add_argument(
        "--no-gitignore",
        action="store_true",
        help="Disable .gitignore parsing (only use default ignore dirs)"
    )
    parser.add_argument(
        "--ignore",
        action="append",
        default=[],
        metavar="PATTERN",
        help="Additional ignore pattern (gitignore syntax, can be repeated)"
    )
    args = parser.parse_args()

    if args.list_models:
        print(list_models())
        sys.exit(0)

    # Validate and set the model
    try:
        get_model_config(args.model)
        EMBEDDING_MODEL = args.model
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    config = get_current_model_config()
    print(f"Using embedding model: {config.short_name} (dim={config.dimension})")
    print(f"Collection: {get_collection_name()}")

    repo_root = Path(args.repo_root).resolve()
    print(f"Repo root: {repo_root}")

    # Create ignore handler
    use_gitignore = not args.no_gitignore
    ignore_handler = get_ignore_handler(
        root=repo_root,
        use_gitignore=use_gitignore,
        extra_patterns=args.ignore if args.ignore else None,
    )
    print(f"Gitignore parsing: {'enabled' if use_gitignore else 'disabled'}")
    if args.ignore:
        print(f"Extra ignore patterns: {args.ignore}")

    index_repo(repo_root, args.max_files, ignore_handler)


if __name__ == "__main__":
    main()
