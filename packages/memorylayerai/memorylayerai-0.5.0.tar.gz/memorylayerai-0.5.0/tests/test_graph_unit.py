"""Unit tests for Python SDK graph methods.

These are true unit tests that mock the HTTP client.
They test the GraphResource class in isolation.

Requirements: 6.1, 6.2, 6.3
"""

import pytest
from unittest.mock import Mock, AsyncMock

from memorylayer.resources.graph import GraphResource, AsyncGraphResource
from memorylayer.types import (
    GetGraphRequest,
    GetNodeDetailsRequest,
    GetNodeEdgesRequest,
    GraphData,
    GraphNode,
    GraphNodeData,
    GraphEdge,
    GraphMetadata,
    PaginationInfo,
    NodeDetails,
    GetNodeEdgesResponse,
)
from memorylayer.exceptions import ValidationError


def create_empty_graph_data() -> dict:
    """Helper to create empty graph data response."""
    return {
        "nodes": [],
        "edges": [],
        "metadata": {
            "totalNodes": 0,
            "memoryCount": 0,
            "documentCount": 0,
            "entityCount": 0,
            "totalEdges": 0,
            "relationshipCount": 0,
            "similarityCount": 0,
        },
        "pagination": {
            "hasMore": False,
            "nextCursor": None,
        },
    }


def create_test_node_dict(node_id: str, label: str) -> dict:
    """Helper to create a test node dictionary."""
    return {
        "id": node_id,
        "type": "memory",
        "label": label,
        "data": {
            "status": "latest",
            "createdAt": "2026-01-20T00:00:00Z",
            "content": f"Content {node_id}",
        },
    }


class TestGraphResource:
    """Unit tests for GraphResource."""

    def test_get_graph_minimal_parameters(self):
        """Test get_graph with minimal parameters."""
        mock_response = create_empty_graph_data()
        mock_http_client = Mock()
        mock_http_client.request.return_value = mock_response

        graph_resource = GraphResource(mock_http_client)
        result = graph_resource.get_graph(GetGraphRequest(space_id="test-space-123"))

        mock_http_client.request.assert_called_once_with(
            "GET",
            "/v1/graph/spaces/test-space-123",
            query={},
        )

        assert isinstance(result, GraphData)
        assert len(result.nodes) == 0
        assert len(result.edges) == 0

    def test_get_graph_with_cursor(self):
        """Test get_graph includes cursor in query parameters."""
        mock_response = create_empty_graph_data()
        mock_http_client = Mock()
        mock_http_client.request.return_value = mock_response

        graph_resource = GraphResource(mock_http_client)
        graph_resource.get_graph(
            GetGraphRequest(space_id="test-space-123", cursor="cursor-abc")
        )

        mock_http_client.request.assert_called_once_with(
            "GET",
            "/v1/graph/spaces/test-space-123",
            query={"cursor": "cursor-abc"},
        )

    def test_get_graph_with_limit(self):
        """Test get_graph includes limit in query parameters."""
        mock_response = create_empty_graph_data()
        mock_http_client = Mock()
        mock_http_client.request.return_value = mock_response

        graph_resource = GraphResource(mock_http_client)
        graph_resource.get_graph(GetGraphRequest(space_id="test-space-123", limit=50))

        mock_http_client.request.assert_called_once_with(
            "GET",
            "/v1/graph/spaces/test-space-123",
            query={"limit": "50"},
        )

    def test_get_graph_with_node_types(self):
        """Test get_graph includes node types in query parameters."""
        mock_response = create_empty_graph_data()
        mock_http_client = Mock()
        mock_http_client.request.return_value = mock_response

        graph_resource = GraphResource(mock_http_client)
        graph_resource.get_graph(
            GetGraphRequest(space_id="test-space-123", node_types=["memory", "document"])
        )

        mock_http_client.request.assert_called_once_with(
            "GET",
            "/v1/graph/spaces/test-space-123",
            query={"nodeTypes": "memory,document"},
        )

    def test_get_graph_with_relationship_types(self):
        """Test get_graph includes relationship types in query parameters."""
        mock_response = create_empty_graph_data()
        mock_http_client = Mock()
        mock_http_client.request.return_value = mock_response

        graph_resource = GraphResource(mock_http_client)
        graph_resource.get_graph(
            GetGraphRequest(
                space_id="test-space-123", relationship_types=["extends", "updates"]
            )
        )

        mock_http_client.request.assert_called_once_with(
            "GET",
            "/v1/graph/spaces/test-space-123",
            query={"relationshipTypes": "extends,updates"},
        )

    def test_get_graph_with_date_range(self):
        """Test get_graph includes date range in query parameters."""
        mock_response = create_empty_graph_data()
        mock_http_client = Mock()
        mock_http_client.request.return_value = mock_response

        graph_resource = GraphResource(mock_http_client)
        graph_resource.get_graph(
            GetGraphRequest(
                space_id="test-space-123",
                start_date="2026-01-01T00:00:00Z",
                end_date="2026-01-31T23:59:59Z",
            )
        )

        mock_http_client.request.assert_called_once_with(
            "GET",
            "/v1/graph/spaces/test-space-123",
            query={
                "startDate": "2026-01-01T00:00:00Z",
                "endDate": "2026-01-31T23:59:59Z",
            },
        )

    def test_get_graph_with_all_parameters(self):
        """Test get_graph includes all parameters when provided."""
        mock_response = create_empty_graph_data()
        mock_http_client = Mock()
        mock_http_client.request.return_value = mock_response

        graph_resource = GraphResource(mock_http_client)
        graph_resource.get_graph(
            GetGraphRequest(
                space_id="test-space-123",
                cursor="cursor-abc",
                limit=50,
                node_types=["memory"],
                relationship_types=["extends"],
                start_date="2026-01-01T00:00:00Z",
                end_date="2026-01-31T23:59:59Z",
            )
        )

        mock_http_client.request.assert_called_once_with(
            "GET",
            "/v1/graph/spaces/test-space-123",
            query={
                "cursor": "cursor-abc",
                "limit": "50",
                "nodeTypes": "memory",
                "relationshipTypes": "extends",
                "startDate": "2026-01-01T00:00:00Z",
                "endDate": "2026-01-31T23:59:59Z",
            },
        )

    def test_get_graph_missing_space_id(self):
        """Test get_graph raises ValidationError for missing space_id."""
        mock_http_client = Mock()
        graph_resource = GraphResource(mock_http_client)

        with pytest.raises(ValidationError) as exc_info:
            graph_resource.get_graph(GetGraphRequest(space_id=""))

        assert "Space ID is required" in str(exc_info.value)

    def test_get_graph_whitespace_space_id(self):
        """Test get_graph raises ValidationError for whitespace space_id."""
        mock_http_client = Mock()
        graph_resource = GraphResource(mock_http_client)

        with pytest.raises(ValidationError) as exc_info:
            graph_resource.get_graph(GetGraphRequest(space_id="   "))

        assert "Space ID is required" in str(exc_info.value)

    def test_get_node_details(self):
        """Test get_node_details makes correct API request."""
        mock_response = {
            "node": create_test_node_dict("node-123", "Test Node"),
            "edges": [],
            "connectedNodes": [],
        }
        mock_http_client = Mock()
        mock_http_client.request.return_value = mock_response

        graph_resource = GraphResource(mock_http_client)
        result = graph_resource.get_node_details(
            GetNodeDetailsRequest(node_id="node-123")
        )

        mock_http_client.request.assert_called_once_with(
            "GET",
            "/v1/graph/nodes/node-123",
        )

        assert isinstance(result, NodeDetails)
        assert result.node.id == "node-123"

    def test_get_node_details_missing_node_id(self):
        """Test get_node_details raises ValidationError for missing node_id."""
        mock_http_client = Mock()
        graph_resource = GraphResource(mock_http_client)

        with pytest.raises(ValidationError) as exc_info:
            graph_resource.get_node_details(GetNodeDetailsRequest(node_id=""))

        assert "Node ID is required" in str(exc_info.value)

    def test_get_node_edges_without_filters(self):
        """Test get_node_edges without filters."""
        mock_response = {
            "edges": [],
            "connectedNodes": [],
        }
        mock_http_client = Mock()
        mock_http_client.request.return_value = mock_response

        graph_resource = GraphResource(mock_http_client)
        result = graph_resource.get_node_edges(
            GetNodeEdgesRequest(node_id="node-123")
        )

        mock_http_client.request.assert_called_once_with(
            "GET",
            "/v1/graph/nodes/node-123/edges",
            query={},
        )

        assert isinstance(result, GetNodeEdgesResponse)
        assert len(result.edges) == 0

    def test_get_node_edges_with_edge_types(self):
        """Test get_node_edges includes edge types in query parameters."""
        mock_response = {
            "edges": [],
            "connectedNodes": [],
        }
        mock_http_client = Mock()
        mock_http_client.request.return_value = mock_response

        graph_resource = GraphResource(mock_http_client)
        graph_resource.get_node_edges(
            GetNodeEdgesRequest(node_id="node-123", edge_types=["extends", "updates"])
        )

        mock_http_client.request.assert_called_once_with(
            "GET",
            "/v1/graph/nodes/node-123/edges",
            query={"edgeTypes": "extends,updates"},
        )

    def test_get_node_edges_missing_node_id(self):
        """Test get_node_edges raises ValidationError for missing node_id."""
        mock_http_client = Mock()
        graph_resource = GraphResource(mock_http_client)

        with pytest.raises(ValidationError) as exc_info:
            graph_resource.get_node_edges(GetNodeEdgesRequest(node_id=""))

        assert "Node ID is required" in str(exc_info.value)

    def test_get_all_graph_pages(self):
        """Test get_all_graph_pages yields all pages."""
        page1 = {
            "nodes": [create_test_node_dict("node-1", "Node 1")],
            "edges": [],
            "metadata": {
                "totalNodes": 3,
                "memoryCount": 3,
                "documentCount": 0,
                "entityCount": 0,
                "totalEdges": 0,
                "relationshipCount": 0,
                "similarityCount": 0,
            },
            "pagination": {
                "hasMore": True,
                "nextCursor": "cursor-2",
            },
        }

        page2 = {
            "nodes": [create_test_node_dict("node-2", "Node 2")],
            "edges": [],
            "metadata": {
                "totalNodes": 3,
                "memoryCount": 3,
                "documentCount": 0,
                "entityCount": 0,
                "totalEdges": 0,
                "relationshipCount": 0,
                "similarityCount": 0,
            },
            "pagination": {
                "hasMore": True,
                "nextCursor": "cursor-3",
            },
        }

        page3 = {
            "nodes": [create_test_node_dict("node-3", "Node 3")],
            "edges": [],
            "metadata": {
                "totalNodes": 3,
                "memoryCount": 3,
                "documentCount": 0,
                "entityCount": 0,
                "totalEdges": 0,
                "relationshipCount": 0,
                "similarityCount": 0,
            },
            "pagination": {
                "hasMore": False,
                "nextCursor": None,
            },
        }

        mock_http_client = Mock()
        mock_http_client.request.side_effect = [page1, page2, page3]

        graph_resource = GraphResource(mock_http_client)
        pages = list(
            graph_resource.get_all_graph_pages(GetGraphRequest(space_id="test-space-123"))
        )

        assert len(pages) == 3
        assert len(pages[0].nodes) == 1
        assert len(pages[1].nodes) == 1
        assert len(pages[2].nodes) == 1

        # Verify correct API calls
        assert mock_http_client.request.call_count == 3

    def test_get_all_graph_pages_single_page(self):
        """Test get_all_graph_pages handles single page result."""
        page1 = create_empty_graph_data()

        mock_http_client = Mock()
        mock_http_client.request.return_value = page1

        graph_resource = GraphResource(mock_http_client)
        pages = list(
            graph_resource.get_all_graph_pages(GetGraphRequest(space_id="test-space-123"))
        )

        assert len(pages) == 1
        assert mock_http_client.request.call_count == 1

    def test_get_all_graph_pages_preserves_filters(self):
        """Test get_all_graph_pages preserves filters across pages."""
        page1 = {
            **create_empty_graph_data(),
            "pagination": {
                "hasMore": True,
                "nextCursor": "cursor-2",
            },
        }

        page2 = create_empty_graph_data()

        mock_http_client = Mock()
        mock_http_client.request.side_effect = [page1, page2]

        graph_resource = GraphResource(mock_http_client)
        pages = list(
            graph_resource.get_all_graph_pages(
                GetGraphRequest(
                    space_id="test-space-123",
                    limit=10,
                    node_types=["memory"],
                    relationship_types=["extends"],
                )
            )
        )

        assert len(pages) == 2

        # Verify filters are preserved in both calls
        calls = mock_http_client.request.call_args_list
        assert calls[0][1]["query"]["limit"] == "10"
        assert calls[0][1]["query"]["nodeTypes"] == "memory"
        assert calls[0][1]["query"]["relationshipTypes"] == "extends"

        assert calls[1][1]["query"]["cursor"] == "cursor-2"
        assert calls[1][1]["query"]["limit"] == "10"
        assert calls[1][1]["query"]["nodeTypes"] == "memory"
        assert calls[1][1]["query"]["relationshipTypes"] == "extends"


@pytest.mark.asyncio
class TestAsyncGraphResource:
    """Unit tests for AsyncGraphResource."""

    async def test_get_graph_minimal_parameters(self):
        """Test async get_graph with minimal parameters."""
        mock_response = create_empty_graph_data()
        mock_http_client = AsyncMock()
        mock_http_client.request.return_value = mock_response

        graph_resource = AsyncGraphResource(mock_http_client)
        result = await graph_resource.get_graph(GetGraphRequest(space_id="test-space-123"))

        mock_http_client.request.assert_called_once_with(
            "GET",
            "/v1/graph/spaces/test-space-123",
            query={},
        )

        assert isinstance(result, GraphData)
        assert len(result.nodes) == 0

    async def test_get_node_details(self):
        """Test async get_node_details makes correct API request."""
        mock_response = {
            "node": create_test_node_dict("node-123", "Test Node"),
            "edges": [],
            "connectedNodes": [],
        }
        mock_http_client = AsyncMock()
        mock_http_client.request.return_value = mock_response

        graph_resource = AsyncGraphResource(mock_http_client)
        result = await graph_resource.get_node_details(
            GetNodeDetailsRequest(node_id="node-123")
        )

        assert isinstance(result, NodeDetails)
        assert result.node.id == "node-123"

    async def test_get_all_graph_pages(self):
        """Test async get_all_graph_pages yields all pages."""
        page1 = {
            "nodes": [create_test_node_dict("node-1", "Node 1")],
            "edges": [],
            "metadata": {
                "totalNodes": 2,
                "memoryCount": 2,
                "documentCount": 0,
                "entityCount": 0,
                "totalEdges": 0,
                "relationshipCount": 0,
                "similarityCount": 0,
            },
            "pagination": {
                "hasMore": True,
                "nextCursor": "cursor-2",
            },
        }

        page2 = {
            "nodes": [create_test_node_dict("node-2", "Node 2")],
            "edges": [],
            "metadata": {
                "totalNodes": 2,
                "memoryCount": 2,
                "documentCount": 0,
                "entityCount": 0,
                "totalEdges": 0,
                "relationshipCount": 0,
                "similarityCount": 0,
            },
            "pagination": {
                "hasMore": False,
                "nextCursor": None,
            },
        }

        mock_http_client = AsyncMock()
        mock_http_client.request.side_effect = [page1, page2]

        graph_resource = AsyncGraphResource(mock_http_client)
        pages = []
        async for page in graph_resource.get_all_graph_pages(
            GetGraphRequest(space_id="test-space-123")
        ):
            pages.append(page)

        assert len(pages) == 2
        assert len(pages[0].nodes) == 1
        assert len(pages[1].nodes) == 1
        assert mock_http_client.request.call_count == 2
