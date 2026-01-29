"""Models for the Attendance API domain."""

from datetime import date, datetime
from typing import Any

from pydantic import Field

from pybob_sdk._core.base_model import BobModel


# Project Models
class ProjectMetadata(BobModel):
    """Metadata for a project field."""

    id: str | None = None
    name: str | None = None
    type: str | None = None
    description: str | None = None


class Project(BobModel):
    """A project."""

    id: str | None = None
    name: str | None = None
    description: str | None = None
    status: str | None = None
    client_id: str | None = Field(default=None, alias="clientId")
    client_name: str | None = Field(default=None, alias="clientName")
    start_date: date | None = Field(default=None, alias="startDate")
    end_date: date | None = Field(default=None, alias="endDate")
    budget_hours: float | None = Field(default=None, alias="budgetHours")
    billable: bool = False


class ProjectSearchRequest(BobModel):
    """Request body for searching projects."""

    filters: list[dict[str, Any]] = Field(default_factory=list)
    fields: list[str] = Field(default_factory=list)


class ProjectCreateRequest(BobModel):
    """Request body for creating a project."""

    name: str
    description: str | None = None
    client_id: str | None = Field(default=None, alias="clientId")
    start_date: date | None = Field(default=None, alias="startDate")
    end_date: date | None = Field(default=None, alias="endDate")
    budget_hours: float | None = Field(default=None, alias="budgetHours")
    billable: bool = False


class ProjectUpdateRequest(BobModel):
    """Request body for updating a project."""

    name: str | None = None
    description: str | None = None
    client_id: str | None = Field(default=None, alias="clientId")
    start_date: date | None = Field(default=None, alias="startDate")
    end_date: date | None = Field(default=None, alias="endDate")
    budget_hours: float | None = Field(default=None, alias="budgetHours")
    billable: bool | None = None


# Project Client Models
class ProjectClient(BobModel):
    """A project client."""

    id: str | None = None
    name: str | None = None
    description: str | None = None


class ProjectClientMetadata(BobModel):
    """Metadata for project clients."""

    fields: list[dict[str, Any]] = Field(default_factory=list)


# Project Task Models
class ProjectTask(BobModel):
    """A project task."""

    id: str | None = None
    name: str | None = None
    description: str | None = None
    project_id: str | None = Field(default=None, alias="projectId")
    status: str | None = None


class ProjectTaskMetadata(BobModel):
    """Metadata for project tasks."""

    fields: list[dict[str, Any]] = Field(default_factory=list)


class ProjectTaskCreateRequest(BobModel):
    """Request body for creating a project task."""

    name: str
    project_id: str = Field(alias="projectId")
    description: str | None = None


class ProjectTaskUpdateRequest(BobModel):
    """Request body for updating a project task."""

    name: str | None = None
    description: str | None = None


# Attendance Models
class AttendanceEntry(BobModel):
    """An attendance entry for import."""

    employee_id: str = Field(alias="employeeId")
    entry_date: date = Field(alias="date")
    clock_in: str | None = Field(default=None, alias="clockIn")
    clock_out: str | None = Field(default=None, alias="clockOut")
    project_id: str | None = Field(default=None, alias="projectId")
    task_id: str | None = Field(default=None, alias="taskId")
    hours: float | None = None


class AttendanceImportRequest(BobModel):
    """Request body for importing attendance data."""

    entries: list[AttendanceEntry] = Field(default_factory=list)
    override_conflicts: bool = Field(default=False, alias="overrideConflicts")


class AttendanceSummaryRequest(BobModel):
    """Request body for fetching attendance summaries."""

    employee_ids: list[str] = Field(default_factory=list, alias="employeeIds")
    from_date: date = Field(alias="fromDate")
    to_date: date = Field(alias="toDate")


class AttendanceSummary(BobModel):
    """An attendance summary for an employee."""

    employee_id: str | None = Field(default=None, alias="employeeId")
    total_hours: float | None = Field(default=None, alias="totalHours")
    regular_hours: float | None = Field(default=None, alias="regularHours")
    overtime_hours: float | None = Field(default=None, alias="overtimeHours")
    days_worked: int | None = Field(default=None, alias="daysWorked")


class AttendanceBreakdownRequest(BobModel):
    """Request body for fetching attendance breakdown."""

    employee_ids: list[str] = Field(default_factory=list, alias="employeeIds")
    from_date: date = Field(alias="fromDate")
    to_date: date = Field(alias="toDate")


class DailyAttendanceEntry(BobModel):
    """A daily attendance entry."""

    entry_date: date | None = Field(default=None, alias="date")
    clock_in: datetime | None = Field(default=None, alias="clockIn")
    clock_out: datetime | None = Field(default=None, alias="clockOut")
    total_hours: float | None = Field(default=None, alias="totalHours")
    project_id: str | None = Field(default=None, alias="projectId")
    task_id: str | None = Field(default=None, alias="taskId")


class AttendanceBreakdown(BobModel):
    """Attendance breakdown for an employee."""

    employee_id: str | None = Field(default=None, alias="employeeId")
    entries: list[DailyAttendanceEntry] = Field(default_factory=list)


# Response Models
class ProjectSearchResponse(BobModel):
    """Response from project search."""

    projects: list[Project] = Field(default_factory=list)


class ProjectClientSearchResponse(BobModel):
    """Response from project client search."""

    clients: list[ProjectClient] = Field(default_factory=list)


class ProjectTaskSearchResponse(BobModel):
    """Response from project task search."""

    tasks: list[ProjectTask] = Field(default_factory=list)


class AttendanceSummaryResponse(BobModel):
    """Response from attendance summary request."""

    summaries: list[AttendanceSummary] = Field(default_factory=list)


class AttendanceBreakdownResponse(BobModel):
    """Response from attendance breakdown request."""

    employees: list[AttendanceBreakdown] = Field(default_factory=list)
