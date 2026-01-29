"""HTTP client for the PyBob SDK."""

import logging
from typing import Any

import httpx

from pybob_sdk._core.auth import build_auth_header
from pybob_sdk._core.settings import BobSettings
from pybob_sdk.exceptions import (
    BobAPIError,
    BobAuthenticationError,
    BobForbiddenError,
    BobNotFoundError,
    BobRateLimitError,
    BobServerError,
    BobValidationError,
)

logger = logging.getLogger(__name__)


class HTTPClient:
    """Async HTTP client for the Bob API."""

    def __init__(self, settings: BobSettings) -> None:
        """Initialise the HTTP client.

        Args:
            settings: The Bob settings.
        """
        self._settings = settings
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "HTTPClient":
        """Enter the async context manager."""
        await self._ensure_client()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Exit the async context manager."""
        await self.close()

    async def _ensure_client(self) -> httpx.AsyncClient:
        """Ensure the HTTP client is initialised.

        Returns:
            The initialised HTTP client.
        """
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self._settings.base_url,
                headers={
                    "Authorization": build_auth_header(self._settings),
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                timeout=httpx.Timeout(self._settings.timeout),
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    def _handle_error_response(self, response: httpx.Response) -> None:
        """Handle error responses from the API.

        Args:
            response: The HTTP response.

        Raises:
            BobAPIError: The appropriate exception for the status code.
        """
        try:
            body = response.json()
        except Exception:
            body = None

        status_code = response.status_code

        if status_code == 401:
            raise BobAuthenticationError(response_body=body)
        if status_code == 403:
            raise BobForbiddenError(response_body=body)
        if status_code == 404:
            raise BobNotFoundError(response_body=body)
        if status_code == 400:
            message = "Request validation failed."
            if body and isinstance(body, dict):
                message = body.get("message", message)
            raise BobValidationError(message=message, response_body=body)
        if status_code == 429:
            retry_after = response.headers.get("Retry-After")
            raise BobRateLimitError(
                retry_after=int(retry_after) if retry_after else None,
                response_body=body,
            )
        if status_code >= 500:
            raise BobServerError(status_code=status_code, response_body=body)

        raise BobAPIError(
            message=f"API request failed with status {status_code}",
            status_code=status_code,
            response_body=body,
        )

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
        data: Any | None = None,
        files: dict[str, Any] | None = None,
    ) -> dict[str, Any] | list[Any] | None:
        """Make an HTTP request to the Bob API.

        Args:
            method: The HTTP method.
            path: The API path.
            params: Query parameters.
            json_data: JSON body data.
            data: Form data.
            files: Files to upload.

        Returns:
            The JSON response data, or None for empty responses.

        Raises:
            BobAPIError: If the request fails.
        """
        client = await self._ensure_client()

        logger.debug(
            "( http | HTTPClient | request ) %s %s",
            method,
            path,
        )

        # Build request kwargs
        request_kwargs: dict[str, Any] = {}
        if params:
            request_kwargs["params"] = params
        if json_data is not None:
            request_kwargs["json"] = json_data
        if data is not None:
            request_kwargs["data"] = data
        if files is not None:
            request_kwargs["files"] = files
            # Remove Content-Type header for multipart uploads
            request_kwargs["headers"] = {"Content-Type": None}

        response = await client.request(method, path, **request_kwargs)

        if not response.is_success:
            self._handle_error_response(response)

        # Handle empty responses
        if response.status_code == 204 or not response.content:
            return None

        # Try to parse JSON, return None if empty/invalid
        try:
            return response.json()  # type: ignore[no-any-return]
        except Exception:
            # Empty or invalid JSON response
            return None

    async def get(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any] | list[Any] | None:
        """Make a GET request.

        Args:
            path: The API path.
            params: Query parameters.

        Returns:
            The JSON response data.
        """
        return await self.request("GET", path, params=params)

    async def post(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
        data: Any | None = None,
        files: dict[str, Any] | None = None,
    ) -> dict[str, Any] | list[Any] | None:
        """Make a POST request.

        Args:
            path: The API path.
            params: Query parameters.
            json_data: JSON body data.
            data: Form data.
            files: Files to upload.

        Returns:
            The JSON response data.
        """
        return await self.request(
            "POST",
            path,
            params=params,
            json_data=json_data,
            data=data,
            files=files,
        )

    async def put(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
    ) -> dict[str, Any] | list[Any] | None:
        """Make a PUT request.

        Args:
            path: The API path.
            params: Query parameters.
            json_data: JSON body data.

        Returns:
            The JSON response data.
        """
        return await self.request("PUT", path, params=params, json_data=json_data)

    async def patch(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
    ) -> dict[str, Any] | list[Any] | None:
        """Make a PATCH request.

        Args:
            path: The API path.
            params: Query parameters.
            json_data: JSON body data.

        Returns:
            The JSON response data.
        """
        return await self.request("PATCH", path, params=params, json_data=json_data)

    async def delete(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any] | list[Any] | None:
        """Make a DELETE request.

        Args:
            path: The API path.
            params: Query parameters.

        Returns:
            The JSON response data.
        """
        return await self.request("DELETE", path, params=params)
