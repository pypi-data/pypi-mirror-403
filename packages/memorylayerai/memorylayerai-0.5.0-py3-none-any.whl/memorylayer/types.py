"""Type definitions for the MemoryLayer SDK."""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class Memory:
    """Memory object."""

    id: str
    content: str
    project_id: str
    created_at: str
    updated_at: str
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class CreateMemoryRequest:
    """Request to create a new memory."""

    content: str
    project_id: str
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class UpdateMemoryRequest:
    """Request to update an existing memory."""

    content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ListMemoriesRequest:
    """Request to list memories."""

    project_id: str
    limit: Optional[int] = None
    offset: Optional[int] = None
    filter: Optional[Dict[str, Any]] = None


@dataclass
class SearchRequest:
    """Search request.
    
    Defaults:
        limit: 10 (supermemory production default)
        threshold: 0.6 (supermemory production default for broad recall)
    """

    query: str
    project_id: str
    limit: Optional[int] = None
    filter: Optional[Dict[str, Any]] = None
    threshold: Optional[float] = None


@dataclass
class SearchResult:
    """Search result."""

    memory: Memory
    score: float
    highlights: Optional[List[str]] = None


@dataclass
class SearchResponse:
    """Search response."""

    results: List[SearchResult]
    total: int


@dataclass
class IngestFileRequest:
    """Request to ingest a file.
    
    Defaults:
        chunk_size: 512 tokens (supermemory production default)
        chunk_overlap: 10% (supermemory production default)
    """

    file: Any  # File-like object or bytes
    project_id: str
    metadata: Optional[Dict[str, Any]] = None
    chunk_size: Optional[int] = None
    chunk_overlap: Optional[int] = None


@dataclass
class IngestTextRequest:
    """Request to ingest text.
    
    Defaults:
        chunk_size: 512 tokens (supermemory production default)
        chunk_overlap: 10% (supermemory production default)
    """

    text: str
    project_id: str
    metadata: Optional[Dict[str, Any]] = None
    chunk_size: Optional[int] = None
    chunk_overlap: Optional[int] = None


@dataclass
class IngestResponse:
    """Ingestion response."""

    memory_ids: List[str]
    chunks_created: int


@dataclass
class Message:
    """Message in a conversation."""

    role: str  # 'user', 'assistant', or 'system'
    content: str


@dataclass
class RouterRequest:
    """Router request.
    
    Defaults:
        model: 'gpt-4o-mini' (supermemory production default - fast & cost-efficient)
        temperature: 0.7 (supermemory production default - balanced)
        max_tokens: 2000 (supermemory production default)
    """

    messages: List[Message]
    project_id: str
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    stream: Optional[bool] = None


@dataclass
class Usage:
    """Token usage information."""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


@dataclass
class Choice:
    """Choice in a router response."""

    message: Message
    finish_reason: str


@dataclass
class RouterResponse:
    """Router response."""

    id: str
    choices: List[Choice]
    usage: Usage


@dataclass
class StreamDelta:
    """Delta in a streaming choice."""

    role: Optional[str] = None
    content: Optional[str] = None


@dataclass
class StreamChoice:
    """Choice in a streaming response."""

    delta: StreamDelta
    finish_reason: Optional[str] = None


@dataclass
class StreamChunk:
    """Streaming chunk from router."""

    id: str
    choices: List[StreamChoice]


# Graph Visualization Types

@dataclass
class GraphNodeData:
    """Data associated with a graph node."""

    status: str  # 'new', 'latest', 'older', 'expiring', 'forgotten'
    created_at: str
    content: Optional[str] = None
    expires_at: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class GraphNode:
    """Node in the memory graph."""

    id: str
    type: str  # 'memory', 'document', 'entity'
    label: str
    data: GraphNodeData


@dataclass
class GraphEdge:
    """Edge in the memory graph."""

    id: str
    source: str
    target: str
    type: str  # 'extends', 'updates', 'derives', 'similarity'
    label: str
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class GraphMetadata:
    """Graph metadata and statistics."""

    total_nodes: int
    memory_count: int
    document_count: int
    entity_count: int
    total_edges: int
    relationship_count: int
    similarity_count: int


@dataclass
class PaginationInfo:
    """Pagination information."""

    has_more: bool
    next_cursor: Optional[str] = None
    total_count: Optional[int] = None


@dataclass
class GraphData:
    """Complete graph data structure."""

    nodes: List[GraphNode]
    edges: List[GraphEdge]
    metadata: GraphMetadata
    pagination: PaginationInfo


@dataclass
class NodeDetails:
    """Detailed information for a specific node."""

    node: GraphNode
    edges: List[GraphEdge]
    connected_nodes: List[GraphNode]


@dataclass
class GetGraphRequest:
    """Request to get graph data."""

    space_id: str
    cursor: Optional[str] = None
    limit: Optional[int] = None
    node_types: Optional[List[str]] = None
    relationship_types: Optional[List[str]] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


@dataclass
class GetNodeDetailsRequest:
    """Request to get node details."""

    node_id: str


@dataclass
class GetNodeEdgesRequest:
    """Request to get node edges."""

    node_id: str
    edge_types: Optional[List[str]] = None


@dataclass
class GetNodeEdgesResponse:
    """Response with node edges."""

    edges: List[GraphEdge]
    connected_nodes: List[GraphNode]
