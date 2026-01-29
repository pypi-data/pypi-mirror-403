"""Models for the People API domain."""

from datetime import date
from typing import Any

from pydantic import Field

from pybob_sdk._core.base_model import BobModel


class SearchFilter(BobModel):
    """A filter for searching employees."""

    field_path: str = Field(alias="fieldPath")
    operator: str = Field(
        description="Filter operator: equals, notEquals, contains, etc."
    )
    values: list[str] = Field(default_factory=list)


class EmployeeSearchRequest(BobModel):
    """Request body for employee search."""

    fields: list[str] = Field(
        default_factory=list,
        description="Fields to return in the response",
    )
    filters: list[SearchFilter] = Field(
        default_factory=list,
        description="Filters to apply to the search",
    )
    show_inactive: bool = Field(
        default=False,
        alias="showInactive",
        description="Whether to include inactive employees",
    )


class EmployeeSearchResult(BobModel):
    """A single employee result from a search."""

    id: str
    full_name: str | None = Field(default=None, alias="fullName")
    email: str | None = None
    # Additional dynamic fields from the API
    extra_fields: dict[str, Any] = Field(default_factory=dict)

    def model_post_init(self, __context: Any) -> None:
        """Process additional fields from the API response."""
        # Store any extra fields that aren't explicitly defined
        if hasattr(self, "__pydantic_extra__"):
            self.extra_fields = dict(self.__pydantic_extra__ or {})


class EmployeeSearchResponse(BobModel):
    """Response from the employee search endpoint."""

    employees: list[dict[str, Any]] = Field(default_factory=list)


class Employee(BobModel):
    """An employee record."""

    id: str
    first_name: str | None = Field(default=None, alias="firstName")
    surname: str | None = None
    full_name: str | None = Field(default=None, alias="fullName")
    display_name: str | None = Field(default=None, alias="displayName")
    email: str | None = None
    personal_email: str | None = Field(default=None, alias="personalEmail")
    work_phone: str | None = Field(default=None, alias="workPhone")
    mobile_phone: str | None = Field(default=None, alias="mobilePhone")
    site: str | None = None
    site_id: int | None = Field(default=None, alias="siteId")
    department: str | None = None
    title: str | None = None
    about: str | None = None
    avatar_url: str | None = Field(default=None, alias="avatarUrl")
    cover_image_url: str | None = Field(default=None, alias="coverImageUrl")
    start_date: date | None = Field(default=None, alias="startDate")
    creation_date_time: str | None = Field(default=None, alias="creationDateTime")
    tenure_years: float | None = Field(default=None, alias="tenureYears")
    direct_reports: int | None = Field(default=None, alias="directReports")
    company_id: int | None = Field(default=None, alias="companyId")
    work: dict[str, Any] | None = None
    home: dict[str, Any] | None = None
    financial: dict[str, Any] | None = None
    internal: dict[str, Any] | None = None


class EmployeeCreateRequest(BobModel):
    """Request body for creating a new employee."""

    first_name: str = Field(alias="firstName")
    surname: str
    email: str
    site: str | None = None
    department: str | None = None
    title: str | None = None
    start_date: date | None = Field(default=None, alias="startDate")
    personal_email: str | None = Field(default=None, alias="personalEmail")
    work_phone: str | None = Field(default=None, alias="workPhone")
    mobile_phone: str | None = Field(default=None, alias="mobilePhone")
    about: str | None = None
    work: dict[str, Any] | None = None
    home: dict[str, Any] | None = None
    financial: dict[str, Any] | None = None


class EmployeeUpdateRequest(BobModel):
    """Request body for updating an employee."""

    first_name: str | None = Field(default=None, alias="firstName")
    surname: str | None = None
    email: str | None = None
    display_name: str | None = Field(default=None, alias="displayName")
    site: str | None = None
    department: str | None = None
    title: str | None = None
    about: str | None = None
    personal_email: str | None = Field(default=None, alias="personalEmail")
    work_phone: str | None = Field(default=None, alias="workPhone")
    mobile_phone: str | None = Field(default=None, alias="mobilePhone")
    work: dict[str, Any] | None = None
    home: dict[str, Any] | None = None
    financial: dict[str, Any] | None = None


class TerminateRequest(BobModel):
    """Request body for terminating an employee."""

    termination_date: date = Field(alias="terminationDate")
    termination_reason: str | None = Field(default=None, alias="terminationReason")
    reason_type: str | None = Field(default=None, alias="reasonType")
    notice_period: dict[str, Any] | None = Field(default=None, alias="noticePeriod")


class PublicProfile(BobModel):
    """Public profile information for an employee."""

    id: str
    display_name: str | None = Field(default=None, alias="displayName")
    email: str | None = None
    avatar_url: str | None = Field(default=None, alias="avatarUrl")
    site: str | None = None
    department: str | None = None
    title: str | None = None


class Avatar(BobModel):
    """Avatar information for an employee."""

    url: str | None = None
