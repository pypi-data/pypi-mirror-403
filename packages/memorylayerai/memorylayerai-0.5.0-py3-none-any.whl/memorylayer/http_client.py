"""HTTP client with retry logic for the MemoryLayer SDK."""

import asyncio
import json
import time
from typing import Any, AsyncIterator, Dict, List, Optional
from dataclasses import dataclass

import httpx

from .exceptions import (
    MemoryLayerError,
    AuthenticationError,
    RateLimitError,
    ValidationError,
    NetworkError,
    APIError,
)


@dataclass
class ClientConfig:
    """Configuration for the HTTP client."""

    api_key: str
    base_url: str = "https://api.memorylayer.com"
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    headers: Optional[Dict[str, str]] = None
    logger: Optional[Any] = None


@dataclass
class RetryConfig:
    """Retry configuration."""

    max_retries: int = 3
    initial_delay: float = 1.0
    max_delay: float = 30.0
    backoff_multiplier: float = 2.0
    retryable_status_codes: List[int] = None

    def __post_init__(self):
        if self.retryable_status_codes is None:
            self.retryable_status_codes = [429, 500, 502, 503, 504]


class HTTPClient:
    """HTTP client with retry logic and error handling."""

    def __init__(self, config: ClientConfig, retry_config: Optional[RetryConfig] = None):
        self.config = config
        self.retry_config = retry_config or RetryConfig(
            max_retries=config.max_retries,
            initial_delay=config.retry_delay,
        )
        self.client = httpx.Client(
            base_url=config.base_url,
            timeout=config.timeout,
            headers=self._build_headers(),
        )

    def _build_headers(self, additional_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """Build request headers."""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.api_key}",
            "X-SDK-Version": "0.1.0",
            "X-API-Version": "v1",
        }
        if self.config.headers:
            headers.update(self.config.headers)
        if additional_headers:
            headers.update(additional_headers)
        return headers

    def request(
        self,
        method: str,
        path: str,
        body: Optional[Any] = None,
        query: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        """Make an HTTP request with retry logic."""
        last_error: Optional[Exception] = None

        for attempt in range(self.retry_config.max_retries + 1):
            try:
                return self._make_request(method, path, body, query, headers)
            except MemoryLayerError as error:
                last_error = error
                if not self._should_retry(error, attempt):
                    raise
                delay = self._get_retry_delay(error, attempt)
                if self.config.logger:
                    self.config.logger.debug(
                        f"Retrying request after {delay}s (attempt {attempt + 1}/{self.retry_config.max_retries})"
                    )
                time.sleep(delay)

        raise last_error  # type: ignore

    def _make_request(
        self,
        method: str,
        path: str,
        body: Optional[Any] = None,
        query: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        """Make the actual HTTP request."""
        try:
            response = self.client.request(
                method=method,
                url=path,
                json=body,
                params=query,
                headers=self._build_headers(headers),
            )

            if not response.is_success:
                raise self._handle_error_response(response)

            return response.json()
        except httpx.HTTPError as error:
            raise NetworkError("Request failed", error)

    def _handle_error_response(self, response: httpx.Response) -> MemoryLayerError:
        """Handle error responses from the API."""
        request_id = response.headers.get("x-request-id")

        try:
            error_data = response.json()
        except Exception:
            error_data = {"message": response.text}

        message = error_data.get("error", {}).get("message") or error_data.get("message", "Unknown error")
        details = error_data.get("error", {}).get("details") or error_data.get("details")

        if response.status_code == 401:
            return AuthenticationError(message, request_id)
        elif response.status_code == 429:
            retry_after = int(response.headers.get("retry-after", "60"))
            return RateLimitError(message, retry_after, request_id)
        elif response.status_code == 400:
            errors = error_data.get("error", {}).get("errors", [])
            return ValidationError(message, errors, request_id)
        else:
            return APIError(message, response.status_code, request_id, details)

    def _should_retry(self, error: MemoryLayerError, attempt: int) -> bool:
        """Determine if an error should be retried."""
        if attempt >= self.retry_config.max_retries:
            return False

        if isinstance(error, NetworkError):
            return True

        if isinstance(error, RateLimitError):
            return True

        if error.status_code and error.status_code in self.retry_config.retryable_status_codes:
            return True

        if error.status_code and 400 <= error.status_code < 500:
            return False

        return False

    def _get_retry_delay(self, error: MemoryLayerError, attempt: int) -> float:
        """Calculate retry delay with exponential backoff."""
        if isinstance(error, RateLimitError):
            return float(error.retry_after)

        exponential_delay = self.retry_config.initial_delay * (
            self.retry_config.backoff_multiplier ** attempt
        )
        import random
        jitter = random.random() * 0.1 * exponential_delay
        delay = min(exponential_delay + jitter, self.retry_config.max_delay)

        return delay

    def close(self):
        """Close the HTTP client."""
        self.client.close()


class AsyncHTTPClient:
    """Async HTTP client with retry logic and error handling."""

    def __init__(self, config: ClientConfig, retry_config: Optional[RetryConfig] = None):
        self.config = config
        self.retry_config = retry_config or RetryConfig(
            max_retries=config.max_retries,
            initial_delay=config.retry_delay,
        )
        self.client = httpx.AsyncClient(
            base_url=config.base_url,
            timeout=config.timeout,
            headers=self._build_headers(),
        )

    def _build_headers(self, additional_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """Build request headers."""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.api_key}",
            "X-SDK-Version": "0.1.0",
            "X-API-Version": "v1",
        }
        if self.config.headers:
            headers.update(self.config.headers)
        if additional_headers:
            headers.update(additional_headers)
        return headers

    async def request(
        self,
        method: str,
        path: str,
        body: Optional[Any] = None,
        query: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        """Make an async HTTP request with retry logic."""
        last_error: Optional[Exception] = None

        for attempt in range(self.retry_config.max_retries + 1):
            try:
                return await self._make_request(method, path, body, query, headers)
            except MemoryLayerError as error:
                last_error = error
                if not self._should_retry(error, attempt):
                    raise
                delay = self._get_retry_delay(error, attempt)
                if self.config.logger:
                    self.config.logger.debug(
                        f"Retrying request after {delay}s (attempt {attempt + 1}/{self.retry_config.max_retries})"
                    )
                await asyncio.sleep(delay)

        raise last_error  # type: ignore

    async def _make_request(
        self,
        method: str,
        path: str,
        body: Optional[Any] = None,
        query: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        """Make the actual async HTTP request."""
        try:
            response = await self.client.request(
                method=method,
                url=path,
                json=body,
                params=query,
                headers=self._build_headers(headers),
            )

            if not response.is_success:
                raise self._handle_error_response(response)

            return response.json()
        except httpx.HTTPError as error:
            raise NetworkError("Request failed", error)

    async def stream(
        self,
        method: str,
        path: str,
        body: Optional[Any] = None,
        query: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> AsyncIterator[Any]:
        """Make a streaming async HTTP request."""
        try:
            async with self.client.stream(
                method=method,
                url=path,
                json=body,
                params=query,
                headers=self._build_headers(headers),
            ) as response:
                if not response.is_success:
                    raise self._handle_error_response(response)

                buffer = ""
                async for chunk in response.aiter_text():
                    buffer += chunk
                    lines = buffer.split("\n")
                    buffer = lines.pop()

                    for line in lines:
                        if not line.strip():
                            continue
                        if line.startswith("data: "):
                            data = line[6:]
                            if data == "[DONE]":
                                continue
                            try:
                                yield json.loads(data)
                            except json.JSONDecodeError:
                                if self.config.logger:
                                    self.config.logger.warning(f"Failed to parse streaming chunk: {data}")
        except httpx.HTTPError as error:
            raise NetworkError("Streaming request failed", error)

    def _handle_error_response(self, response: httpx.Response) -> MemoryLayerError:
        """Handle error responses from the API."""
        request_id = response.headers.get("x-request-id")

        try:
            error_data = response.json()
        except Exception:
            error_data = {"message": response.text}

        message = error_data.get("error", {}).get("message") or error_data.get("message", "Unknown error")
        details = error_data.get("error", {}).get("details") or error_data.get("details")

        if response.status_code == 401:
            return AuthenticationError(message, request_id)
        elif response.status_code == 429:
            retry_after = int(response.headers.get("retry-after", "60"))
            return RateLimitError(message, retry_after, request_id)
        elif response.status_code == 400:
            errors = error_data.get("error", {}).get("errors", [])
            return ValidationError(message, errors, request_id)
        else:
            return APIError(message, response.status_code, request_id, details)

    def _should_retry(self, error: MemoryLayerError, attempt: int) -> bool:
        """Determine if an error should be retried."""
        if attempt >= self.retry_config.max_retries:
            return False

        if isinstance(error, NetworkError):
            return True

        if isinstance(error, RateLimitError):
            return True

        if error.status_code and error.status_code in self.retry_config.retryable_status_codes:
            return True

        if error.status_code and 400 <= error.status_code < 500:
            return False

        return False

    def _get_retry_delay(self, error: MemoryLayerError, attempt: int) -> float:
        """Calculate retry delay with exponential backoff."""
        if isinstance(error, RateLimitError):
            return float(error.retry_after)

        exponential_delay = self.retry_config.initial_delay * (
            self.retry_config.backoff_multiplier ** attempt
        )
        import random
        jitter = random.random() * 0.1 * exponential_delay
        delay = min(exponential_delay + jitter, self.retry_config.max_delay)

        return delay

    async def close(self):
        """Close the async HTTP client."""
        await self.client.aclose()
