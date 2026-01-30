"""Ingest resource for the MemoryLayer SDK."""

from ..http_client import HTTPClient, AsyncHTTPClient
from ..types import IngestFileRequest, IngestTextRequest, IngestResponse
from ..exceptions import ValidationError


class IngestResource:
    """Synchronous ingestion operations."""

    def __init__(self, http_client: HTTPClient):
        self._http_client = http_client

    def file(self, request: IngestFileRequest) -> IngestResponse:
        """Ingest a PDF file using the unified /v1/ingest endpoint."""
        if not request.file:
            raise ValidationError(
                "File is required",
                [{"field": "file", "message": "File is required"}],
            )

        if not request.project_id or not request.project_id.strip():
            raise ValidationError(
                "Project ID is required",
                [{"field": "project_id", "message": "Project ID is required"}],
            )

        # Use multipart/form-data for file upload to match backend expectations
        # The HTTP client should handle multipart encoding automatically
        body = {
            "type": "pdf",
            "projectId": request.project_id,
            "metadata": request.metadata or {},
            "file": request.file,
        }

        # Note: chunkSize and chunkOverlap are handled by the backend automatically
        data = self._http_client.request("POST", "/v1/ingest", body=body)
        return IngestResponse(**data)

    def text(self, request: IngestTextRequest) -> IngestResponse:
        """Ingest text using the unified /v1/ingest endpoint."""
        if not request.text or not request.text.strip():
            raise ValidationError(
                "Text cannot be empty",
                [{"field": "text", "message": "Text is required and cannot be empty"}],
            )

        if not request.project_id or not request.project_id.strip():
            raise ValidationError(
                "Project ID is required",
                [{"field": "project_id", "message": "Project ID is required"}],
            )

        body = {
            "type": "text",
            "content": request.text,
            "projectId": request.project_id,
            "metadata": request.metadata or {},
        }

        # Note: chunkSize and chunkOverlap are handled by the backend automatically
        data = self._http_client.request("POST", "/v1/ingest", body=body)
        return IngestResponse(**data)

    def url(self, url: str, project_id: str, metadata: dict = None) -> IngestResponse:
        """Ingest content from a URL using the unified /v1/ingest endpoint.

        Args:
            url: The URL to ingest content from
            project_id: Project ID
            metadata: Optional metadata

        Returns:
            IngestResponse with job details
        """
        if not url or not url.strip():
            raise ValidationError(
                "URL cannot be empty",
                [{"field": "url", "message": "URL is required and cannot be empty"}],
            )

        if not project_id or not project_id.strip():
            raise ValidationError(
                "Project ID is required",
                [{"field": "project_id", "message": "Project ID is required"}],
            )

        body = {
            "type": "url",
            "url": url,
            "projectId": project_id,
            "metadata": metadata or {},
        }

        data = self._http_client.request("POST", "/v1/ingest", body=body)
        return IngestResponse(**data)

    def get_job(self, job_id: str, project_id: str) -> dict:
        """Get the status of an ingestion job.

        Args:
            job_id: The job ID returned from ingest
            project_id: Project ID

        Returns:
            Job status information including progress, memories created, etc.
        """
        if not job_id or not job_id.strip():
            raise ValidationError(
                "Job ID is required",
                [{"field": "job_id", "message": "Job ID is required"}],
            )

        if not project_id or not project_id.strip():
            raise ValidationError(
                "Project ID is required",
                [{"field": "project_id", "message": "Project ID is required"}],
            )

        data = self._http_client.request(
            "GET",
            f"/v1/jobs/{job_id}",
            query={"projectId": project_id}
        )
        return data.get("data", data)


class AsyncIngestResource:
    """Asynchronous ingestion operations."""

    def __init__(self, http_client: AsyncHTTPClient):
        self._http_client = http_client

    async def file(self, request: IngestFileRequest) -> IngestResponse:
        """Ingest a PDF file using the unified /v1/ingest endpoint."""
        if not request.file:
            raise ValidationError(
                "File is required",
                [{"field": "file", "message": "File is required"}],
            )

        if not request.project_id or not request.project_id.strip():
            raise ValidationError(
                "Project ID is required",
                [{"field": "project_id", "message": "Project ID is required"}],
            )

        # Use multipart/form-data for file upload to match backend expectations
        # The HTTP client should handle multipart encoding automatically
        body = {
            "type": "pdf",
            "projectId": request.project_id,
            "metadata": request.metadata or {},
            "file": request.file,
        }

        # Note: chunkSize and chunkOverlap are handled by the backend automatically
        data = await self._http_client.request("POST", "/v1/ingest", body=body)
        return IngestResponse(**data)

    async def text(self, request: IngestTextRequest) -> IngestResponse:
        """Ingest text using the unified /v1/ingest endpoint."""
        if not request.text or not request.text.strip():
            raise ValidationError(
                "Text cannot be empty",
                [{"field": "text", "message": "Text is required and cannot be empty"}],
            )

        if not request.project_id or not request.project_id.strip():
            raise ValidationError(
                "Project ID is required",
                [{"field": "project_id", "message": "Project ID is required"}],
            )

        body = {
            "type": "text",
            "content": request.text,
            "projectId": request.project_id,
            "metadata": request.metadata or {},
        }

        # Note: chunkSize and chunkOverlap are handled by the backend automatically
        data = await self._http_client.request("POST", "/v1/ingest", body=body)
        return IngestResponse(**data)

    async def url(self, url: str, project_id: str, metadata: dict = None) -> IngestResponse:
        """Ingest content from a URL using the unified /v1/ingest endpoint.

        Args:
            url: The URL to ingest content from
            project_id: Project ID
            metadata: Optional metadata

        Returns:
            IngestResponse with job details
        """
        if not url or not url.strip():
            raise ValidationError(
                "URL cannot be empty",
                [{"field": "url", "message": "URL is required and cannot be empty"}],
            )

        if not project_id or not project_id.strip():
            raise ValidationError(
                "Project ID is required",
                [{"field": "project_id", "message": "Project ID is required"}],
            )

        body = {
            "type": "url",
            "url": url,
            "projectId": project_id,
            "metadata": metadata or {},
        }

        data = await self._http_client.request("POST", "/v1/ingest", body=body)
        return IngestResponse(**data)

    async def get_job(self, job_id: str, project_id: str) -> dict:
        """Get the status of an ingestion job (async).

        Args:
            job_id: The job ID returned from ingest
            project_id: Project ID

        Returns:
            Job status information including progress, memories created, etc.
        """
        if not job_id or not job_id.strip():
            raise ValidationError(
                "Job ID is required",
                [{"field": "job_id", "message": "Job ID is required"}],
            )

        if not project_id or not project_id.strip():
            raise ValidationError(
                "Project ID is required",
                [{"field": "project_id", "message": "Project ID is required"}],
            )

        data = await self._http_client.request(
            "GET",
            f"/v1/jobs/{job_id}",
            query={"projectId": project_id}
        )
        return data.get("data", data)
