"""Model registry for embedding models."""

from dataclasses import dataclass


@dataclass
class ModelConfig:
    """Configuration for an embedding model."""
    name: str  # HuggingFace model name
    dimension: int  # Embedding dimension
    query_prefix: str  # Prefix for queries (empty if none)
    doc_prefix: str  # Prefix for documents (empty if none)
    short_name: str  # Short name for CLI/env var
    description: str  # Human-readable description
    trust_remote_code: bool = False  # Whether to trust remote code


# Registry of supported embedding models
MODEL_REGISTRY: dict[str, ModelConfig] = {
    "all-MiniLM-L6-v2": ModelConfig(
        name="sentence-transformers/all-MiniLM-L6-v2",
        dimension=384,
        query_prefix="",
        doc_prefix="",
        short_name="all-MiniLM-L6-v2",
        description="Fastest, ~90MB, good general-purpose model",
    ),
    "bge-small-en-v1.5": ModelConfig(
        name="BAAI/bge-small-en-v1.5",
        dimension=384,
        query_prefix="query: ",
        doc_prefix="",
        short_name="bge-small-en-v1.5",
        description="Good balance, ~67MB, uses query prefix",
    ),
    "snowflake-arctic-embed-xs": ModelConfig(
        name="Snowflake/snowflake-arctic-embed-xs",
        dimension=384,
        query_prefix="",
        doc_prefix="",
        short_name="snowflake-arctic-embed-xs",
        description="Good quality, ~90MB, no prefix needed",
    ),
    "snowflake-arctic-embed-s": ModelConfig(
        name="Snowflake/snowflake-arctic-embed-s",
        dimension=384,
        query_prefix="",
        doc_prefix="",
        short_name="snowflake-arctic-embed-s",
        description="Better quality, ~130MB, no prefix needed",
    ),
    "bge-base-en-v1.5": ModelConfig(
        name="BAAI/bge-base-en-v1.5",
        dimension=768,
        query_prefix="query: ",
        doc_prefix="",
        short_name="bge-base-en-v1.5",
        description="Best quality (default), ~438MB, uses query prefix",
    ),
    "nomic-embed-text-v1.5": ModelConfig(
        name="nomic-ai/nomic-embed-text-v1.5",
        dimension=768,
        query_prefix="search_query: ",
        doc_prefix="search_document: ",
        short_name="nomic-embed-text-v1.5",
        description="Multimodal capable, ~130MB, uses search prefixes",
        trust_remote_code=True,
    ),
}

# Default model
DEFAULT_MODEL = "bge-base-en-v1.5"


def get_model_config(model_name: str) -> ModelConfig:
    """Get model configuration by short name.

    Args:
        model_name: Short name of the model (e.g., 'bge-base-en-v1.5')

    Returns:
        ModelConfig for the requested model

    Raises:
        ValueError: If model is not found in registry
    """
    if model_name not in MODEL_REGISTRY:
        available = ", ".join(MODEL_REGISTRY.keys())
        raise ValueError(
            f"Unknown model: {model_name}\n"
            f"Available models: {available}"
        )
    return MODEL_REGISTRY[model_name]


def list_models() -> str:
    """Return a formatted string listing all available models."""
    lines = ["Available embedding models:", ""]
    lines.append(f"{'Model':<28} {'Dim':>4}  {'Description'}")
    lines.append("-" * 80)
    for short_name, config in MODEL_REGISTRY.items():
        default_marker = " (default)" if short_name == DEFAULT_MODEL else ""
        lines.append(
            f"{short_name:<28} {config.dimension:>4}  {config.description}{default_marker}"
        )
    return "\n".join(lines)


def get_collection_name_for_model(model_name: str, override: str | None = None) -> str:
    """Generate collection name for a model.

    Args:
        model_name: Short name of the model
        override: Optional override for collection name

    Returns:
        Collection name string
    """
    if override:
        return override
    # Convert model name to collection-safe format
    # e.g., "bge-base-en-v1.5" -> "code_bge_base_en_v15"
    safe_name = model_name.replace("-", "_").replace(".", "")
    return f"code_{safe_name}"
