"""Test configuration and fixtures for PyBob SDK tests."""

import pytest


@pytest.fixture
def service_account_id() -> str:
    """Return a test service account ID."""
    return "test_service_account_id"


@pytest.fixture
def service_account_token() -> str:
    """Return a test service account token."""
    return "test_service_account_token"


@pytest.fixture
def base_url() -> str:
    """Return the test base URL."""
    return "https://api.hibob.com/v1"
