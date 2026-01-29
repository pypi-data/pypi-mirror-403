"""Base Pydantic model configuration for the PyBob SDK."""

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class BobModel(BaseModel):
    """Base model for all Bob API models.

    Provides consistent configuration across all models:
    - Allows population by field name or alias
    - Converts camelCase API fields to snake_case
    - Validates assignments
    - Strips whitespace from strings
    """

    model_config = ConfigDict(
        populate_by_name=True,
        validate_assignment=True,
        str_strip_whitespace=True,
        extra="ignore",
    )

    def to_api_dict(self, *, exclude_none: bool = True) -> dict[str, Any]:
        """Convert the model to a dictionary suitable for API requests.

        Uses field aliases (camelCase) for API compatibility.

        Args:
            exclude_none: Whether to exclude None values.

        Returns:
            A dictionary with camelCase keys for the API.
        """
        return self.model_dump(
            by_alias=True,
            exclude_none=exclude_none,
            mode="json",
        )


class PaginatedResponse(BobModel):
    """Base model for paginated API responses."""

    pass


def parse_date(value: str | date | None) -> date | None:
    """Parse a date string or date object.

    Args:
        value: The date string (YYYY-MM-DD) or date object.

    Returns:
        The parsed date or None.
    """
    if value is None:
        return None
    if isinstance(value, date):
        return value
    return datetime.strptime(value, "%Y-%m-%d").date()


def parse_datetime(value: str | datetime | None) -> datetime | None:
    """Parse a datetime string or datetime object.

    Args:
        value: The datetime string (ISO 8601) or datetime object.

    Returns:
        The parsed datetime or None.
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    # Handle various ISO 8601 formats
    for fmt in [
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
    ]:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    raise ValueError(f"Unable to parse datetime: {value}")
