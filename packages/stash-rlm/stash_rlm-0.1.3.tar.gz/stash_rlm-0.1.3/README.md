# 🗃️ stash

[![PyPI](https://img.shields.io/pypi/v/stash-rlm.svg)](https://pypi.org/project/stash-rlm/)
[![License](https://img.shields.io/github/license/klodshannon/stash.svg)](LICENSE)
[![Python](https://img.shields.io/pypi/pyversions/stash-rlm.svg)](https://pypi.org/project/stash-rlm/)

**External memory for AI agents** - a lightweight RLM (Recursive Language Model) that any Clawdbot can use.

Store persistent key-value data, load large files into searchable contexts, and manage agent memory - all without consuming precious tokens.

## Features

- **Key-value storage** - `stash set/get` for persistent data
- **Context loading** - Load large files without eating tokens
- **Fast search** - Full-text search with FTS5, plus regex
- **Chunking** - Split large contexts into manageable pieces
- **Memory helpers** - Quick `remember/recall` for agent notes
- **Zero dependencies** - Pure Python, just sqlite3 (built-in)
- **Portable** - Single SQLite database, easy to sync/backup

## Installation

```bash
pip install stash-rlm
```

Or install from source:

```bash
git clone https://github.com/klodshannon/stash.git
cd stash
pip install -e .
```

## Quick Start

```bash
# Store things persistently
stash set api:openai "sk-12345..."
stash get api:openai

# Load large files into context (doesn't eat tokens!)
stash load server.log --as logs
stash peek logs 0:50              # View lines 0-50
stash search "ERROR" --in logs    # Search within context

# Quick memory for agent notes
stash remember "Hunter prefers concise answers" --tag prefs
stash recall prefs
stash recall                      # List all memories

# Manage entries
stash list
stash stats
stash forget logs
```

## Commands

### Key-Value Storage

```bash
stash set <key> <value>     # Store a value
stash set config - < file   # Store from stdin
stash get <key>             # Retrieve a value
stash get <key> --json      # Output as JSON
```

### Context Management

```bash
stash load <file> [--as <id>]    # Load file into context
stash peek <id> [range]          # View slice (e.g., "10:20")
stash peek <id> 100 -n           # 20 lines from 100, numbered
stash search <pattern> --in <id> # Search within context
stash search <pattern>           # Search all entries
```

### Memory Helpers

```bash
stash remember "note" [--tag <tag>]  # Store a memory
stash recall [tag]                   # Recall memories
```

### Management

```bash
stash list [--type <type>]    # List entries
stash stats                   # Storage statistics
stash forget <key>            # Delete entry
stash version                 # Show version
stash export -o backup.json   # Export to JSON
stash import backup.json      # Import from JSON
stash ctx-list                # List contexts
stash ctx-info <id>           # Context details
```

## Use Cases

### For Clawdbots / AI Agents

```bash
# Store frequently needed data
stash set user:tz "America/Chicago"
stash set user:name "Hunter"

# Load documentation for reference
stash load ~/project/README.md --as docs
stash search "API" --in docs

# Remember things between sessions
stash remember "Project uses FastAPI, not Flask"
stash remember "Deploy target is Railway" --tag deploy
```

### Context Window Management

```bash
# Load a huge log file
stash load production.log --as prod

# Search instead of loading entire file
stash search "OutOfMemory" --in prod

# Peek at relevant sections
stash peek prod 1000:1050
```

### Knowledge Base

```bash
# Build up knowledge over time
stash remember "User prefers dark mode" --tag ui
stash remember "Always use TypeScript" --tag code
stash remember "Meetings are Tue/Thu 10am" --tag schedule

# Recall by topic
stash recall code
stash recall schedule
```

## Storage

Data is stored in a SQLite database at:
- Linux/macOS: `~/.local/share/stash/stash.db`
- Or set `STASH_HOME` environment variable
- Or use `--db <path>` flag

The database is fully portable - copy it to sync between machines.

## Comparison with Aleph

| Feature | stash | Aleph |
|---------|-------|-------|
| Installation | `pip install` | MCP server |
| Dependencies | None (pure Python) | MCP, various |
| Storage | SQLite | In-memory |
| Persistence | ✅ Survives restarts | ❌ Session only |
| Python sandbox | ❌ | ✅ |
| Sub-queries | ❌ | ✅ |
| Use case | Simple persistent memory | Complex analysis |

**stash** is for simple, persistent storage. **Aleph** is for complex analysis sessions.

## License

MIT - Built by [Klod](https://github.com/klodshannon) at Shannon Labs.
