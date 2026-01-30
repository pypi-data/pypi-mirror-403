"""Graph resource for the MemoryLayer SDK."""

from typing import AsyncGenerator, Generator, List, Optional

from ..http_client import HTTPClient, AsyncHTTPClient
from ..types import (
    GraphData,
    GraphNode,
    GraphNodeData,
    GraphEdge,
    GraphMetadata,
    PaginationInfo,
    NodeDetails,
    GetGraphRequest,
    GetNodeDetailsRequest,
    GetNodeEdgesRequest,
    GetNodeEdgesResponse,
)
from ..exceptions import ValidationError


class GraphResource:
    """Synchronous graph visualization operations.
    
    Provides methods to fetch graph data (nodes and edges) for visualization.
    
    Requirements: 6.1, 6.2, 6.3, 6.4
    """

    def __init__(self, http_client: HTTPClient):
        self._http_client = http_client

    def get_graph(self, request: GetGraphRequest) -> GraphData:
        """Get graph data for a space/project.
        
        Fetches nodes (memories, documents, entities) and edges (relationships)
        for visualization. Supports pagination and filtering.
        
        Args:
            request: Graph data request with filters
            
        Returns:
            Graph data with nodes, edges, metadata, and pagination
            
        Example:
            >>> graph_data = client.graph.get_graph(GetGraphRequest(
            ...     space_id='project-123',
            ...     limit=100,
            ...     node_types=['memory', 'document'],
            ...     relationship_types=['extends', 'updates']
            ... ))
            >>> print(f"Found {len(graph_data.nodes)} nodes")
            
        Requirements: 6.1
        """
        # Validate request
        if not request.space_id or not request.space_id.strip():
            raise ValidationError(
                "Space ID is required",
                [{"field": "space_id", "message": "Space ID is required"}],
            )

        # Build query parameters
        query = {}

        if request.cursor:
            query["cursor"] = request.cursor

        if request.limit is not None:
            query["limit"] = str(request.limit)

        if request.node_types:
            query["nodeTypes"] = ",".join(request.node_types)

        if request.relationship_types:
            query["relationshipTypes"] = ",".join(request.relationship_types)

        if request.start_date:
            query["startDate"] = request.start_date

        if request.end_date:
            query["endDate"] = request.end_date

        data = self._http_client.request(
            "GET",
            f"/v1/graph/spaces/{request.space_id}",
            query=query,
        )

        return self._parse_graph_data(data)

    def get_node_details(self, request: GetNodeDetailsRequest) -> NodeDetails:
        """Get detailed information for a specific node.
        
        Fetches node data, connected edges, and neighboring nodes.
        
        Args:
            request: Node details request
            
        Returns:
            Node details with edges and connected nodes
            
        Example:
            >>> details = client.graph.get_node_details(GetNodeDetailsRequest(
            ...     node_id='memory-456'
            ... ))
            >>> print(f"Node: {details.node.label}")
            >>> print(f"Connected to {len(details.connected_nodes)} nodes")
            
        Requirements: 6.2
        """
        # Validate request
        if not request.node_id or not request.node_id.strip():
            raise ValidationError(
                "Node ID is required",
                [{"field": "node_id", "message": "Node ID is required"}],
            )

        data = self._http_client.request(
            "GET",
            f"/v1/graph/nodes/{request.node_id}",
        )

        return self._parse_node_details(data)

    def get_node_edges(self, request: GetNodeEdgesRequest) -> GetNodeEdgesResponse:
        """Get edges connected to a specific node.
        
        Fetches edges and connected nodes, optionally filtered by edge type.
        
        Args:
            request: Node edges request
            
        Returns:
            Edges and connected nodes
            
        Example:
            >>> edges = client.graph.get_node_edges(GetNodeEdgesRequest(
            ...     node_id='memory-456',
            ...     edge_types=['extends', 'updates']
            ... ))
            >>> print(f"Found {len(edges.edges)} edges")
            
        Requirements: 6.3
        """
        # Validate request
        if not request.node_id or not request.node_id.strip():
            raise ValidationError(
                "Node ID is required",
                [{"field": "node_id", "message": "Node ID is required"}],
            )

        # Build query parameters
        query = {}

        if request.edge_types:
            query["edgeTypes"] = ",".join(request.edge_types)

        data = self._http_client.request(
            "GET",
            f"/v1/graph/nodes/{request.node_id}/edges",
            query=query,
        )

        return self._parse_node_edges_response(data)

    def get_all_graph_pages(self, request: GetGraphRequest) -> Generator[GraphData, None, None]:
        """Get all graph pages using iteration.
        
        Automatically handles pagination to fetch all nodes and edges.
        Yields each page of results as they are fetched.
        
        Args:
            request: Initial graph request (without cursor)
            
        Yields:
            Graph data for each page
            
        Example:
            >>> for page in client.graph.get_all_graph_pages(GetGraphRequest(space_id='project-123')):
            ...     print(f"Page has {len(page.nodes)} nodes")
            ...     # Process nodes...
            
        Example:
            >>> # Collect all nodes
            >>> all_nodes = []
            >>> for page in client.graph.get_all_graph_pages(GetGraphRequest(space_id='project-123')):
            ...     all_nodes.extend(page.nodes)
            >>> print(f"Total nodes: {len(all_nodes)}")
            
        Requirements: 6.4
        """
        cursor = None
        has_more = True

        while has_more:
            # Create request with current cursor
            page_request = GetGraphRequest(
                space_id=request.space_id,
                cursor=cursor,
                limit=request.limit,
                node_types=request.node_types,
                relationship_types=request.relationship_types,
                start_date=request.start_date,
                end_date=request.end_date,
            )

            page = self.get_graph(page_request)
            yield page

            cursor = page.pagination.next_cursor
            has_more = page.pagination.has_more

    def _parse_graph_data(self, data: dict) -> GraphData:
        """Parse graph data from API response."""
        return GraphData(
            nodes=[self._parse_node(n) for n in data["nodes"]],
            edges=[self._parse_edge(e) for e in data["edges"]],
            metadata=self._parse_metadata(data["metadata"]),
            pagination=self._parse_pagination(data["pagination"]),
        )

    def _parse_node(self, data: dict) -> GraphNode:
        """Parse a graph node from API response."""
        return GraphNode(
            id=data["id"],
            type=data["type"],
            label=data["label"],
            data=GraphNodeData(
                status=data["data"]["status"],
                created_at=data["data"]["createdAt"],
                content=data["data"].get("content"),
                expires_at=data["data"].get("expiresAt"),
                metadata=data["data"].get("metadata"),
            ),
        )

    def _parse_edge(self, data: dict) -> GraphEdge:
        """Parse a graph edge from API response."""
        return GraphEdge(
            id=data["id"],
            source=data["source"],
            target=data["target"],
            type=data["type"],
            label=data["label"],
            metadata=data.get("metadata"),
        )

    def _parse_metadata(self, data: dict) -> GraphMetadata:
        """Parse graph metadata from API response."""
        return GraphMetadata(
            total_nodes=data["totalNodes"],
            memory_count=data["memoryCount"],
            document_count=data["documentCount"],
            entity_count=data["entityCount"],
            total_edges=data["totalEdges"],
            relationship_count=data["relationshipCount"],
            similarity_count=data["similarityCount"],
        )

    def _parse_pagination(self, data: dict) -> PaginationInfo:
        """Parse pagination info from API response."""
        return PaginationInfo(
            has_more=data["hasMore"],
            next_cursor=data.get("nextCursor"),
            total_count=data.get("totalCount"),
        )

    def _parse_node_details(self, data: dict) -> NodeDetails:
        """Parse node details from API response."""
        return NodeDetails(
            node=self._parse_node(data["node"]),
            edges=[self._parse_edge(e) for e in data["edges"]],
            connected_nodes=[self._parse_node(n) for n in data["connectedNodes"]],
        )

    def _parse_node_edges_response(self, data: dict) -> GetNodeEdgesResponse:
        """Parse node edges response from API response."""
        return GetNodeEdgesResponse(
            edges=[self._parse_edge(e) for e in data["edges"]],
            connected_nodes=[self._parse_node(n) for n in data["connectedNodes"]],
        )


class AsyncGraphResource:
    """Asynchronous graph visualization operations.
    
    Provides async methods to fetch graph data (nodes and edges) for visualization.
    
    Requirements: 6.1, 6.2, 6.3, 6.4
    """

    def __init__(self, http_client: AsyncHTTPClient):
        self._http_client = http_client

    async def get_graph(self, request: GetGraphRequest) -> GraphData:
        """Get graph data for a space/project (async).
        
        Fetches nodes (memories, documents, entities) and edges (relationships)
        for visualization. Supports pagination and filtering.
        
        Args:
            request: Graph data request with filters
            
        Returns:
            Graph data with nodes, edges, metadata, and pagination
            
        Requirements: 6.1
        """
        # Validate request
        if not request.space_id or not request.space_id.strip():
            raise ValidationError(
                "Space ID is required",
                [{"field": "space_id", "message": "Space ID is required"}],
            )

        # Build query parameters
        query = {}

        if request.cursor:
            query["cursor"] = request.cursor

        if request.limit is not None:
            query["limit"] = str(request.limit)

        if request.node_types:
            query["nodeTypes"] = ",".join(request.node_types)

        if request.relationship_types:
            query["relationshipTypes"] = ",".join(request.relationship_types)

        if request.start_date:
            query["startDate"] = request.start_date

        if request.end_date:
            query["endDate"] = request.end_date

        data = await self._http_client.request(
            "GET",
            f"/v1/graph/spaces/{request.space_id}",
            query=query,
        )

        return self._parse_graph_data(data)

    async def get_node_details(self, request: GetNodeDetailsRequest) -> NodeDetails:
        """Get detailed information for a specific node (async).
        
        Fetches node data, connected edges, and neighboring nodes.
        
        Args:
            request: Node details request
            
        Returns:
            Node details with edges and connected nodes
            
        Requirements: 6.2
        """
        # Validate request
        if not request.node_id or not request.node_id.strip():
            raise ValidationError(
                "Node ID is required",
                [{"field": "node_id", "message": "Node ID is required"}],
            )

        data = await self._http_client.request(
            "GET",
            f"/v1/graph/nodes/{request.node_id}",
        )

        return self._parse_node_details(data)

    async def get_node_edges(self, request: GetNodeEdgesRequest) -> GetNodeEdgesResponse:
        """Get edges connected to a specific node (async).
        
        Fetches edges and connected nodes, optionally filtered by edge type.
        
        Args:
            request: Node edges request
            
        Returns:
            Edges and connected nodes
            
        Requirements: 6.3
        """
        # Validate request
        if not request.node_id or not request.node_id.strip():
            raise ValidationError(
                "Node ID is required",
                [{"field": "node_id", "message": "Node ID is required"}],
            )

        # Build query parameters
        query = {}

        if request.edge_types:
            query["edgeTypes"] = ",".join(request.edge_types)

        data = await self._http_client.request(
            "GET",
            f"/v1/graph/nodes/{request.node_id}/edges",
            query=query,
        )

        return self._parse_node_edges_response(data)

    async def get_all_graph_pages(self, request: GetGraphRequest) -> AsyncGenerator[GraphData, None]:
        """Get all graph pages using async iteration.
        
        Automatically handles pagination to fetch all nodes and edges.
        Yields each page of results as they are fetched.
        
        Args:
            request: Initial graph request (without cursor)
            
        Yields:
            Graph data for each page
            
        Example:
            >>> async for page in client.graph.get_all_graph_pages(GetGraphRequest(space_id='project-123')):
            ...     print(f"Page has {len(page.nodes)} nodes")
            ...     # Process nodes...
            
        Requirements: 6.4
        """
        cursor = None
        has_more = True

        while has_more:
            # Create request with current cursor
            page_request = GetGraphRequest(
                space_id=request.space_id,
                cursor=cursor,
                limit=request.limit,
                node_types=request.node_types,
                relationship_types=request.relationship_types,
                start_date=request.start_date,
                end_date=request.end_date,
            )

            page = await self.get_graph(page_request)
            yield page

            cursor = page.pagination.next_cursor
            has_more = page.pagination.has_more

    def _parse_graph_data(self, data: dict) -> GraphData:
        """Parse graph data from API response."""
        return GraphData(
            nodes=[self._parse_node(n) for n in data["nodes"]],
            edges=[self._parse_edge(e) for e in data["edges"]],
            metadata=self._parse_metadata(data["metadata"]),
            pagination=self._parse_pagination(data["pagination"]),
        )

    def _parse_node(self, data: dict) -> GraphNode:
        """Parse a graph node from API response."""
        return GraphNode(
            id=data["id"],
            type=data["type"],
            label=data["label"],
            data=GraphNodeData(
                status=data["data"]["status"],
                created_at=data["data"]["createdAt"],
                content=data["data"].get("content"),
                expires_at=data["data"].get("expiresAt"),
                metadata=data["data"].get("metadata"),
            ),
        )

    def _parse_edge(self, data: dict) -> GraphEdge:
        """Parse a graph edge from API response."""
        return GraphEdge(
            id=data["id"],
            source=data["source"],
            target=data["target"],
            type=data["type"],
            label=data["label"],
            metadata=data.get("metadata"),
        )

    def _parse_metadata(self, data: dict) -> GraphMetadata:
        """Parse graph metadata from API response."""
        return GraphMetadata(
            total_nodes=data["totalNodes"],
            memory_count=data["memoryCount"],
            document_count=data["documentCount"],
            entity_count=data["entityCount"],
            total_edges=data["totalEdges"],
            relationship_count=data["relationshipCount"],
            similarity_count=data["similarityCount"],
        )

    def _parse_pagination(self, data: dict) -> PaginationInfo:
        """Parse pagination info from API response."""
        return PaginationInfo(
            has_more=data["hasMore"],
            next_cursor=data.get("nextCursor"),
            total_count=data.get("totalCount"),
        )

    def _parse_node_details(self, data: dict) -> NodeDetails:
        """Parse node details from API response."""
        return NodeDetails(
            node=self._parse_node(data["node"]),
            edges=[self._parse_edge(e) for e in data["edges"]],
            connected_nodes=[self._parse_node(n) for n in data["connectedNodes"]],
        )

    def _parse_node_edges_response(self, data: dict) -> GetNodeEdgesResponse:
        """Parse node edges response from API response."""
        return GetNodeEdgesResponse(
            edges=[self._parse_edge(e) for e in data["edges"]],
            connected_nodes=[self._parse_node(n) for n in data["connectedNodes"]],
        )
