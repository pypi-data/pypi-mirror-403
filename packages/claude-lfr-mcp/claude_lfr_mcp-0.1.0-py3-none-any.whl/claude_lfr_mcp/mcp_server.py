"""MCP server for code-indexer - semantic code search integration."""

import os
import sys
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from .indexer import (
    index_repo,
    get_qdrant_client,
    get_collection_name,
    get_current_model_config,
    EMBEDDING_MODEL,
)
from .searcher import search
from .models import MODEL_REGISTRY, list_models
from .ignore import get_ignore_handler


# Create MCP server instance
server = Server("code-indexer")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="search_code",
            description=(
                "Search code by natural language query using semantic similarity. "
                "Returns ranked results with file paths, line numbers, similarity scores, "
                "and code snippets. Use for understanding functionality, finding patterns, "
                "or discovering related code."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Natural language search query (e.g., 'authentication logic', 'database connection')",
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of results to return (default: 10)",
                        "default": 10,
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="index_directory",
            description=(
                "Index a codebase directory for semantic search. "
                "Processes code files, generates embeddings, and stores in Qdrant. "
                "Supports: .py, .ts, .tsx, .js, .jsx, .rs, .go, .java, .cs, .php, .c, .cpp, .h, .hpp"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "Absolute path to the directory to index",
                    },
                    "max_files": {
                        "type": "integer",
                        "description": "Maximum files to index (0 = no limit)",
                        "default": 0,
                    },
                    "use_gitignore": {
                        "type": "boolean",
                        "description": "Whether to parse .gitignore files (default: true)",
                        "default": True,
                    },
                    "extra_ignore_patterns": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Additional ignore patterns in gitignore syntax",
                    },
                },
                "required": ["directory"],
            },
        ),
        Tool(
            name="get_index_status",
            description=(
                "Get status of the code index including collection info and point count."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""

    if name == "search_code":
        query = arguments.get("query", "")
        top_k = arguments.get("top_k", 10)

        if not query:
            return [TextContent(type="text", text="Error: query is required")]

        try:
            results = search(query, top_k=top_k)

            if not results:
                return [TextContent(type="text", text="No results found.")]

            output_lines = [f"Found {len(results)} results for: {query}\n"]
            for i, hit in enumerate(results, 1):
                p = hit.payload
                output_lines.append(
                    f"{i}. {p['path']}:{p['start_line']}-{p['end_line']} "
                    f"(score: {hit.score:.3f})\n"
                    f"```\n{p['snippet'][:500]}{'...' if len(p['snippet']) > 500 else ''}\n```\n"
                )

            return [TextContent(type="text", text="\n".join(output_lines))]

        except Exception as e:
            return [TextContent(type="text", text=f"Search error: {e}")]

    elif name == "index_directory":
        directory = arguments.get("directory", "")
        max_files = arguments.get("max_files", 0)
        use_gitignore = arguments.get("use_gitignore", True)
        extra_ignore_patterns = arguments.get("extra_ignore_patterns", [])

        if not directory:
            return [TextContent(type="text", text="Error: directory is required")]

        path = Path(directory).resolve()
        if not path.exists():
            return [TextContent(type="text", text=f"Error: directory does not exist: {path}")]
        if not path.is_dir():
            return [TextContent(type="text", text=f"Error: not a directory: {path}")]

        try:
            ignore_handler = get_ignore_handler(
                root=path,
                use_gitignore=use_gitignore,
                extra_patterns=extra_ignore_patterns if extra_ignore_patterns else None,
            )
            index_repo(path, max_files=max_files, ignore_handler=ignore_handler)
            return [TextContent(type="text", text=f"Successfully indexed: {path}")]
        except Exception as e:
            return [TextContent(type="text", text=f"Indexing error: {e}")]

    elif name == "get_index_status":
        try:
            client = get_qdrant_client()
            collections = client.get_collections().collections
            collection_name = get_collection_name()
            model_config = get_current_model_config()

            status_lines = ["Code Index Status\n"]
            status_lines.append(f"Qdrant URL: {os.getenv('QDRANT_URL', 'http://localhost:6333')}")
            status_lines.append(f"Collection: {collection_name}")
            status_lines.append(f"\nEmbedding Model: {model_config.short_name}")
            status_lines.append(f"Model Dimension: {model_config.dimension}")
            status_lines.append(f"Query Prefix: '{model_config.query_prefix}' (empty=none)")
            status_lines.append(f"Doc Prefix: '{model_config.doc_prefix}' (empty=none)\n")

            collection_exists = any(c.name == collection_name for c in collections)
            if collection_exists:
                info = client.get_collection(collection_name)
                status_lines.append(f"Points indexed: {info.points_count}")
                status_lines.append(f"Indexed vectors: {info.indexed_vectors_count}")
                status_lines.append(f"Status: {info.status}")
            else:
                status_lines.append("Collection does not exist yet. Run index_directory first.")

            # List available models
            status_lines.append("\n" + list_models())

            return [TextContent(type="text", text="\n".join(status_lines))]

        except Exception as e:
            return [TextContent(type="text", text=f"Status check error: {e}")]

    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]


def check_qdrant_health() -> bool:
    """Validate Qdrant connection on startup."""
    try:
        client = get_qdrant_client()
        client.get_collections()  # Simple health check
        return True
    except Exception as e:
        print(f"ERROR: Cannot connect to Qdrant: {e}", file=sys.stderr)
        print(f"Qdrant URL: {os.getenv('QDRANT_URL', 'http://localhost:6333')}", file=sys.stderr)
        return False


async def run_server():
    """Run the MCP server."""
    if not check_qdrant_health():
        print("MCP server not starting due to Qdrant connection failure.", file=sys.stderr)
        sys.exit(1)

    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def main():
    """Entry point for the MCP server."""
    import asyncio
    asyncio.run(run_server())


if __name__ == "__main__":
    main()
