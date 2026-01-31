"""
Veri API Client implementations
"""

from __future__ import annotations

import base64
import time
from pathlib import Path
from typing import Any, BinaryIO, Union

import httpx

from veri.errors import (
    VeriAPIError,
    VeriInsufficientCreditsError,
    VeriRateLimitError,
    VeriTimeoutError,
    VeriValidationError,
)
from veri.types import (
    DetectionOptions,
    DetectionResult,
)

DEFAULT_BASE_URL = "https://api.veri.studio/v1"
DEFAULT_TIMEOUT = 30.0
DEFAULT_MAX_RETRIES = 3


ImageInput = Union[bytes, str, Path, BinaryIO]  # noqa: UP007 - Union needed for mypy type alias


class VeriClient:
    """
    Synchronous Veri API client.

    Example:
        >>> from veri import VeriClient
        >>> client = VeriClient(api_key="your-api-key")
        >>> result = client.detect(open("image.jpg", "rb"))
        >>> print(f"Is fake: {result.is_fake} ({result.confidence:.1%})")
    """

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ) -> None:
        """
        Initialize the Veri client.

        Args:
            api_key: Your Veri API key
            base_url: Base URL for the API
            timeout: Request timeout in seconds
            max_retries: Number of retry attempts for failed requests
        """
        if not api_key:
            raise VeriValidationError("API key is required", "api_key")

        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries

        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=timeout,
            headers={
                "X-API-Key": api_key,
                "User-Agent": "veri-sdk-python/0.1.0",
                "Content-Type": "application/json",
            },
        )

    def __enter__(self) -> VeriClient:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def close(self) -> None:
        """Close the client and release resources."""
        self._client.close()

    def detect(
        self,
        image: ImageInput,
        *,
        options: DetectionOptions | None = None,
    ) -> DetectionResult:
        """
        Detect whether an image is AI-generated.

        Args:
            image: Image data as bytes, file path, file object, or base64 string
            options: Detection options

        Returns:
            Detection result with confidence scores

        Example:
            >>> # From file path
            >>> result = client.detect(Path("image.jpg"))
            >>>
            >>> # From bytes
            >>> result = client.detect(image_bytes)
            >>>
            >>> # With options
            >>> result = client.detect(
            ...     image_bytes,
            ...     options=DetectionOptions(models=["veri_face"])
            ... )
        """
        image_b64 = self._image_to_base64(image)
        payload: dict[str, Any] = {"image": image_b64}

        if options:
            payload.update(options.model_dump(by_alias=True, exclude_none=True))

        response = self._request("POST", "/api/detect", json=payload)
        return DetectionResult.model_validate(response)

    def detect_url(
        self,
        url: str,
        *,
        options: DetectionOptions | None = None,
    ) -> DetectionResult:
        """
        Detect an image from a URL.

        Args:
            url: URL of the image to analyze
            options: Detection options

        Returns:
            Detection result
        """
        if not url.startswith(("http://", "https://")):
            raise VeriValidationError("Invalid URL format", "url")

        payload: dict[str, Any] = {"url": url}
        if options:
            payload.update(options.model_dump(by_alias=True, exclude_none=True))

        response = self._request("POST", "/api/detect/url", json=payload)
        return DetectionResult.model_validate(response)

    def get_profile(self) -> dict[str, Any]:
        """
        Get the authenticated user's profile.

        Returns:
            User profile data including userId, email, credits, etc.
        """
        return self._request("GET", "/api/user/profile")

    # ============ Private methods ============

    def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs: Any,
    ) -> Any:
        """Make an HTTP request with retries."""
        last_error: Exception | None = None

        for attempt in range(self.max_retries):
            try:
                response = self._client.request(method, endpoint, **kwargs)

                if response.status_code == 429:
                    retry_after = int(response.headers.get("retry-after", "60"))
                    request_id = response.headers.get("x-request-id")
                    raise VeriRateLimitError(
                        "Rate limit exceeded",
                        retry_after,
                        request_id,
                    )

                if response.status_code == 402:
                    error_data = self._safe_json(response)
                    request_id = response.headers.get("x-request-id")
                    raise VeriInsufficientCreditsError(
                        error_data.get("message", "Insufficient credits"),
                        request_id,
                    )

                if not response.is_success:
                    error_data = self._safe_json(response)
                    request_id = response.headers.get("x-request-id")
                    raise VeriAPIError(
                        error_data.get("message", f"Request failed: {response.status_code}"),
                        response.status_code,
                        error_data.get("code", "UNKNOWN_ERROR"),
                        request_id,
                    )

                return self._safe_json(response)

            except httpx.TimeoutException as e:
                raise VeriTimeoutError(
                    f"Request timed out after {self.timeout}s",
                    int(self.timeout * 1000),
                ) from e

            except VeriAPIError as e:
                if not e.is_retryable:
                    raise
                last_error = e

            except httpx.HTTPError as e:
                last_error = e

            # Exponential backoff
            if attempt < self.max_retries - 1:
                time.sleep(2**attempt)

        if last_error:
            raise last_error
        raise VeriAPIError("Request failed after retries", 500, "RETRY_EXHAUSTED")

    def _safe_json(self, response: httpx.Response) -> dict[str, Any]:
        """Safely parse JSON response, returning empty dict on failure."""
        if not response.content:
            return {}
        try:
            return response.json()
        except Exception:
            return {"message": response.text[:500] if response.text else "Unknown error"}

    def _image_to_base64(self, image: ImageInput) -> str:
        """Convert various image inputs to base64 string."""
        # Already base64 string
        if isinstance(image, str):
            if image.startswith("data:"):
                return image.split(",", 1)[1]
            # Assume it's already base64 or a file path
            if Path(image).exists():
                with open(image, "rb") as f:
                    return base64.b64encode(f.read()).decode("utf-8")
            return image

        # Path object
        if isinstance(image, Path):
            with open(image, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")

        # Bytes
        if isinstance(image, bytes):
            return base64.b64encode(image).decode("utf-8")

        # File-like object
        if hasattr(image, "read"):
            content = image.read()
            if isinstance(content, str):
                content = content.encode("utf-8")
            return base64.b64encode(content).decode("utf-8")

        raise VeriValidationError(
            "Invalid image format. Expected bytes, Path, file object, or base64 string",
            "image",
        )


class AsyncVeriClient:
    """
    Asynchronous Veri API client.

    Example:
        >>> import asyncio
        >>> from veri import AsyncVeriClient
        >>>
        >>> async def main():
        ...     async with AsyncVeriClient(api_key="your-api-key") as client:
        ...         result = await client.detect(image_bytes)
        ...         print(f"Is fake: {result.is_fake}")
        >>>
        >>> asyncio.run(main())
    """

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ) -> None:
        if not api_key:
            raise VeriValidationError("API key is required", "api_key")

        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries

        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=timeout,
            headers={
                "X-API-Key": api_key,
                "User-Agent": "veri-sdk-python/0.1.0",
                "Content-Type": "application/json",
            },
        )

    async def __aenter__(self) -> AsyncVeriClient:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    async def close(self) -> None:
        """Close the client and release resources."""
        await self._client.aclose()

    async def detect(
        self,
        image: ImageInput,
        *,
        options: DetectionOptions | None = None,
    ) -> DetectionResult:
        """Detect whether an image is AI-generated (async version)."""
        image_b64 = self._image_to_base64(image)
        payload: dict[str, Any] = {"image": image_b64}

        if options:
            payload.update(options.model_dump(by_alias=True, exclude_none=True))

        response = await self._request("POST", "/api/detect", json=payload)
        return DetectionResult.model_validate(response)

    async def detect_url(
        self,
        url: str,
        *,
        options: DetectionOptions | None = None,
    ) -> DetectionResult:
        """Detect an image from a URL (async version)."""
        if not url.startswith(("http://", "https://")):
            raise VeriValidationError("Invalid URL format", "url")

        payload: dict[str, Any] = {"url": url}
        if options:
            payload.update(options.model_dump(by_alias=True, exclude_none=True))

        response = await self._request("POST", "/api/detect/url", json=payload)
        return DetectionResult.model_validate(response)

    async def get_profile(self) -> dict[str, Any]:
        """Get the authenticated user's profile (async version)."""
        return await self._request("GET", "/api/user/profile")

    # ============ Private methods ============

    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs: Any,
    ) -> Any:
        """Make an async HTTP request with retries."""
        import asyncio

        last_error: Exception | None = None

        for attempt in range(self.max_retries):
            try:
                response = await self._client.request(method, endpoint, **kwargs)

                if response.status_code == 429:
                    retry_after = int(response.headers.get("retry-after", "60"))
                    request_id = response.headers.get("x-request-id")
                    raise VeriRateLimitError(
                        "Rate limit exceeded",
                        retry_after,
                        request_id,
                    )

                if response.status_code == 402:
                    error_data = self._safe_json(response)
                    request_id = response.headers.get("x-request-id")
                    raise VeriInsufficientCreditsError(
                        error_data.get("message", "Insufficient credits"),
                        request_id,
                    )

                if not response.is_success:
                    error_data = self._safe_json(response)
                    request_id = response.headers.get("x-request-id")
                    raise VeriAPIError(
                        error_data.get("message", f"Request failed: {response.status_code}"),
                        response.status_code,
                        error_data.get("code", "UNKNOWN_ERROR"),
                        request_id,
                    )

                return self._safe_json(response)

            except httpx.TimeoutException as e:
                raise VeriTimeoutError(
                    f"Request timed out after {self.timeout}s",
                    int(self.timeout * 1000),
                ) from e

            except VeriAPIError as e:
                if not e.is_retryable:
                    raise
                last_error = e

            except httpx.HTTPError as e:
                last_error = e

            # Exponential backoff
            if attempt < self.max_retries - 1:
                await asyncio.sleep(2**attempt)

        if last_error:
            raise last_error
        raise VeriAPIError("Request failed after retries", 500, "RETRY_EXHAUSTED")

    def _safe_json(self, response: httpx.Response) -> dict[str, Any]:
        """Safely parse JSON response, returning empty dict on failure."""
        if not response.content:
            return {}
        try:
            return response.json()
        except Exception:
            return {"message": response.text[:500] if response.text else "Unknown error"}

    def _image_to_base64(self, image: ImageInput) -> str:
        """Convert various image inputs to base64 string."""
        # Already base64 string
        if isinstance(image, str):
            if image.startswith("data:"):
                return image.split(",", 1)[1]
            if Path(image).exists():
                with open(image, "rb") as f:
                    return base64.b64encode(f.read()).decode("utf-8")
            return image

        # Path object
        if isinstance(image, Path):
            with open(image, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")

        # Bytes
        if isinstance(image, bytes):
            return base64.b64encode(image).decode("utf-8")

        # File-like object
        if hasattr(image, "read"):
            content = image.read()
            if isinstance(content, str):
                content = content.encode("utf-8")
            return base64.b64encode(content).decode("utf-8")

        raise VeriValidationError(
            "Invalid image format. Expected bytes, Path, file object, or base64 string",
            "image",
        )
