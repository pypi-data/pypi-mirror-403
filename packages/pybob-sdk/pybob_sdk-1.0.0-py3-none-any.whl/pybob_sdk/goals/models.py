"""Models for the Goals API domain."""

from datetime import date
from typing import Any

from pydantic import Field

from pybob_sdk._core.base_model import BobModel


# Metadata Models
class GoalTypeMetadata(BobModel):
    """Metadata for goal types."""

    fields: list[dict[str, Any]] = Field(default_factory=list)


class GoalMetadata(BobModel):
    """Metadata for goals."""

    fields: list[dict[str, Any]] = Field(default_factory=list)


class KeyResultMetadata(BobModel):
    """Metadata for key results."""

    fields: list[dict[str, Any]] = Field(default_factory=list)


class GoalCycleMetadata(BobModel):
    """Metadata for goal cycles."""

    fields: list[dict[str, Any]] = Field(default_factory=list)


# Goal Type Models
class GoalType(BobModel):
    """A goal type."""

    id: str | None = None
    name: str | None = None
    description: str | None = None


class GoalTypeSearchRequest(BobModel):
    """Request body for searching goal types."""

    filters: list[dict[str, Any]] = Field(default_factory=list)
    fields: list[str] = Field(default_factory=list)


# Goal Models
class Goal(BobModel):
    """A goal in Bob."""

    id: str | None = None
    name: str | None = None
    description: str | None = None
    owner_id: str | None = Field(default=None, alias="ownerId")
    owner_name: str | None = Field(default=None, alias="ownerName")
    goal_type_id: str | None = Field(default=None, alias="goalTypeId")
    goal_type_name: str | None = Field(default=None, alias="goalTypeName")
    cycle_id: str | None = Field(default=None, alias="cycleId")
    cycle_name: str | None = Field(default=None, alias="cycleName")
    start_date: date | None = Field(default=None, alias="startDate")
    end_date: date | None = Field(default=None, alias="endDate")
    status: str | None = None
    progress: float | None = None
    parent_goal_id: str | None = Field(default=None, alias="parentGoalId")


class GoalSearchRequest(BobModel):
    """Request body for searching goals."""

    filters: list[dict[str, Any]] = Field(default_factory=list)
    fields: list[str] = Field(default_factory=list)


class GoalCreateRequest(BobModel):
    """Request body for creating a goal."""

    name: str
    description: str | None = None
    owner_id: str = Field(alias="ownerId")
    goal_type_id: str | None = Field(default=None, alias="goalTypeId")
    cycle_id: str | None = Field(default=None, alias="cycleId")
    start_date: date | None = Field(default=None, alias="startDate")
    end_date: date | None = Field(default=None, alias="endDate")
    parent_goal_id: str | None = Field(default=None, alias="parentGoalId")


class GoalUpdateRequest(BobModel):
    """Request body for updating a goal."""

    name: str | None = None
    description: str | None = None
    start_date: date | None = Field(default=None, alias="startDate")
    end_date: date | None = Field(default=None, alias="endDate")


class GoalStatusUpdateRequest(BobModel):
    """Request body for updating a goal's status."""

    status: str


# Key Result Models
class KeyResult(BobModel):
    """A key result for a goal."""

    id: str | None = None
    goal_id: str | None = Field(default=None, alias="goalId")
    name: str | None = None
    description: str | None = None
    target: float | None = None
    current: float | None = None
    unit: str | None = None
    progress: float | None = None


class KeyResultSearchRequest(BobModel):
    """Request body for searching key results."""

    filters: list[dict[str, Any]] = Field(default_factory=list)
    fields: list[str] = Field(default_factory=list)


class KeyResultCreateRequest(BobModel):
    """Request body for creating a key result."""

    goal_id: str = Field(alias="goalId")
    name: str
    description: str | None = None
    target: float
    current: float | None = None
    unit: str | None = None


class KeyResultUpdateRequest(BobModel):
    """Request body for updating a key result."""

    name: str | None = None
    description: str | None = None
    target: float | None = None
    unit: str | None = None


class KeyResultProgressUpdateRequest(BobModel):
    """Request body for updating a key result's progress."""

    current: float


# Goal Cycle Models
class GoalCycle(BobModel):
    """A goal cycle."""

    id: str | None = None
    name: str | None = None
    start_date: date | None = Field(default=None, alias="startDate")
    end_date: date | None = Field(default=None, alias="endDate")
    status: str | None = None


class GoalCycleSearchRequest(BobModel):
    """Request body for searching goal cycles."""

    filters: list[dict[str, Any]] = Field(default_factory=list)
    fields: list[str] = Field(default_factory=list)


# Response Models
class GoalTypeSearchResponse(BobModel):
    """Response from goal type search."""

    goal_types: list[GoalType] = Field(default_factory=list, alias="goalTypes")


class GoalSearchResponse(BobModel):
    """Response from goal search."""

    goals: list[Goal] = Field(default_factory=list)


class KeyResultSearchResponse(BobModel):
    """Response from key result search."""

    key_results: list[KeyResult] = Field(default_factory=list, alias="keyResults")


class GoalCycleSearchResponse(BobModel):
    """Response from goal cycle search."""

    cycles: list[GoalCycle] = Field(default_factory=list)
