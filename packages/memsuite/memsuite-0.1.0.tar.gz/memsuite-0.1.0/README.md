# MemSuite

A lightweight, PostgreSQL-backed memory management system for AI agents and chatbots. MemSuite provides structured storage and retrieval of conversation history, agent interactions, and contextual data.

## 🚀 Current Status: Phase 1 (Complete)

### ✅ Phase 1: Core Memory Storage & Retrieval

A fully functional memory system with:

- **SQLAlchemy-based persistence** - PostgreSQL database integration with connection pooling
- **Memory Store API** - Simple write/read interface for agent memory operations
- **UUID-based indexing** - Efficient querying by user, session, and agent IDs
- **Flexible memory types** - Support for different categories of memories (conversation, facts, preferences, etc.)
- **Metadata support** - JSON-based metadata storage for extensible memory attributes

### Core Components

- **`MemoryStore`** - High-level API for writing and reading memories
- **`SQLMemoryDB`** - Database layer with connection management and query building
- **`Memory` model** - SQLAlchemy ORM model with indexed fields for fast retrieval

### Quick Start

```python
import os
from uuid import uuid4
from dotenv import load_dotenv
from memsuite.store import MemoryStore

# Load environment variables
load_dotenv()

# Initialize with your PostgreSQL connection string from environment
store = MemoryStore(os.getenv("DB_URL"))

user_id = uuid4()
session_id = uuid4()

# Write a memory
store.write(
    user_id=user_id,
    session_id=session_id,
    agent_id="chatbot",
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

## 🗺️ Roadmap

### Phase 2: Context Building & Token Budgeting
- Smart context window management
- Automatic memory prioritization and selection
- Token counting and budget enforcement
- Sliding window strategies for long conversations

### Phase 3: Long-term Memory (Embeddings)
- Vector embeddings for semantic search
- Similarity-based memory retrieval
- Integration with embedding models (OpenAI, local models)
- Hybrid search (keyword + semantic)

### Phase 4: Multi-agent Policies
- Agent-specific memory isolation and sharing
- Memory access control and permissions
- Cross-agent memory coordination
- Agent collaboration patterns

### Phase 5: Dashboard & Hosted Options
- Web-based memory visualization dashboard
- Real-time memory analytics
- Cloud-hosted SaaS offering
- API gateway and authentication

## 📦 Installation

```bash
pip install memsuite
```

Or with UV:
```bash
uv pip install memsuite
```

## ⚙️ Configuration

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Set your database URL in `.env`:
   ```bash
   DB_URL=postgresql://user:password@host:port/database
   ```

3. **Never commit `.env` to version control** - it's already in `.gitignore`

## 🛠️ Requirements

- Python >= 3.10
- PostgreSQL database
- Dependencies: SQLAlchemy, FastAPI, psycopg2-binary

## 📝 Example Usage

See [examples/simple_chat_backend.py](examples/simple_chat_backend.py) for a complete chatbot integration example.

## 🤝 Contributing

Contributions are welcome! This project is in active development.

## 📄 License

MIT
