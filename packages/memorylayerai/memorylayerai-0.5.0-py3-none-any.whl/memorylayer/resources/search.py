"""Search resource for the MemoryLayer SDK."""

from ..http_client import HTTPClient, AsyncHTTPClient
from ..types import SearchRequest, SearchResponse, SearchResult, Memory
from ..exceptions import ValidationError


class SearchResource:
    """Synchronous search operations."""

    def __init__(self, http_client: HTTPClient):
        self._http_client = http_client

    def search(
        self,
        query: str,
        project_id: str,
        limit: int = None,
        threshold: float = None,
        filter: dict = None,
        enable_query_rewriting: bool = None,
        enable_entity_expansion: bool = None,
        enable_graph_connectivity: bool = None,
        enable_semantic_dedup: bool = None,
        reranking_strategy: str = None,
        fusion_weights: dict = None,
    ) -> SearchResponse:
        """Search memories using the unified /v1/search endpoint with hybrid retrieval.

        This uses the app's full retrieval pipeline with:
        - Vector similarity search
        - BM25 keyword search
        - Recency scoring
        - Graph connectivity (optional)
        - Entity expansion (optional)
        - LLM/Cross-encoder reranking (optional)

        Args:
            query: Search query string
            project_id: Project ID to search in
            limit: Maximum number of results (default: 20)
            threshold: Minimum relevance score threshold (0-1)
            filter: Filter criteria for search
            enable_query_rewriting: Enable query rewriting (default: False)
            enable_entity_expansion: Enable entity expansion search (default: False)
            enable_graph_connectivity: Enable graph connectivity search (default: False)
            enable_semantic_dedup: Enable semantic deduplication (default: False)
            reranking_strategy: Reranking strategy: 'none', 'cross-encoder', 'llm' (default: 'cross-encoder')
            fusion_weights: Custom fusion weights dict with keys: vector, bm25, recency, entity, graph

        Returns:
            SearchResponse with results and metadata
        """
        if not query or not query.strip():
            raise ValidationError(
                "Search query cannot be empty",
                [{"field": "query", "message": "Query is required and cannot be empty"}],
            )

        if not project_id or not project_id.strip():
            raise ValidationError(
                "Project ID is required",
                [{"field": "project_id", "message": "Project ID is required"}],
            )

        # Build request body matching the app's POST /v1/search endpoint
        body = {
            "query": query,
            "project_id": project_id,
        }

        if limit is not None:
            body["limit"] = limit

        # Match the app's rerank_strategy parameter
        if reranking_strategy is not None:
            body["rerank_strategy"] = reranking_strategy
        else:
            body["rerank_strategy"] = "cross-encoder"  # App's default

        # Include text format for LLM-ready output
        body["include_text_format"] = True

        # Use POST method to match the app's endpoint
        data = self._http_client.request("POST", "/v1/search", body=body)

        # Parse the response from memory_pack format
        memory_pack = data.get("memory_pack", {})
        results = []

        # Extract memories from the memory pack structure
        for memory_type in ["facts", "preferences", "entities", "sources"]:
            for item in memory_pack.get(memory_type, []):
                results.append(SearchResult(
                    memory=Memory(**item),
                    score=item.get("score", 1.0),
                    highlights=item.get("highlights", [])
                ))

        return SearchResponse(
            results=results,
            total=len(results)
        )


class AsyncSearchResource:
    """Asynchronous search operations."""

    def __init__(self, http_client: AsyncHTTPClient):
        self._http_client = http_client

    async def search(
        self,
        query: str,
        project_id: str,
        limit: int = None,
        threshold: float = None,
        filter: dict = None,
        enable_query_rewriting: bool = None,
        enable_entity_expansion: bool = None,
        enable_graph_connectivity: bool = None,
        enable_semantic_dedup: bool = None,
        reranking_strategy: str = None,
        fusion_weights: dict = None,
    ) -> SearchResponse:
        """Search memories using the unified /v1/search endpoint with hybrid retrieval.

        This uses the app's full retrieval pipeline with:
        - Vector similarity search
        - BM25 keyword search
        - Recency scoring
        - Graph connectivity (optional)
        - Entity expansion (optional)
        - LLM/Cross-encoder reranking (optional)

        Args:
            query: Search query string
            project_id: Project ID to search in
            limit: Maximum number of results (default: 20)
            threshold: Minimum relevance score threshold (0-1)
            filter: Filter criteria for search
            enable_query_rewriting: Enable query rewriting (default: False)
            enable_entity_expansion: Enable entity expansion search (default: False)
            enable_graph_connectivity: Enable graph connectivity search (default: False)
            enable_semantic_dedup: Enable semantic deduplication (default: False)
            reranking_strategy: Reranking strategy: 'none', 'cross-encoder', 'llm' (default: 'cross-encoder')
            fusion_weights: Custom fusion weights dict with keys: vector, bm25, recency, entity, graph

        Returns:
            SearchResponse with results and metadata
        """
        if not query or not query.strip():
            raise ValidationError(
                "Search query cannot be empty",
                [{"field": "query", "message": "Query is required and cannot be empty"}],
            )

        if not project_id or not project_id.strip():
            raise ValidationError(
                "Project ID is required",
                [{"field": "project_id", "message": "Project ID is required"}],
            )

        # Build request body matching the app's POST /v1/search endpoint
        body = {
            "query": query,
            "project_id": project_id,
        }

        if limit is not None:
            body["limit"] = limit

        # Match the app's rerank_strategy parameter
        if reranking_strategy is not None:
            body["rerank_strategy"] = reranking_strategy
        else:
            body["rerank_strategy"] = "cross-encoder"  # App's default

        # Include text format for LLM-ready output
        body["include_text_format"] = True

        # Use POST method to match the app's endpoint
        data = await self._http_client.request("POST", "/v1/search", body=body)

        # Parse the response from memory_pack format
        memory_pack = data.get("memory_pack", {})
        results = []

        # Extract memories from the memory pack structure
        for memory_type in ["facts", "preferences", "entities", "sources"]:
            for item in memory_pack.get(memory_type, []):
                results.append(SearchResult(
                    memory=Memory(**item),
                    score=item.get("score", 1.0),
                    highlights=item.get("highlights", [])
                ))

        return SearchResponse(
            results=results,
            total=len(results)
        )
