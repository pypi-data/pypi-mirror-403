# Cowork History MCP

An MCP (Model Context Protocol) server for searching and browsing your Claude conversation history stored in `~/.claude/`. Works with both Claude Code and Cowork conversations.

## Features

- **Hybrid Search** - Combines multiple search methods for best results:
  - **SQLite FTS5** - Fast full-text search with BM25 ranking
  - **macOS Spotlight** - Leverages system content indexing via `mdfind`
  - **Vector Embeddings** - Semantic similarity search (optional, requires Ollama)
- **Smart Path Reconstruction** - Recovers actual filesystem paths via probing (not heuristic guessing)
- **Persistent Index** - SQLite database with incremental updates for fast queries
- **Ollama Setup Tools** - Automated installation and configuration for embeddings

## Installation

### Option 1: Claude Desktop (One-Click Install)

Download `cowork-history.mcpb` from the [latest release](https://github.com/egoughnour/cowork-history/releases/latest) and double-click to install.

### Option 2: Via uvx (Recommended for CLI)

```bash
uvx cowork-history
```

### Option 3: Via pip

```bash
pip install cowork-history
```

### Option 4: Manual Configuration

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "cowork-history": {
      "command": "uvx",
      "args": ["cowork-history"],
      "env": {
        "OLLAMA_URL": "http://localhost:11434",
        "EMBEDDING_MODEL": "nomic-embed-text"
      }
    }
  }
}
```

## Quick Start

Once installed, Claude can search your conversation history:

```
"What did we discuss about authentication last week?"
"Find the conversation where we debugged the payment webhook"
"Show me my conversations in the my-project folder"
```

## Available Tools

### Search & Browse

| Tool | Description |
|------|-------------|
| `cowork_history_search` | Search conversations using hybrid search (FTS + Spotlight + vector) |
| `cowork_history_list` | List recent conversations, optionally filtered by project |
| `cowork_history_get` | Get full content of a specific conversation by session ID |
| `cowork_history_projects` | List all projects with conversation history |
| `cowork_history_stats` | Get statistics and search capability status |
| `cowork_history_reindex` | Rebuild index and optionally generate embeddings |

### Ollama Setup (for Vector Search)

| Tool | Description |
|------|-------------|
| `history_system_check` | Check system requirements for Ollama |
| `history_setup_ollama` | Install Ollama via Homebrew (macOS) |
| `history_setup_ollama_direct` | Install Ollama via direct download (no Homebrew) |
| `history_ollama_status` | Check Ollama status and embedding model availability |

## Search Modes

The `cowork_history_search` tool supports multiple search modes:

| Mode | Description |
|------|-------------|
| `auto` (default) | Uses all available methods, best results |
| `fts` | Full-text search only (fastest) |
| `spotlight` | macOS Spotlight only |
| `vector` | Semantic similarity only (requires Ollama) |
| `hybrid` | Explicit combination with ranking |

### Search Examples

```
"authentication bug"           → finds conversations with both words
"how to deploy"                → semantic search finds related discussions
"\"exact phrase\""             → exact phrase matching
project:"my-app" "database"    → filter by project
```

## Enabling Vector Search

Vector search provides semantic similarity matching (finding related concepts even without exact keywords). It requires Ollama with an embedding model.

### Quick Setup

Ask Claude to set it up for you:
```
"Set up Ollama for vector search"
```

Or manually:

```bash
# Install Ollama (macOS)
brew install ollama

# Start Ollama service
brew services start ollama

# Pull the embedding model
ollama pull nomic-embed-text
```

Then generate embeddings:
```
"Rebuild the history index with embeddings"
```

## How It Works

### Indexing

The server maintains a SQLite database at `~/.claude/.history-index/conversations.db` with:
- FTS5 virtual table for fast full-text search
- Conversation metadata (session ID, project, timestamps, topic)
- Full content for comprehensive search
- Path cache for reconstructed paths
- Embeddings table for vector search (optional)

The index updates automatically when you search (if >5 minutes old) or you can force a rebuild with `cowork_history_reindex`.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_URL` | `http://localhost:11434` | Ollama server URL |
| `EMBEDDING_MODEL` | `nomic-embed-text` | Ollama embedding model |

## Troubleshooting

### No conversations found

1. Make sure `~/.claude/` directory exists
2. Check that you have conversation history (use Claude Code or Cowork first)
3. Verify the MCP server is properly configured

### Vector search not available

1. Check Ollama is installed: `ollama --version`
2. Check Ollama is running: `curl http://localhost:11434/api/tags`
3. Check model is available: `ollama list`
4. Pull embedding model: `ollama pull nomic-embed-text`

### Search not finding expected results

- Try natural language queries (semantic search is more flexible)
- Use `mode: "fts"` for exact phrase matching
- Check `cowork_history_stats` to see which search backends are active

## Development

### Running locally

```bash
# Clone the repository
git clone https://github.com/egoughnour/cowork-history
cd cowork-history

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest tests/

# Run the server directly
python -m src.cowork_history_server
```

### Testing with MCP Inspector

```bash
npx @modelcontextprotocol/inspector uvx cowork-history
```

## License

MIT License - see LICENSE file for details.
