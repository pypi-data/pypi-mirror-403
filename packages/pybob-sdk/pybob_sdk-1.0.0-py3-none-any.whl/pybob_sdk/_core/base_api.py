"""Base API class for the PyBob SDK."""

from typing import Any, TypeVar

from pydantic import BaseModel

from pybob_sdk._core.http import HTTPClient

T = TypeVar("T", bound=BaseModel)


class BaseAPI:
    """Base class for all API domains.

    Provides common functionality for making API requests and
    parsing responses into Pydantic models.
    """

    def __init__(self, http_client: HTTPClient) -> None:
        """Initialise the API domain.

        Args:
            http_client: The HTTP client for making requests.
        """
        self._http = http_client

    def _parse_response(
        self,
        response: dict[str, Any] | list[Any] | None,
        model: type[T],
    ) -> T:
        """Parse a response dictionary into a Pydantic model.

        Args:
            response: The API response data.
            model: The Pydantic model class to parse into.

        Returns:
            The parsed model instance.

        Raises:
            ValueError: If the response is None or invalid.
        """
        if response is None:
            raise ValueError("Expected response data but received None")
        if isinstance(response, list):
            raise ValueError("Expected dict response but received list")
        return model.model_validate(response)

    def _parse_response_list(
        self,
        response: dict[str, Any] | list[Any] | None,
        model: type[T],
        *,
        key: str | None = None,
    ) -> list[T]:
        """Parse a response into a list of Pydantic models.

        Args:
            response: The API response data.
            model: The Pydantic model class to parse into.
            key: Optional key to extract the list from a dict response.

        Returns:
            A list of parsed model instances.
        """
        if response is None:
            return []

        if isinstance(response, dict):
            if key is None:
                raise ValueError("Response is a dict but no key was provided")
            items = response.get(key, [])
        else:
            items = response

        if not isinstance(items, list):
            raise ValueError(f"Expected list but received {type(items)}")

        return [model.model_validate(item) for item in items]

    def _build_params(
        self,
        *,
        include_none: bool = False,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Build query parameters, optionally excluding None values.

        Args:
            include_none: Whether to include None values.
            **kwargs: The parameter key-value pairs.

        Returns:
            A dictionary of query parameters.
        """
        if include_none:
            return kwargs
        return {k: v for k, v in kwargs.items() if v is not None}
