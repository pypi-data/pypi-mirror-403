"""Settings for the PyBob SDK."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class BobSettings(BaseSettings):
    """Settings for the Bob API client."""

    model_config = SettingsConfigDict(
        env_prefix="BOB_",  # Environment variables are prefixed with BOB_
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    service_account_id: str | None = Field(
        default=None,
        description="The service account ID for authentication",
    )
    service_account_token: str | None = Field(
        default=None,
        description="The service account token for authentication",
    )
    base_url: str = Field(
        default="https://api.hibob.com/v1",
        description="The base URL for the Bob API",
    )
    timeout: float = Field(
        default=30.0,
        description="Request timeout in seconds",
    )

    def is_configured(self) -> bool:
        """Check if the required credentials are configured.

        Returns:
            True if both service_account_id and service_account_token are set.
        """
        return bool(self.service_account_id and self.service_account_token)


def get_settings() -> BobSettings:
    """Get the Bob settings from environment variables.

    Returns:
        The Bob settings instance.
    """
    return BobSettings()
