"""Models for the Tasks API domain."""

from datetime import date, datetime

from pydantic import Field, field_validator

from pybob_sdk._core.base_model import BobModel


class Task(BobModel):
    """A task in Bob."""

    id: str | None = None
    employee_id: str | None = Field(default=None, alias="employeeId")
    title: str | None = None
    description: str | None = None
    task_type: str | None = Field(default=None, alias="taskType")
    status: str | None = None
    due_date: date | None = Field(default=None, alias="dueDate")
    created_at: datetime | None = Field(default=None, alias="createdAt")
    completed_at: datetime | None = Field(default=None, alias="completedAt")
    owner_id: str | None = Field(default=None, alias="ownerId")
    owner_display_name: str | None = Field(default=None, alias="ownerDisplayName")

    @field_validator("id", "employee_id", "owner_id", mode="before")
    @classmethod
    def coerce_id_to_string(cls, v: int | str | None) -> str | None:
        """Coerce ID to string if it's an integer."""
        if v is None:
            return None
        return str(v)


class TaskCompleteRequest(BobModel):
    """Request body for completing a task."""

    task_id: str = Field(alias="taskId")


class TasksResponse(BobModel):
    """Response containing tasks."""

    tasks: list[Task] = Field(default_factory=list)
