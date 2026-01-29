"""Models for the Workforce Planning API domain."""

from datetime import date
from typing import Any

from pydantic import Field

from pybob_sdk._core.base_model import BobModel


# Field Metadata Models
class PositionField(BobModel):
    """A position field definition."""

    id: str | None = None
    name: str | None = None
    type: str | None = None
    description: str | None = None


class PositionOpeningField(BobModel):
    """A position opening field definition."""

    id: str | None = None
    name: str | None = None
    type: str | None = None
    description: str | None = None


class PositionBudgetField(BobModel):
    """A position budget field definition."""

    id: str | None = None
    name: str | None = None
    type: str | None = None
    description: str | None = None


# Position Models
class Position(BobModel):
    """A position."""

    id: str | None = None
    name: str | None = None
    department: str | None = None
    department_id: str | None = Field(default=None, alias="departmentId")
    site: str | None = None
    site_id: str | None = Field(default=None, alias="siteId")
    reports_to_id: str | None = Field(default=None, alias="reportsToId")
    job_profile_id: str | None = Field(default=None, alias="jobProfileId")
    status: str | None = None
    employee_id: str | None = Field(default=None, alias="employeeId")


class PositionSearchRequest(BobModel):
    """Request body for searching positions."""

    filters: list[dict[str, Any]] = Field(default_factory=list)
    fields: list[str] = Field(default_factory=list)


class PositionCreateRequest(BobModel):
    """Request body for creating a position."""

    name: str
    department: str | None = None
    department_id: str | None = Field(default=None, alias="departmentId")
    site: str | None = None
    site_id: str | None = Field(default=None, alias="siteId")
    reports_to_id: str | None = Field(default=None, alias="reportsToId")
    job_profile_id: str | None = Field(default=None, alias="jobProfileId")


class PositionUpdateRequest(BobModel):
    """Request body for updating a position."""

    name: str | None = None
    department: str | None = None
    department_id: str | None = Field(default=None, alias="departmentId")
    site: str | None = None
    site_id: str | None = Field(default=None, alias="siteId")
    reports_to_id: str | None = Field(default=None, alias="reportsToId")
    job_profile_id: str | None = Field(default=None, alias="jobProfileId")


# Position Opening Models
class PositionOpening(BobModel):
    """A position opening."""

    id: str | None = None
    position_id: str | None = Field(default=None, alias="positionId")
    status: str | None = None
    start_date: date | None = Field(default=None, alias="startDate")
    employment_type: str | None = Field(default=None, alias="employmentType")
    reason: str | None = None


class PositionOpeningSearchRequest(BobModel):
    """Request body for searching position openings."""

    filters: list[dict[str, Any]] = Field(default_factory=list)
    fields: list[str] = Field(default_factory=list)


class PositionOpeningCreateRequest(BobModel):
    """Request body for creating a position opening."""

    position_id: str = Field(alias="positionId")
    start_date: date | None = Field(default=None, alias="startDate")
    employment_type: str | None = Field(default=None, alias="employmentType")
    reason: str | None = None


class PositionOpeningUpdateRequest(BobModel):
    """Request body for updating a position opening."""

    start_date: date | None = Field(default=None, alias="startDate")
    employment_type: str | None = Field(default=None, alias="employmentType")
    reason: str | None = None


# Position Budget Models
class PositionBudget(BobModel):
    """A position budget."""

    id: str | None = None
    position_id: str | None = Field(default=None, alias="positionId")
    fiscal_year: int | None = Field(default=None, alias="fiscalYear")
    amount: float | None = None
    currency: str | None = None


class PositionBudgetSearchRequest(BobModel):
    """Request body for searching position budgets."""

    filters: list[dict[str, Any]] = Field(default_factory=list)
    fields: list[str] = Field(default_factory=list)


class PositionBudgetCreateRequest(BobModel):
    """Request body for creating a position budget."""

    position_id: str = Field(alias="positionId")
    fiscal_year: int = Field(alias="fiscalYear")
    amount: float
    currency: str | None = None


class PositionBudgetUpdateRequest(BobModel):
    """Request body for updating a position budget."""

    amount: float | None = None
    currency: str | None = None


# Position Cancellation Models
class PositionCancellationRequest(BobModel):
    """Request body for scheduling position cancellation."""

    position_ids: list[str] = Field(alias="positionIds")
    cancellation_date: date = Field(alias="cancellationDate")
    reason: str | None = None


# Response Models
class PositionFieldsResponse(BobModel):
    """Response containing position fields."""

    fields: list[PositionField] = Field(default_factory=list)


class PositionOpeningFieldsResponse(BobModel):
    """Response containing position opening fields."""

    fields: list[PositionOpeningField] = Field(default_factory=list)


class PositionBudgetFieldsResponse(BobModel):
    """Response containing position budget fields."""

    fields: list[PositionBudgetField] = Field(default_factory=list)


class PositionSearchResponse(BobModel):
    """Response from position search."""

    positions: list[Position] = Field(default_factory=list)


class PositionOpeningSearchResponse(BobModel):
    """Response from position opening search."""

    openings: list[PositionOpening] = Field(default_factory=list)


class PositionBudgetSearchResponse(BobModel):
    """Response from position budget search."""

    budgets: list[PositionBudget] = Field(default_factory=list)
