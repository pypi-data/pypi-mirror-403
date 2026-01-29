"""Metadata API endpoints."""

from pybob_sdk._core.base_api import BaseAPI
from pybob_sdk.metadata.models import (
    CompanyList,
    CompanyListItem,
    EmployeeField,
    FieldCreateRequest,
    FieldsResponse,
    FieldUpdateRequest,
    ListItemCreateRequest,
    ListItemUpdateRequest,
    ListsResponse,
)


class MetadataAPI(BaseAPI):
    """API for managing metadata (fields and lists) in Bob."""

    # Employee Fields Methods
    async def get_fields(self) -> list[EmployeeField]:
        """Get all employee fields.

        Returns:
            List of employee field definitions.
        """
        response = await self._http.get("/company/people/fields")

        # Handle both list and wrapped dict responses
        if isinstance(response, list):
            return [EmployeeField.model_validate(field) for field in response]

        if response is None:
            return []

        parsed = self._parse_response(response, FieldsResponse)
        return parsed.fields

    async def create_field(self, field: FieldCreateRequest) -> EmployeeField:
        """Create a new employee field.

        Args:
            field: The field data.

        Returns:
            The created field.
        """
        response = await self._http.post(
            "/company/people/fields",
            json_data=field.to_api_dict(),
        )
        return self._parse_response(response, EmployeeField)

    async def update_field(
        self,
        field_id: str,
        field: FieldUpdateRequest,
    ) -> None:
        """Update an employee field.

        Args:
            field_id: The field ID.
            field: The updated field data.
        """
        await self._http.put(
            f"/company/people/fields/{field_id}",
            json_data=field.to_api_dict(),
        )

    async def delete_field(self, field_id: str) -> None:
        """Delete an employee field.

        Args:
            field_id: The field ID.
        """
        await self._http.delete(f"/company/people/fields/{field_id}")

    # Company Lists Methods
    async def get_lists(self) -> list[CompanyList]:
        """Get all company lists.

        Returns:
            List of company lists.
        """
        response = await self._http.get("/company/named-lists")
        parsed = self._parse_response(response, ListsResponse)
        return parsed.lists

    async def get_list(self, list_name: str) -> CompanyList:
        """Get a specific company list by name.

        Args:
            list_name: The list name.

        Returns:
            The company list.
        """
        response = await self._http.get(f"/company/named-lists/{list_name}")
        return self._parse_response(response, CompanyList)

    async def create_list_item(
        self,
        list_name: str,
        item: ListItemCreateRequest,
    ) -> CompanyListItem:
        """Add a new item to a company list.

        Args:
            list_name: The list name.
            item: The list item data.

        Returns:
            The created list item.
        """
        response = await self._http.post(
            f"/company/named-lists/{list_name}",
            json_data=item.to_api_dict(),
        )
        return self._parse_response(response, CompanyListItem)

    async def update_list_item(
        self,
        list_name: str,
        item_id: str,
        item: ListItemUpdateRequest,
    ) -> None:
        """Update a list item.

        Args:
            list_name: The list name.
            item_id: The item ID.
            item: The updated item data.
        """
        await self._http.put(
            f"/company/named-lists/{list_name}/{item_id}",
            json_data=item.to_api_dict(),
        )

    async def delete_list_item(
        self,
        list_name: str,
        item_id: str,
    ) -> None:
        """Delete a list item.

        Args:
            list_name: The list name.
            item_id: The item ID.
        """
        await self._http.delete(f"/company/named-lists/{list_name}/{item_id}")
