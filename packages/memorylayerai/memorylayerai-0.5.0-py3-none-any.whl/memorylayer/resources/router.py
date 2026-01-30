"""Router resource for the MemoryLayer SDK."""

from typing import AsyncIterator

from ..http_client import HTTPClient, AsyncHTTPClient
from ..types import RouterRequest, RouterResponse, StreamChunk, Message, Choice, Usage, StreamChoice, StreamDelta
from ..exceptions import ValidationError


class RouterResource:
    """Synchronous router operations."""

    def __init__(self, http_client: HTTPClient):
        self._http_client = http_client

    def complete(self, request: RouterRequest) -> RouterResponse:
        """Complete a router request (non-streaming)."""
        if not request.messages or len(request.messages) == 0:
            raise ValidationError(
                "Messages array cannot be empty",
                [{"field": "messages", "message": "At least one message is required"}],
            )

        if not request.project_id or not request.project_id.strip():
            raise ValidationError(
                "Project ID is required",
                [{"field": "project_id", "message": "Project ID is required"}],
            )

        body = {
            "messages": [{"role": m.role, "content": m.content} for m in request.messages],
            "projectId": request.project_id,
            "model": request.model,
            "temperature": request.temperature,
            "maxTokens": request.max_tokens,
            "stream": False,
        }

        data = self._http_client.request("POST", "/v1/router/complete", body=body)
        return RouterResponse(
            id=data["id"],
            choices=[Choice(message=Message(**c["message"]), finish_reason=c["finishReason"]) for c in data["choices"]],
            usage=Usage(**data["usage"])
        )


class AsyncRouterResource:
    """Asynchronous router operations."""

    def __init__(self, http_client: AsyncHTTPClient):
        self._http_client = http_client

    async def complete(self, request: RouterRequest) -> RouterResponse:
        """Complete a router request (non-streaming)."""
        if not request.messages or len(request.messages) == 0:
            raise ValidationError(
                "Messages array cannot be empty",
                [{"field": "messages", "message": "At least one message is required"}],
            )

        if not request.project_id or not request.project_id.strip():
            raise ValidationError(
                "Project ID is required",
                [{"field": "project_id", "message": "Project ID is required"}],
            )

        body = {
            "messages": [{"role": m.role, "content": m.content} for m in request.messages],
            "projectId": request.project_id,
            "model": request.model,
            "temperature": request.temperature,
            "maxTokens": request.max_tokens,
            "stream": False,
        }

        data = await self._http_client.request("POST", "/v1/router/complete", body=body)
        return RouterResponse(
            id=data["id"],
            choices=[Choice(message=Message(**c["message"]), finish_reason=c["finishReason"]) for c in data["choices"]],
            usage=Usage(**data["usage"])
        )

    async def stream(self, request: RouterRequest) -> AsyncIterator[StreamChunk]:
        """Stream a router request."""
        if not request.messages or len(request.messages) == 0:
            raise ValidationError(
                "Messages array cannot be empty",
                [{"field": "messages", "message": "At least one message is required"}],
            )

        if not request.project_id or not request.project_id.strip():
            raise ValidationError(
                "Project ID is required",
                [{"field": "project_id", "message": "Project ID is required"}],
            )

        body = {
            "messages": [{"role": m.role, "content": m.content} for m in request.messages],
            "projectId": request.project_id,
            "model": request.model,
            "temperature": request.temperature,
            "maxTokens": request.max_tokens,
            "stream": True,
        }

        async for chunk in self._http_client.stream("POST", "/v1/router/complete", body=body):
            yield StreamChunk(
                id=chunk["id"],
                choices=[StreamChoice(delta=StreamDelta(**c["delta"]), finish_reason=c.get("finishReason")) for c in chunk["choices"]]
            )
