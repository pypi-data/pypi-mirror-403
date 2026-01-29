"""Models for the Onboarding API domain."""

from typing import Any

from pydantic import Field, field_validator

from pybob_sdk._core.base_model import BobModel


class OnboardingWizard(BobModel):
    """An onboarding wizard."""

    id: str | None = None

    @field_validator("id", mode="before")
    @classmethod
    def coerce_id_to_string(cls, v: int | str | None) -> str | None:
        """Coerce ID to string if it's an integer."""
        if v is None:
            return None
        return str(v)

    name: str | None = None
    description: str | None = None
    is_default: bool = Field(default=False, alias="isDefault")


class OnboardingWizardSummary(BobModel):
    """Summary of all onboarding wizards."""

    wizards: list[OnboardingWizard] = Field(default_factory=list)


class OnboardingWizardsResponse(BobModel):
    """Response containing onboarding wizards."""

    wizards: list[dict[str, Any]] = Field(default_factory=list)
