"""Workforce Planning API endpoints."""

from pybob_sdk._core.base_api import BaseAPI
from pybob_sdk.workforce.models import (
    Position,
    PositionBudget,
    PositionBudgetCreateRequest,
    PositionBudgetField,
    PositionBudgetFieldsResponse,
    PositionBudgetSearchRequest,
    PositionBudgetSearchResponse,
    PositionBudgetUpdateRequest,
    PositionCancellationRequest,
    PositionCreateRequest,
    PositionField,
    PositionFieldsResponse,
    PositionOpening,
    PositionOpeningCreateRequest,
    PositionOpeningField,
    PositionOpeningFieldsResponse,
    PositionOpeningSearchRequest,
    PositionOpeningSearchResponse,
    PositionOpeningUpdateRequest,
    PositionSearchRequest,
    PositionSearchResponse,
    PositionUpdateRequest,
)


class WorkforceAPI(BaseAPI):
    """API for workforce planning in Bob."""

    # Field Metadata Methods
    async def get_position_fields(self) -> list[PositionField]:
        """Get all position fields.

        Returns:
            List of position field definitions.
        """
        response = await self._http.get("/metadata/objects/position")
        if response is None:
            return []
        parsed = self._parse_response(response, PositionFieldsResponse)
        return parsed.fields

    async def get_opening_fields(self) -> list[PositionOpeningField]:
        """Get all position opening fields.

        Returns:
            List of position opening field definitions.
        """
        response = await self._http.get("/positions/position-openings/metadata")
        if response is None:
            return []
        parsed = self._parse_response(response, PositionOpeningFieldsResponse)
        return parsed.fields

    async def get_budget_fields(self) -> list[PositionBudgetField]:
        """Get all position budget fields.

        Returns:
            List of position budget field definitions.
        """
        response = await self._http.get("/positions/position-budget/metadata")
        if response is None:
            return []
        parsed = self._parse_response(response, PositionBudgetFieldsResponse)
        return parsed.fields

    # Position Methods
    async def search_positions(
        self,
        request: PositionSearchRequest | None = None,
    ) -> list[Position]:
        """Search positions.

        Args:
            request: The search request.

        Returns:
            List of matching positions.
        """
        json_data = request.to_api_dict() if request else {}
        response = await self._http.post(
            "/objects/position/search",
            json_data=json_data,
        )
        parsed = self._parse_response(response, PositionSearchResponse)
        return parsed.positions

    async def create_position(
        self,
        position: PositionCreateRequest,
    ) -> Position:
        """Create a position.

        Args:
            position: The position data.

        Returns:
            The created position.
        """
        response = await self._http.post(
            "/workforce-planning/positions",
            json_data=position.to_api_dict(),
        )
        return self._parse_response(response, Position)

    async def update_position(
        self,
        position_id: str,
        position: PositionUpdateRequest,
    ) -> None:
        """Update a position.

        Args:
            position_id: The position ID.
            position: The updated position data.
        """
        await self._http.patch(
            f"/workforce-planning/positions/{position_id}",
            json_data=position.to_api_dict(),
        )

    async def schedule_cancellation(
        self,
        request: PositionCancellationRequest,
    ) -> None:
        """Schedule position cancellation.

        Args:
            request: The cancellation request.
        """
        await self._http.post(
            "/workforce-planning/positions/cancel",
            json_data=request.to_api_dict(),
        )

    async def cancel_position(self, position_id: str) -> None:
        """Cancel a position immediately.

        Args:
            position_id: The position ID.
        """
        await self._http.patch(f"/workforce-planning/positions/{position_id}/cancel")

    # Position Opening Methods
    async def search_openings(
        self,
        request: PositionOpeningSearchRequest | None = None,
    ) -> list[PositionOpening]:
        """Search position openings.

        Args:
            request: The search request.

        Returns:
            List of matching position openings.
        """
        json_data = request.to_api_dict() if request else {}
        response = await self._http.post(
            "/positions/position-openings/search",
            json_data=json_data,
        )
        parsed = self._parse_response(response, PositionOpeningSearchResponse)
        return parsed.openings

    async def create_opening(
        self,
        opening: PositionOpeningCreateRequest,
    ) -> PositionOpening:
        """Create a position opening.

        Args:
            opening: The opening data.

        Returns:
            The created opening.
        """
        response = await self._http.post(
            "/workforce-planning/openings",
            json_data=opening.to_api_dict(),
        )
        return self._parse_response(response, PositionOpening)

    async def update_opening(
        self,
        opening_id: str,
        opening: PositionOpeningUpdateRequest,
    ) -> None:
        """Update a position opening.

        Args:
            opening_id: The opening ID.
            opening: The updated opening data.
        """
        await self._http.patch(
            f"/workforce-planning/openings/{opening_id}",
            json_data=opening.to_api_dict(),
        )

    async def delete_opening(self, opening_id: str) -> None:
        """Delete a position opening.

        Args:
            opening_id: The opening ID.
        """
        await self._http.delete(f"/workforce-planning/openings/{opening_id}")

    # Position Budget Methods
    async def search_budgets(
        self,
        request: PositionBudgetSearchRequest | None = None,
    ) -> list[PositionBudget]:
        """Search position budgets.

        Args:
            request: The search request.

        Returns:
            List of matching position budgets.
        """
        json_data = request.to_api_dict() if request else {}
        response = await self._http.post(
            "/positions/position-budget/search",
            json_data=json_data,
        )
        parsed = self._parse_response(response, PositionBudgetSearchResponse)
        return parsed.budgets

    async def create_budget(
        self,
        budget: PositionBudgetCreateRequest,
    ) -> PositionBudget:
        """Create a position budget.

        Args:
            budget: The budget data.

        Returns:
            The created budget.
        """
        response = await self._http.post(
            "/workforce-planning/budgets",
            json_data=budget.to_api_dict(),
        )
        return self._parse_response(response, PositionBudget)

    async def update_budget(
        self,
        budget_id: str,
        budget: PositionBudgetUpdateRequest,
    ) -> None:
        """Update a position budget.

        Args:
            budget_id: The budget ID.
            budget: The updated budget data.
        """
        await self._http.patch(
            f"/workforce-planning/budgets/{budget_id}",
            json_data=budget.to_api_dict(),
        )
