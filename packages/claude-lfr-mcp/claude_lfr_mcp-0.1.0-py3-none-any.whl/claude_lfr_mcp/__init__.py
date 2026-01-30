"""Code indexer using configurable embedding models + Qdrant."""

from .indexer import (
    embed_texts,
    index_repo,
    get_qdrant_client,
    get_collection_name,
    get_current_model_config,
    EMBEDDING_MODEL,
)
from .searcher import search
from .models import MODEL_REGISTRY, ModelConfig, DEFAULT_MODEL, list_models

__all__ = [
    "embed_texts",
    "index_repo",
    "get_qdrant_client",
    "get_collection_name",
    "get_current_model_config",
    "search",
    "EMBEDDING_MODEL",
    "MODEL_REGISTRY",
    "ModelConfig",
    "DEFAULT_MODEL",
    "list_models",
]


def __getattr__(name):
    """Lazy import for MCP server to avoid loading heavy dependencies."""
    if name == "mcp_server":
        from . import mcp_server
        return mcp_server
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
