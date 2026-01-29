"""Models for the Metadata API domain."""

from typing import Any

from pydantic import Field

from pybob_sdk._core.base_model import BobModel


class EmployeeField(BobModel):
    """An employee field definition."""

    id: str | None = None
    name: str | None = None
    category: str | None = None
    description: str | None = None
    type: str | None = None
    json_path: str | None = Field(default=None, alias="jsonPath")
    historical: bool = False
    type_data: dict[str, Any] | None = Field(default=None, alias="typeData")


class FieldCreateRequest(BobModel):
    """Request body for creating a new field."""

    name: str
    category: str
    description: str | None = None
    type: str
    historical: bool = False
    type_data: dict[str, Any] | None = Field(default=None, alias="typeData")


class FieldUpdateRequest(BobModel):
    """Request body for updating a field."""

    name: str | None = None
    description: str | None = None
    type_data: dict[str, Any] | None = Field(default=None, alias="typeData")


class CompanyListItem(BobModel):
    """An item in a company list."""

    id: str | None = None
    name: str | None = None
    value: str | None = None
    archived: bool = False


class CompanyList(BobModel):
    """A company list definition."""

    name: str | None = None
    items: list[CompanyListItem] = Field(default_factory=list)


class ListItemCreateRequest(BobModel):
    """Request body for creating a list item."""

    name: str
    parent_id: str | None = Field(default=None, alias="parentId")


class ListItemUpdateRequest(BobModel):
    """Request body for updating a list item."""

    name: str | None = None
    archived: bool | None = None


class FieldsResponse(BobModel):
    """Response containing employee fields."""

    fields: list[EmployeeField] = Field(default_factory=list)


class ListsResponse(BobModel):
    """Response containing company lists."""

    lists: list[CompanyList] = Field(default_factory=list)
