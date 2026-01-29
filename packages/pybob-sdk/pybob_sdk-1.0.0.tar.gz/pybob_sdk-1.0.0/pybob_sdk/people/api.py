"""People API endpoints."""

from typing import Any

from pybob_sdk._core.base_api import BaseAPI
from pybob_sdk.people.models import (
    Avatar,
    Employee,
    EmployeeCreateRequest,
    EmployeeSearchRequest,
    EmployeeSearchResponse,
    EmployeeUpdateRequest,
    PublicProfile,
    SearchFilter,
    TerminateRequest,
)


class PeopleAPI(BaseAPI):
    """API for managing people/employees in Bob."""

    async def search(
        self,
        fields: list[str] | None = None,
        filters: list[SearchFilter] | list[dict[str, Any]] | None = None,
        *,
        show_inactive: bool = False,
    ) -> EmployeeSearchResponse:
        """Search for employees.

        Args:
            fields: List of field paths to return (e.g., ["root.id", "root.fullName"]).
            filters: List of filters to apply.
            show_inactive: Whether to include inactive employees.

        Returns:
            The search response containing matching employees.
        """
        # Convert dict filters to SearchFilter if needed
        parsed_filters: list[SearchFilter] = []
        if filters:
            for f in filters:
                if isinstance(f, dict):
                    parsed_filters.append(SearchFilter.model_validate(f))
                else:
                    parsed_filters.append(f)

        request = EmployeeSearchRequest(
            fields=fields or [],
            filters=parsed_filters,
            show_inactive=show_inactive,
        )

        response = await self._http.post(
            "/people/search",
            json_data=request.to_api_dict(),
        )

        return self._parse_response(response, EmployeeSearchResponse)

    async def get(self, employee_id: str) -> Employee:
        """Get an employee by ID.

        Args:
            employee_id: The employee ID.

        Returns:
            The employee record.
        """
        response = await self._http.post(
            f"/people/{employee_id}",
            json_data={"fields": []},
        )
        return self._parse_response(response, Employee)

    async def get_public_profiles(self) -> list[PublicProfile]:
        """Get public profile information for all active employees.

        Returns:
            List of public profiles.
        """
        response = await self._http.get("/profiles")
        return self._parse_response_list(response, PublicProfile, key="employees")

    async def create(self, employee: EmployeeCreateRequest) -> Employee:
        """Create a new employee.

        Args:
            employee: The employee data.

        Returns:
            The created employee record.
        """
        response = await self._http.post(
            "/people",
            json_data=employee.to_api_dict(),
        )
        return self._parse_response(response, Employee)

    async def update(
        self,
        employee_id: str,
        employee: EmployeeUpdateRequest,
    ) -> None:
        """Update an employee.

        Args:
            employee_id: The employee ID.
            employee: The updated employee data.
        """
        await self._http.put(
            f"/people/{employee_id}",
            json_data=employee.to_api_dict(),
        )

    async def terminate(
        self,
        employee_id: str,
        termination: TerminateRequest,
    ) -> None:
        """Terminate an employee.

        Args:
            employee_id: The employee ID.
            termination: The termination details.
        """
        await self._http.post(
            f"/people/{employee_id}/terminate",
            json_data=termination.to_api_dict(),
        )

    async def revoke_access(self, employee_id: str) -> None:
        """Revoke access to Bob for an employee.

        Args:
            employee_id: The employee ID.
        """
        await self._http.post(f"/people/{employee_id}/uninvite")

    async def invite(
        self,
        employee_id: str,
        *,
        welcome_wizard_id: str | None = None,
    ) -> None:
        """Invite an employee with a welcome wizard.

        Args:
            employee_id: The employee ID.
            welcome_wizard_id: The welcome wizard ID to use.
        """
        path = f"/people/{employee_id}/invitations"
        if welcome_wizard_id:
            path = f"{path}/{welcome_wizard_id}"

        await self._http.post(path)

    async def set_start_date(
        self,
        employee_id: str,
        start_date: str,
    ) -> None:
        """Set or update an employee's start date.

        Args:
            employee_id: The employee ID.
            start_date: The start date in YYYY-MM-DD format.
        """
        await self._http.post(
            f"/people/{employee_id}/start-date",
            json_data={"startDate": start_date},
        )

    async def get_avatar_by_email(self, email: str) -> Avatar:
        """Get an employee's avatar by email.

        Args:
            email: The employee's email address.

        Returns:
            The avatar information.
        """
        response = await self._http.get(f"/avatars/{email}")
        return self._parse_response(response, Avatar)

    async def get_avatar_by_id(self, employee_id: str) -> Avatar:
        """Get an employee's avatar by ID.

        Args:
            employee_id: The employee ID.

        Returns:
            The avatar information.
        """
        response = await self._http.get(f"/avatars/employee/{employee_id}")
        return self._parse_response(response, Avatar)

    async def upload_avatar(
        self,
        employee_id: str,
        *,
        image_url: str,
    ) -> None:
        """Upload an employee's avatar from a URL.

        Args:
            employee_id: The employee ID.
            image_url: The URL of the image to upload.
        """
        await self._http.put(
            f"/people/{employee_id}/avatar",
            json_data={"url": image_url},
        )

    async def update_email(
        self,
        employee_id: str,
        *,
        email: str,
    ) -> None:
        """Update an employee's email address.

        Args:
            employee_id: The employee ID.
            email: The new email address.
        """
        await self._http.put(
            f"/people/{employee_id}/email",
            json_data={"email": email},
        )
