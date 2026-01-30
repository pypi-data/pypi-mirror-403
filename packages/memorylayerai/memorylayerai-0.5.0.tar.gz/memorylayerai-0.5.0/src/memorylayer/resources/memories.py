"""Memory resource for the MemoryLayer SDK."""

from typing import List

from ..http_client import HTTPClient, AsyncHTTPClient
from ..types import Memory, CreateMemoryRequest, UpdateMemoryRequest, ListMemoriesRequest
from ..exceptions import ValidationError


class MemoriesResource:
    """Synchronous memory operations."""

    def __init__(self, http_client: HTTPClient):
        self._http_client = http_client

    def add(self, request: CreateMemoryRequest) -> Memory:
        """Add a new memory."""
        if not request.content or not request.content.strip():
            raise ValidationError(
                "Memory content cannot be empty",
                [{"field": "content", "message": "Content is required and cannot be empty"}],
            )

        if not request.project_id or not request.project_id.strip():
            raise ValidationError(
                "Project ID is required",
                [{"field": "project_id", "message": "Project ID is required"}],
            )

        data = self._http_client.request(
            "POST",
            "/v1/memories",
            body={
                "content": request.content,
                "projectId": request.project_id,
                "metadata": request.metadata,
            },
        )
        return Memory(**data)

    def get(self, id: str) -> Memory:
        """Get a memory by ID."""
        if not id or not id.strip():
            raise ValidationError(
                "Memory ID is required",
                [{"field": "id", "message": "Memory ID is required"}],
            )

        data = self._http_client.request("GET", f"/v1/memories/{id}")
        return Memory(**data)

    def update(self, id: str, content: str = None, metadata: dict = None) -> Memory:
        """Update a memory."""
        if not id or not id.strip():
            raise ValidationError(
                "Memory ID is required",
                [{"field": "id", "message": "Memory ID is required"}],
            )

        if content is None and metadata is None:
            raise ValidationError(
                "At least one of content or metadata must be provided",
                [{"field": "request", "message": "Nothing to update"}],
            )

        body = {}
        if content is not None:
            body["content"] = content
        if metadata is not None:
            body["metadata"] = metadata

        data = self._http_client.request("PATCH", f"/v1/memories/{id}", body=body)
        return Memory(**data)

    def delete(self, id: str) -> None:
        """Delete a memory."""
        if not id or not id.strip():
            raise ValidationError(
                "Memory ID is required",
                [{"field": "id", "message": "Memory ID is required"}],
            )

        self._http_client.request("DELETE", f"/v1/memories/{id}")

    def list(self, request: ListMemoriesRequest) -> List[Memory]:
        """List memories."""
        if not request.project_id or not request.project_id.strip():
            raise ValidationError(
                "Project ID is required",
                [{"field": "project_id", "message": "Project ID is required"}],
            )

        query = {"projectId": request.project_id}
        if request.limit is not None:
            query["limit"] = str(request.limit)
        if request.offset is not None:
            query["offset"] = str(request.offset)
        if request.filter:
            import json
            query["filter"] = json.dumps(request.filter)

        data = self._http_client.request("GET", "/v1/memories", query=query)
        return [Memory(**item) for item in data]


class AsyncMemoriesResource:
    """Asynchronous memory operations."""

    def __init__(self, http_client: AsyncHTTPClient):
        self._http_client = http_client

    async def add(self, request: CreateMemoryRequest) -> Memory:
        """Add a new memory."""
        if not request.content or not request.content.strip():
            raise ValidationError(
                "Memory content cannot be empty",
                [{"field": "content", "message": "Content is required and cannot be empty"}],
            )

        if not request.project_id or not request.project_id.strip():
            raise ValidationError(
                "Project ID is required",
                [{"field": "project_id", "message": "Project ID is required"}],
            )

        data = await self._http_client.request(
            "POST",
            "/v1/memories",
            body={
                "content": request.content,
                "projectId": request.project_id,
                "metadata": request.metadata,
            },
        )
        return Memory(**data)

    async def get(self, id: str) -> Memory:
        """Get a memory by ID."""
        if not id or not id.strip():
            raise ValidationError(
                "Memory ID is required",
                [{"field": "id", "message": "Memory ID is required"}],
            )

        data = await self._http_client.request("GET", f"/v1/memories/{id}")
        return Memory(**data)

    async def update(self, id: str, content: str = None, metadata: dict = None) -> Memory:
        """Update a memory."""
        if not id or not id.strip():
            raise ValidationError(
                "Memory ID is required",
                [{"field": "id", "message": "Memory ID is required"}],
            )

        if content is None and metadata is None:
            raise ValidationError(
                "At least one of content or metadata must be provided",
                [{"field": "request", "message": "Nothing to update"}],
            )

        body = {}
        if content is not None:
            body["content"] = content
        if metadata is not None:
            body["metadata"] = metadata

        data = await self._http_client.request("PATCH", f"/v1/memories/{id}", body=body)
        return Memory(**data)

    async def delete(self, id: str) -> None:
        """Delete a memory."""
        if not id or not id.strip():
            raise ValidationError(
                "Memory ID is required",
                [{"field": "id", "message": "Memory ID is required"}],
            )

        await self._http_client.request("DELETE", f"/v1/memories/{id}")

    async def list(self, request: ListMemoriesRequest) -> List[Memory]:
        """List memories."""
        if not request.project_id or not request.project_id.strip():
            raise ValidationError(
                "Project ID is required",
                [{"field": "project_id", "message": "Project ID is required"}],
            )

        query = {"projectId": request.project_id}
        if request.limit is not None:
            query["limit"] = str(request.limit)
        if request.offset is not None:
            query["offset"] = str(request.offset)
        if request.filter:
            import json
            query["filter"] = json.dumps(request.filter)

        data = await self._http_client.request("GET", "/v1/memories", query=query)
        return [Memory(**item) for item in data]
