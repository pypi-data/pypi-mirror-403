# MemoryLayer Python SDK

Official Python SDK for [MemoryLayer](https://memorylayer.com) - The intelligent memory layer for AI applications.

[![PyPI version](https://badge.fury.io/py/memorylayerai.svg)](https://pypi.org/project/memorylayerai/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

## Features

- 🧠 **Memory Management**: Store, retrieve, and manage AI memories
- 🔍 **Hybrid Search**: Vector + keyword + graph-based retrieval
- 🕸️ **Memory Graph**: Visualize and traverse memory relationships
- 🎯 **Smart Retrieval**: LLM reranking and query rewriting
- 📊 **Observability**: Track performance and quality metrics
- 🔐 **Type-Safe**: Full type hints with Pydantic models

## Installation

```bash
pip install memorylayerai
```

## Quick Start

### 1. Get Your API Key

Sign up at [memorylayer.com](https://memorylayer.com) and create an API key from your project settings.

### 2. Initialize the Client

```python
from memorylayer import MemoryLayer

client = MemoryLayer(
    api_key="ml_key_...",
    # Optional: specify custom base URL
    # base_url="https://api.memorylayer.com"
)
```

### 3. Create Memories

```python
# Create a single memory
memory = client.memories.create(
    project_id="your-project-id",
    content="The user prefers dark mode in their applications",
    type="preference",
    tags={
        "category": "ui",
        "importance": "high"
    }
)

print(f"Memory created: {memory.id}")
```

### 4. Search Memories

```python
# Hybrid search (vector + keyword + graph)
results = client.search.hybrid(
    project_id="your-project-id",
    query="What are the user UI preferences?",
    limit=10,
    # Optional: enable advanced features
    use_reranking=True,      # LLM-based reranking
    use_query_rewriting=True, # Query expansion
    use_graph_traversal=True  # Follow memory relationships
)

for result in results:
    print(f"Score: {result.score}")
    print(f"Content: {result.content}")
    print(f"Type: {result.type}")
```

## Core Features

### Memory Management

#### Create Memory

```python
memory = client.memories.create(
    project_id="project-id",
    content="User completed onboarding on 2024-01-15",
    type="fact",
    tags={
        "event": "onboarding",
        "date": "2024-01-15"
    },
    metadata={
        "source": "mobile-app",
        "version": "2.1.0"
    }
)
```

#### List Memories

```python
memories = client.memories.list(
    project_id="project-id",
    types=["fact", "preference"],
    status=["active"],
    page=1,
    page_size=50
)

print(f"Total: {memories.total}")
for memory in memories.items:
    print(memory.content)
```

#### Get Memory

```python
memory = client.memories.get("memory-id")
print(memory.content)
```

#### Update Memory

```python
updated = client.memories.update(
    "memory-id",
    content="Updated content",
    tags={"updated": "true"}
)
```

#### Delete Memory

```python
client.memories.delete("memory-id")
```

### Search & Retrieval

#### Hybrid Search

Combines vector search, keyword search, and graph traversal:

```python
results = client.search.hybrid(
    project_id="project-id",
    query="What does the user like?",
    limit=10,
    
    # Scoring weights (optional)
    vector_weight=0.5,
    keyword_weight=0.3,
    recency_weight=0.2,
    
    # Advanced features
    use_reranking=True,      # Use LLM to rerank results
    use_query_rewriting=True, # Expand and clarify query
    use_graph_traversal=True, # Follow memory relationships
    graph_depth=2            # How many hops to traverse
)
```

#### Vector Search Only

```python
results = client.search.vector(
    project_id="project-id",
    query="user preferences",
    limit=5,
    threshold=0.7  # Minimum similarity score
)
```

#### Keyword Search Only

```python
results = client.search.keyword(
    project_id="project-id",
    query="dark mode",
    limit=5
)
```

### Memory Graph

#### Get Graph Data

```python
graph = client.graph.get(
    project_id="project-id",
    # Optional filters
    memory_types=["fact", "preference"],
    search_query="user preferences",
    date_range={
        "start": "2024-01-01",
        "end": "2024-12-31"
    }
)

print(f"Nodes: {len(graph.nodes)}")
print(f"Edges: {len(graph.edges)}")

# Nodes
for node in graph.nodes:
    print(f"{node.id}: {node.content}")

# Edges (relationships)
for edge in graph.edges:
    print(f"{edge.source} -> {edge.target} ({edge.type})")
```

#### Create Edge

```python
edge = client.graph.create_edge(
    project_id="project-id",
    source_memory_id="memory-1",
    target_memory_id="memory-2",
    relationship_type="derives",  # or 'similarity', 'temporal', etc.
    metadata={
        "confidence": 0.95,
        "reason": "User explicitly linked these"
    }
)
```

#### Traverse Graph

```python
related = client.graph.traverse(
    project_id="project-id",
    start_memory_ids=["memory-1"],
    depth=2,  # How many hops
    relationship_types=["similarity", "derives"]
)

print(f"Found {len(related)} related memories")
```

### Ingestion

#### Ingest Document

```python
job = client.ingestion.ingest(
    project_id="project-id",
    content="Long document content...",
    metadata={
        "title": "Product Documentation",
        "source": "docs.example.com"
    },
    # Chunking strategy
    chunking_strategy="semantic",  # or 'fixed-size', 'sentence', 'paragraph'
    chunk_size=512,
    chunk_overlap=50
)

print(f"Job ID: {job.id}")
print(f"Status: {job.status}")
```

#### Check Job Status

```python
job = client.ingestion.get_job("job-id")
print(f"Status: {job.status}")
print(f"Progress: {job.progress}%")
print(f"Memories created: {job.memories_created}")
```

## Advanced Features

### LLM Reranking

Improve search relevance using LLM-based reranking:

```python
results = client.search.hybrid(
    project_id="project-id",
    query="complex user question",
    limit=20,
    use_reranking=True,
    reranking_model="gpt-4",  # or 'claude-3'
    reranking_top_k=10  # Return top 10 after reranking
)
```

### Query Rewriting

Expand and clarify queries for better results:

```python
results = client.search.hybrid(
    project_id="project-id",
    query="ML preferences",  # Will expand to "machine learning preferences"
    use_query_rewriting=True,
    query_rewriting_strategy="expansion"  # or 'clarification', 'multi-query'
)
```

### Graph Traversal

Follow memory relationships for contextual retrieval:

```python
results = client.search.hybrid(
    project_id="project-id",
    query="user settings",
    use_graph_traversal=True,
    graph_depth=2,  # Follow relationships 2 hops deep
    graph_relationship_types=["similarity", "derives"]
)
```

## Type Safety

The SDK uses Pydantic for full type safety:

```python
from memorylayer import (
    MemoryLayer,
    Memory,
    SearchResult,
    GraphData,
    IngestionJob
)

# All methods return typed objects
client = MemoryLayer(api_key="ml_key_...")

# Type hints and validation
memory: Memory = client.memories.create(
    project_id="project-id",
    content="typed content",
    type="fact"  # Validated against allowed types
)
```

## Async Support

The SDK supports async/await for better performance:

```python
import asyncio
from memorylayer import AsyncMemoryLayer

async def main():
    client = AsyncMemoryLayer(api_key="ml_key_...")
    
    # All methods are async
    memory = await client.memories.create(
        project_id="project-id",
        content="async memory"
    )
    
    results = await client.search.hybrid(
        project_id="project-id",
        query="async search"
    )
    
    print(f"Found {len(results)} results")

asyncio.run(main())
```

## Error Handling

```python
from memorylayer import MemoryLayerError

try:
    memory = client.memories.create(
        project_id="project-id",
        content="test"
    )
except MemoryLayerError as e:
    print(f"API Error: {e.message}")
    print(f"Status: {e.status_code}")
    print(f"Request ID: {e.request_id}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Configuration

### Custom Base URL

```python
client = MemoryLayer(
    api_key="ml_key_...",
    base_url="https://your-custom-domain.com"
)
```

### Timeout

```python
client = MemoryLayer(
    api_key="ml_key_...",
    timeout=30.0  # 30 seconds
)
```

### Retry Configuration

```python
client = MemoryLayer(
    api_key="ml_key_...",
    max_retries=3,
    retry_delay=1.0  # 1 second
)
```

## Examples

### Chatbot with Memory

```python
from memorylayer import MemoryLayer
import os

client = MemoryLayer(api_key=os.getenv("MEMORYLAYER_API_KEY"))
project_id = "your-project-id"

def chat_with_memory(user_message: str, user_id: str) -> str:
    # 1. Search for relevant memories
    memories = client.search.hybrid(
        project_id=project_id,
        query=user_message,
        limit=5,
        use_reranking=True,
        use_graph_traversal=True
    )
    
    # 2. Build context from memories
    context = "\n\n".join([m.content for m in memories])
    
    # 3. Send to LLM with context
    response = call_your_llm(
        system=f"You are a helpful assistant. Use this context about the user:\n\n{context}",
        user=user_message
    )
    
    # 4. Store new memory from conversation
    client.memories.create(
        project_id=project_id,
        content=f'User said: "{user_message}". Assistant responded: "{response}"',
        type="fact",
        tags={"user_id": user_id, "timestamp": datetime.now().isoformat()}
    )
    
    return response
```

### Document Q&A

```python
import time

def ingest_and_query(document_content: str, question: str) -> str:
    # 1. Ingest document
    job = client.ingestion.ingest(
        project_id="your-project-id",
        content=document_content,
        chunking_strategy="semantic",
        chunk_size=512
    )
    
    # 2. Wait for ingestion to complete
    while True:
        status = client.ingestion.get_job(job.id)
        if status.status != "processing":
            break
        time.sleep(1)
    
    # 3. Query the document
    results = client.search.hybrid(
        project_id="your-project-id",
        query=question,
        limit=3,
        use_reranking=True
    )
    
    return "\n\n".join([r.content for r in results])
```

### LangChain Integration

```python
from memorylayer import MemoryLayer
from langchain.memory import BaseMemory
from typing import Any, Dict, List

class MemoryLayerMemory(BaseMemory):
    """LangChain memory backed by MemoryLayer"""
    
    def __init__(self, api_key: str, project_id: str):
        self.client = MemoryLayer(api_key=api_key)
        self.project_id = project_id
    
    @property
    def memory_variables(self) -> List[str]:
        return ["history"]
    
    def load_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        # Search for relevant memories
        results = self.client.search.hybrid(
            project_id=self.project_id,
            query=inputs.get("input", ""),
            limit=5,
            use_reranking=True
        )
        
        history = "\n".join([r.content for r in results])
        return {"history": history}
    
    def save_context(self, inputs: Dict[str, Any], outputs: Dict[str, str]) -> None:
        # Save conversation to MemoryLayer
        self.client.memories.create(
            project_id=self.project_id,
            content=f"User: {inputs['input']}\nAssistant: {outputs['output']}",
            type="fact"
        )
    
    def clear(self) -> None:
        pass  # MemoryLayer handles memory lifecycle

# Usage with LangChain
memory = MemoryLayerMemory(
    api_key="ml_key_...",
    project_id="your-project-id"
)
```

## API Reference

Full API documentation available at [docs.memorylayer.com](https://docs.memorylayer.com)

## Support

- 📧 Email: support@memorylayer.com
- 💬 Discord: [discord.gg/memorylayer](https://discord.gg/memorylayer)
- 📖 Docs: [docs.memorylayer.com](https://docs.memorylayer.com)
- 🐛 Issues: [github.com/memorylayer/sdk/issues](https://github.com/memorylayer/sdk/issues)

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Changelog

### v0.2.0 (2024-01-20)

- ✨ Added Memory Graph API support
- ✨ Added Hybrid Search with LLM reranking
- ✨ Added Query Rewriting capabilities
- ✨ Added Graph Traversal for contextual retrieval
- ✨ Added async/await support
- 🐛 Fixed type hints for better IDE support
- 📚 Comprehensive documentation and examples

### v0.1.1 (2024-01-10)

- 🐛 Bug fixes and stability improvements

### v0.1.0 (2024-01-01)

- 🎉 Initial release
- ✨ Basic memory CRUD operations
- ✨ Vector search
- ✨ Ingestion API
