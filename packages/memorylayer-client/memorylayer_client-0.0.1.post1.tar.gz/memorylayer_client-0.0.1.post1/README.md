# MemoryLayer.ai Python SDK

Python SDK for [MemoryLayer.ai](https://memorylayer.ai) - Memory infrastructure for AI agents.

## Installation

```bash
pip install memorylayer-client
```

## Quick Start

```python
from memorylayer import MemoryLayerClient, MemoryType

async with MemoryLayerClient(
        base_url="https://api.memorylayer.ai",
        api_key="your-api-key",
        workspace_id="ws_123"
) as client:
    # Store a memory
    memory = await client.remember(
        content="User prefers Python for backend development",
        type=MemoryType.SEMANTIC,
        importance=0.8,
        tags=["preferences", "programming"]
    )

    # Search memories
    results = await client.recall(
        query="what programming language does the user prefer?",
        limit=5
    )

    for memory in results.memories:
        print(f"{memory.content} (relevance: {memory.importance})")

    # Synthesize memories
    reflection = await client.reflect(
        query="summarize user's technology preferences"
    )
    print(reflection.reflection)
```

## Features

- **Simple, Pythonic API** - Async/await support with context managers
- **Type-safe** - Full type hints with Pydantic models
- **Memory Operations** - Remember, recall, reflect, forget
- **Relationship Graph** - Link memories with typed relationships
- **Session Management** - Working memory with TTL
- **Error Handling** - Comprehensive exception hierarchy

## Core Operations

### Remember (Store Memory)

```python
memory = await client.remember(
    content="User prefers FastAPI over Flask",
    type=MemoryType.SEMANTIC,
    subtype=MemorySubtype.PREFERENCE,
    importance=0.8,
    tags=["preferences", "frameworks"],
    metadata={"source": "conversation"}
)
```

### Recall (Search Memories)

```python
from memorylayer import RecallMode, SearchTolerance

results = await client.recall(
    query="what frameworks does the user prefer?",
    types=[MemoryType.SEMANTIC],
    mode=RecallMode.RAG,  # or RecallMode.LLM for deep semantic search
    limit=10,
    min_relevance=0.7,
    tolerance=SearchTolerance.MODERATE
)
```

### Reflect (Synthesize Memories)

```python
reflection = await client.reflect(
    query="summarize everything about the user's development workflow",
    max_tokens=500,
    include_sources=True
)

print(reflection.reflection)
print(f"Based on {len(reflection.source_memories)} memories")
```

### Associate (Link Memories)

```python
from memorylayer import RelationshipType

association = await client.associate(
    source_id="mem_problem_123",
    target_id="mem_solution_456",
    relationship=RelationshipType.SOLVES,
    strength=0.9
)
```

### Session Management

```python
# Create session for working memory
session = await client.create_session(ttl_seconds=3600)

# Store temporary context
await client.set_context(
    session.id,
    "current_task",
    {"description": "Debugging auth", "file": "auth.py"}
)

# Retrieve context
context = await client.get_context(session.id, ["current_task"])
```

## Memory Types

### Cognitive Types

- **Episodic** - Specific events/interactions
- **Semantic** - Facts, concepts, relationships
- **Procedural** - How to do things
- **Working** - Current task context (session-scoped)

### Domain Subtypes

- **Solution** - Working fixes to problems
- **Problem** - Issues encountered
- **CodePattern** - Reusable patterns
- **Fix** - Bug fixes with context
- **Error** - Error patterns and resolutions
- **Workflow** - Process knowledge
- **Preference** - User/project preferences
- **Decision** - Architectural decisions

## Relationship Types

Link memories with typed relationships:

```python
from memorylayer import RelationshipType

# Causal
RelationshipType.CAUSES
RelationshipType.TRIGGERS
RelationshipType.LEADS_TO

# Solution
RelationshipType.SOLVES
RelationshipType.ADDRESSES
RelationshipType.IMPROVES

# Learning
RelationshipType.BUILDS_ON
RelationshipType.CONTRADICTS
RelationshipType.SUPERSEDES

# ... and more
```

## Error Handling

```python
from memorylayer import (
    AuthenticationError,
    NotFoundError,
    ValidationError,
    RateLimitError,
    ServerError
)

try:
    memory = await client.get_memory("mem_123")
except NotFoundError:
    print("Memory not found")
except AuthenticationError:
    print("Invalid API key")
except RateLimitError:
    print("Rate limit exceeded")
```

## Advanced Usage

### Get Session Briefing

```python
briefing = await client.get_briefing(lookback_hours=24)

print(f"Total memories: {briefing.workspace_summary['total_memories']}")
print(f"Recent activity: {len(briefing.recent_activity)} events")

for thread in briefing.open_threads:
    print(f"Open: {thread.topic} - {thread.status}")
```

### Update Memory

```python
updated = await client.update_memory(
    "mem_123",
    importance=0.9,
    tags=["critical", "preferences"]
)
```

### Get Associations

```python
associations = await client.get_associations(
    "mem_123",
    direction="both"  # or "outgoing" or "incoming"
)

for assoc in associations:
    print(f"{assoc.relationship}: {assoc.target_id}")
```

## Development

### Install Development Dependencies

```bash
pip install -e ".[dev]"
```

### Run Tests

```bash
pytest
```

### Type Checking

```bash
mypy src/memorylayer
```

### Linting

```bash
ruff check src/memorylayer
black src/memorylayer
```

## License

Apache 2.0 License - see LICENSE file for details.

## Links

- [Documentation](https://docs.memorylayer.ai)
- [GitHub](https://github.com/scitrera/memorylayer)
- [Homepage](https://memorylayer.ai)
