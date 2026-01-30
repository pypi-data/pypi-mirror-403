"""Property-based tests for Python SDK graph methods.

These tests use Hypothesis to verify universal properties hold across all inputs.

Requirements: 6.4
"""

import pytest
from hypothesis import given, strategies as st
from unittest.mock import Mock, AsyncMock

from memorylayer.resources.graph import GraphResource, AsyncGraphResource
from memorylayer.types import (
    GetGraphRequest,
    GraphData,
    GraphNode,
    GraphNodeData,
    GraphEdge,
    GraphMetadata,
    PaginationInfo,
)


# Strategies for generating test data

@st.composite
def graph_node_strategy(draw):
    """Generate a random GraphNode."""
    node_id = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_characters="\x00")))
    node_type = draw(st.sampled_from(["memory", "document", "entity"]))
    label = draw(st.text(min_size=1, max_size=100, alphabet=st.characters(blacklist_characters="\x00")))
    status = draw(st.sampled_from(["new", "latest", "older", "expiring", "forgotten"]))
    created_at = "2026-01-20T00:00:00Z"
    
    return GraphNode(
        id=node_id,
        type=node_type,
        label=label,
        data=GraphNodeData(
            status=status,
            created_at=created_at,
            content=draw(st.one_of(st.none(), st.text(max_size=200))),
            expires_at=draw(st.one_of(st.none(), st.just("2026-12-31T23:59:59Z"))),
            metadata=draw(st.one_of(st.none(), st.dictionaries(st.text(max_size=10), st.text(max_size=20), max_size=3))),
        ),
    )


@st.composite
def graph_edge_strategy(draw, node_ids):
    """Generate a random GraphEdge."""
    if len(node_ids) < 2:
        # Need at least 2 nodes for an edge
        source = "node-1"
        target = "node-2"
    else:
        source = draw(st.sampled_from(node_ids))
        # Filter out source to ensure different target
        other_nodes = [n for n in node_ids if n != source]
        if not other_nodes:
            # Fallback if somehow we only have one unique node
            target = source + "-target"
        else:
            target = draw(st.sampled_from(other_nodes))
    
    edge_id = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_characters="\x00")))
    edge_type = draw(st.sampled_from(["extends", "updates", "derives", "similarity"]))
    label = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_characters="\x00")))
    
    return GraphEdge(
        id=edge_id,
        source=source,
        target=target,
        type=edge_type,
        label=label,
        metadata=draw(st.one_of(st.none(), st.dictionaries(st.text(max_size=10), st.text(max_size=20), max_size=3))),
    )


@st.composite
def graph_data_strategy(draw, min_nodes=0, max_nodes=20):
    """Generate random GraphData."""
    nodes = draw(st.lists(graph_node_strategy(), min_size=min_nodes, max_size=max_nodes))
    
    # Ensure unique node IDs by adding index suffix if duplicates exist
    seen_ids = set()
    for i, node in enumerate(nodes):
        original_id = node.id
        counter = 0
        while node.id in seen_ids:
            counter += 1
            node.id = f"{original_id}-{counter}"
        seen_ids.add(node.id)
    
    node_ids = [n.id for n in nodes]
    
    # Generate edges only if we have nodes
    if len(node_ids) >= 2:
        edges = draw(st.lists(graph_edge_strategy(node_ids), max_size=min(len(nodes) * 2, 30)))
    else:
        edges = []
    
    # Calculate metadata
    memory_count = sum(1 for n in nodes if n.type == "memory")
    document_count = sum(1 for n in nodes if n.type == "document")
    entity_count = sum(1 for n in nodes if n.type == "entity")
    
    relationship_count = sum(1 for e in edges if e.type in ["extends", "updates", "derives"])
    similarity_count = sum(1 for e in edges if e.type == "similarity")
    
    metadata = GraphMetadata(
        total_nodes=len(nodes),
        memory_count=memory_count,
        document_count=document_count,
        entity_count=entity_count,
        total_edges=len(edges),
        relationship_count=relationship_count,
        similarity_count=similarity_count,
    )
    
    has_more = draw(st.booleans())
    next_cursor = draw(st.one_of(st.none(), st.text(min_size=1, max_size=20))) if has_more else None
    
    pagination = PaginationInfo(
        has_more=has_more,
        next_cursor=next_cursor,
        total_count=draw(st.one_of(st.none(), st.integers(min_value=len(nodes), max_value=1000))),
    )
    
    return GraphData(
        nodes=nodes,
        edges=edges,
        metadata=metadata,
        pagination=pagination,
    )


class TestGraphResourceProperties:
    """Property-based tests for GraphResource."""

    @given(graph_data_strategy(min_nodes=5, max_nodes=20))
    def test_pagination_completeness(self, graph_data: GraphData):
        """Property 12: SDK pagination returns each node exactly once.
        
        Validates: Requirements 6.4
        """
        # Create mock HTTP client
        mock_http_client = Mock()
        
        # Create multiple pages
        page_size = 5
        all_nodes = graph_data.nodes
        pages = []
        
        for i in range(0, len(all_nodes), page_size):
            page_nodes = all_nodes[i:i + page_size]
            has_more = (i + page_size) < len(all_nodes)
            next_cursor = f"cursor-{i + page_size}" if has_more else None
            
            page = GraphData(
                nodes=page_nodes,
                edges=[],
                metadata=GraphMetadata(
                    total_nodes=len(all_nodes),
                    memory_count=sum(1 for n in all_nodes if n.type == "memory"),
                    document_count=sum(1 for n in all_nodes if n.type == "document"),
                    entity_count=sum(1 for n in all_nodes if n.type == "entity"),
                    total_edges=0,
                    relationship_count=0,
                    similarity_count=0,
                ),
                pagination=PaginationInfo(
                    has_more=has_more,
                    next_cursor=next_cursor,
                ),
            )
            pages.append(page)
        
        # Mock the HTTP client to return pages
        mock_http_client.request.side_effect = [
            self._graph_data_to_dict(page) for page in pages
        ]
        
        # Create GraphResource
        graph_resource = GraphResource(mock_http_client)
        
        # Collect all nodes from pagination
        collected_nodes = []
        collected_node_ids = set()
        
        for page in graph_resource.get_all_graph_pages(
            GetGraphRequest(space_id="test-space")
        ):
            for node in page.nodes:
                # Property: Each node should appear exactly once
                assert node.id not in collected_node_ids, f"Duplicate node ID: {node.id}"
                collected_node_ids.add(node.id)
                collected_nodes.append(node)
        
        # Property: All nodes should be collected
        assert len(collected_nodes) == len(all_nodes)
        assert collected_node_ids == {n.id for n in all_nodes}

    @given(graph_data_strategy(min_nodes=3, max_nodes=10))
    def test_node_type_filtering(self, graph_data: GraphData):
        """Property: Filtered results only contain matching node types.
        
        Validates: Requirements 6.1
        """
        # Filter for memory nodes only
        memory_nodes = [n for n in graph_data.nodes if n.type == "memory"]
        
        if not memory_nodes:
            # Skip if no memory nodes
            return
        
        filtered_data = GraphData(
            nodes=memory_nodes,
            edges=[],
            metadata=GraphMetadata(
                total_nodes=len(memory_nodes),
                memory_count=len(memory_nodes),
                document_count=0,
                entity_count=0,
                total_edges=0,
                relationship_count=0,
                similarity_count=0,
            ),
            pagination=PaginationInfo(has_more=False),
        )
        
        # Mock HTTP client
        mock_http_client = Mock()
        mock_http_client.request.return_value = self._graph_data_to_dict(filtered_data)
        
        # Create GraphResource
        graph_resource = GraphResource(mock_http_client)
        
        # Get filtered graph
        result = graph_resource.get_graph(
            GetGraphRequest(space_id="test-space", node_types=["memory"])
        )
        
        # Property: All returned nodes should be memory nodes
        assert all(n.type == "memory" for n in result.nodes)
        assert len(result.nodes) == len(memory_nodes)

    @given(graph_data_strategy(min_nodes=2, max_nodes=10))
    def test_metadata_accuracy(self, graph_data: GraphData):
        """Property: Metadata counts match actual data.
        
        Validates: Requirements 6.1
        """
        # Mock HTTP client
        mock_http_client = Mock()
        mock_http_client.request.return_value = self._graph_data_to_dict(graph_data)
        
        # Create GraphResource
        graph_resource = GraphResource(mock_http_client)
        
        # Get graph
        result = graph_resource.get_graph(GetGraphRequest(space_id="test-space"))
        
        # Property: Metadata should match actual counts
        assert result.metadata.total_nodes == len(result.nodes)
        assert result.metadata.total_edges == len(result.edges)
        
        # Count by type
        memory_count = sum(1 for n in result.nodes if n.type == "memory")
        document_count = sum(1 for n in result.nodes if n.type == "document")
        entity_count = sum(1 for n in result.nodes if n.type == "entity")
        
        assert result.metadata.memory_count == memory_count
        assert result.metadata.document_count == document_count
        assert result.metadata.entity_count == entity_count

    @staticmethod
    def _graph_data_to_dict(graph_data: GraphData) -> dict:
        """Convert GraphData to dict for mocking API response."""
        return {
            "nodes": [
                {
                    "id": n.id,
                    "type": n.type,
                    "label": n.label,
                    "data": {
                        "status": n.data.status,
                        "createdAt": n.data.created_at,
                        "content": n.data.content,
                        "expiresAt": n.data.expires_at,
                        "metadata": n.data.metadata,
                    },
                }
                for n in graph_data.nodes
            ],
            "edges": [
                {
                    "id": e.id,
                    "source": e.source,
                    "target": e.target,
                    "type": e.type,
                    "label": e.label,
                    "metadata": e.metadata,
                }
                for e in graph_data.edges
            ],
            "metadata": {
                "totalNodes": graph_data.metadata.total_nodes,
                "memoryCount": graph_data.metadata.memory_count,
                "documentCount": graph_data.metadata.document_count,
                "entityCount": graph_data.metadata.entity_count,
                "totalEdges": graph_data.metadata.total_edges,
                "relationshipCount": graph_data.metadata.relationship_count,
                "similarityCount": graph_data.metadata.similarity_count,
            },
            "pagination": {
                "hasMore": graph_data.pagination.has_more,
                "nextCursor": graph_data.pagination.next_cursor,
                "totalCount": graph_data.pagination.total_count,
            },
        }


@pytest.mark.asyncio
class TestAsyncGraphResourceProperties:
    """Property-based tests for AsyncGraphResource."""

    @given(graph_data_strategy(min_nodes=5, max_nodes=15))
    async def test_async_pagination_completeness(self, graph_data: GraphData):
        """Property 12: Async SDK pagination returns each node exactly once.
        
        Validates: Requirements 6.4
        """
        # Create mock HTTP client
        mock_http_client = AsyncMock()
        
        # Create multiple pages
        page_size = 5
        all_nodes = graph_data.nodes
        pages = []
        
        for i in range(0, len(all_nodes), page_size):
            page_nodes = all_nodes[i:i + page_size]
            has_more = (i + page_size) < len(all_nodes)
            next_cursor = f"cursor-{i + page_size}" if has_more else None
            
            page = GraphData(
                nodes=page_nodes,
                edges=[],
                metadata=GraphMetadata(
                    total_nodes=len(all_nodes),
                    memory_count=sum(1 for n in all_nodes if n.type == "memory"),
                    document_count=sum(1 for n in all_nodes if n.type == "document"),
                    entity_count=sum(1 for n in all_nodes if n.type == "entity"),
                    total_edges=0,
                    relationship_count=0,
                    similarity_count=0,
                ),
                pagination=PaginationInfo(
                    has_more=has_more,
                    next_cursor=next_cursor,
                ),
            )
            pages.append(page)
        
        # Mock the HTTP client to return pages
        mock_http_client.request.side_effect = [
            self._graph_data_to_dict(page) for page in pages
        ]
        
        # Create AsyncGraphResource
        graph_resource = AsyncGraphResource(mock_http_client)
        
        # Collect all nodes from pagination
        collected_nodes = []
        collected_node_ids = set()
        
        async for page in graph_resource.get_all_graph_pages(
            GetGraphRequest(space_id="test-space")
        ):
            for node in page.nodes:
                # Property: Each node should appear exactly once
                assert node.id not in collected_node_ids, f"Duplicate node ID: {node.id}"
                collected_node_ids.add(node.id)
                collected_nodes.append(node)
        
        # Property: All nodes should be collected
        assert len(collected_nodes) == len(all_nodes)
        assert collected_node_ids == {n.id for n in all_nodes}

    @staticmethod
    def _graph_data_to_dict(graph_data: GraphData) -> dict:
        """Convert GraphData to dict for mocking API response."""
        return {
            "nodes": [
                {
                    "id": n.id,
                    "type": n.type,
                    "label": n.label,
                    "data": {
                        "status": n.data.status,
                        "createdAt": n.data.created_at,
                        "content": n.data.content,
                        "expiresAt": n.data.expires_at,
                        "metadata": n.data.metadata,
                    },
                }
                for n in graph_data.nodes
            ],
            "edges": [
                {
                    "id": e.id,
                    "source": e.source,
                    "target": e.target,
                    "type": e.type,
                    "label": e.label,
                    "metadata": e.metadata,
                }
                for e in graph_data.edges
            ],
            "metadata": {
                "totalNodes": graph_data.metadata.total_nodes,
                "memoryCount": graph_data.metadata.memory_count,
                "documentCount": graph_data.metadata.document_count,
                "entityCount": graph_data.metadata.entity_count,
                "totalEdges": graph_data.metadata.total_edges,
                "relationshipCount": graph_data.metadata.relationship_count,
                "similarityCount": graph_data.metadata.similarity_count,
            },
            "pagination": {
                "hasMore": graph_data.pagination.has_more,
                "nextCursor": graph_data.pagination.next_cursor,
                "totalCount": graph_data.pagination.total_count,
            },
        }
