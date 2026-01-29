"""Time Off API endpoints."""

from datetime import date

from pybob_sdk._core.base_api import BaseAPI
from pybob_sdk.time_off.models import (
    BalanceAdjustment,
    BalanceAdjustmentCreateRequest,
    OutOfOfficeEntry,
    OutOfOfficeResponse,
    PoliciesResponse,
    Policy,
    PolicyDetails,
    PolicyTypesResponse,
    ReasonCode,
    ReasonCodesResponse,
    TimeOffBalance,
    TimeOffChangesResponse,
    TimeOffRequest,
    TimeOffRequestChange,
    TimeOffRequestCreateRequest,
)


class TimeOffAPI(BaseAPI):
    """API for managing time off in Bob."""

    # Time Off Request Methods
    async def create_request(
        self,
        request: TimeOffRequestCreateRequest,
    ) -> TimeOffRequest:
        """Submit a new time off request.

        Args:
            request: The time off request data.

        Returns:
            The created time off request.
        """
        response = await self._http.post(
            "/timeoff/employees/requests",
            json_data=request.to_api_dict(),
        )
        return self._parse_response(response, TimeOffRequest)

    async def get_request(self, request_id: int) -> TimeOffRequest:
        """Get details of a time off request.

        Args:
            request_id: The request ID.

        Returns:
            The time off request.
        """
        response = await self._http.get(f"/timeoff/requests/{request_id}")
        return self._parse_response(response, TimeOffRequest)

    async def cancel_request(self, request_id: int) -> None:
        """Cancel a time off request.

        Args:
            request_id: The request ID.
        """
        await self._http.delete(f"/timeoff/requests/{request_id}")

    async def get_request_changes(
        self,
        *,
        since: str | None = None,
        until: str | None = None,
    ) -> list[TimeOffRequestChange]:
        """Get time off request changes.

        Args:
            since: Start datetime (ISO 8601 format).
            until: End datetime (ISO 8601 format).

        Returns:
            List of time off request changes.
        """
        params = self._build_params(since=since, until=until)
        response = await self._http.get(
            "/timeoff/requests/changes",
            params=params or None,
        )
        parsed = self._parse_response(response, TimeOffChangesResponse)
        return parsed.changes

    # Out of Office Methods
    async def get_whos_out(
        self,
        *,
        from_date: date | str | None = None,
        to_date: date | str | None = None,
        include_pending: bool = False,
        include_private: bool = False,
    ) -> list[OutOfOfficeEntry]:
        """Get a list of who's out of the office.

        Args:
            from_date: Start date.
            to_date: End date.
            include_pending: Include pending requests.
            include_private: Include private requests.

        Returns:
            List of out of office entries.
        """
        params = self._build_params(
            from_date=str(from_date) if from_date else None,
            to_date=str(to_date) if to_date else None,
            includePending=include_pending if include_pending else None,
            includePrivate=include_private if include_private else None,
        )
        response = await self._http.get("/timeoff/outtoday", params=params or None)
        parsed = self._parse_response(response, OutOfOfficeResponse)
        return parsed.outs

    async def get_whos_out_today(
        self,
        *,
        target_date: date | str | None = None,
    ) -> list[OutOfOfficeEntry]:
        """Get a list of who's out today or on a specific date.

        Args:
            target_date: The target date (defaults to today).

        Returns:
            List of out of office entries.
        """
        path = "/timeoff/outtoday"
        if target_date:
            path = f"{path}/{target_date}"

        response = await self._http.get(path)
        parsed = self._parse_response(response, OutOfOfficeResponse)
        return parsed.outs

    # Policy Methods
    async def get_policy_type_reason_codes(
        self,
        policy_type: str,
    ) -> list[ReasonCode]:
        """Get reason codes for a policy type.

        Args:
            policy_type: The policy type name.

        Returns:
            List of reason codes.
        """
        response = await self._http.get(f"/timeoff/policy-types/{policy_type}/reasons")
        parsed = self._parse_response(response, ReasonCodesResponse)
        return parsed.reason_codes

    async def add_policy_type_reason_codes(
        self,
        policy_type: str,
        reason_codes: list[str],
    ) -> None:
        """Add reason codes to a policy type.

        Args:
            policy_type: The policy type name.
            reason_codes: List of reason codes to add.
        """
        await self._http.post(
            f"/timeoff/policy-types/{policy_type}/reasons",
            json_data={"reasonCodes": reason_codes},
        )

    async def get_policy_type_details(self, policy_type: str) -> PolicyDetails:
        """Get details of a policy type.

        Args:
            policy_type: The policy type name.

        Returns:
            The policy type details.
        """
        response = await self._http.get(f"/timeoff/policy-types/{policy_type}")
        return self._parse_response(response, PolicyDetails)

    async def get_policy_types(self) -> list[str]:
        """Get all policy type names.

        Returns:
            List of policy type names.
        """
        response = await self._http.get("/timeoff/policy-types")

        # Handle both list of strings and wrapped response
        if isinstance(response, list):
            return [str(pt) for pt in response]

        if response is None:
            return []

        parsed = self._parse_response(response, PolicyTypesResponse)
        return parsed.policy_types

    async def get_policy(
        self,
        policy_type: str,
        policy_name: str,
    ) -> Policy:
        """Get details of a policy.

        Args:
            policy_type: The policy type name.
            policy_name: The policy name.

        Returns:
            The policy details.
        """
        response = await self._http.get(
            f"/timeoff/policy-types/{policy_type}/policies/{policy_name}"
        )
        return self._parse_response(response, Policy)

    async def get_policies(self, policy_type: str) -> list[Policy]:
        """Get all policies for a policy type.

        Args:
            policy_type: The policy type name.

        Returns:
            List of policies.
        """
        response = await self._http.get(f"/timeoff/policy-types/{policy_type}/policies")
        parsed = self._parse_response(response, PoliciesResponse)
        return parsed.policies

    # Balance Methods
    async def get_balance(
        self,
        employee_id: str,
        *,
        policy_type: str | None = None,
        target_date: date | str | None = None,
    ) -> list[TimeOffBalance]:
        """Get time off balance for an employee.

        Args:
            employee_id: The employee ID.
            policy_type: Optional policy type to filter by.
            target_date: Optional date for the balance.

        Returns:
            List of time off balances.
        """
        params = self._build_params(
            policyType=policy_type,
            date=str(target_date) if target_date else None,
        )
        response = await self._http.get(
            f"/timeoff/employees/{employee_id}/balance",
            params=params or None,
        )
        return self._parse_response_list(response, TimeOffBalance, key="balances")

    async def create_balance_adjustment(
        self,
        adjustment: BalanceAdjustmentCreateRequest,
    ) -> BalanceAdjustment:
        """Create a balance adjustment.

        Args:
            adjustment: The balance adjustment data.

        Returns:
            The created balance adjustment.
        """
        response = await self._http.post(
            "/timeoff/employees/adjustments",
            json_data=adjustment.to_api_dict(),
        )
        return self._parse_response(response, BalanceAdjustment)
