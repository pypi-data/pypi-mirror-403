# Claude LFR MCP

Lightning fast CPU-based semantic code search for Claude Code. Uses configurable embedding models and Qdrant vector database to provide intelligent code retrieval without requiring GPU resources.

## Quick Start

### Prerequisites

A running Qdrant instance is required. Start one with Docker:

```bash
docker run -p 6333:6333 qdrant/qdrant
```

### Installation


```bash
uv tool install claude-lfr-mcp
```

### Claude Code Setup

Add the MCP server to Claude Code project:

```bash
claude mcp add claude-lfr -- claude-lfr-mcp
```

Verify the installation:

```
/mcp
```

You should see `claude-lfr` listed with its available tools.

Then ask claude to `index codebase`.

## Embedding Models

This tool supports multiple embedding models, allowing you to choose the best tradeoff between speed, memory usage, and retrieval quality for your use case.

### Model Comparison

| Model | Dimension | Size | Speed | Quality | Best For |
|-------|-----------|------|-------|---------|----------|
| `all-MiniLM-L6-v2` | 384 | ~90MB | Fastest | Good | Quick prototyping, CI pipelines, large codebases |
| `bge-small-en-v1.5` | 384 | ~67MB | Fast | Good+ | Balance of speed and accuracy |
| `snowflake-arctic-embed-xs` | 384 | ~90MB | Fast | Good+ | Modern alternative to MiniLM |
| `snowflake-arctic-embed-s` | 384 | ~130MB | Medium | Better | Production use with speed needs |
| `bge-base-en-v1.5` | 768 | ~438MB | Slower | Best | **Default** - Best retrieval quality |
| `nomic-embed-text-v1.5` | 768 | ~130MB | Medium | Better | When using Nomic ecosystem |

### Model Details

**all-MiniLM-L6-v2**
- ✅ Fastest inference, smallest memory footprint
- ✅ No query prefix required (simpler usage)
- ❌ Lower retrieval accuracy than larger models
- Best for: CI/CD pipelines, quick iteration, very large codebases where speed matters

**bge-small-en-v1.5**
- ✅ Excellent speed with better accuracy than MiniLM
- ✅ Smallest download size (~67MB)
- ❌ Requires "query: " prefix (handled automatically)
- Best for: Daily development, good balance of speed and quality

**snowflake-arctic-embed-xs / snowflake-arctic-embed-s**
- ✅ Modern architecture, competitive performance
- ✅ No prefix required
- ❌ Less established than BGE family
- Best for: Production deployments wanting modern alternatives

**bge-base-en-v1.5** (Default)
- ✅ Best retrieval quality, well-tested
- ✅ Strong performance on code search tasks
- ❌ Larger model size (~438MB), slower inference
- Best for: When accuracy is the priority, smaller codebases

**nomic-embed-text-v1.5**
- ✅ Good balance of size and quality
- ✅ 768 dimensions in compact ~130MB package
- ❌ Uses different prefix convention (search_query/search_document)
- Best for: Nomic ecosystem users, medium-large codebases

### Choosing a Model

| Priority | Recommended Model |
|----------|-------------------|
| **Speed first** | `all-MiniLM-L6-v2` |
| **Quality first** | `bge-base-en-v1.5` (default) |
| **Balanced** | `bge-small-en-v1.5` or `snowflake-arctic-embed-s` |
| **Modern + compact** | `nomic-embed-text-v1.5` |

### Configuring the Model

**Via CLI flag:**

```bash
claude-lfr-index --model all-MiniLM-L6-v2 -r /path/to/code
```

**Via environment variable:**

```bash
EMBEDDING_MODEL=bge-small-en-v1.5 claude-lfr-index
```

**List available models:**

```bash
claude-lfr-index --list-models
```

> **Note:** Each model uses a separate Qdrant collection (e.g., `code_bge_base_en_v15`, `code_minilm_l6_v2`). You can override this with `QDRANT_COLLECTION`.

## MCP Tools

| Tool | Description |
|------|-------------|
| `search_code` | Search indexed code by natural language query with ranked results |
| `index_directory` | Index a codebase directory for semantic search |
| `get_index_status` | Check Qdrant collection status and point count |

## Advanced Usage

### CLI Tools

Index a codebase:

```bash
REPO_ROOT=/path/to/your/codebase claude-lfr-index
```

Search indexed code:

```bash
claude-lfr-search "authentication logic"
claude-lfr-search "database connection"
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `QDRANT_URL` | `http://localhost:6333` | Qdrant server URL |
| `QDRANT_API_KEY` | None | Qdrant API key (optional) |
| `QDRANT_COLLECTION` | Auto-generated | Collection name (e.g., `code_bge_base_en_v15`) |
| `EMBEDDING_MODEL` | `bge-base-en-v1.5` | Embedding model to use (see [Embedding Models](#embedding-models)) |
| `REPO_ROOT` | `.` | Directory to index |
| `MAX_FILES` | `0` | Max files to index (0 = unlimited) |

### Manual MCP Configuration

**Project-specific** (`.mcp.json` in project root) or **user-global** (`~/.mcp.json`):

```json
{
  "mcpServers": {
    "claude-lfr": {
      "command": "claude-lfr-mcp"
    }
  }
}
```

Using uvx (no install required):

```json
{
  "mcpServers": {
    "claude-lfr": {
      "command": "uvx",
      "args": ["--from", "claude-lfr-mcp", "claude-lfr-mcp"]
    }
  }
}
```

**Alternative Claude Code commands:**

```bash
# Add to project scope
claude mcp add claude-lfr -s project -- claude-lfr-mcp

# Add globally
claude mcp add claude-lfr -s user -- claude-lfr-mcp

# Using uvx
claude mcp add claude-lfr -- uvx --from claude-lfr-mcp claude-lfr-mcp
```

## Technical Details

### How It Works

1. **Indexing**: Walks the codebase, chunks files into 80-line segments, generates embeddings (384 or 768 dimensions depending on model), and upserts to Qdrant in batches of 256
2. **Searching**: Embeds your query with the model-appropriate prefix, finds most similar code chunks via cosine similarity

### Supported File Types

`.py`, `.ts`, `.tsx`, `.js`, `.jsx`, `.rs`, `.go`, `.java`, `.cs`, `.php`, `.c`, `.cpp`, `.h`, `.hpp`

### Ignored Directories

`.git`, `node_modules`, `.venv`, `dist`, `build`, `__pycache__`

## Development

### Install from Source

```bash
git clone https://gitlab.com/derico/claude-lfr-mcp.git
cd claude-lfr-mcp
uv sync
uv tool install -e .
```

### Running MCP Server Locally

```bash
uv run claude-lfr-mcp
```

Development MCP configuration:

```json
{
  "mcpServers": {
    "claude-lfr": {
      "command": "uv",
      "args": ["run", "claude-lfr-mcp"]
    }
  }
}
```

### Running Tests

Install dev dependencies and run tests:

```bash
uv sync --extra dev
uv run pytest
```

Run with coverage report:

```bash
uv run pytest --cov=claude_lfr_mcp
```

Run specific test file:

```bash
uv run pytest tests/test_mcp_server.py -v
```

## Requirements

- Python 3.10+
- Running Qdrant instance
