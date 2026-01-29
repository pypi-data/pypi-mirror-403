"""Goals API endpoints."""

from pybob_sdk._core.base_api import BaseAPI
from pybob_sdk.goals.models import (
    Goal,
    GoalCreateRequest,
    GoalCycle,
    GoalCycleMetadata,
    GoalCycleSearchRequest,
    GoalCycleSearchResponse,
    GoalMetadata,
    GoalSearchRequest,
    GoalSearchResponse,
    GoalStatusUpdateRequest,
    GoalType,
    GoalTypeMetadata,
    GoalTypeSearchRequest,
    GoalTypeSearchResponse,
    GoalUpdateRequest,
    KeyResult,
    KeyResultCreateRequest,
    KeyResultMetadata,
    KeyResultProgressUpdateRequest,
    KeyResultSearchRequest,
    KeyResultSearchResponse,
    KeyResultUpdateRequest,
)


class GoalsAPI(BaseAPI):
    """API for managing goals in Bob."""

    # Metadata Methods
    async def get_goal_type_metadata(self) -> GoalTypeMetadata:
        """Get goal type metadata.

        Returns:
            Goal type metadata.
        """
        response = await self._http.get("/goals/types/metadata")
        return self._parse_response(response, GoalTypeMetadata)

    async def get_goal_metadata(self) -> GoalMetadata:
        """Get goal metadata.

        Returns:
            Goal metadata.
        """
        response = await self._http.get("/goals/metadata")
        return self._parse_response(response, GoalMetadata)

    async def get_key_result_metadata(self) -> KeyResultMetadata:
        """Get key result metadata.

        Returns:
            Key result metadata.
        """
        response = await self._http.get("/goals/key-results/metadata")
        return self._parse_response(response, KeyResultMetadata)

    async def get_cycle_metadata(self) -> GoalCycleMetadata:
        """Get goal cycle metadata.

        Returns:
            Goal cycle metadata.
        """
        response = await self._http.get("/goals/cycles/metadata")
        return self._parse_response(response, GoalCycleMetadata)

    # Goal Type Methods
    async def search_goal_types(
        self,
        request: GoalTypeSearchRequest | None = None,
    ) -> list[GoalType]:
        """Search goal types.

        Args:
            request: The search request.

        Returns:
            List of matching goal types.
        """
        json_data = request.to_api_dict() if request else {}
        response = await self._http.post("/goals/types/search", json_data=json_data)
        parsed = self._parse_response(response, GoalTypeSearchResponse)
        return parsed.goal_types

    # Goal Methods
    async def search_goals(
        self,
        request: GoalSearchRequest | None = None,
    ) -> list[Goal]:
        """Search goals.

        Args:
            request: The search request.

        Returns:
            List of matching goals.
        """
        json_data = request.to_api_dict() if request else {}
        response = await self._http.post("/goals/search", json_data=json_data)
        parsed = self._parse_response(response, GoalSearchResponse)
        return parsed.goals

    async def create_goals(
        self,
        goals: list[GoalCreateRequest],
    ) -> list[Goal]:
        """Create one or more goals.

        Args:
            goals: List of goal data.

        Returns:
            List of created goals.
        """
        response = await self._http.post(
            "/goals",
            json_data={"goals": [g.to_api_dict() for g in goals]},
        )
        return self._parse_response_list(response, Goal, key="goals")

    async def update_goal_status(
        self,
        goal_id: str,
        request: GoalStatusUpdateRequest,
    ) -> None:
        """Update a goal's status.

        Args:
            goal_id: The goal ID.
            request: The status update request.
        """
        await self._http.patch(
            f"/goals/{goal_id}/status",
            json_data=request.to_api_dict(),
        )

    async def update_goal(
        self,
        goal_id: str,
        request: GoalUpdateRequest,
    ) -> None:
        """Update a goal.

        Args:
            goal_id: The goal ID.
            request: The update request.
        """
        await self._http.patch(
            f"/goals/{goal_id}",
            json_data=request.to_api_dict(),
        )

    async def delete_goal(self, goal_id: str) -> None:
        """Delete a goal.

        Args:
            goal_id: The goal ID.
        """
        await self._http.delete(f"/goals/{goal_id}")

    # Key Result Methods
    async def search_key_results(
        self,
        request: KeyResultSearchRequest | None = None,
    ) -> list[KeyResult]:
        """Search key results.

        Args:
            request: The search request.

        Returns:
            List of matching key results.
        """
        json_data = request.to_api_dict() if request else {}
        response = await self._http.post(
            "/goals/key-results/search", json_data=json_data
        )
        parsed = self._parse_response(response, KeyResultSearchResponse)
        return parsed.key_results

    async def create_key_results(
        self,
        key_results: list[KeyResultCreateRequest],
    ) -> list[KeyResult]:
        """Create one or more key results.

        Args:
            key_results: List of key result data.

        Returns:
            List of created key results.
        """
        response = await self._http.post(
            "/goals/key-results",
            json_data={"keyResults": [kr.to_api_dict() for kr in key_results]},
        )
        return self._parse_response_list(response, KeyResult, key="keyResults")

    async def update_key_result_progress(
        self,
        key_result_id: str,
        request: KeyResultProgressUpdateRequest,
    ) -> None:
        """Update a key result's progress.

        Args:
            key_result_id: The key result ID.
            request: The progress update request.
        """
        await self._http.patch(
            f"/goals/key-results/{key_result_id}/progress",
            json_data=request.to_api_dict(),
        )

    async def update_key_result(
        self,
        key_result_id: str,
        request: KeyResultUpdateRequest,
    ) -> None:
        """Update a key result's details.

        Args:
            key_result_id: The key result ID.
            request: The update request.
        """
        await self._http.patch(
            f"/goals/key-results/{key_result_id}",
            json_data=request.to_api_dict(),
        )

    async def delete_key_result(self, key_result_id: str) -> None:
        """Delete a key result.

        Args:
            key_result_id: The key result ID.
        """
        await self._http.delete(f"/goals/key-results/{key_result_id}")

    # Goal Cycle Methods
    async def search_cycles(
        self,
        request: GoalCycleSearchRequest | None = None,
    ) -> list[GoalCycle]:
        """Search goal cycles.

        Args:
            request: The search request.

        Returns:
            List of matching goal cycles.
        """
        json_data = request.to_api_dict() if request else {}
        response = await self._http.post("/goals/cycles/search", json_data=json_data)
        parsed = self._parse_response(response, GoalCycleSearchResponse)
        return parsed.cycles
