"""PyBob SDK - An unofficial Python SDK for the HiBob HR API."""

from pybob_sdk._core.settings import BobSettings, get_settings
from pybob_sdk.client import Bob
from pybob_sdk.exceptions import (
    BobAPIError,
    BobAuthenticationError,
    BobNotFoundError,
    BobRateLimitError,
    BobValidationError,
)

__all__ = [
    "Bob",
    "BobAPIError",
    "BobAuthenticationError",
    "BobNotFoundError",
    "BobRateLimitError",
    "BobSettings",
    "BobValidationError",
    "get_settings",
]

__version__ = "0.1.0"
