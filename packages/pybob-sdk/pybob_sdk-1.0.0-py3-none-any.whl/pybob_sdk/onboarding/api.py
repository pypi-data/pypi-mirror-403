"""Onboarding API endpoints."""

from pybob_sdk._core.base_api import BaseAPI
from pybob_sdk.onboarding.models import OnboardingWizard


class OnboardingAPI(BaseAPI):
    """API for managing onboarding in Bob."""

    async def get_wizards(self) -> list[OnboardingWizard]:
        """Get a summary of all onboarding wizards.

        Returns:
            List of onboarding wizards.
        """
        response = await self._http.get("/onboarding/wizards")
        return self._parse_response_list(response, OnboardingWizard, key="wizards")
