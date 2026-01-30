"""MemoryLayer SDK client."""

import os
from typing import Optional

from .http_client import HTTPClient, AsyncHTTPClient, ClientConfig as HTTPClientConfig
from .exceptions import ValidationError
from .resources.memories import MemoriesResource, AsyncMemoriesResource
from .resources.search import SearchResource, AsyncSearchResource
from .resources.ingest import IngestResource, AsyncIngestResource
from .resources.router import RouterResource, AsyncRouterResource
from .resources.graph import GraphResource, AsyncGraphResource


class ClientConfig:
    """Configuration for the MemoryLayer client."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.memorylayer.com",
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        headers: Optional[dict] = None,
        logger: Optional[any] = None,
    ):
        self.api_key = api_key or os.environ.get("MEMORYLAYER_API_KEY")
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.headers = headers
        self.logger = logger


class MemoryLayerClient:
    """Synchronous MemoryLayer SDK client."""

    def __init__(self, config: Optional[ClientConfig] = None, **kwargs):
        if config is None:
            config = ClientConfig(**kwargs)

        if not config.api_key:
            raise ValidationError(
                "API key is required. Provide it via config or MEMORYLAYER_API_KEY environment variable.",
                [{"field": "api_key", "message": "API key is required"}],
            )

        if not isinstance(config.api_key, str) or not config.api_key.strip():
            raise ValidationError(
                "API key must be a non-empty string",
                [{"field": "api_key", "message": "API key must be a non-empty string"}],
            )

        http_config = HTTPClientConfig(
            api_key=config.api_key,
            base_url=config.base_url,
            timeout=config.timeout,
            max_retries=config.max_retries,
            retry_delay=config.retry_delay,
            headers=config.headers,
            logger=config.logger,
        )

        self._http_client = HTTPClient(http_config)
        self._memories = MemoriesResource(self._http_client)
        self._search = SearchResource(self._http_client)
        self._ingest = IngestResource(self._http_client)
        self._router = RouterResource(self._http_client)
        self._graph = GraphResource(self._http_client)

    @property
    def memories(self) -> MemoriesResource:
        """Access memory operations."""
        return self._memories

    @property
    def search(self) -> SearchResource:
        """Access search operations."""
        return self._search

    @property
    def ingest(self) -> IngestResource:
        """Access ingestion operations."""
        return self._ingest

    @property
    def router(self) -> RouterResource:
        """Access router operations."""
        return self._router

    @property
    def graph(self) -> GraphResource:
        """Access graph visualization operations."""
        return self._graph

    def close(self):
        """Close the HTTP client."""
        self._http_client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class AsyncMemoryLayerClient:
    """Asynchronous MemoryLayer SDK client."""

    def __init__(self, config: Optional[ClientConfig] = None, **kwargs):
        if config is None:
            config = ClientConfig(**kwargs)

        if not config.api_key:
            raise ValidationError(
                "API key is required. Provide it via config or MEMORYLAYER_API_KEY environment variable.",
                [{"field": "api_key", "message": "API key is required"}],
            )

        if not isinstance(config.api_key, str) or not config.api_key.strip():
            raise ValidationError(
                "API key must be a non-empty string",
                [{"field": "api_key", "message": "API key must be a non-empty string"}],
            )

        http_config = HTTPClientConfig(
            api_key=config.api_key,
            base_url=config.base_url,
            timeout=config.timeout,
            max_retries=config.max_retries,
            retry_delay=config.retry_delay,
            headers=config.headers,
            logger=config.logger,
        )

        self._http_client = AsyncHTTPClient(http_config)
        self._memories = AsyncMemoriesResource(self._http_client)
        self._search = AsyncSearchResource(self._http_client)
        self._ingest = AsyncIngestResource(self._http_client)
        self._router = AsyncRouterResource(self._http_client)
        self._graph = AsyncGraphResource(self._http_client)

    @property
    def memories(self) -> AsyncMemoriesResource:
        """Access async memory operations."""
        return self._memories

    @property
    def search(self) -> AsyncSearchResource:
        """Access async search operations."""
        return self._search

    @property
    def ingest(self) -> AsyncIngestResource:
        """Access async ingestion operations."""
        return self._ingest

    @property
    def router(self) -> AsyncRouterResource:
        """Access async router operations."""
        return self._router

    @property
    def graph(self) -> AsyncGraphResource:
        """Access async graph visualization operations."""
        return self._graph

    async def close(self):
        """Close the async HTTP client."""
        await self._http_client.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
