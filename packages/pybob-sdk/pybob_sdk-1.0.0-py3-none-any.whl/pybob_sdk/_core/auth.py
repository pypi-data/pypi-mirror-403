"""Authentication handling for the PyBob SDK."""

import base64

from pybob_sdk._core.settings import BobSettings


def build_auth_header(settings: BobSettings) -> str:
    """Build the Basic Auth header value from service account credentials.

    Args:
        settings: The Bob settings containing credentials.

    Returns:
        The Basic Auth header value.
    """
    credentials = f"{settings.service_account_id}:{settings.service_account_token}"
    encoded = base64.b64encode(credentials.encode()).decode()
    return f"Basic {encoded}"
