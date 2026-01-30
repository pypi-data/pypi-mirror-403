"""
MemoryLayer Python SDK

Official Python SDK for integrating MemoryLayer into your applications.
"""

from .client import MemoryLayerClient, AsyncMemoryLayerClient, ClientConfig
from .exceptions import (
    MemoryLayerError,
    AuthenticationError,
    RateLimitError,
    ValidationError,
    NetworkError,
    APIError,
)
from .types import (
    Memory,
    CreateMemoryRequest,
    UpdateMemoryRequest,
    ListMemoriesRequest,
    SearchRequest,
    SearchResult,
    SearchResponse,
    IngestFileRequest,
    IngestTextRequest,
    IngestResponse,
    Message,
    RouterRequest,
    RouterResponse,
    Usage,
    Choice,
    StreamChunk,
    StreamChoice,
    StreamDelta,
)

__version__ = "0.5.0"

__all__ = [
    # Client
    "MemoryLayerClient",
    "AsyncMemoryLayerClient",
    "ClientConfig",
    # Exceptions
    "MemoryLayerError",
    "AuthenticationError",
    "RateLimitError",
    "ValidationError",
    "NetworkError",
    "APIError",
    # Types
    "Memory",
    "CreateMemoryRequest",
    "UpdateMemoryRequest",
    "ListMemoriesRequest",
    "SearchRequest",
    "SearchResult",
    "SearchResponse",
    "IngestFileRequest",
    "IngestTextRequest",
    "IngestResponse",
    "Message",
    "RouterRequest",
    "RouterResponse",
    "Usage",
    "Choice",
    "StreamChunk",
    "StreamChoice",
    "StreamDelta",
]
