# MemSuite

[![PyPI version](https://badge.fury.io/py/memsuite.svg)](https://pypi.org/project/memsuite/)
[![Python](https://img.shields.io/pypi/pyversions/memsuite.svg)](https://pypi.org/project/memsuite/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A lightweight, PostgreSQL-backed memory management system for AI agents and chatbots. MemSuite provides structured storage and retrieval of conversation history, agent interactions, and contextual data with minimal configuration.

## Features

- **PostgreSQL persistence** with SQLAlchemy ORM and connection pooling
- **Simple API** for reading and writing agent memories
- **UUID-based indexing** for efficient queries by user, session, and agent
- **Flexible memory types** to categorize memories (conversation, facts, preferences, etc.)
- **Metadata support** via JSON for extensible memory attributes

## Installation

```bash
pip install memsuite
```

Using UV:

```bash
uv pip install memsuite
```

## Quick Start

```python
import os
from uuid import uuid4
from dotenv import load_dotenv
from memsuite import MemoryStore

load_dotenv()

store = MemoryStore(os.getenv("DB_URL"))

user_id = uuid4()
session_id = uuid4()

# Write a memory
store.write(
    user_id=user_id,
    session_id=session_id,
    agent_id="assistant",
    content="User prefers concise responses",
    memory_type="preference",
    metadata={"importance": "high"}
)

# Read memories
memories = store.read(
    user_id=user_id,
    session_id=session_id,
    memory_type="preference"
)
```

## Configuration

1. Create a `.env` file in your project root:

```bash
DB_URL=postgresql://user:password@host:port/database
```

2. Load environment variables with `python-dotenv` or your preferred method.

## Requirements

- Python >= 3.10
- PostgreSQL database
- SQLAlchemy, psycopg2-binary, pydantic, python-dotenv

## API Reference

### MemoryStore

The primary interface for memory operations.

```python
from memsuite import MemoryStore

store = MemoryStore(database_url)
```

#### write()

Store a memory record.

| Parameter | Type | Description |
|-----------|------|-------------|
| `user_id` | `UUID` | Unique identifier for the user |
| `session_id` | `UUID` | Unique identifier for the session |
| `agent_id` | `str` | Identifier for the agent |
| `content` | `str` | The memory content |
| `memory_type` | `str` | Category of the memory |
| `metadata` | `dict` (optional) | Additional key-value metadata |

#### read()

Retrieve memory records with optional filters.

| Parameter | Type | Description |
|-----------|------|-------------|
| `user_id` | `UUID` (optional) | Filter by user |
| `session_id` | `UUID` (optional) | Filter by session |
| `memory_type` | `str` (optional) | Filter by memory type |

## Examples

See [examples/simple_chat_backend.py](examples/simple_chat_backend.py) for a complete integration example.

## Roadmap

**Phase 2: Context Building**
- Token-aware context window management
- Automatic memory prioritization and selection

**Phase 3: Long-term Memory**
- Vector embeddings for semantic search
- Hybrid retrieval (keyword + semantic)

**Phase 4: Multi-agent Support**
- Memory isolation and sharing policies
- Cross-agent coordination

**Phase 5: Management Dashboard**
- Web-based memory visualization
- Usage analytics and monitoring

## Contributing

Contributions are welcome. Please open an issue to discuss proposed changes before submitting a pull request.

## License

MIT License. See [LICENSE](LICENSE) for details.
